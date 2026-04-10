# QA 스킬 코드/설계 리뷰

> 리뷰 대상: `/qa/` 디렉토리 전체 (skills.yaml, agents/4, prompts/4, examples/9)
> 리뷰어: Claude Opus 4.6
> 일시: 2026-04-10

---

## 1. 구조 분석

### 디렉토리 구조

```
qa/
  skills.yaml
  agents/
    strategy.md
    generate.md
    review.md
    report.md
  prompts/
    strategy.md
    generate.md
    review.md
    report.md
  examples/
    strategy-input.md
    strategy-output.md
    generate-input.md
    generate-output.md
    review-input.md
    review-output.md
    report-input.md
    report-output.md
    lightweight-example.md
    escalation-example.md
```

**평가: 구조 자체는 합리적이다.** 4개 에이전트 각각에 대해 agent 정의, 프롬프트 템플릿, 입출력 예제가 1:1:2로 대응된다. `lightweight-example.md`와 `escalation-example.md`는 경량 모드와 에스컬레이션이라는 특수 시나리오를 별도 예제로 분리한 점이 좋다.

**문제점:**

- `agents/` 와 `prompts/` 간 역할 분리가 모호하다. `agents/generate.md`와 `prompts/generate.md`를 비교하면, agent 파일이 "역할 + 핵심 역량 + 출력 형식 + 상호작용 모델"을, prompt 파일이 "입력 + 지시사항(Step 1~N) + CoT 가이드 + 주의사항"을 담고 있다. 그러나 양쪽에 중복 내용이 상당하다. 예를 들어 `agents/generate.md`의 "acceptance_criteria -> 테스트 케이스 변환" 설명과 `prompts/generate.md`의 "Step 2: acceptance_criteria -> 테스트 케이스 변환"은 동일한 내용을 다른 형식으로 반복한다. 이 구조적 중복은 유지보수 시 한쪽만 수정하고 다른 쪽을 놓치는 동기화 문제를 야기할 수 있다.
- 예제 파일이 모두 하나의 도메인(휴가 관리 시스템)에 의존한다. 다양한 도메인 예제가 없어서 스킬의 일반성을 검증할 수 없다.

---

## 2. skills.yaml 분석

### 긍정적 측면

- 4단계 파이프라인(strategy -> generate -> review -> report)이 논리적으로 잘 설계되어 있다.
- review -> generate 루프(max 3회)와 에스컬레이션 조건이 명확하다.
- `supported_frameworks`, `quality_gate_defaults`, `consumers`, `dependencies` 등 메타데이터가 충실하다.
- 각 에이전트의 input/output 스키마가 상세하게 정의되어 있다.

### 문제점

**[심각] input 스키마의 items 정의 불일치.** `strategy` 에이전트의 input에서 `requirements_spec`, `constraints` 등은 `type: array`만 명시하고 `items` 스키마를 정의하지 않는다. 반면 상위 스킬인 `re/skills.yaml`과 `arch/skills.yaml`은 각 input의 items 스키마(id, type, title 등)를 상세히 정의한다. QA 스킬의 input은 description 문자열로만 구조를 암시하고 있어, 실제 런타임에서 유효성 검증이 불가능하다.

**[심각] adaptive_depth가 strategy 에이전트에만 정의되어 있다.** 경량/중량 모드의 영향은 generate, review, report 에이전트에도 파급되어야 하나, 이들 에이전트에는 `adaptive_depth`가 없다. 실제로 `lightweight-example.md`에서 경량 모드 전체 파이프라인을 보여주는데, skills.yaml에서는 이 분기 로직이 strategy에만 정의되어 있어 모순이다.

**[중간] output의 properties가 불완전하다.** `test_strategy.output.test_strategy.properties`를 보면, `scope`는 `type: object, description: "테스트 범위"`라고만 되어 있고, 하위 필드(included, excluded)가 정의되지 않았다. 이는 `pyramid`, `quality_gate` 등 다른 properties도 마찬가지다. output 스키마가 느슨해서 downstream consumer가 어떤 구조를 기대해야 하는지 명확하지 않다.

**[중간] pipeline.stages의 checkpoint 설정이 의문스럽다.** strategy, generate, review 모두 `checkpoint: false`이고 report만 `checkpoint: true`이다. 하지만 strategy의 산출물은 전체 QA 프로세스의 방향을 결정하는데, 이 단계에서 사용자 확인 없이 진행하는 것이 과연 적절한가? 특히 테스트 범위 제외 결정(Won't 항목 제외)이나 피라미드 비율 결정은 사용자가 확인하고 싶을 수 있다. strategy 에이전트의 description에서 "사용자 개입 없음"을 강조하는데, 이는 유연성을 떨어뜨린다.

**[경미] review 에이전트의 escalation 정의와 pipeline의 escalation 정의가 분산되어 있다.** review 에이전트 내부에 `escalation` 섹션이 있고, pipeline.stages에도 `escalation` 섹션이 있다. 두 곳의 정보가 동일하지만 중복 관리가 필요하다.

**[경미] `consumers` 섹션에서 `deployment`, `operation`, `management`, `security` 스킬을 참조하는데, `dependencies.upstream`에는 `re`, `arch`, `impl`만 있다.** downstream 스킬에 대한 정의는 있지만, 이들 스킬이 실제로 존재하는지 확인할 수 없다. 디렉토리 목록(devops, sec)과 consumer 이름(deployment, security)이 다르다는 점에서, 네이밍 불일치가 의심된다.

**[경미] interaction_mode가 모든 에이전트에서 `auto`인데, 이것이 skills.yaml에서 사용되는 정규 enum인지 불명확하다.** 상위 스킬들은 `multi-turn`, `auto-execute` 등 다른 값을 사용한다. `auto`가 `auto-execute`와 같은 것인지, 별도 모드인지 정의가 없다.

---

## 3. 에이전트 정의 분석

### agents/strategy.md

**잘된 점:** 선행 산출물의 각 필드를 어떻게 해석하여 테스트 전략으로 변환하는지 매핑 테이블이 명확하다. 아키텍처 패턴별 피라미드 비율, 의존성 유형별 테스트 더블 전략 등 의사결정 테이블이 구체적이다.

**문제점:**

- "에스컬레이션 조건: 없음 — 모든 전략 결정은 선행 산출물에서 기계적으로 도출 가능합니다"라고 단언하지만, 이는 비현실적이다. 예: 아키텍처가 "마이크로서비스 + 이벤트 드리븐" 혼합 패턴일 때 피라미드 비율을 어떻게 결정하는가? "혼합 패턴인 경우 주요 패턴의 비율을 기준으로 조정하세요"라는 프롬프트의 지시와 에이전트 정의의 "기계적으로 도출" 사이에 모순이 있다. 조정 기준이 모호하면 에스컬레이션이 필요할 수 있다.
- 적응적 깊이의 경량/중량 판별 기준이 "5개 이하 / 10개 이상"으로, 6~9개인 중간 영역의 처리가 에이전트 정의에 없고 프롬프트에만 있다.
- 출력 형식의 예시에서 `id: TSTR-001`이 고정값인데, 복수의 테스트 전략이 생성되는 경우는 고려하지 않았다. 파이프라인 구조상 하나의 전략만 생성되겠지만, 이 제약이 명시되어 있지 않다.

### agents/generate.md

**잘된 점:** acceptance_criteria -> Given-When-Then 변환 예시가 구체적이다. 테스트 설계 기법(경계값, 동등분할 등) 적용 기준이 테이블로 명확하다. 5개 언어/프레임워크에 대한 코드 예시가 프롬프트에 포함되어 있어 실용적이다.

**문제점:**

- **테스트 "코드" 생성의 범위가 모호하다.** 에이전트 정의에서 "실행 가능한 테스트 코드를 생성합니다"라고 하지만, LLM이 생성하는 코드가 실제로 컴파일/실행 가능한지 검증하는 메커니즘이 없다. import문, 의존성 설정(pom.xml, package.json 등), 테스트 fixture 등이 빠져 있을 때 어떻게 처리하는가?
- "커버리지 충분성은 review 에이전트가 자동 검증"이라고 하면서, generate 자체에서는 충분성을 전혀 검증하지 않는다. 이는 review 에이전트에 과도한 책임을 전가한다. generate 단계에서 최소한 acceptance_criteria 매핑 완전성을 자가 검증하는 것이 합리적이다.
- `test_cases`의 `technique` enum에 `boundary_value`, `equivalence_partition`, `decision_table`, `state_transition`, `property_based`만 있다. 현실적으로 자주 사용되는 error guessing, pairwise testing, risk-based testing 등이 빠져 있다.

### agents/review.md

**잘된 점:** 갭 분류 로직(auto_remediate / risk_accepted / escalate)이 명확하다. RTM 생성 프로세스가 체계적이다. 에스컬레이션 메시지 형식이 구체적이어서 사용자 경험이 좋을 것이다.

**문제점:**

- **"뮤테이션 테스트 관점"이라고 하면서 실제 뮤테이션 테스트를 수행하지 않는다.** 이 표현은 오해의 소지가 있다. 실제로는 정적 패턴 매칭 기반의 약한 테스트 탐지를 수행하는 것이지, 뮤테이션 테스트 도구(PIT, Stryker 등)를 실행하는 것이 아니다.
- **코드 커버리지 분석(라인, 분기, 경로)을 수행한다고 하지만, 이 시점에서 테스트가 실행된 적이 없다.** review 에이전트의 input에는 테스트 실행 결과가 포함되지 않는다. skills.yaml의 review input에도 `test_suites`(generate 산출물)만 있고 커버리지 데이터는 없다. 그러면 코드 커버리지를 어떻게 분석하는가? 이는 generate가 코드만 생성하고 실행하지 않는 구조에서 논리적 공백이다.
- Should/Could 갭을 무조건 risk_accepted로 분류하는 규칙이 너무 경직되어 있다. Should 중에서도 컴플라이언스 관련 항목(예: NFR-003 감사 로그)은 자동 수용이 부적절할 수 있다.

### agents/report.md

**잘된 점:** 품질 게이트 판정 3단계(PASS / CONDITIONAL PASS / FAIL)가 명확하다. 잔여 리스크 분류, 개선 권고의 우선순위화가 체계적이다. 후속 스킬 전달 사항을 명시한 점이 좋다.

**문제점:**

- **트렌드 분석("이전 측정 데이터가 있는 경우")이라고 하지만, 이전 데이터를 어떻게 접근하는지 input에 정의되지 않았다.** report 에이전트의 input에 과거 리포트 데이터를 받는 필드가 없다. 이 기능은 구현 불가능한 상태로 명세에만 존재한다.
- **"독립 실행" 모드를 지원한다고 하면서, 독립 실행 시 필요한 input이 무엇인지 정의가 없다.** 파이프라인 외부에서 호출할 때의 최소 입력 세트가 명확하지 않다.
- 코드 커버리지 데이터의 출처가 불명확하다. `test_suites`에 `results`(total, passed, failed)는 있지만, 라인/분기 커버리지 데이터는 별도 도구(JaCoCo, Istanbul 등)에서 수집해야 하는데, 이 과정이 파이프라인에 없다.

---

## 4. 프롬프트 분석

### 공통 문제점

**[심각] 에이전트 정의와 프롬프트 간 대규모 내용 중복.** 앞서 지적했듯이, agent 파일과 prompt 파일이 같은 내용을 다른 형식으로 반복한다. 특히 strategy, generate, review 모두에서 이 문제가 심하다. prompt가 "시스템 프롬프트(agent) + 사용자 프롬프트(prompt)"로 분리되는 구조라면, agent 파일은 역할/정체성/원칙만, prompt 파일은 구체적 실행 단계만 담아야 한다. 현재는 경계가 불분명하다.

**[중간] Chain of Thought 가이드가 형식적이다.** 각 프롬프트 끝에 "사고 과정 예시"가 있지만, 이것이 실제 LLM의 추론을 개선하는지 의문이다. 특히 예시가 모두 같은 도메인(휴가 관리 시스템)의 것이라 다른 도메인에서의 적용 지침이 부족하다.

### prompts/strategy.md

- Step 1의 적응적 깊이 판별에서 "6~9개 → 산출물 복잡도를 기준으로 판단"이라는 지시가 있으나, "복잡도"의 구체적 측정 기준이 없어서 비결정적이다. 의존성 수와 NFR 유무를 기준으로 한다고 되어 있지만, 구체적 임계값이 없다.
- Step 3에서 아키텍처 패턴을 "키워드"로 식별한다고 했는데, `architecture_decisions.decision` 문자열에서 키워드를 추출하는 방식은 fragile하다. "event-driven microservice"처럼 복수 키워드가 있을 때의 우선순위 규칙이 없다.

### prompts/generate.md

- Step 4의 프레임워크별 코드 예시가 매우 길다(TypeScript, Python, Java, Go, Rust 5개). 이 예시가 모두 하나의 프롬프트에 포함되면 토큰 낭비가 심각하다. 실제 사용 시에는 선택된 기술 스택에 해당하는 예시만 포함하는 동적 프롬프트가 필요하지만, 현재 구조에서는 이를 지원하지 않는다.
- `additional_generation_request` 변수가 input에 있지만, skills.yaml의 generate input 정의에는 이 필드가 없다. 프롬프트와 스키마 간 불일치이다.
- Jest 예시 코드에서 `it` 콜백이 `async`가 아닌데 내부에서 `await`를 사용한다. 사소하지만 "실행 가능한 코드"를 표방하는 예시에서 문법 오류가 있으면 신뢰도가 떨어진다.

### prompts/review.md

- Step 4에서 "quality_attribute_priorities의 각 항목에 대해" NFR 테스트 충분성을 검증한다고 하는데, review 에이전트의 input에 `quality_attribute_priorities`가 없다. skills.yaml의 review input을 확인하면 `requirements_spec`, `constraints`, `component_structure`, `implementation_map`, `test_suites`, `test_strategy`만 있고 `quality_attribute_priorities`는 빠져 있다. 이는 프롬프트가 접근할 수 없는 데이터를 참조하는 것이다.

### prompts/report.md

- 전반적으로 가장 잘 작성된 프롬프트이다. 7개 Step이 논리적으로 진행되고, 판정 규칙이 테이블로 명확하다.
- 다만 "이전 측정 데이터가 있으면 트렌드를 포함하세요"는 input에 없는 데이터를 요구하므로 실현 불가능하다.

---

## 5. 예제 분석

### 긍정적 측면

- 예제들이 하나의 일관된 도메인(휴가 관리 시스템)을 사용하여 파이프라인 전체를 추적할 수 있다.
- strategy-input -> strategy-output -> generate-input -> generate-output -> review-input -> review-output -> report-input -> report-output 순으로 데이터가 연결된다.
- escalation-example은 FAIL 시나리오와 에스컬레이션 시나리오를 모두 보여준다.
- lightweight-example은 경량 모드의 전체 흐름을 한 파일에 보여준다.

### 문제점

**[심각] 예제 간 데이터 정합성 오류.**

- `strategy-input.md`의 RE spec에 `NFR-001`(응답 시간, priority: Should)과 `NFR-003`(감사 로그, priority: Should)이 정의되어 있다. 그런데 `report-input.md`의 RTM에서 `NFR-001`과 `NFR-003`이 모두 `re_priority: Should`로 되어 있고 uncovered인데, `report-output.md`의 품질 게이트에서 Should 요구사항 커버리지가 33%(1/3)이다. Should 요구사항은 FR-004, NFR-001, NFR-003의 3개인데, 맞다. 하지만 FR-004는 partial이지 covered가 아닌데, covered를 1로 세었다. partial을 covered로 세는 것인지, uncovered만 제외하는 것인지 기준이 불명확하다.

- `generate-output.md`에서 테스트 스위트 ID가 `TS-002`와 `TS-008`인데, `review-input.md`에서는 `TS-001`, `TS-002`, `TS-003`, `TS-004`, `TS-005`, `TS-008`, `TS-010`이 있다. generate 예제에서는 FR-002와 FR-008만 발췌한 것이라 다른 TS가 빠진 것으로 이해할 수 있지만, generate-output이 "전체" 산출물이 아님을 명시하지 않아 혼란을 줄 수 있다.

- `review-input.md`에서 `TS-008`이 "전체 누락"으로 주석되어 있는데, `generate-output.md`에서는 TS-008이 정상적으로 생성되어 있다. 이 불일치는 review 예제가 "generate가 갭을 남긴 상태"를 시뮬레이션하기 위해 의도적으로 TS-008을 제거한 것이지만, generate-output과 review-input이 같은 파이프라인의 연속이라면 모순이다. 이 의도를 명시하는 주석이 필요하다.

**[중간] 예제가 단일 도메인(휴가 관리)에만 의존한다.** TODO API 경량 예제를 제외하면 모든 예제가 같은 도메인이다. 마이크로서비스 아키텍처, 이벤트 드리븐 아키텍처 등 다른 아키텍처 패턴의 예제가 없어서, strategy 에이전트의 피라미드 비율 결정 로직(계약 테스트 20% 등)이 실제로 어떻게 동작하는지 예시가 없다.

**[중간] 경량 모드 예제(lightweight-example.md)가 파이프라인 전체를 단일 파일에 담으면서 generate/review/report 에이전트의 독립적 동작을 보여주지 않는다.** 전략부터 최종 리포트까지 한 파일에 있어 각 에이전트의 역할 경계가 모호하다.

**[경미] generate-output.md에서 Jest 예시가 없고 JUnit5만 있다.** `supported_frameworks`에 Jest, Vitest, pytest, JUnit5, Go testing, Rust #[test] 등이 나열되어 있으나 예제에서는 Java만 다룬다. (경량 예제는 Python/pytest.)

---

## 6. 일관성 검토

### 용어 불일치

| 항목 | 위치 A | 위치 B | 문제 |
|------|--------|--------|------|
| interaction_mode | QA skills.yaml: `auto` | Impl skills.yaml: `auto-execute` | 같은 의미로 추정되나 enum 값이 다름 |
| consumer 스킬명 | skills.yaml consumers: `deployment` | 디렉토리: `devops/` | 이름 불일치 |
| consumer 스킬명 | skills.yaml consumers: `security` | 디렉토리: `sec/` | 이름 불일치 |
| consumer 스킬명 | skills.yaml consumers: `operation` | 디렉토리 없음 | 존재 여부 불확실 |
| consumer 스킬명 | skills.yaml consumers: `management` | 디렉토리 없음 | 존재 여부 불확실 |

### 스키마 불일치

| 항목 | skills.yaml | 프롬프트 | 문제 |
|------|-------------|----------|------|
| generate input | `additional_generation_request` 없음 | prompts/generate.md에서 참조 | 스키마에 미정의 |
| review input | `quality_attribute_priorities` 없음 | prompts/review.md Step 4에서 사용 | 스키마에 미정의 |
| report input | 이전 리포트 데이터 없음 | agents/report.md 트렌드 분석 | 입력 부재 |

### ID 패턴 불일치

- skills.yaml에서 `test_strategy.id`의 패턴은 `^TSTR-\\d{3}$`이고 `test_suites[].id`는 `^TS-\\d{3}$`이다.
- 그런데 예제에서 `impl_refs`에 `IDR-002` 같은 ID가 사용되는데, 이 ID 패턴(`^IDR-\\d{3}$`)은 QA skills.yaml 어디에도 정의되지 않았다. impl 스킬의 산출물 ID 패턴이지만, QA의 input 스키마에서 이를 명시적으로 받아들이지 않는다.

### 형식 불일치

- `agents/` 파일들은 "## 역할 > ## 핵심 역량 > ## 출력 형식 > ## 상호작용 모델" 구조를 따르지만, `report.md`만 "## 독립 실행" 섹션이 추가되어 있다.
- `agents/strategy.md`와 `agents/review.md`에는 "## 에스컬레이션 조건" 섹션이 있지만, `agents/generate.md`와 `agents/report.md`에는 없다. generate에 에스컬레이션이 없는 건 맞지만, report도 FAIL 판정 시 사실상 사용자에게 보고하므로 에스컬레이션과 유사한 동작을 한다.

---

## 7. 주요 문제점 (심각도 순)

### Critical

1. **review 에이전트의 코드 커버리지 분석이 논리적으로 불가능하다.** 파이프라인 상 generate 이후 테스트 코드가 실행된 적이 없는데, review가 "라인, 분기, 경로 커버리지 분석"을 수행한다고 명세한다. 테스트 실행 -> 커버리지 수집 단계가 파이프라인에 누락되어 있다. report 에이전트도 동일한 문제를 안고 있으며, `report-input.md`에서 `code_coverage` 데이터가 마법처럼 존재한다.

2. **프롬프트가 skills.yaml에 정의되지 않은 input을 참조한다.** `prompts/generate.md`의 `additional_generation_request`, `prompts/review.md`의 `quality_attribute_priorities` 등이 해당 에이전트의 input 스키마에 없다. 이는 런타임에서 데이터 접근 실패를 유발한다.

### High

3. **에이전트 정의와 프롬프트 간 대규모 내용 중복.** 유지보수 비용이 높고 불일치 리스크가 크다. 두 파일 중 하나를 수정하면 다른 하나도 수정해야 하는데, 이를 강제하는 메커니즘이 없다.

4. **적응적 깊이(경량/중량 모드)가 strategy에만 정의되어 있어 downstream 에이전트의 동작이 불명확하다.** generate는 경량 모드에서 어떤 테스트 유형을 생략하는가? review는 경량 모드에서 RTM을 간소화하는가? 이런 질문에 대한 답이 skills.yaml에 없다.

5. **Should/Could 갭의 무조건 risk_accepted 분류가 과도하게 경직되어 있다.** 컴플라이언스(regulatory) 관련 Should 항목은 자동 수용이 부적절할 수 있다. constraints의 `type: regulatory`와 연계된 Should 요구사항은 별도 취급이 필요하다.

### Medium

6. **예제 간 데이터 흐름 불일치.** generate-output에서 TS-008이 생성되었는데 review-input에서 누락된 것처럼 되어 있는 등, 예제가 파이프라인의 연속적 흐름을 정확히 반영하지 않는다.

7. **"실행 가능한 테스트 코드"를 표방하면서 코드 품질에 문제가 있다.** prompts/generate.md의 Jest 예시에서 `async` 없이 `await` 사용. 사소하지만 예시 코드의 신뢰성에 영향을 미친다.

8. **트렌드 분석 기능이 입력 없이 명세되어 있다.** report 에이전트의 트렌드 분석은 이전 리포트 데이터가 input에 없어 실현 불가능하다.

### Low

9. **consumer 스킬명과 실제 디렉토리명 불일치** (deployment vs devops, security vs sec).

10. **interaction_mode enum 불일치** (auto vs auto-execute).

11. **단일 도메인 예제만 존재.** 마이크로서비스, 이벤트 드리븐 등 다른 아키텍처 패턴의 예제가 없다.

---

## 8. 개선 제안

### 즉시 조치 (Critical/High 해소)

1. **파이프라인에 "테스트 실행" 단계를 추가하거나, review/report의 커버리지 분석을 "추정치"로 재정의하라.** 현재 파이프라인은 generate(코드 생성) -> review(리뷰)인데, 중간에 테스트 실행 단계가 없다. 두 가지 선택지가 있다:
   - (A) generate 이후 테스트를 실제 실행하는 `execute` 에이전트/단계를 추가.
   - (B) review에서 코드 커버리지를 "정적 분석 기반 추정"으로 재정의하고, 실제 커버리지는 report의 선택적 입력으로 받도록 변경.

2. **프롬프트와 skills.yaml의 input 스키마를 동기화하라.**
   - generate input에 `additional_generation_request: { type: object, required: false }` 추가.
   - review input에 `quality_attribute_priorities: { type: array, required: true }` 추가.
   - report input에 `previous_reports: { type: array, required: false }` 추가 (트렌드 분석용).

3. **에이전트 정의와 프롬프트의 역할을 명확히 분리하라.**
   - `agents/*.md`: 역할, 정체성, 핵심 원칙, 판단 기준만 기술 (시스템 프롬프트 역할).
   - `prompts/*.md`: 구체적 실행 단계, 입력 변수, 출력 형식만 기술 (사용자 프롬프트 역할).
   - 양쪽에서 중복되는 테이블과 설명을 한쪽으로 통합.

4. **적응적 깊이를 모든 에이전트에 전파하라.** strategy가 결정한 `mode: lightweight/heavyweight`를 downstream 에이전트가 받아서 동작을 분기하도록 skills.yaml에 정의하라. 최소한 각 에이전트의 agents/*.md에 경량/중량 모드별 동작 차이를 명시하라.

### 단기 개선

5. **Should 갭의 분류 규칙을 정교화하라.** `constraints`에서 `type: regulatory`와 연관된 Should 요구사항은 자동 수용 대신 에스컬레이션하도록 예외 규칙을 추가하라.

6. **예제 데이터 흐름을 검증하고 불일치를 수정하라.**
   - review-input의 "TS-008 누락" 시나리오가 generate-output과 별도 상황임을 명시하거나, generate-output에서도 TS-008을 누락시켜 예제 간 일관성을 확보하라.
   - Should 커버리지 계산 기준(partial을 covered로 세는지 여부)을 명확히 하라.

7. **interaction_mode enum을 하네스 전체에서 통일하라.** `auto`, `auto-execute`, `multi-turn` 등의 정규 값 목록을 정의하고 모든 스킬에서 동일하게 사용하라.

8. **consumer 스킬명을 실제 디렉토리명과 일치시키라.** `deployment` -> `devops`, `security` -> `sec` 등.

### 중기 개선

9. **다른 아키텍처 패턴(마이크로서비스, 이벤트 드리븐)의 예제를 추가하라.** 특히 계약 테스트(contract test)가 포함되는 시나리오의 전체 파이프라인 예제가 필요하다.

10. **프롬프트의 프레임워크별 코드 예시를 동적으로 포함하는 메커니즘을 고려하라.** 5개 언어의 코드를 모두 포함하면 토큰 효율이 떨어진다. 기술 스택에 따라 해당 언어의 예시만 주입하는 방식이 바람직하다.

11. **skills.yaml의 input/output 스키마를 상위 스킬 수준으로 상세화하라.** 현재 대부분의 input이 `type: array, description: "..."` 수준이다. RE, Arch 스킬처럼 items의 필드별 스키마를 정의하면 자동 검증과 문서화가 가능해진다.

---

## 총평

QA 스킬은 테스트 전략 수립부터 품질 리포트 생성까지의 파이프라인을 체계적으로 설계했다. 특히 RTM(요구사항 추적 매트릭스)을 중심으로 RE -> Arch -> Impl -> QA의 추적성 체인을 유지하려는 설계 의도가 명확하고, 갭 자동 분류/보완 루프는 실용적이다.

그러나 **"테스트 실행" 단계의 부재**가 전체 설계의 가장 큰 약점이다. 코드를 생성하고 리뷰하고 리포트를 만들지만, 정작 테스트를 실행하는 단계가 없다. 이로 인해 review의 커버리지 분석과 report의 실측치 대비 분석이 공중에 떠 있다. 또한 에이전트 정의와 프롬프트 간의 대규모 중복, 프롬프트와 스키마 간의 불일치는 유지보수 시 지속적인 문제를 야기할 것이다.

설계의 야심에 비해 구현 디테일에서 빈 곳이 여럿 있으며, 이를 해소하지 않으면 실제 실행 시 예측 불가능한 동작이 발생할 수 있다.
