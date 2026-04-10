# DevOps 스킬 코드/설계 리뷰

---

## 1. 구조 분석

### 디렉토리 구조

```
devops/
├── skills.yaml
├── agents/          (8개 파일: slo, iac, pipeline, strategy, monitor, log, incident, review)
├── prompts/         (8개 파일: 동일 구성)
├── examples/        (16개 파일: 에이전트당 input/output 쌍)
```

**긍정적인 점**: 에이전트 8개에 대해 agent 정의, prompt, example이 1:1:1로 대응되어 구조적 일관성이 확보되어 있다. 타 스킬(arch, impl)과 비교했을 때 동일한 디렉토리 컨벤션을 따르고 있다.

**문제점**:

- **에이전트 수 과다 (8개)**: arch 스킬은 agent 2개(design, review), impl은 2개(generate, review)인 반면, devops는 8개로 급격히 팽창했다. 이는 DevOps 영역의 복잡성을 반영한 것일 수 있으나, 8개 에이전트 간의 의존성 체인이 skills.yaml의 pipeline 섹션에서 보이듯 매우 복잡하다. 실제 오케스트레이션 엔진이 이 수준의 DAG를 안정적으로 실행할 수 있는지 의문이다.
- **review.md 파일명 충돌**: `agents/review.md`가 에이전트 정의 파일인데, 이 리뷰 파일(`review.md`)과 혼동 가능성이 있다. 실질적인 문제는 아니지만, 네이밍에 주의가 필요하다.

---

## 2. skills.yaml 분석

### 완성도

skills.yaml은 430줄 이상으로, 타 스킬 대비 가장 방대하다. 다음 요소를 포함한다:

- 스킬 메타데이터 (name, version, description)
- execution_model, adaptive_depth
- supported_platforms
- 8개 에이전트 정의 (input/output 스키마 포함)
- pipeline (실행 순서, 의존성, 피드백 루프)
- predecessors, consumers

### 문제점

#### 2-1. execution_model의 비현실성

```yaml
execution_model: auto-execute-with-escalation
```

"선행 스킬에서 의사결정이 완료된 상태이므로 자동 실행"이라고 주석되어 있으나, 실제로는:

- IaC 에이전트가 클라우드 리소스를 매핑할 때 ambiguity가 빈번하다 (예: ECS vs EKS 선택)
- Pipeline 에이전트가 CI 플랫폼을 "기술 스택 맥락에 따라" 자동 결정한다고 하지만, 실제로는 조직의 기존 인프라에 따라 결정되는 경우가 대부분이다
- 8개 에이전트 전부 `interaction_mode: auto`인 것은 현실적이지 않다. 적어도 IaC와 Pipeline은 사용자 확인이 필요한 결정이 다수 존재한다.

#### 2-2. adaptive_depth의 이분법적 기준

```yaml
adaptive_depth:
  lightweight:
    trigger: "Arch 컴포넌트 ≤ 3개, 단일 배포 환경"
  heavyweight:
    trigger: "Arch 컴포넌트 > 3개 또는 멀티 환경/리전"
```

컴포넌트 3개라는 기준이 자의적이다. 컴포넌트 3개이지만 멀티 리전인 경우, 컴포넌트 4개이지만 단순한 CRUD인 경우 등을 적절히 분류하지 못한다. 또한 이 adaptive_depth가 개별 에이전트에는 정의되어 있지 않고 스킬 레벨에서만 정의되어 있어서, 각 에이전트가 경량/중량 모드를 어떻게 반영하는지 명시되어 있지 않다.

#### 2-3. supported_platforms의 용도 불명확

```yaml
supported_platforms:
  ci_cd: [github-actions, jenkins, gitlab-ci]
  iac: [terraform, ansible, helm, pulumi]
  cloud: [aws, gcp, azure]
  monitoring: [prometheus, grafana, datadog, cloudwatch]
  logging: [elk, loki, cloudwatch-logs]
```

이 목록이 "지원한다"는 선언인지, "이 중에서 선택한다"는 제약인지 모호하다. 또한 에이전트 정의나 프롬프트에서 이 목록을 직접 참조하는 메커니즘이 없다. 단순한 문서화 용도라면 불필요한 복잡성이다.

#### 2-4. pipeline.stages의 parallel_with 불일치

```yaml
- agent: monitor
  depends_on: [slo]
  parallel_with: [pipeline, strategy]
```

monitor는 `depends_on: [slo]`이고 `parallel_with: [pipeline, strategy]`인데, strategy는 `depends_on: [slo, pipeline]`이다. monitor와 strategy가 동시 실행 가능하려면 monitor는 pipeline에 의존하지 않아야 하는데, 실제로 monitor의 입력에 `strategy_output`이 `required: false`로 되어 있다. 이 설계가 의도된 것이라면, monitor가 strategy 없이 실행된 후 strategy 결과를 나중에 반영하는 메커니즘이 필요하지만, 그런 메커니즘은 기술되어 있지 않다.

#### 2-5. feedback_loops의 실행 메커니즘 부재

```yaml
feedback_loops:
  - from: strategy
    to: pipeline
    description: "배포 방식 결정 → pipeline 배포 스테이지에 역반영"
```

6개의 피드백 루프가 선언되어 있지만, 이것이 어떻게 실행되는지에 대한 메커니즘이 없다. strategy가 pipeline보다 나중에 실행되는데, strategy 결과를 pipeline에 "역반영"한다는 것은 pipeline을 다시 실행한다는 의미인가, 아니면 strategy가 pipeline 산출물을 수정한다는 의미인가? 전자라면 무한 루프 방지 전략이 필요하고, 후자라면 에이전트 간 산출물 수정 권한 문제가 발생한다.

#### 2-6. output 스키마의 불완전한 정의

IaC 에이전트의 output에서 `infrastructure_code`가 `type: object`이고 properties에 `id`, `tool`, `provider` 등이 있는데, 실제 예제 출력을 보면 이 구조와 정확히 대응되지 않는다. 예를 들어 `code_files` 필드가 스키마에 정의되어 있지만 예제에서는 "생성된 IaC 파일" 테이블로 제시되고 있다. 스키마와 실제 출력 형태 간의 매핑이 느슨하다.

#### 2-7. consumers 정의에서 참조하는 output 키 불일치

```yaml
consumers:
  - skill: management
    consumes: [pipeline_configuration, observability_configuration, operational_runbooks]
```

`observability_configuration`이라는 키는 에이전트 output에서 명시적으로 정의된 적이 없다. SLO 에이전트는 `slo_definitions`를, Monitor 에이전트는 `monitoring_rules` + `dashboards` + `tracing_config`를, Log 에이전트는 `logging_config`를 출력한다. 이것들을 묶어서 `observability_configuration`이라고 부르는 것은 암묵적이며, 이 통합 과정이 어디에서 이루어지는지 명시되어 있지 않다.

---

## 3. 에이전트 정의 분석

### 공통 구조적 문제

모든 8개 에이전트 파일이 동일한 구조를 따른다: 역할 -> 핵심 원칙 -> 핵심 역량 -> 실행 프로세스 -> 에스컬레이션 조건 -> 출력 형식. 이 일관성은 좋으나, 다음 문제가 있다:

#### 3-1. "당신은 ~전문가입니다" 패턴의 남용

8개 에이전트 모두 "당신은 [X] 전문가입니다"로 시작한다. 이 패턴이 LLM 프롬프팅에서 역할 부여에 유효한 것은 사실이나, 8개가 모두 동일 패턴이면 각 에이전트의 차별성을 약화시킨다. 특히 monitor, log, slo 에이전트가 모두 "관찰 가능성"이라는 유사한 영역을 다루는데, 이들 간의 경계가 역할 설명만으로는 명확하지 않다.

#### 3-2. 에스컬레이션 조건의 형식적 선언

각 에이전트가 에스컬레이션 조건과 템플릿을 포함하고 있지만, incident 에이전트의 경우:

```yaml
escalation_condition: "없음 — 다른 에이전트 산출물 기반 자동 생성. 품질은 review에서 검증"
```

에스컬레이션이 "없음"이면서도 에이전트 파일에는 에스컬레이션 관련 내용이 없다. 에스컬레이션 조건이 없는 에이전트는 이 필드 자체를 생략하는 것이 더 깔끔하다.

### 개별 에이전트 분석

#### SLO 에이전트 (`agents/slo.md`)

- **강점**: SLI 변환 패턴, 번-레이트 알림, 에러 버짓 정책이 체계적이다. Google SRE 방법론을 충실히 반영했다.
- **문제**: "컴포넌트별 SLO 분배"에서 `시스템 SLO^(1/n)` 공식은 모든 컴포넌트가 동일한 신뢰도라는 가정을 깔고 있다. 실제로는 컴포넌트별로 성숙도와 안정성이 다르므로 이 공식은 출발점일 뿐이다. 그런데 프롬프트에서는 이것을 확정적 공식처럼 제시한다.

#### IaC 에이전트 (`agents/iac.md`)

- **강점**: 컴포넌트 유형 -> 클라우드 리소스 매핑 테이블이 구체적이다.
- **문제**: AWS/GCP/Azure 3개 프로바이더를 모두 지원한다고 선언하지만, 예제는 AWS만 있다. 프롬프트와 에이전트 정의도 AWS에 편향되어 있다 (S3, DynamoDB locking 등). GCP/Azure를 지원한다는 주장의 실현 가능성이 의심스럽다.
- **문제**: 모듈 구조가 Terraform 기준으로만 예시되어 있다. Pulumi나 Ansible을 선택하면 완전히 다른 구조가 필요한데, 이에 대한 안내가 없다.

#### Pipeline 에이전트 (`agents/pipeline.md`)

- **강점**: Impl 산출물 필드와 파이프라인 적용의 매핑이 상세하다.
- **문제**: "후속 스킬 연동 지점"으로 `qa`와 `security` 스킬을 언급하지만, 이 연동이 placeholder인지 실제 인터페이스인지 불명확하다. 예제 출력에서도 "qa 스킬 연동 지점", "security 스킬 연동 지점"이라는 주석만 있을 뿐 구체적인 인터페이스 계약이 없다.

#### Strategy 에이전트 (`agents/strategy.md`)

- **강점**: 의사결정 트리가 명확하고, 배포 방식별 장단점이 정리되어 있다.
- **문제**: 의사결정 트리가 가용성 SLO만을 기준으로 한다. 성능 SLO(응답시간)나 데이터 지속성 SLO는 배포 전략에 영향을 주지 않는가? 예를 들어, 데이터 지속성 100% SLO가 있으면 DB 마이그레이션 전략이 크게 달라져야 하는데, 이 부분이 반영되지 않았다.

#### Monitor 에이전트 (`agents/monitor.md`)

- **강점**: RED/USE 프레임워크 적용, 알림 피로도 방지 설계가 실무적이다.
- **문제**: 출력에 `format: { type: string, enum: [grafana-json, datadog-json] }`이 있는데, 모니터링 도구 선택 기준이 에이전트 정의에 없다. Prometheus+Grafana vs Datadog 선택이 어디에서 결정되는지 불명확하다. `supported_platforms.monitoring`에 4개 도구가 나열되어 있지만, 이것이 에이전트의 선택 기준과 어떻게 연결되는지 경로가 없다.

#### Log 에이전트 (`agents/log.md`)

- **강점**: 민감 정보 마스킹 규칙, 보존 정책이 실무적이다.
- **문제**: Log 에이전트의 입력에 `slo_output`이 없다. 그런데 로그 기반 메트릭을 monitor에 제공한다고 하면서, SLO 기준을 알지 못한 채 어떤 메트릭이 중요한지 어떻게 판단하는가? pipeline에서도 마찬가지로, SLO와의 직접적인 연결 없이 운영된다.

#### Incident 에이전트 (`agents/incident.md`)

- **강점**: 런북 구조, 에스컬레이션 매트릭스, 커뮤니케이션 템플릿, 포스트모템 템플릿 등 실무 운영에 필요한 요소를 포괄한다.
- **문제**: "알림-런북 1:1 매핑"이라는 원칙이 있는데, 실제로는 하나의 런북이 여러 알림에 대응하거나, 하나의 알림이 여러 런북을 트리거하는 경우가 더 일반적이다. 예제에서도 RB-005가 MON-012와 MON-013 두 개에 연결되어 있어 이미 1:1이 아니다. 원칙과 현실이 괴리된다.

#### Review 에이전트 (`agents/review.md`)

- **강점**: 배포-관찰 피드백 루프 검증, 추적성 검증 체크리스트가 체계적이다.
- **문제**: "자동 수정"이라는 개념이 반복적으로 등장하지만, 에이전트가 다른 에이전트의 산출물을 어떻게 수정하는지 메커니즘이 전혀 없다. Review 에이전트가 "monitor에 누락 규칙 추가 요청"을 한다는데, 이 요청은 어떤 프로토콜로 전달되고, monitor 에이전트가 이미 실행 완료된 상태에서 어떻게 재실행되는가? 오케스트레이션 레벨의 설계가 빠져 있다.

---

## 4. 프롬프트 분석

### 공통 구조

모든 프롬프트가 동일 구조를 따른다: 입력 (템플릿 변수) -> 지시사항 (Step 1~N) -> 주의사항.

#### 4-1. 에이전트 정의와 프롬프트의 과도한 중복

`agents/slo.md`와 `prompts/slo.md`를 비교하면, 프롬프트가 에이전트 정의의 내용을 거의 그대로 반복한다. 예:

- 에이전트: "RE 품질 속성 → SLI 변환" 테이블 -> 프롬프트: "Step 2: SLI 변환" 동일 테이블
- 에이전트: "번-레이트 알림" 설정 -> 프롬프트: "Step 5: 번-레이트 알림 설계" 동일 내용
- 에이전트: "에러 버짓 정책" -> 프롬프트: "Step 6: 에러 버짓 정책" 동일 내용

이 구조는 LLM에게 system prompt(에이전트 정의)와 user prompt(프롬프트 템플릿) 두 곳에서 동일 지시를 반복하는 것이다. 토큰 낭비일 뿐 아니라, 두 곳의 내용이 diverge하면 혼란을 야기한다. **에이전트 정의는 "이 에이전트가 무엇인가"를, 프롬프트는 "지금 이 입력으로 무엇을 하라"를 담아야 하는데**, 현재는 둘 다 "무엇을 하라"를 담고 있다.

#### 4-2. 템플릿 변수의 형식 불일치

프롬프트의 입력 섹션:

```
Arch 산출물: {{arch_output}}
Impl 산출물: {{impl_output}}
```

이것이 Jinja2 스타일 템플릿 변수인지, 단순 placeholder인지 명시가 없다. 또한 `{{arch_output}}`이 어떤 형식(JSON, YAML, Markdown)으로 주입되는지 정의가 없다. skills.yaml의 input 스키마는 `type: object`로 정의되어 있지만, 실제 프롬프트에 주입될 때의 직렬화 형식이 불명확하다.

#### 4-3. "~하세요" vs "~합니다" 혼재

프롬프트에서는 "변환하세요", "생성하세요" (명령형)를 사용하고, 에이전트에서는 "변환합니다", "생성합니다" (서술형)를 사용한다. 의도된 구분이라면 나쁘지 않으나, 일부 에이전트 파일에서도 "~하세요"가 섞여 있다.

---

## 5. 예제 분석

### 전체 평가

16개 예제 파일(8 input + 8 output)이 모두 **동일한 "온라인 주문 처리 시스템"** 시나리오를 사용한다. 이것은 예제 간 일관성을 확보하는 데 유리하지만, 다음 문제가 있다:

#### 5-1. 단일 시나리오의 한계

"컴포넌트 5개, AWS, ECS Fargate, Node.js 모노레포" 하나의 시나리오만으로는 다음을 커버하지 못한다:

- 서버리스 아키텍처 (Lambda, Cloud Functions)
- 멀티 리전 배포
- 경량 모드 (adaptive_depth.lightweight) 시나리오
- GCP/Azure 프로바이더
- Jenkins/GitLab CI 플랫폼
- Pulumi/Ansible 도구
- 마이크로서비스가 아닌 모놀리식 아키텍처

`supported_platforms`에서 선언한 도구의 90% 이상이 예제에서 커버되지 않는다. 이는 선언만 하고 실제 지원하지 않는다는 의심을 강화한다.

#### 5-2. "모든 것이 완벽한" 예제

review-output.md에서:

```
배포-관찰 피드백 루프: 완전 (6/6)
선행 스킬 추적성: 완전 (5/5)
에스컬레이션 항목: (해당 없음)
자동 수정 내역: (해당 없음)
```

모든 항목이 통과하는 예제만 있으면, 실패 시나리오(에스컬레이션 발동, 자동 수정 실행, 선행 스킬 계약 위반)를 LLM이 학습할 수 없다. **실패 예제가 성공 예제보다 더 중요하다.** Review 에이전트의 핵심 역량인 "자동 수정"과 "에스컬레이션"이 예제에서 한 번도 시연되지 않는다.

#### 5-3. SLO-003 에러 버짓 "-" 처리

slo-output.md에서:

```
| SLO-003 | ... | ≥ 500/s | 30d | - | QA:scalability | COMP-002, COMP-005 |
```

처리량 SLO의 에러 버짓이 "-"로 되어 있다. 처리량도 에러 버짓을 정의할 수 있는데 (예: "목표 대비 10% 미달 시간"), 왜 "-"인지 설명이 없다. 에이전트 정의에서도 처리량 SLO의 에러 버짓 처리 방법에 대한 가이드가 없다.

#### 5-4. pipeline-output.md의 YAML 오류

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  push:           # 중복 키!
    tags: ['v*']
```

YAML에서 동일 키(`push`)가 두 번 등장하면 나중 것이 이전 것을 덮어쓴다. 이 예제를 그대로 사용하면 `push to main` 트리거가 사라진다. 실제 GitHub Actions에서는 이것이 문법 오류가 아니라 silent override이므로 디버깅이 어려운 버그다. 예제가 "실행 가능한 수준"이어야 한다는 원칙을 에이전트가 스스로 위반하고 있다.

#### 5-5. 스테이지 수 불일치

pipeline-output.md의 파이프라인 설정에서 "스테이지 수: 8"이라고 하면서, 스테이지 상세 테이블에는 9개 행(Setup, Install, Build, Test, Security Scan, Package, Deploy dev, Deploy staging, Deploy prod)이 있다.

#### 5-6. 비용 추정의 현실성

iac-output.md에서:

```
| dev | $150 ~ $200 | ECS Fargate ($50), RDS ($30), NAT Gateway ($35), 기타 |
```

2024년 기준 NAT Gateway는 $35/월이 아니라 시간당 $0.045 + 데이터 처리 비용으로, 최소 $32~$45 정도다. ECS Fargate 0.25 vCPU / 512MB 1개가 $50/월이라는 것도 과다 추정이다 (실제로는 약 $10/월). 비용 추정이 부정확하면 이 산출물의 신뢰성 전체가 의심된다.

---

## 6. 일관성 검토

#### 6-1. 출력 키 명칭 불일치

| 위치 | 사용하는 키 |
|------|-----------|
| skills.yaml SLO output | `slo_definitions` |
| skills.yaml consumers | `observability_configuration` |
| SLO 에이전트 실행 프로세스 | `observability_configuration.slo_definitions` |
| Monitor 에이전트 실행 프로세스 | `observability_configuration 모니터링 부분` |
| Log 에이전트 실행 프로세스 | `observability_configuration 로깅 부분` |

`observability_configuration`이라는 상위 키가 어디에서도 정의되지 않았는데, SLO/Monitor/Log 에이전트는 이 키 아래에 자신의 출력을 넣으라고 말한다. skills.yaml의 각 에이전트 output 스키마에는 이 상위 키가 없다.

#### 6-2. ID 패턴의 불일치

| 에이전트 | ID 패턴 (스키마) | 예제에서 사용 |
|---------|----------------|-------------|
| SLO | `^SLO-\d{3}$` | SLO-001~004 (일치) |
| IaC | `^IAC-\d{3}$` | IAC-001 (일치) |
| Pipeline | `^PL-\d{3}$` | PL-001 (일치) |
| Monitor | `^MON-\d{3}$` | MON-001~016 (일치) |
| Incident | `^RB-\d{3}$` | RB-001~007 (일치) |
| Dashboard | `^DASH-\d{3}$` | DASH-001~006 (일치) |

ID 패턴은 일관적이다. 이 부분은 잘 설계되어 있다.

#### 6-3. 에이전트 간 입력 참조의 비대칭

- IaC는 `arch_output` + `slo_output`을 받는다
- Pipeline은 `impl_output` + `iac_output`을 받는다 (arch_output 없음)
- Strategy는 `slo_output` + `arch_output` + `pipeline_output`을 받는다
- Monitor는 `slo_output` + `arch_output` + `strategy_output`(optional)을 받는다
- Log는 `arch_output` + `iac_output`을 받는다 (slo_output 없음)
- Incident는 `strategy_output` + `monitor_output` + `arch_output` + `iac_output`을 받는다

Pipeline이 `arch_output`을 직접 받지 않는 것은 문제다. Pipeline의 output 스키마에 `arch_refs`가 있고, 예제에서도 `COMP-001~005`를 참조하는데, 이 정보를 어디서 얻는가? `iac_output`을 통해 간접적으로 얻을 수 있지만, 이는 IaC 에이전트가 arch 정보를 passthrough해야 한다는 암묵적 계약이다.

---

## 7. 주요 문제점 (심각도 순)

### [Critical] C1. 피드백 루프와 자동 수정의 실행 메커니즘 부재

6개의 피드백 루프와 review 에이전트의 "자동 수정" 기능이 선언만 되어 있고, 실행 메커니즘이 전혀 없다. 이것은 이 스킬의 핵심 차별점("배포와 관찰을 하나의 피드백 루프로 통합")이 사실상 구현되지 않았다는 의미다.

### [Critical] C2. 에이전트 정의와 프롬프트의 과도한 중복

8쌍의 에이전트-프롬프트 파일에서 내용의 60~70%가 동일하다. 이는 유지보수 부담을 2배로 만들고, 두 곳이 diverge할 리스크를 만든다.

### [High] H1. 단일 시나리오 예제로 인한 커버리지 부족

선언된 지원 범위(3개 클라우드, 3개 CI/CD, 4개 IaC, 4개 모니터링)의 대부분이 예제에서 검증되지 않는다.

### [High] H2. 모든 것이 auto 모드인 비현실적 실행 모델

8개 에이전트 전부가 `interaction_mode: auto`이고, `checkpoint: false`(review만 true)인 것은 현실의 DevOps 의사결정 과정과 괴리된다.

### [High] H3. pipeline-output.md의 YAML 중복 키 오류

예제가 실제로 실행 불가능한 YAML을 포함하고 있어 예제의 신뢰성을 훼손한다.

### [Medium] M1. supported_platforms 선언과 실제 구현의 괴리

### [Medium] M2. 에이전트 간 입력/출력 계약의 암묵적 의존성

### [Medium] M3. observability_configuration 상위 키 미정의

### [Low] L1. adaptive_depth가 에이전트 레벨에서 미반영

### [Low] L2. 비용 추정 수치의 부정확성

---

## 8. 개선 제안

### 8-1. 에이전트-프롬프트 역할 분리 (C2 해결)

**현재**: 에이전트 정의 = 역할 + 역량 + 절차 + 에스컬레이션 + 출력형식, 프롬프트 = 입력 + 동일 절차 반복 + 주의사항

**제안**: 에이전트 정의는 "이 에이전트가 무엇인지" (역할, 원칙, 역량 테이블, 에스컬레이션 조건)만 담고, 프롬프트는 "이 입력으로 무엇을 생성하라" (입력 참조, 출력 형식 명시, 주의사항)만 담는다. 절차(Step 1~N)는 한 곳에만 존재해야 한다.

### 8-2. 피드백 루프 실행 프로토콜 정의 (C1 해결)

skills.yaml의 `feedback_loops` 섹션에 실행 프로토콜을 추가:

```yaml
feedback_loops:
  - from: strategy
    to: pipeline
    mechanism: output_merge  # strategy가 pipeline 산출물의 deploy 섹션을 직접 수정
    conflict_resolution: strategy_wins  # 충돌 시 strategy 우선
```

또는, 피드백이 실제로는 "strategy가 pipeline의 deploy 스테이지를 자체적으로 생성한다"는 의미라면, 그렇게 명시하고 pipeline 에이전트의 책임 범위를 "배포 스테이지 제외"로 축소한다.

### 8-3. 실패 시나리오 예제 추가 (H1 부분 해결)

최소한 다음 예제를 추가해야 한다:

- Review에서 에스컬레이션이 발동하는 경우 (Arch 컴포넌트 미매핑)
- Review에서 자동 수정이 실행되는 경우 (Monitor-Incident 누락 연결)
- IaC에서 에스컬레이션이 발동하는 경우 (관리형 서비스 미제공)
- 경량 모드 시나리오 (컴포넌트 2~3개)

### 8-4. auto 모드 재검토 (H2 해결)

최소한 IaC와 Pipeline 에이전트는 `interaction_mode: auto-with-confirmation`으로 변경하여, 클라우드 프로바이더/CI 플랫폼 선택과 같은 고영향 결정에서 사용자 확인을 받도록 한다. 또는, 이미 Arch/Impl에서 확정된 결정이라면 그 결정이 어떤 필드에서 전달되는지를 명시적으로 문서화한다.

### 8-5. YAML 예제 수정 (H3 해결)

pipeline-output.md의 트리거 설정을 수정:

```yaml
on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]
```

### 8-6. supported_platforms를 에이전트 결정 로직에 연결 (M1 해결)

현재 `supported_platforms`가 선언만 되어 있으므로, 각 에이전트의 프롬프트에서 이 목록을 참조하여 도구 선택을 하도록 연결한다. 또는, 현실적으로 AWS + Terraform + GitHub Actions만 충분히 지원할 수 있다면, supported_platforms를 축소하고 나머지는 "향후 지원 예정"으로 명시하는 것이 정직하다.

### 8-7. 에이전트 수 축소 검토

현재 8개 에이전트를 기능적 응집도 기준으로 재그룹핑할 수 있다:

- **Observe**: SLO + Monitor + Log를 하나로 통합 (관찰 가능성 전체)
- **Deploy**: IaC + Pipeline + Strategy를 하나로 통합 (배포 인프라 전체)
- **Operate**: Incident 유지
- **Review**: 유지

이렇게 하면 4개 에이전트로 줄이면서 에이전트 간 의존성이 단순해지고, 피드백 루프도 줄어든다. 다만, 각 에이전트의 프롬프트가 길어지는 트레이드오프가 있다.

### 8-8. 출력 스키마와 예제의 정합성 검증

skills.yaml의 output 스키마와 예제 출력이 1:1로 대응되는지 자동 검증하는 스크립트를 추가한다. 현재 `observability_configuration`처럼 암묵적 키가 존재하는 상태를 해소한다.

---

## 총평

DevOps 스킬은 야심찬 설계를 보여준다. SLO 기반 의사결정, 배포-관찰 피드백 루프, 선행 스킬 추적성 등 DevOps/SRE 영역의 핵심 개념을 체계적으로 구조화한 점은 인상적이다. 그러나 **선언과 구현 사이의 격차**가 가장 큰 문제다. 6개 피드백 루프, 자동 수정, 멀티 클라우드/도구 지원 등이 선언만 되어 있고 실행 메커니즘이 없다. 에이전트 정의와 프롬프트 간의 과도한 중복은 유지보수 비용을 불필요하게 높이고, 단일 시나리오만의 예제는 스킬의 범용성 주장을 뒷받침하지 못한다. 에이전트 8개의 복잡한 DAG는 오케스트레이션 엔진의 안정적 실행이 전제되어야 하는데, 그 전제가 검증되지 않은 상태에서 이 수준의 복잡성은 리스크다.
