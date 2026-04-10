# Sec 스킬 코드/설계 리뷰

## 1. 구조 분석

### 디렉토리 구조

```
sec/
├── skills.yaml
├── agents/
│   ├── audit.md
│   ├── compliance.md
│   ├── review.md
│   └── threat-model.md
├── prompts/
│   ├── audit.md
│   ├── compliance.md
│   ├── review.md
│   └── threat-model.md
└── examples/
    ├── audit-input.md / audit-output.md
    ├── compliance-input.md / compliance-output.md
    ├── review-input.md / review-output.md
    └── threat-model-input.md / threat-model-output.md
```

**양호한 점**: 4개 에이전트 모두 agent/prompt/example이 1:1:1로 대응되며, 다른 스킬(arch, impl)과 구조적으로 일관된다. 파일 네이밍이 에이전트 이름과 정확히 일치한다.

**문제점 없음**: 구조 자체는 깔끔하다. 굳이 지적하자면, examples/ 디렉토리의 파일이 8개로 가장 많은데, 이는 4개 에이전트 x (input + output) 구조이므로 합리적이다.

---

## 2. skills.yaml 분석

### 2.1 과도한 스키마 정의 (Over-specification)

**심각도: 중간**

skills.yaml이 **436줄**에 달한다. 이 파일은 에이전트 정의, 입출력 스키마, 파이프라인, 적응적 깊이, 보안 표준 목록, 심각도 분류, 의존성 관계까지 모든 것을 한 파일에 담고 있다.

문제는 이 YAML 파일에 정의된 스키마가 **런타임에서 실제로 검증되는지 불명확하다**는 것이다. `pattern: "^AD-\\d{3}$"` 같은 정규식, `enum` 제약, `minimum/maximum` 같은 검증 규칙이 YAML에 선언되어 있지만, 이를 실제로 파싱하고 검증하는 코드가 harness 프레임워크에 존재하는지 확인이 필요하다. 만약 단순히 "문서화 목적"이라면, 이 수준의 스키마 정의는 과도한 엔지니어링이며 유지보수 부담만 증가시킨다.

### 2.2 adaptive_depth 중복 정의

**심각도: 중간**

`adaptive_depth`가 두 곳에 정의되어 있다:
1. `agents.threat-model.adaptive_depth` (라인 18-24)
2. 최상위 `adaptive_depth` (라인 370-376)

두 정의의 내용이 다르다. 최상위 adaptive_depth는 스킬 전체 수준이고, threat-model 에이전트의 adaptive_depth는 해당 에이전트 전용이다. 그런데 **다른 세 에이전트(audit, review, compliance)에는 adaptive_depth가 없다**. audit 에이전트가 경량/중량 모드에 따라 감사 범위를 달리해야 한다면, 에이전트별 adaptive_depth가 필요하다. 현재는 threat-model만 있고 나머지는 없어서 일관성이 없다.

### 2.3 input 스키마의 비대칭적 상세도

**심각도: 낮음**

threat-model과 audit의 input은 필드별 `type`, `pattern`, `enum`까지 상세하게 정의되어 있는 반면, review와 compliance의 input은 `type`과 `description`만 있는 간략한 정의다. 예를 들어:

```yaml
# review의 input — 간략
implementation_map:
  type: array
  required: true
  description: "Impl generate 산출물 — 코드 모듈 매핑"

# audit의 input — 상세
implementation_map:
  type: array
  required: true
  description: "Impl generate 산출물 — Arch 컴포넌트와 코드 모듈 매핑"
  items:
    id: { type: string, pattern: "^IM-\\d{3}$" }
    ...
```

review와 compliance는 이전 에이전트의 산출물을 그대로 받으므로 스키마를 재정의할 필요가 없다는 논리일 수 있지만, 파일 내에서 일관성이 깨진다. "산출물은 앞 에이전트의 output 스키마를 참조한다"는 규칙이 명시되어 있지 않으므로 혼란스럽다.

### 2.4 pipeline 정의에서 의존 관계 암묵적

**심각도: 낮음**

pipeline.stages는 순서만 정의하고, 각 단계의 입력이 어느 단계의 출력에서 오는지 명시적으로 선언하지 않는다. 예를 들어 review 에이전트는 threat-model의 `threat_model`과 audit의 `vulnerability_report`를 모두 필요로 하지만, 이 의존 관계는 pipeline이 아닌 review의 input에서만 유추할 수 있다. `depends_on: [threat-model, audit]` 같은 명시적 선언이 있으면 파이프라인 실행 엔진이 의존성을 자동으로 해석할 수 있다.

### 2.5 consumers 섹션의 실효성

**심각도: 낮음**

`consumers` 섹션이 devops, qa, impl, arch가 sec의 어떤 산출물을 소비하는지 정의하고 있다. 그런데 이 정보가 **소비자 측 skills.yaml에서도 동일하게 정의되는지, 아니면 sec 측에서만 일방적으로 선언하는지** 불명확하다. 양쪽에서 정의한다면 동기화 문제가 발생하고, 한쪽에서만 정의한다면 소비자가 이 정보를 어떻게 발견하는지 메커니즘이 없다.

---

## 3. 에이전트 정의 분석

### 3.1 agents/threat-model.md — 가장 높은 품질

**양호한 점**:
- 역할 정의가 명확하고, 다른 에이전트와의 경계가 분명 ("아키텍처 레벨까지, 코드 레벨은 audit 영역")
- Arch 산출물에서 보안 모델로의 변환 규칙이 테이블 형태로 체계적
- STRIDE/DREAD 방법론을 구체적 기준과 함께 제시
- 대화 규칙(한 번에 3-4개 질문, 재질문 금지, 보수적 가정)이 실용적

**문제점**:
- **기술 스택 취약점 패턴 매핑이 정적이고 불완전** (심각도: 중간). Express, Django, Spring 등 특정 프레임워크의 취약점 패턴이 하드코딩되어 있다. 이 목록은 시간이 지남에 따라 구식이 되며, 목록에 없는 기술 스택(예: Rust/Axum, Kotlin/Ktor)을 사용하면 어떻게 되는지 지침이 없다.
- **DREAD 점수의 주관성에 대한 안전장치 부재** (심각도: 낮음). 1-10점 범위의 DREAD 점수를 LLM이 산정하는데, 동일한 위협에 대해 실행할 때마다 다른 점수가 나올 수 있다. 보정 메커니즘이나 "DREAD 점수는 참고용이며, 최종 risk_level 판정은 사용자 확인 필수"라는 안내가 없다.

### 3.2 agents/audit.md — 체크리스트형 구조의 강점과 한계

**양호한 점**:
- OWASP Top 10 체크리스트가 구체적이고 실행 가능
- CWE 매핑 가이드가 있어 분류의 일관성 확보
- CVSS v3.1 점수 산정 기준이 명시적
- 에스컬레이션 형식이 구체적 (이모지, 옵션 A/B/C)

**문제점**:
- **LLM이 실제로 CVE 데이터베이스를 조회할 수 없다는 현실적 한계에 대한 언급 부재** (심각도: 높음). "의존성 취약점 스캔"이라고 하지만, LLM은 학습 시점 이후의 CVE를 알 수 없고, 특정 버전의 알려진 CVE를 정확히 매핑하는 것은 hallucination 위험이 높다. `external_dependencies`의 CVE 매핑이 실질적으로 정확하게 수행될 수 있는지에 대한 제한사항이나 면책 조항이 필요하다. "LLM 기반 감사의 한계"를 명시하고 별도 도구(Snyk, Dependabot) 사용을 권고해야 한다.
- **정적 분석이라고 하지만 실제로는 코드를 읽는 것** (심각도: 중간). "정적 분석"이라는 용어가 사용되지만, 실제로 LLM이 하는 것은 코드를 읽고 패턴을 식별하는 것이다. SAST 도구(SonarQube, Semgrep)와 혼동될 수 있으며, LLM 기반 분석의 신뢰도 수준을 명확히 해야 한다.

### 3.3 agents/review.md — audit과의 경계가 여전히 모호

**양호한 점**:
- "audit과 중복 보고하지 않음" 원칙이 명시
- 대응 전략 구현 매트릭스가 위협 모델의 모든 항목을 커버하도록 설계
- 리뷰 영역 6개가 체계적이고 구체적

**문제점**:
- **audit과 review의 실질적 구분이 "패턴 매칭 vs 로직 검증"인데, LLM 관점에서 이 구분이 유의미한가?** (심각도: 중간). SAST 도구가 패턴 매칭을 하고 사람이 로직 리뷰를 하는 것은 현실적 구분이지만, 같은 LLM이 두 에이전트를 모두 실행할 때 "패턴만 보라"와 "로직을 보라"를 실질적으로 구분할 수 있는지 의문이다. 결과적으로 audit과 review가 유사한 발견 사항을 다른 형식으로 중복 생산할 가능성이 높다.
- **"audit이 이미 보고한 항목은 중복 보고하지 않음"이 실현 가능한지** (심각도: 중간). review 에이전트가 audit의 `vulnerability_report`를 입력으로 받아 중복을 회피하려면, LLM이 두 보고서의 의미적 동등성을 정확히 판단해야 한다. 이는 비결정적(non-deterministic)이며, 중복 또는 누락이 발생할 수 있다.

### 3.4 agents/compliance.md — 가장 야심적이지만 가장 비현실적

**양호한 점**:
- OWASP ASVS, PCI DSS, GDPR, HIPAA의 코드 레벨 요구사항이 구체적
- 통합 권고 생성의 우선순위 결정 매트릭스가 합리적
- 최종 보안 리포트 형식이 실용적

**문제점**:
- **OWASP ASVS Level 2의 286개 항목을 LLM이 자동으로 매핑/검증할 수 있다는 전제가 비현실적** (심각도: 높음). ASVS Level 2는 286개 요구사항이 있고, 각 항목에 대해 "준수/미준수/부분 준수/해당 없음"을 판정하려면 코드 전체에 대한 깊은 이해가 필요하다. LLM이 이를 자동으로 수행하면 대부분의 항목이 hallucination 기반 판정이 될 위험이 크다. compliance-output 예시에서도 `total_requirements: 134`로 되어 있어 286개가 아닌 점에서 이 문제를 이미 회피하고 있는 것으로 보인다.
- **"세 에이전트의 발견 사항을 중복하여 권고에 포함하지 마세요"가 compliance에서 반복됨** (심각도: 낮음). 이 지시는 review 에이전트에도 있고 compliance에도 있다. 하지만 compliance는 세 에이전트의 결과를 "통합"하는 역할이므로, 중복 제거가 오히려 핵심 기능이어야 한다. 그런데 중복 기준이 "동일한 근본 원인"이라는 주관적 판단에 의존한다.

---

## 4. 프롬프트 분석

### 4.1 agents/*.md와 prompts/*.md의 중복

**심각도: 높음**

이것이 이 스킬의 가장 큰 구조적 문제다. `agents/` 파일과 `prompts/` 파일의 내용이 **대폭 중복**된다. 비교해보면:

| 내용 | agents/audit.md | prompts/audit.md |
|------|----------------|-----------------|
| 역할 정의 | 있음 | 있음 (거의 동일) |
| OWASP Top 10 체크리스트 | 있음 (상세) | 있음 (체크박스 형식) |
| CWE 분류 가이드 | 있음 | 없음 |
| CVSS 점수 산정 | 있음 | 있음 (간략) |
| 실행 절차 | 있음 (단계별) | 있음 (Step 형식, 더 상세) |
| 산출물 구조 | 있음 | 있음 (동일) |
| 에스컬레이션 조건 | 있음 | 있음 |
| 주의사항 | 있음 | 있음 (거의 동일) |

두 파일의 차이는 주로 **형식(format)**이다. agents/는 "설명형 문서"이고, prompts/는 "Step-by-step 지시형"이다. 그러나 내용의 80% 이상이 중복된다.

이 설계가 의도적인 것인지(system_prompt와 prompt_template를 분리하여 두 번 강화), 아니면 복사-붙여넣기의 결과인지 불명확하다. 의도적이라면, 두 파일의 역할 구분을 skills.yaml에 명시해야 한다. 예를 들어:
- `system_prompt` (agents/): 에이전트의 정체성, 원칙, 제약 조건 (변하지 않는 것)
- `prompt_template` (prompts/): 실행 시 주입되는 구체적 지시사항과 입력 (매 실행마다 달라지는 것)

현재는 두 파일 모두 "정체성 + 원칙 + 지시사항 + 산출물 형식"을 전부 포함하고 있어, 역할 분리가 되어 있지 않다.

### 4.2 prompts/의 입력 템플릿 형식 불일치

**심각도: 낮음**

모든 프롬프트의 입력이 `{{variable}}` 형식의 템플릿 변수를 사용하는데, 이를 실제로 치환하는 메커니즘이 harness에 있는지 불명확하다. 또한 코드 블록 안에 있어서 템플릿 엔진이 이를 올바르게 파싱하는지도 의문이다:

```
## 입력

```
구현 맵: {{implementation_map}}
```
```

### 4.3 prompts/threat-model.md — 가장 높은 품질

Step 1~9가 논리적으로 연결되어 있고, 각 단계의 출력이 다음 단계의 입력으로 자연스럽게 흐른다. "사용자에게 제시하세요" 형식의 출력 포맷이 구체적이다.

단, **Step 5에서 경량/중량 모드별 분석 깊이 차이가 충분히 구체적이지 않다**. "시스템 전체 수준에서 STRIDE 6개 카테고리를 분석하여 상위 5개 위협을 도출합니다"라고만 되어 있는데, "상위 5개"의 기준이 무엇인지 불명확하다.

---

## 5. 예제 분석

### 5.1 단일 도메인 편향

**심각도: 중간**

모든 예제가 "휴가 관리 시스템"이라는 **단일 도메인**에 기반한다. 이 도메인은:
- 소규모 모놀리스 (컴포넌트 5개)
- 단일 서비스, 단일 DB
- 규제: 개인정보보호법 (GDPR 유사)
- 위협 수준: 낮음~중간

이 도메인 선택으로 인해 다음 시나리오가 커버되지 않는다:
- **마이크로서비스 아키텍처**: 서비스 간 인증, 네트워크 정책, 시크릿 분산 관리
- **PCI DSS / HIPAA**: 카드 데이터나 의료 데이터 처리 시나리오
- **경량 모드**: 예제는 중량 모드(컴포넌트 5개)만 보여준다
- **에스컬레이션 시나리오**: 모든 예제가 에스컬레이션 없이 완료된다. CVSS 9.0 이상 취약점이 발견되거나 규제 미준수로 에스컬레이션되는 예제가 없다.

### 5.2 compliance-input.md의 과도한 참조

**심각도: 중간**

compliance-input.md의 7개 입력 중 5개가 "xxx-output.md의 yyy 섹션 참조"로 되어 있다. 입력 예시 파일인데 실제 데이터가 없고 다른 파일을 참조하기만 한다. 이는 예시의 **자기 완결성(self-containedness)**을 심각하게 해친다. review-input.md도 동일한 문제가 있다 (5개 입력 중 5개가 참조).

예시 파일의 목적이 "이런 형식의 데이터가 들어온다"를 보여주는 것이라면, 간략하더라도 인라인으로 데이터를 포함해야 한다. 현재 구조에서는 compliance의 입력을 이해하려면 최소 3개의 다른 파일을 열어야 한다.

### 5.3 threat-model 예제에서 DREAD 점수와 risk_level 불일치

**심각도: 낮음**

threat-model-output.md에서 TM-006의 DREAD 점수를 계산하면:
- damage: 6, reproducibility: 9, exploitability: 8, affected_users: 9, discoverability: 8
- 총점: 40

agents/threat-model.md의 기준에 따르면 총점 40은 **Critical** (40-50)인데, 예시에서는 `risk_level: high`로 되어 있다. 이는 DREAD 기준과 예시 간의 명백한 불일치다.

마찬가지로 TM-001의 총점은 36 (9+7+6+9+5)이고 이는 High (30-39) 범위에 맞지만, TM-002의 총점은 38 (7+9+8+7+7)로 High 범위에 맞다.

### 5.4 예제의 VA-008에 threat_refs가 빈 배열

**심각도: 낮음**

audit-output.md의 VA-008 (보안 응답 헤더 미설정)에서 `threat_refs: []`로 되어 있다. threat-model에서 이에 대응하는 위협이 없다는 의미인데, agents/audit.md의 원칙 "threat-model 연동"과 다소 모순된다. 보안 헤더 미설정은 information_disclosure나 다른 STRIDE 카테고리에 매핑될 수 있음에도 위협이 식별되지 않았다.

### 5.5 compliance-output에서 gap_summary의 severity 기준 누락

**심각도: 낮음**

compliance-output.md의 `gap_summary`에서 severity가 "high"와 "medium"만 있고 "critical"이 없다. 그런데 remediation_roadmap에서는 gap_summary에 없는 항목 ID를 참조하고 있다 (예: `V8.3.4`가 gap_summary.medium.items에 있지만, findings에는 `V8.3.4`에 대한 항목이 없다). 이는 예제 데이터의 정합성 오류다.

---

## 6. 일관성 검토

### 6.1 에이전트 간 산출물 ID 체계

| 에이전트 | ID 패턴 | 정의 위치 |
|---------|---------|----------|
| threat-model | TM-xxx, TB-xxx, DFS-xxx | skills.yaml output |
| audit | VA-xxx | skills.yaml output |
| review | SRV-xxx | skills.yaml output |
| compliance | CR-xxx, SR-xxx | skills.yaml output |

ID 체계는 일관되게 유지되고 있다. 각 에이전트의 주의사항에도 ID 체계 준수가 명시되어 있어 양호하다.

### 6.2 용어 불일치

- **"에스컬레이션"**: 모든 에이전트에서 일관되게 사용. 양호.
- **"산출물" vs "결과"**: agents/compliance.md에서는 "세 에이전트의 결과"와 "산출물"이 혼용된다. 대부분 "산출물"로 통일되어 있지만 가끔 "결과"가 등장한다.
- **"대응 전략" vs "mitigation"**: 한글과 영문이 혼용된다. agents/threat-model.md에서는 주로 한글, 예시에서는 영문. 문서 전체에서 "대응 전략(mitigation)"처럼 병기하는 것이 나을 것이다.

### 6.3 에스컬레이션 형식의 이모지 일관성

| 에이전트 | 이모지 |
|---------|--------|
| audit | 🚨 (긴급 보안 에스컬레이션) |
| review | ⚠️ (보안 리뷰 에스컬레이션) |
| compliance | 🚨 (규제 컴플라이언스 에스컬레이션) |

audit과 compliance는 동일한 🚨를 사용하고 review는 ⚠️를 사용한다. 이것이 의도적인 구분(critical vs warning)인지 불명확하다. 의도적이라면 skills.yaml에 명시해야 하고, 아니라면 통일해야 한다.

### 6.4 완료 메시지 형식 불일치

- audit 프롬프트: `✅ 보안 감사 완료` + 요약
- review 프롬프트: `✅ 보안 코드 리뷰 완료` + 요약
- compliance 프롬프트: `📋 보안 분석 최종 리포트` + 4섹션
- threat-model: 명시적 완료 메시지 없음 (대화형이므로)

형식이 비슷하지만 미묘하게 다르다. audit/review는 체크마크 + 요약이고, compliance는 클립보드 이모지 + 상세 리포트다. 일관성을 위해 표준 완료 형식을 정의하는 것이 좋다.

---

## 7. 주요 문제점 (심각도 순)

### P1 (높음): agents/와 prompts/의 대량 중복
- 두 디렉토리의 파일 내용이 80% 이상 중복
- system_prompt와 prompt_template의 역할 구분이 부재
- 유지보수 시 양쪽 모두 수정해야 하며, 한쪽을 놓치면 불일치 발생
- 토큰 소비 관점에서도 비효율적 (동일 내용이 system + user 메시지에 이중 투입)

### P2 (높음): LLM 기반 분석의 한계에 대한 면책/제한 사항 부재
- CVE 데이터베이스 조회 불가 (학습 시점 이후 CVE 모름)
- CVSS 점수 산정의 비결정성
- OWASP ASVS 286개 항목 자동 검증의 비현실성
- "정적 분석"이라는 용어가 SAST 도구와 혼동 유발
- 전체 스킬에 걸쳐 "이것은 LLM 기반 보안 분석이며, 전문 보안 감사를 대체하지 않는다"는 면책이 필요

### P3 (중간): 에스컬레이션 시나리오 예제 부재
- 모든 예제가 "정상 완료" 시나리오만 다룸
- CVSS 9.0+ critical 취약점 발견 시 에스컬레이션 예제 없음
- hard 규제 미준수 에스컬레이션 예제 없음
- 에스컬레이션은 스킬의 핵심 차별점인데 예제가 없으면 올바르게 동작하는지 검증 불가

### P4 (중간): 예제의 단일 도메인 편향
- 휴가 관리 시스템만으로는 마이크로서비스, PCI DSS, HIPAA, 경량 모드 등을 커버 불가
- 최소 1개의 경량 모드 예제와 1개의 규제 집약적(PCI DSS/HIPAA) 예제가 필요

### P5 (중간): audit과 review의 실질적 구분 불명확
- 같은 LLM이 "패턴 매칭"과 "로직 분석"을 분리해서 수행하기 어려움
- 중복 보고 회피 메커니즘이 의미적 판단에 의존하여 비결정적
- 두 에이전트를 하나로 합치는 것이 더 효율적일 수 있음

### P6 (낮음): DREAD 점수와 risk_level 불일치 (예제)
- TM-006의 DREAD 총점 40은 기준표에 따르면 Critical이지만, 예제에서는 High

---

## 8. 개선 제안

### 8.1 agents/와 prompts/의 역할 명확화 및 중복 제거

**제안**: 두 파일의 역할을 명확히 분리한다.

- `agents/*.md` (system_prompt): 에이전트의 정체성, 핵심 원칙, 제약 조건, 참조 자료(OWASP 체크리스트, CWE 매핑 등). 변하지 않는 지식.
- `prompts/*.md` (prompt_template): 입력 변수 주입, Step-by-step 실행 지시, 산출물 형식. 매 실행마다 달라지는 부분.

현재 양쪽에 중복되는 내용(에스컬레이션 조건, 주의사항, 산출물 구조)은 agents/ 에만 두고, prompts/에서는 참조한다.

### 8.2 LLM 한계 면책 조항 추가

**제안**: skills.yaml 또는 별도 섹션에 다음을 추가한다:

```yaml
limitations:
  - "CVE 매핑은 LLM 학습 데이터 기준이며, 최신 CVE는 누락될 수 있음. 프로덕션에서는 Snyk/Dependabot 등 전용 도구 병행 필수"
  - "CVSS 점수는 LLM의 추정치이며, 공식 CVSS 계산기 결과와 다를 수 있음"
  - "컴플라이언스 판정은 코드 레벨 검증 한정이며, 조직/프로세스 수준의 컴플라이언스는 별도 감사 필요"
  - "이 스킬의 결과는 전문 보안 감사를 보조하는 용도이며, 대체하지 않음"
```

### 8.3 에스컬레이션 예제 추가

**제안**: 최소 2개 에스컬레이션 예제를 추가한다.

1. `examples/audit-escalation-output.md`: CVSS 9.8 SQL Injection 발견 시 에스컬레이션
2. `examples/compliance-escalation-output.md`: PCI DSS hard 제약 non_compliant 시 에스컬레이션

### 8.4 경량 모드 예제 추가

**제안**: 컴포넌트 2-3개의 소규모 시스템(예: 간단한 TODO API)에 대한 경량 모드 예제 세트를 추가한다.

### 8.5 audit/review 통합 검토

**제안**: audit과 review를 하나의 에이전트로 통합하고, 내부적으로 두 단계(패턴 탐지 → 로직 검증)로 실행하는 것을 검토한다. 이렇게 하면:
- 중복 보고 회피 문제가 근본적으로 해결됨
- 파이프라인 단계 수 감소로 토큰 소비 절감
- 단, threat-model의 mitigation 검증(현재 review의 핵심 기능)은 유지 필요

### 8.6 예제 데이터 정합성 수정

- TM-006의 `risk_level`을 `critical`로 수정하거나, DREAD 점수를 조정하여 high 범위(30-39)에 맞춘다
- compliance-output의 `gap_summary`에서 `V8.3.4` 참조를 제거하거나 해당 finding을 추가한다
- compliance-input과 review-input에 최소한의 인라인 데이터를 포함하여 자기 완결성을 확보한다

### 8.7 pipeline에 명시적 의존성 선언 추가

```yaml
pipeline:
  stages:
    - agent: threat-model
      checkpoint: true
    - agent: audit
      depends_on: [threat-model]
    - agent: review
      depends_on: [threat-model, audit]
    - agent: compliance
      depends_on: [threat-model, audit, review]
```

### 8.8 adaptive_depth 일관성 확보

threat-model에만 에이전트 레벨 adaptive_depth가 있고 나머지에는 없다. 두 가지 선택지:
1. 모든 에이전트에 adaptive_depth를 추가 (audit의 경량 모드는 OWASP Top 10 체크리스트만, 중량 모드는 전체 분석 등)
2. 에이전트 레벨 adaptive_depth를 제거하고 최상위 adaptive_depth만 사용. 이 경우 각 에이전트의 agents/*.md에서 모드별 동작 차이를 설명.
