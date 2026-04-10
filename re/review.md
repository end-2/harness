# RE (Requirements Engineering) 스킬 코드 리뷰

---

## 1. 구조 분석

### 디렉토리 구조

```
re/
├── skills.yaml
├── agents/
│   ├── elicit.md
│   ├── analyze.md
│   ├── spec.md
│   └── review.md
├── prompts/
│   ├── elicit.md
│   ├── analyze.md
│   ├── spec.md
│   └── review.md
└── examples/
    ├── elicit-input.md / elicit-output.md
    ├── analyze-input.md / analyze-output.md
    ├── spec-input.md / spec-output.md
    └── review-input.md / review-output.md
```

**양호한 점**: 4개 에이전트(elicit, analyze, spec, review)에 대해 agents/prompts/examples가 1:1:1로 정확하게 대응한다. 파이프라인 단계별 명확한 파일 분리.

**문제점**:

- `agents/`와 `prompts/`의 역할 구분이 모호하다. `agents/*.md`는 시스템 프롬프트(역할, 핵심 역량, 프로세스)이고 `prompts/*.md`는 턴별 프롬프트 템플릿인데, 실제 내용을 비교하면 **상당 부분이 중복**된다. 예를 들어 `agents/analyze.md`의 "충돌 및 모순 탐지" 설명과 `prompts/analyze.md`의 "Step 1: 충돌 분석"은 같은 내용을 다른 표현으로 반복한다. 이는 유지보수 시 동기화 실패의 원인이 된다.
- `arch` 스킬과 비교하면 구조는 동일하므로 일관성 자체는 있다. 다만, 이 중복 구조가 harness 전체의 설계 결함인지 의도적 분리인지 명시된 곳이 없다.

---

## 2. skills.yaml 분석

### 양호한 점

- 4단계 파이프라인(elicit → analyze → spec → review) 정의가 명확하고, 각 단계에 `checkpoint: true`가 설정되어 사용자 개입 지점이 보장된다.
- 입출력 스키마가 필드 수준까지 정의되어 있고, ID 패턴(`^(FR|NFR)-\d{3}$`, `^CON-\d{3}$`)이 명시되어 있다.
- `consumers` 섹션에서 하류 스킬(arch, qa, impl, sec, devops)이 어떤 산출물을 소비하는지 정의하여 스킬 간 계약이 명확하다.

### 문제점

1. **`dependencies` (upstream) 섹션 누락**: `arch/skills.yaml`에는 `dependencies.upstream`에서 `re:spec`을 명시적으로 참조한다. 반면 `re/skills.yaml`에는 `dependencies` 섹션 자체가 없다. RE가 파이프라인의 첫 단계라면 `dependencies: { upstream: [] }`을 명시적으로 기록하는 것이 다른 스킬과의 일관성을 위해 필요하다. `ex` 스킬은 `dependencies: { upstream: [] }`을 명시하고 있다.

2. **`consumers`의 스킬 이름 불일치**: `re/skills.yaml`에서 `sec`, `devops`로 참조하고, 실제 스킬 이름도 `sec`, `devops`이다. 그런데 `arch/skills.yaml`, `impl/skills.yaml`, `devops/skills.yaml` 등에서는 같은 스킬을 `security`, `deployment`, `operation`으로 참조하고 있다. 이것은 harness 전체의 명명 불일치 문제이지만, RE 스킬의 `consumers` 테이블에서 참조하는 하류 에이전트 이름(`arch:design`, `qa:strategy` 등)이 실제 해당 스킬의 에이전트 이름과 일치하는지 검증이 필요하다. `qa`의 에이전트는 `strategy`가 맞고, `sec`의 에이전트는 `threat-model`이 맞고, `devops`의 에이전트는 `slo`가 맞지만, `impl`의 에이전트 중에 `generate`라는 이름의 에이전트가 실제로 존재하는지는 확인이 필요하다.

3. **`adaptive_depth` 정의의 불완전성**: `elicit`의 `adaptive_depth`는 `high_level` / `mid_level` / `detailed` 3단계인 반면, `spec`의 `adaptive_depth`는 `lightweight` / `heavyweight` 2단계다. `analyze`와 `review`에는 `adaptive_depth`가 아예 없다. 이 비대칭이 의도적인지 불분명하다. 또한 `elicit`의 3단계 키 네이밍(`high_level`, `mid_level`, `detailed`)과 `spec`의 2단계 키 네이밍(`lightweight`, `heavyweight`)이 다른 스킬(`ex`, `arch`)의 관례(`lightweight`/`heavyweight`)와 맞지 않는다.

4. **elicit 출력과 analyze 입력 간의 스키마 불일치**: `elicit.output`에는 `requirements_candidates`, `constraints_candidates`, `quality_attribute_hints`, `open_questions` 4개 필드가 있다. 그런데 `analyze.input`은 단순히 `elicit_output: { type: object }`로만 정의되어 있어, 구체적 필드 참조가 없다. 반면 `prompts/analyze.md`에서는 `{{requirements_candidates}}`, `{{constraints_candidates}}` 등을 직접 참조한다. 스키마 정의와 프롬프트 템플릿 간에 암묵적 의존이 발생하고 있다. `spec.input`과 `review.input`도 동일한 문제가 있다 — 모두 `type: object`로 뭉개져 있어 필드 수준의 계약이 깨져 있다.

5. **출력 필드의 `required` 누락**: `spec.output`의 세 섹션에는 `required: true`가 붙어 있지만, `elicit.output`과 `analyze.output`의 필드에는 `required` 표시가 전혀 없다. `review.output`도 마찬가지다.

6. **`max_turns` 근거 부재**: elicit=20, analyze=10, spec=10, review=5로 설정되어 있다. 이 수치의 근거가 없다. 특히 elicit의 20턴은 사용자 피로도를 고려했을 때 과도할 수 있고, review의 5턴은 Critical 이슈 발견 시 수정-재검증 루프에 불충분할 수 있다.

---

## 3. 에이전트 정의 분석

### agents/elicit.md

**양호한 점**: 적응적 질문 전략(3단계), 대화 상태 관리(`확인됨/미확인/가정됨`), 이해관계자 역할 대행, 대화 종료 조건이 잘 정의되어 있다.

**문제점**:

- "3-5턴마다 또는 주요 주제가 전환될 때" 요약을 제시한다고 되어 있으나, "주요 주제 전환"의 판단 기준이 모호하다.
- 출력 형식 테이블의 컬럼이 skills.yaml의 스키마와 미묘하게 다르다. 에이전트 md에서는 `수용 기준`이라 하고, skills.yaml에서는 `acceptance_criteria`다. 이런 한-영 혼용이 혼란을 준다.
- "targeted question"이라는 영어 표현이 갑자기 등장한다. 전체적으로 한국어로 작성된 문서에서 불필요한 영어 혼용이 산발적이다.

### agents/analyze.md

**양호한 점**: 5가지 핵심 역량(충돌 탐지, 누락 식별, 실현 가능성, 의존 관계, 트레이드오프)이 체계적이다. 트레이드오프 제시 포맷이 구체적이다.

**문제점**:

- 분석 프로세스가 8단계로 나열되어 있으나, 이것은 프롬프트 `prompts/analyze.md`의 7 Step과 거의 동일하면서 미묘하게 다르다. 에이전트 md에는 "입력 검수"가 1단계로 있으나 프롬프트에는 없다. 에이전트에는 "결과 제시"가 있고 프롬프트에도 "Step 7: 결과 제시"가 있지만, 에이전트 md는 8단계이고 프롬프트는 7단계다. 이 차이는 혼란을 야기한다.
- "모든 요구사항 쌍에 대해 충돌 가능성 평가"라는 지시는 요구사항이 많을 때 O(n^2) 조합 폭발을 암시하지만, 실질적으로 LLM이 이를 수행할 수 있는지에 대한 고려가 없다.

### agents/spec.md

**양호한 점**: 세 섹션 구조가 명확하고, YAML 예시가 포함되어 구체적이다. 후속 스킬 소비 계약 테이블이 유용하다.

**문제점**:

- "적응적 명세 수준"의 경량/중량 판별 기준이 skills.yaml과 불일치한다. agents/spec.md에서는 경량 "요구사항 5개 이하", 중량 "10개 이상"이라 하고, skills.yaml에서도 동일하게 정의한다. 그런데 **5~9개인 경우의 기준이 없다**. 이 갭은 실제 사용 시 판단 불가 상황을 만든다.
- ID 체계에서 FR-XXX와 NFR-XXX는 정의되어 있으나, 품질 속성(Quality Attribute)에 대한 ID 체계가 없다. 제약 조건은 CON-XXX가 있다.

### agents/review.md

**양호한 점**: SMART 기준 검증이 구체적이고, 모호성 탐지 패턴이 실용적이다. 후속 스킬 소비 적합성 체크리스트가 있다. 3단계 판정(APPROVED/CONDITIONAL/REJECTED)이 명확하다.

**문제점**:

- 리뷰 에이전트의 후속 스킬 소비 적합성 테이블에서 `impl:generate`를 참조하는데, impl 스킬의 실제 에이전트 이름이 `generate`인지 확인되지 않는다. impl 스킬에 `generate`라는 에이전트가 존재하지 않으면 이 참조는 사실상 무효다.
- "자동 검증"이라는 단계 1이 있으나, 실제로는 LLM이 수행하는 수동 리뷰다. "자동"이라는 용어가 오해를 유발한다.
- REJECTED 시 "수정 후 재리뷰"가 필요하다고 하지만, 재리뷰의 루프 메커니즘이 skills.yaml의 파이프라인에 정의되어 있지 않다. 파이프라인은 단순히 `elicit → analyze → spec → review` 순차 실행이고, review에서 REJECTED가 나왔을 때 spec 단계로 돌아가는 메커니즘이 없다.

---

## 4. 프롬프트 분석

### prompts/elicit.md

**양호한 점**: Step 1~7의 단계적 지시가 명확하다. 질문 우선순위(범위 → 핵심 기능 → NFR → 제약 → 경계 조건) 가이드가 실용적이다.

**문제점**:

- "한 번에 3개 이하의 질문을 제시하세요"라는 규칙이 있으나, 이것이 agents/elicit.md에는 없다. 시스템 프롬프트와 턴 프롬프트 사이의 규칙 분배가 일관적이지 않다.
- 주의사항의 "기술적 결정은 이 단계에서 확정하지 않습니다"는 중요한 규칙이지만, 사용자가 "React로 해주세요"라고 명시할 경우 어떻게 처리하는지의 가이드가 없다.

### prompts/analyze.md

**양호한 점**: 체크리스트 기반 누락 분석(기능/비기능/예외 관점)이 체계적이다. 실현 가능성 평가의 구체적 포맷이 좋다.

**문제점**:

- 템플릿 변수 `{{requirements_candidates}}`가 사용되지만, 이 변수가 어떤 형식으로 주입되는지(JSON? YAML? 테이블?) 정의되지 않았다. LLM이 파싱할 수 있는 형식인지 보장이 없다.
- Step 4의 의존 관계 다이어그램이 ASCII 트리 형태인데, 이것이 기계적으로 파싱 가능한 형식인지 불분명하다. 실제 출력 예시에서도 비공식적인 ASCII 트리를 사용한다.

### prompts/spec.md

**양호한 점**: 각 섹션별 체크리스트가 포함되어 자체 검증이 가능하다.

**문제점**:

- "우선순위 간 동률이 없는가 (동률 시 사용자에게 질문)"라는 체크 항목이 있는데, 이것은 품질 속성의 priority가 정수형 순위(1, 2, 3...)라서 동률이 발생할 수 있음을 전제한다. 그런데 실제로 LLM이 "동률 없음"을 강제할 메커니즘이 없다.

### prompts/review.md

**양호한 점**: 5개 후속 스킬 각각에 대한 소비 적합성 체크리스트가 구체적이다.

**문제점**:

- agents/review.md와의 내용 중복이 극심하다. SMART 검증, 모호성 탐지, 제약 검증, 품질 속성 검증, 후속 스킬 적합성의 거의 모든 내용이 양쪽에 동시 존재한다. 어느 쪽이 canonical source인지 불분명하다.

---

## 5. 예제 분석

### 전체 평가

모든 예제가 **"사내 휴가 관리 시스템"**이라는 단일 도메인을 사용하여 일관되게 연결된다. elicit의 출력이 analyze의 입력이 되고, analyze의 출력이 spec의 입력이 되는 파이프라인 흐름이 예제로 추적 가능하다. 이 점은 좋다.

### 문제점

1. **도메인 다양성 부족**: 4개 에이전트 모두 동일한 "휴가 관리 시스템" 예제만 사용한다. elicit-input.md에 3가지 수준(고수준/중간/상세)의 입력 예시가 있으나, 출력 예시는 고수준 입력에 대한 것만 있다. 중간 수준(할일 관리)과 상세 수준(채팅 시스템)의 출력 예시가 없어, 적응적 깊이의 실제 차이를 확인할 수 없다.

2. **spec-output.md의 모드 판별 오류**: 파일 헤더에 "경량 모드 (요구사항 12개)"라고 되어 있다. 그런데 skills.yaml과 agents/spec.md에서 경량 모드의 조건은 "요구사항 5개 이하"이다. 12개 요구사항은 중량 모드(10개 이상) 조건에 해당한다. **이것은 명백한 오류**로, 예제가 자체 정의와 모순된다.

3. **elicit-output에 multi-turn 대화 과정 미포함**: elicit은 `interaction_mode: multi-turn`이고 최대 20턴까지 가능한 대화형 에이전트다. 그런데 출력 예시에는 최종 산출물만 있고, 중간 대화 과정(질문-답변 시퀀스)이 없다. 실제 동작을 이해하려면 최소한 주요 턴의 대화 예시가 필요하다. `source` 필드에 "(Turn 2)", "(Turn 8)" 등이 적혀 있어 대화가 있었음을 암시하지만, 그 대화 자체는 볼 수 없다.

4. **analyze-output에서 FR-009(대리 승인)의 처리**: 추가 제안으로 FR-009가 등장하는데, spec-input에서 사용자가 "Won't"으로 결정했다고 한다. 그런데 spec-output에는 FR-009가 아예 등장하지 않는다. Won't 항목도 명세에 포함하여 "의도적으로 제외된 범위"를 기록하는 것이 일반적인 요구사항 공학 관행이지만, 이에 대한 가이드가 없다.

5. **review-input.md가 지나치게 간략**: 3줄짜리 요약에 불과하다. "spec-output.md의 전체 내용이 입력됩니다"라고만 되어 있어, 실제 입력 형식을 보여주지 못한다. 다른 예제(analyze-input)는 실제 데이터를 포함하고 있어 이와 대조적이다.

6. **review-output에서 판정 용어 불일치**: skills.yaml에서 `review.output.review_report.properties.downstream_readiness`를 정의하고, agents/review.md에서는 "후속 스킬 소비 적합성" 테이블에 "판정" 컬럼을 사용한다. 그런데 review-output.md에서는 PASS/CONDITIONAL을 사용하고, 최종 판정에서는 APPROVED/CONDITIONAL/REJECTED를 사용한다. 소비 적합성의 개별 판정(PASS)과 전체 판정(APPROVED)의 용어 체계가 분리되어 있지만 이것이 어디에도 정의되어 있지 않다.

---

## 6. 일관성 검토

### 용어 불일치

| 위치 | 표현 A | 표현 B | 문제 |
|------|--------|--------|------|
| skills.yaml vs agents/*.md | `acceptance_criteria` | `수용 기준` | 한-영 혼용 |
| skills.yaml `consumers` vs 실제 스킬명 | `sec`, `devops` (RE) | `security`, `deployment` (arch, impl) | 하네스 전체 명명 불일치. RE는 올바른 이름 사용 |
| agents/analyze.md vs prompts/analyze.md | 8단계 프로세스 | 7 Step | 단계 수 불일치 |
| agents/spec.md vs prompts/spec.md | "단계 1~5" | "Step 1~6" | 단계 수 불일치 (agents는 5단계, prompts는 6단계) |
| review-output.md 내부 | PASS (개별 적합성) | APPROVED (전체 판정) | 미정의된 용어 분리 |

### 네이밍 불일치

| 항목 | RE 스킬 | 다른 스킬(ex, arch) |
|------|---------|-------------------|
| adaptive_depth 키 | `high_level`, `mid_level`, `detailed` (elicit) / `lightweight`, `heavyweight` (spec) | `lightweight`, `heavyweight` 통일 |
| dependencies 섹션 | 누락 | `dependencies: { upstream: [...] }` |

### 형식 불일치

- `elicit.output.requirements_candidates.items`의 각 필드에 `{ type: string }`이 명시되어 있으나, `spec.output.requirements_spec.items`에서 `acceptance_criteria`는 `{ type: array }`로만 되어 있고 `items`의 타입이 빠져 있다. `dependencies`도 마찬가지다.
- `elicit.output.requirements_candidates.items.id`에는 `pattern: "^(FR|NFR)-\\d{3}$"`가 있지만, `spec.output.requirements_spec.items.id`에는 `{ type: string }`만 있고 패턴이 없다.

---

## 7. 주요 문제점 (심각도 순)

### Critical

1. **agents/*.md와 prompts/*.md의 역할 분리 실패 및 대규모 중복**: 시스템 프롬프트와 턴 프롬프트에 동일한 내용이 다른 표현으로 반복되어 있다. 둘 중 하나가 변경되면 나머지가 동기화되지 않아 LLM에 모순된 지시가 전달될 수 있다. 특히 analyze와 review에서 이 문제가 심각하다.

2. **파이프라인에 재작업(rework) 루프가 없음**: review 에이전트가 REJECTED 판정을 내릴 수 있지만, skills.yaml의 파이프라인은 단순 순차(`elicit → analyze → spec → review`)이고 이전 단계로 돌아가는 메커니즘이 정의되지 않았다. 요구사항 공학에서 반복(iteration)은 핵심인데, 이것이 구조적으로 지원되지 않는다.

3. **중간 에이전트의 입력 스키마가 `type: object`로 뭉개져 있음**: analyze, spec, review의 입력이 모두 이전 에이전트의 출력을 `type: object`로만 참조하여 필드 수준의 계약이 없다. 이전 에이전트의 출력 스키마가 변경되어도 하류 에이전트의 입력 스키마에는 변경이 감지되지 않는다.

### Major

4. **spec-output 예제의 모드 판별 오류**: "경량 모드 (요구사항 12개)"라고 표기되어 있으나, 정의상 12개는 중량 모드 조건이다.

5. **적응적 깊이 5~9개 갭**: 경량(5개 이하)과 중량(10개 이상) 사이에 6~9개 요구사항에 대한 판별 기준이 없다.

6. **Won't 항목의 처리 가이드 부재**: MoSCoW에서 Won't은 "이번 범위에서 제외"를 의미하지만, 제외된 항목을 명세에 기록할지 말지에 대한 가이드가 없다. 예제에서도 FR-009(대리 승인)가 Won't으로 결정되었으나 spec-output에서 사라진다.

### Minor

7. **elicit의 `adaptive_depth` 키 네이밍이 관례와 불일치**: `high_level`/`mid_level`/`detailed`는 다른 스킬의 `lightweight`/`heavyweight` 관례와 다르다. elicit만 3단계라는 차이는 있지만, 최소한 키 네이밍 스타일(snake_case는 동일)은 통일되어야 한다.

8. **프롬프트 템플릿 변수의 주입 형식 미정의**: `{{requirements_candidates}}`, `{{refined_requirements}}` 등이 어떤 형식(JSON, YAML, Markdown 테이블)으로 치환되는지 정의되지 않았다.

9. **review-input.md의 내용 빈약**: 실제 입력 데이터 없이 참조만 있어 예제로서의 가치가 낮다.

---

## 8. 개선 제안

### 즉시 수정 (Critical/Major)

1. **agents와 prompts의 책임 분리 재설계**: agents/*.md는 에이전트의 정체성(역할, 원칙, 제약)만 기술하고, prompts/*.md는 실행 절차(Step-by-step)와 출력 형식만 기술하도록 분리한다. 현재 양쪽 모두에 들어 있는 실행 절차와 출력 형식을 한쪽으로 통합한다.

2. **파이프라인에 조건부 루프 추가**: review가 REJECTED를 반환하면 spec(또는 analyze)으로 돌아가는 루프를 `pipeline` 정의에 추가한다.
   ```yaml
   pipeline:
     stages:
       - agent: review
         checkpoint: true
         on_rejected: spec  # 또는 analyze
   ```

3. **중간 에이전트의 입력 스키마를 필드 수준으로 구체화**: `analyze.input`을 `elicit_output: { type: object }` 대신 `requirements_candidates: { type: array, ... }`, `constraints_candidates: { type: array, ... }` 등으로 분해한다. spec과 review도 동일하게 적용한다.

4. **spec-output.md의 모드 표기를 "중량 모드"로 수정**: 또는 예제의 요구사항 수를 5개 이하로 줄여 실제 경량 모드 예제를 만든다. 양쪽 모드의 예제가 각각 있는 것이 이상적이다.

5. **적응적 깊이 갭 해소**: 5~9개 범위에 대한 판별 기준을 추가하거나, 경량/중량 경계를 단일 임계값(예: 7개)으로 통합한다.

### 중기 개선 (Minor)

6. **Won't 항목 처리 규칙 추가**: spec 에이전트에 "Won't 항목도 명세에 포함하되, 제외 사유와 함께 기록한다"는 규칙을 추가한다.

7. **`dependencies` 섹션을 RE에 명시 추가**: `dependencies: { upstream: [] }`을 추가하여 harness 전체 스킬과 형식 일관성을 맞춘다.

8. **템플릿 변수 주입 형식 표준 정의**: 하네스 수준에서 `{{variable}}`이 YAML 블록으로 치환되는지, Markdown 테이블인지 등을 표준화한다.

9. **예제 다양성 확보**: 최소 1개의 추가 도메인 예제(예: 중간 수준 입력인 "할일 관리 앱"의 전체 파이프라인 예제)를 추가하여 적응적 깊이의 차이를 보여준다.

10. **review-input.md에 실제 데이터 포함**: spec-output.md의 내용을 그대로 복사하거나, 최소한 주요 섹션의 요약을 포함한다.

11. **elicit의 adaptive_depth 키를 관례에 맞게 변경**: `high_level` → `exploratory`, `mid_level` → `clarifying`, `detailed` → `boundary` 등 의미 기반 네이밍으로 통일하거나, 최소한 다른 스킬과의 불일치를 skills.yaml 주석으로 설명한다.

---

## 총평

RE 스킬은 요구사항 공학의 4단계 프로세스(도출, 분석, 명세, 검증)를 체계적으로 구조화한 점에서 설계 의도는 명확하다. 후속 스킬과의 소비 계약, MoSCoW 우선순위, 적응적 깊이 등 실용적인 요소가 포함되어 있다.

그러나 agents와 prompts 간의 대규모 중복, 파이프라인의 재작업 루프 부재, 중간 에이전트의 느슨한 입력 스키마는 실제 운용 시 유지보수 비용과 오류 가능성을 높인다. 특히 예제에서 자체 규칙을 위반하는 모드 판별 오류는 신뢰도를 떨어뜨린다. 이 문제들은 스킬이 단독으로 존재하는 것이 아니라 harness 파이프라인의 첫 단계로서 하류 스킬 전체에 영향을 미치기 때문에, 조기에 수정하는 것이 바람직하다.
