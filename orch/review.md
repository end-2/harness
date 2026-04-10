# Orchestration(orch) 스킬 코드/설계 리뷰

> 리뷰 대상: `/orch/` 디렉토리 전체  
> 리뷰어: Claude Opus 4.6  
> 일자: 2026-04-10

---

## 1. 구조 분석

### 디렉토리 구조

```
orch/
├── skills.yaml
├── agents/          (6개: config, dispatch, pipeline, relay, run, status)
├── prompts/         (6개: 위와 1:1 대응)
├── pipelines/       (8개: 사전 정의 파이프라인)
├── rules/           (4개: base, dialogue-protocol, escalation-protocol, output-format)
└── examples/        (4개: dialogue-relay, escalation, full-run, resume)
```

**긍정적**: agents/와 prompts/가 1:1로 대응하여 구조가 명확하다. 파이프라인이 독립 파일로 분리되어 있고, 규칙도 관심사별로 분리되어 있다.

**문제점**:

- **agents/와 prompts/ 분리의 실효성이 의문.** 두 디렉토리의 파일이 완전히 1:1 대응하며, 내용도 상당 부분 중복된다(예: dispatch의 agents/dispatch.md와 prompts/dispatch.md 모두 파이프라인 선택 매트릭스를 포함). 에이전트 정의(역할+역량)와 프롬프트 템플릿(실행 시 주입되는 변수+단계별 지시)이라는 구분이 있으나, 실제로는 에이전트 파일의 "출력" 섹션과 프롬프트 파일의 "결과 출력" 섹션이 같은 내용을 반복한다. 하나로 합치거나 명확한 역할 분리 기준을 문서화해야 한다.
- **examples/ 디렉토리에 부정적 시나리오(실패 케이스)가 전무.** 파이프라인 실패, 스킬 검증 실패, 동시 실행 충돌, 잘못된 프로젝트 경로 등 엣지 케이스 예제가 없다.

---

## 2. skills.yaml 분석

### 완성도

skills.yaml은 347줄로 상당히 포괄적이다. 에이전트 6개, 규칙 4개, 파이프라인 8개, 의존 스킬 7개, 설계 원칙 10개를 정의한다.

### 문제점

1. **`interaction_mode` 값이 하위 스킬과 불일치.** orch의 skills.yaml에서 re:elicit은 `dialogue` 모드로 참조되지만, `re/skills.yaml`에서는 `multi-turn`으로 정의되어 있다. 용어가 통일되지 않았다. `dialogue`와 `multi-turn`이 같은 의미인지, 다른 의미인지 명세가 없다.

2. **pipeline 에이전트의 output에서 `outputs.items` 정의가 YAML 문법적으로 부정확.** 94~95행의 items 아래에 `skill`, `sections`, `status`가 나열되어 있는데, 이것은 `items.properties`여야 한다. 현재는 배열의 아이템 타입이 아니라 직접 필드를 나열하는 형태로, JSON Schema와도 YAML 관습과도 맞지 않는다.

3. **`dispatch_result`의 output properties에서 `single_skill` 액션의 필요 필드가 누락.** dispatch 에이전트의 출력 정의에는 `action`, `pipeline`, `user_request`, `project_root`, `run_id`, `resume_from`, `parameters`가 있지만, agents/dispatch.md의 "단일 스킬 호출" 출력에 있는 `skill`, `agent` 필드가 skills.yaml에 없다. 스키마와 실제 출력이 불일치한다.

4. **`dependencies.managed_skills`의 agents 목록이 하위 스킬과 불일치 가능성.** 예: `qa`의 agents가 `[strategy, generate, review, report]`로 명시되어 있지만, 파이프라인에서는 `qa:generate`만 사용된다. `qa:strategy`, `qa:review`, `qa:report`를 사용하는 파이프라인이 없다. 선언은 했으나 실제 통합이 부재하다.

5. **`output_structure.files`에 `run.meta.md`가 있으나 `current-run.md`는 `global_state`로만 참조.** 파일 목록과 역할의 구분이 모호하다. `current-run.md`가 어디에 위치하는지(`<output-root>/current-run.md`) skills.yaml에서 한 줄로만 언급된다.

6. **version 필드가 `1.0.0`인데, 다른 스킬들도 모두 `1.0.0`.** dependencies에서 `>=1.0.0`으로 참조하고 있어 실질적으로 버전 관리가 무의미하다. 버전 체계의 실제 운용 계획이 없다면 불필요한 복잡성이다.

---

## 3. 에이전트 정의 분석

### dispatch (agents/dispatch.md)

- **잘된 점**: 파이프라인 선택 매트릭스가 명확하다. 기존 프로젝트 감지 신호 목록이 구체적이다.
- **문제점**: 
  - "코드 리뷰" 요청에 대해 `quick-review`를 선택하는데, `quick-review`는 `re:review -> arch:review -> impl:review` 순서다. 리뷰 대상 산출물이 어디서 오는지에 대한 설명이 없다. 이전 run의 산출물을 참조한다면 그 메커니즘이 정의되어야 하고, 없으면 리뷰 대상이 없는 셈이다.
  - `explore` 파이프라인은 "기존 프로젝트 O"일 때만 선택 가능하나, "코드 분석/탐색" 요청에 기존 프로젝트가 없으면 어떻게 처리하는지 정의가 없다.

### pipeline (agents/pipeline.md)

- **잘된 점**: 에이전트 스폰 프로토콜 9단계가 매우 구체적이다. 업스트림 입력 조립 테이블이 명확하다.
- **문제점**:
  - "DAG 기반"이라 주장하지만 실제 파이프라인 정의는 단순 순차 + 마지막 단계 병렬이다. 진짜 DAG(조건 분기, 복잡한 의존 그래프)를 지원하는 것인지, 과장된 표현인지 모호하다. 조건부 분기가 "(해당 시)"로만 언급되어 구현 방법이 불명확하다.
  - "각 스킬이 실제로 소비하는 섹션만 전달"이라 했으나, 어떤 스킬이 어떤 섹션을 소비하는지의 매핑이 pipeline.md의 테이블에만 있고, skills.yaml이나 다른 곳에서 선언적으로 정의되지 않는다. 이 매핑이 하드코딩 기반이라면 스킬 추가 시 pipeline 에이전트를 수정해야 한다.
  - 업스트림 입력 테이블에서 `re:elicit`이 `ex`의 `project_structure_map, technology_stack_detection, component_relationship_analysis`를 소비한다고 하는데, `architecture_inference`는 빠져 있다. 의도적 누락인지 실수인지 불명확하다.

### relay (agents/relay.md)

- **잘된 점**: 변환 예시가 구체적이다. 특수 응답(`__SKIP__`, `__DEFAULT__`, `__SKIP_ALL__`) 매핑이 명확하다.
- **문제점**:
  - "사용자의 응답을 임의로 해석하거나 보완하지 마세요"와 "사용자가 명확히 답하지 않은 질문은 재질문을 고려하세요"가 모순된다. 재질문 판단 자체가 해석 행위이다. 어느 쪽이 우선인지 기준이 없다.
  - "턴이 누적될수록 이전 턴의 요약은 더 간결해진다"는 지시가 있으나, 구체적인 압축 규칙(몇 턴 이후? 어떤 정보를 줄이나?)이 없다.

### run (agents/run.md)

- **잘된 점**: 생명주기 다이어그램이 명확하다. run.meta.md와 current-run.md의 스키마가 구체적이다. 산출물 검증 테이블이 상세하다.
- **문제점**:
  - run-id 형식이 `YYYYMMDD-HHmmss-<4자리 해시>`인데, "4자리 해시"의 생성 방법(랜덤? 입력 기반?)이 명시되지 않았다. 동일 초에 두 run이 시작되면 충돌 가능성이 있다.
  - `current-run.md`가 단일 파일이므로 동시에 여러 파이프라인을 실행할 수 없다. 설계 원칙의 "실행 격리"와 모순된다. 각 run은 격리되지만, 활성 run은 항상 하나뿐이라는 제약이 명시적으로 언급되지 않았다.
  - CLEANUP 단계에서 `current-run.md`를 idle로 갱신하는데, 파이프라인 실패(failed) 시에도 idle로 갱신하는지 정의가 불완전하다.

### config (agents/config.md)

- **문제점**:
  - "사용자 정의 파이프라인"이 Markdown 코드 블록으로 정의되어 있지만, 이 정의를 어떻게 파싱하고, 어디에 저장하며, pipeline 에이전트가 어떻게 로드하는지 메커니즘이 전혀 없다.
  - "프로필 기반 설정" 테이블이 있지만, 프로필을 전환하는 구체적인 흐름이 없다. 
  - 설정 저장 위치가 `<output-root>/config/`인데, output-root 자체를 변경하면 기존 설정에 접근이 불가능해진다. 닭과 달걀 문제.

### status (agents/status.md)

- **문제점**:
  - "산출물 내 키워드 검색"이 명시되어 있으나, 수십~수백 개의 Markdown 파일을 LLM이 직접 읽어서 키워드를 검색해야 하는지, 인덱스가 있는지 메커니즘이 없다. LLM에게 파일시스템 전문 검색을 맡기는 것은 비현실적이다.
  - "사용 통계"(파이프라인별 실행 횟수, 평균 실행 시간 등)를 산출하려면 집계 데이터가 필요하지만, run.meta.md에 실행 시간만 있고 집계 저장소가 없다. 매번 모든 run.meta.md를 스캔해야 하는데, 이는 확장성이 없다.

---

## 4. 프롬프트 분석

### 공통 문제

- **agents/ 파일과의 중복이 심각하다.** 거의 모든 프롬프트가 대응하는 에이전트 파일의 내용을 축약 복사한 것이다. 예를 들어:
  - `agents/dispatch.md`의 "파이프라인 선택 매트릭스" 테이블 = `prompts/dispatch.md`의 "Step 3: 파이프라인 선택" 테이블 (동일)
  - `agents/relay.md`의 "특수 응답 인식" 테이블 = `prompts/relay.md`의 "Step 3: 응답 매핑" (동일)
  - `agents/run.md`의 모든 액션 설명 = `prompts/run.md`의 액션별 섹션 (동일 구조, 동일 내용)
  
  이 수준의 중복은 변경 시 두 곳을 모두 수정해야 하는 동기화 비용을 발생시킨다. 하나를 수정하고 다른 하나를 빠뜨리면 불일치가 생긴다.

- **프롬프트 변수(`{{variable}}`)의 실제 주입 메커니즘이 정의되지 않았다.** skills.yaml의 input 필드명과 프롬프트의 `{{variable}}` 이름이 일치하는 것으로 보아 자동 매핑을 의도한 것 같지만, 이를 처리하는 런타임이 어디에도 명세되지 않았다.

### 개별 프롬프트 문제

- **prompts/pipeline.md**: `parallel: true`로 표시된 그룹이라 했으나, 파이프라인 정의 YAML에는 `parallel: true`가 별도 step의 속성이다. 프롬프트에서 이 구조를 어떻게 인식하는지 모호하다.
- **prompts/status.md**: "각 스킬 디렉토리의 `skills.yaml` 읽기"라 했으나, LLM이 파일시스템의 특정 경로에서 YAML을 읽는 것은 도구(tool) 호출을 전제로 한다. 어떤 도구를 사용하는지 명시되지 않았다.

---

## 5. 파이프라인/규칙 분석

### 파이프라인

**문제점**:

1. **-existing 변형의 기계적 복사.** `full-sdlc-existing`, `new-feature-existing`, `security-gate-existing`은 모두 원본 파이프라인 앞에 `ex:scan -> ex:detect -> ex:analyze -> ex:map` 4단계를 붙인 것이다. 이 패턴이 3번 반복되며, ex 단계의 정의가 파이프라인마다 완전히 동일하다. 이는 명백한 DRY 위반이며, ex 스킬에 에이전트가 추가되거나 순서가 바뀌면 모든 -existing 파이프라인을 수정해야 한다. "파이프라인 상속" 또는 "프리픽스 블록" 같은 재사용 메커니즘이 필요하다.

2. **`quick-review` 파이프라인의 입력 소스 불명.** re:review가 무엇을 리뷰하는가? 현재 파이프라인에는 업스트림이 명시되지 않았다(첫 단계이므로). 이전 run의 산출물을 입력으로 받는 메커니즘이 없다. 결국 리뷰 대상을 사용자가 직접 제공해야 하는데, 그 방법이 정의되지 않았다.

3. **`security-gate` (기존 프로젝트 없음)에서 보안 감사를 하려면 분석 대상이 필요하다.** 아키텍처 문서나 구현 코드 없이 `sec:threat-model`이 무엇을 대상으로 위협을 모델링하는지 불명확하다.

4. **파이프라인 정의 형식이 YAML 코드 블록 내 Markdown이다.** 즉, Markdown 파일 안에 YAML 코드 블록이 있다. 이것을 파싱하는 런타임이 필요한데, 구현체가 없다. skills.yaml의 pipelines.predefined에는 steps가 간략한 배열로만 있고, 각 .md 파일의 YAML은 더 상세하다. 두 정의가 병존하며 진실의 원천(source of truth)이 어디인지 모호하다.

### 규칙

**긍정적**: 4개 규칙이 관심사별로 잘 분리되어 있다. base.md의 7개 규칙이 간결하고 명확하다.

**문제점**:

1. **dialogue-protocol.md에서 `__SKIP_ALL__`의 위치가 비정상적.** `answers`가 배열인 경우와 `"__SKIP_ALL__"` 문자열인 경우가 혼재한다. 타입이 `array | string`인 것은 스키마 관점에서 좋지 않다. 일관된 구조(예: 배열 내 모든 응답을 `__SKIP__`으로)가 더 안전하다.

2. **escalation-protocol.md에서 `devops:*`로 와일드카드를 사용.** 다른 모든 스킬은 개별 에이전트를 명시하는데, devops만 와일드카드다. devops에는 8개 에이전트(slo, iac, pipeline, strategy, monitor, log, incident, review)가 있으므로 각각의 에스컬레이션 조건이 다를 것인데, 뭉뚱그린 것은 lazy한 정의다.

3. **output-format.md의 ID 체계에서 `impl`의 접두사가 `ID-`이다.** `ID-`는 "Implementation Decision"의 약자로 보이지만, 보편적으로 "ID"는 "identifier"와 혼동된다. 차라리 `IMD-` 또는 `IMPL-`이 낫다.

4. **규칙의 scope가 모두 `all`이다.** 차별화된 scope가 없으면 scope 필드의 존재 이유가 없다. 향후 확장을 위한 것이라면 현재는 불필요한 필드다.

---

## 6. 예제 분석

### 커버리지

| 시나리오 | 예제 존재 |
|----------|----------|
| 전체 SDLC 실행 (full-run) | O |
| 대화 릴레이 (dialogue-relay) | O |
| 에스컬레이션 (escalation) | O |
| 실행 재개 (resume) | O |
| 파이프라인 실패 | **X** |
| 산출물 검증 실패 | **X** |
| 동시 실행 충돌 | **X** |
| config 변경 | **X** |
| status 조회 | **X** |
| 사용자 정의 파이프라인 | **X** |
| 단일 스킬 호출 (single_skill) | **X** |
| 기존 프로젝트(-existing) 파이프라인 | **X** |

**4개 예제 중 긍정적 시나리오만 존재.** 실패, 엣지 케이스, 비정상 흐름이 전무하다. 시스템의 견고성을 판단할 수 없다.

### 개별 예제 문제

1. **dialogue-relay-example.md의 `__SKIP_ALL__` 사용이 논란적.** 125~126행에서 "전부 기본값으로"를 `__SKIP_ALL__`로 매핑하면서 "에이전트는 각 질문의 default 값을 사용합니다"라고 설명한다. 그런데 `__SKIP_ALL__`은 dialogue-protocol.md에서 "모든 질문을 건너뛰고 최선의 판단으로 진행"이라 정의되어 있다. "기본값 사용"과 "최선의 판단"은 다른 의미인데, 예제에서 이를 같은 것으로 취급한다. `__DEFAULT__`를 각 질문에 적용하는 것이 의미적으로 정확하다.

2. **full-run-example.md에서 re:elicit의 output_sections에 `constraints`, `quality_attribute_priorities`가 포함.** 그런데 `re:elicit`은 "요구사항 도출"이지 "명세"가 아니다. constraints와 quality_attribute_priorities는 re:spec 또는 re:analyze의 산출물이어야 하는 것이 아닌지 의문이다. 스킬 간 산출물 경계가 혼란스럽다.

3. **resume-example.md의 dialogue_context 필드.** run 에이전트의 resume_info에 `dialogue_context`가 있는데, 이 필드는 run.md에도 skills.yaml에도 정의되지 않은 필드다. 예제에서 즉흥적으로 추가한 것으로 보인다.

---

## 7. 일관성 검토

### 용어 불일치

| 위치 | 용어 A | 용어 B | 문제 |
|------|--------|--------|------|
| re/skills.yaml vs orch/skills.yaml | `multi-turn` | `dialogue` | interaction_mode 불일치 |
| agents/dispatch.md vs prompts/dispatch.md | "선행 조건 검증" | "Step 4: 선행 조건 검증" | 동일 내용의 이름만 다름 (사소) |
| agents/run.md 생명주기 | INIT, CONFIGURE, EXECUTE, ... | init, update_status, validate_and_save, ... | 대문자 생명주기 단계와 소문자 액션이 1:1 매핑되지 않음 |
| dialogue-protocol.md | `__SKIP_ALL__` (answers가 문자열) | `__SKIP__` (answers 배열 내 개별 응답) | 타입 불일치 |

### 네이밍 불일치

- 파이프라인 파일명은 kebab-case (`full-sdlc.md`), 산출물 파일명은 snake_case (`requirements_spec.md`), 에이전트/스킬 참조는 colon 구분 (`re:elicit`). 세 가지 컨벤션이 혼재하는데, 각 컨벤션의 적용 범위가 명시적으로 정의되지 않았다.
- `sec:threat-model`에서 에이전트명에 하이픈을 사용하는데, 다른 에이전트는 모두 단일 단어(`scan`, `detect`, `elicit`, `generate`). 하이픈이 있는 에이전트명이 colon 구분(`sec:threat-model`)에서 파싱 문제를 일으킬 수 있다.

### 형식 불일치

- skills.yaml의 `description` 필드: 일부는 한 줄 문자열, 일부는 YAML `>` 블록.
- 파이프라인 .md 파일: 일부는 "특징" 섹션이 있고(`explore.md`), 일부는 없다(`security-gate.md`). 일부는 "핵심 차이점" 섹션이 있다(`full-sdlc-existing.md`). 템플릿이 통일되지 않았다.

---

## 8. 주요 문제점 (심각도 순)

### [치명적] 런타임 구현체의 부재

skills.yaml과 에이전트 정의가 아무리 정교해도, 이것을 실제로 실행하는 런타임(프롬프트 변수 주입, 에이전트 스폰, 파이프라인 순차/병렬 실행, 파일 I/O)이 어디에도 없다. 이 모든 문서는 LLM이 자연어로 읽고 자율적으로 해석하여 실행하는 것을 전제로 하는데, 그렇다면 정밀한 YAML 스키마와 프로토콜이 LLM에 의해 정확히 이행될 것이라는 강한 가정이 필요하다. 이 가정의 타당성이 검증되지 않았다.

### [치명적] 에이전트/프롬프트 간 대규모 중복

6개 에이전트 정의와 6개 프롬프트 사이에 동일 내용이 반복된다. 변경 시 12개 파일 중 정확히 어디를 수정해야 하는지 불명확하며, 동기화 실패가 거의 확실하다.

### [심각] 파이프라인 정의의 이중성

파이프라인이 skills.yaml의 `steps` 배열과 개별 `.md` 파일의 YAML 코드 블록으로 이중 정의되어 있다. 어느 쪽이 권위 있는 정의인지 불명확하다. 둘이 다르면 어떤 것을 따르는가?

### [심각] -existing 파이프라인의 DRY 위반

ex 4단계 블록이 3개 파이프라인에 복사-붙여넣기 되어 있다. 재사용 메커니즘이 필요하다.

### [심각] 동시 실행 불가 제약의 미명시

`current-run.md`가 싱글톤이므로 동시에 하나의 파이프라인만 실행 가능하다. 이 제약이 어디에도 명시적으로 언급되지 않으며, "실행 격리" 설계 원칙과 혼동을 줄 수 있다.

### [중간] quick-review와 security-gate의 입력 소스 불명

리뷰 대상이나 보안 감사 대상이 이전 run에서 오는 것인지, 사용자가 직접 제공하는 것인지 정의되지 않았다.

### [중간] dialogue-protocol의 `__SKIP_ALL__` 타입 불일치

`answers` 필드가 배열 또는 문자열이 될 수 있는 것은 스키마 오류의 원천이다.

### [경미] status 에이전트의 키워드 검색/통계 비현실성

LLM이 파일시스템을 스캔하여 키워드 검색과 집계 통계를 산출하는 것은 비현실적이다.

---

## 9. 개선 제안

### 제안 1: agents/와 prompts/ 통합

각 에이전트를 단일 파일로 통합한다. 예: `agents/dispatch.md` 하나에 역할(system prompt 부분), 실행 지시(prompt template 부분), 입출력 스키마를 모두 포함한다. `prompts/` 디렉토리를 제거하고, skills.yaml에서 `prompt_template`을 삭제한다.

### 제안 2: 파이프라인 정의 일원화

skills.yaml의 `pipelines.predefined`를 참조 목록으로만 남기고, 각 `.md` 파일의 YAML 블록을 단독 `.yaml` 파일로 추출하여 권위 있는 정의로 삼는다. `.md` 파일은 해당 파이프라인의 문서/설명용으로만 사용한다.

### 제안 3: ex 프리픽스 블록 재사용

```yaml
# shared/ex-prefix.yaml
ex_prefix:
  steps:
    - { order: 1, skill: ex, agent: scan, mode: auto-execute }
    - { order: 2, skill: ex, agent: detect, mode: auto-execute, upstream: [ex:scan] }
    - { order: 3, skill: ex, agent: analyze, mode: auto-execute, upstream: [ex:scan, ex:detect] }
    - { order: 4, skill: ex, agent: map, mode: auto-execute, upstream: [ex:scan, ex:detect, ex:analyze] }
```

각 -existing 파이프라인은 이 블록을 참조하여 확장한다.

### 제안 4: 실패/엣지 케이스 예제 추가

최소한 다음 예제를 추가해야 한다:
- 파이프라인 중간 스킬 실패 + 후속 스킬 처리
- 산출물 검증 실패 + 재시도 흐름
- 잘못된 프로젝트 경로로 인한 ex:scan 실패
- single_skill 호출 예제

### 제안 5: interaction_mode 용어 통일

orch에서 사용하는 `dialogue` / `auto-execute`와 하위 스킬의 `multi-turn` / `auto-execute`를 일원화한다. 가능하면 orch가 하위 스킬의 용어를 그대로 따르는 것이 상위 호환이다.

### 제안 6: 동시 실행 제약 명시 또는 해결

- 단기: 설계 원칙에 "단일 활성 실행" 제약을 명시한다.
- 장기: `current-run.md`를 `current-runs/` 디렉토리로 변경하여 다중 실행을 지원한다.

### 제안 7: 업스트림 매핑의 선언적 정의

pipeline.md에 하드코딩된 업스트림 소비 테이블을 각 스킬의 `skills.yaml`에 `consumers` 또는 `upstream_requires` 필드로 선언한다. 이렇게 하면 스킬 추가 시 pipeline 에이전트를 수정할 필요가 없다.

### 제안 8: `__SKIP_ALL__` 타입 일관성

`answers: "__SKIP_ALL__"` 대신, 모든 question_id에 `__SKIP__`을 채운 배열로 통일하거나, 별도 플래그 필드(`skip_all: true`)를 추가한다.

---

## 총평

orch 스킬은 야심찬 오케스트레이션 시스템의 **설계 문서**로서는 상당한 완성도를 보인다. 파이프라인, 에이전트, 대화 프로토콜, 에스컬레이션 규약, 산출물 형식 등 다양한 관심사를 체계적으로 분리했다. 특히 `current-run.md`를 통한 빠른 컨텍스트 복원, `needs_user_input`/`user_response` 대화 프로토콜, 에스컬레이션 규약은 잘 설계되었다.

그러나 핵심적인 문제는 세 가지다:

1. **문서 중복**: agents/와 prompts/, skills.yaml와 pipeline .md 파일 간의 대규모 중복이 유지보수 비용을 크게 높인다.
2. **구현 갭**: 이 모든 정교한 프로토콜을 실행하는 런타임이 부재하며, LLM의 자율적 해석에 의존한다면 그 신뢰성을 보장하는 메커니즘이 없다.
3. **부정적 시나리오 부재**: 행복 경로(happy path)만 상세하게 설계되었으며, 실패, 충돌, 엣지 케이스에 대한 정의가 취약하다.
