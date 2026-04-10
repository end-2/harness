# Arch 스킬 코드/설계 리뷰

## 1. 구조 분석

### 디렉토리 구조

```
arch/
├── skills.yaml
├── agents/
│   ├── design.md
│   ├── review.md
│   ├── adr.md
│   └── diagram.md
├── prompts/
│   ├── design.md
│   ├── review.md
│   ├── adr.md
│   └── diagram.md
└── examples/
    ├── design-input.md / design-output.md
    ├── review-input.md / review-output.md
    ├── adr-input.md / adr-output.md
    └── diagram-input.md / diagram-output.md
```

구조 자체는 깔끔하다. `agents/`, `prompts/`, `examples/`의 3-tier 분리는 역할이 명확하고, 각 에이전트별로 동일한 파일명 패턴을 유지한다.

**문제점**:

- **agents/ 와 prompts/ 의 역할 경계가 모호하다.** `agents/design.md`와 `prompts/design.md`의 내용이 70% 이상 중복된다. 둘 다 "지시사항", "단계별 프로세스", "주의사항"을 포함한다. `agents/`가 system prompt이고 `prompts/`가 prompt template이라면, system prompt에는 역할/원칙/제약만, prompt template에는 입력 변수 바인딩과 실행 지시만 있어야 한다. 현재는 둘 다 동일한 단계별 프로세스를 반복 기술하고 있어, 하나를 수정하면 다른 하나도 동기화해야 하는 유지보수 부담이 있다.
- **examples/ 의 input 파일 중 adr-input.md, diagram-input.md, review-input.md 는 사실상 내용이 없다.** "design-output.md를 참조하라"는 포인터일 뿐이다. 이는 예제로서의 가치가 없다. 독립적으로 읽을 수 있는 완전한 입력 예제여야 한다.

---

## 2. skills.yaml 분석

### 긍정적 측면
- 4개 에이전트(design, review, adr, diagram)의 역할 분리가 명확하다.
- input/output 스키마 정의가 상세하고, 패턴 검증(`pattern: "^AD-\\d{3}$"`)까지 포함되어 있다.
- `pipeline`, `dependencies`, `consumers`, `architecture_patterns` 섹션이 스킬 간 관계를 명시적으로 표현한다.

### 문제점

1. **파이프라인 순서가 비논리적이다.** `pipeline.stages`의 순서가 design → adr → diagram → review 인데, review 에이전트는 `design_output`과 `re_spec`을 입력으로 받는다. ADR과 다이어그램은 review의 입력에 포함되지 않는다. 그렇다면 review가 ADR/다이어그램의 품질은 검증하지 않는다는 의미인데, 파이프라인 마지막에 위치한 것이 "최종 관문" 역할을 하는 것처럼 보여 오해를 유발한다. review를 design 직후에 놓고, ADR/diagram은 review 통과 후 생성하는 것이 논리적으로 타당하다.

2. **adaptive_depth 의 경량/중량 판별 기준이 design과 diagram에서 불일치한다.** design 에이전트는 `trigger` 조건을 명시(FR ≤ 5, NFR ≤ 2, QA ≤ 3)하지만, diagram 에이전트는 trigger 조건 없이 output만 명시한다. diagram이 어떤 기준으로 경량/중량을 판별하는지 skills.yaml만으로는 알 수 없다. design의 모드를 상속하는 것이라면 그 의존성을 명시해야 한다.

3. **review 에이전트의 input 정의가 느슨하다.** `design_output`과 `re_spec`이 모두 `type: object`로만 정의되어 있고 내부 properties가 없다. design 에이전트의 output 스키마는 상세하게 정의해놓고, 그것을 소비하는 review의 input에서는 "object"로 퉁치는 것은 일관성이 없다.

4. **adr 에이전트의 input에 RE 참조 정보가 없다.** adr 에이전트는 `architecture_decisions`만 입력으로 받는데, ADR 작성 시 RE 산출물 ID를 명시해야 한다고 agents/adr.md에서 강조한다. `architecture_decisions` 내부의 `re_refs`를 통해 간접적으로 참조하겠지만, RE 원본 데이터(requirements_spec, constraints)를 직접 참조할 수 없어 컨텍스트가 불완전하다.

5. **`consumers` 섹션에 존재하지 않는 스킬들이 참조된다.** `security`, `deployment`, `operation` 스킬이 consumers로 명시되어 있으나, 실제 리포지토리에는 `sec`, `devops` 스킬만 존재한다. 네이밍이 불일치하거나 아직 구현되지 않은 스킬을 참조하고 있다.

6. **`architecture_patterns.catalog`이 skills.yaml에 하드코딩되어 있다.** 7개 패턴 카탈로그가 스킬 정의 파일에 직접 포함되어 있는데, 이는 agents/design.md에도 동일한 테이블로 중복되어 있다. 패턴이 추가/변경되면 두 곳을 수정해야 한다.

7. **version이 1.0.0인데 실질적으로 검증되지 않은 상태이다.** 0.x.x가 적절하다.

---

## 3. 에이전트 정의 분석

### agents/design.md

**품질**: 높은 편. RE 산출물 해석 방법, 기술적 맥락 도출 영역, 산출물 구조가 구체적이다.

**문제점**:
- **"기술적 맥락 질문"의 우선순위/순서 전략이 없다.** "다음 영역을 확인합니다"로 4개 영역(팀 역량, 인프라, 비용, 코드베이스)을 나열하지만, 어떤 맥락이 이미 제약 조건에서 확인된 경우 생략하라는 규칙이 없다. prompts/design.md에서는 "제약 조건에서 이미 확인된 정보는 재질문하지 마세요"라고 명시하는데, agents/design.md에는 이 규칙이 빠져있다.
- **"단계 1~5" 상호작용 프로세스가 prompts/design.md의 "Step 1~7"과 단계 수가 다르다.** agents는 5단계, prompts는 7단계. 이는 두 파일이 독립적으로 작성된 증거이며, 어느 것이 정본인지 불명확하다.
- **횡단 관심사(Cross-Cutting Concern)를 NFR에서 식별한다고 했지만, 이를 컴포넌트로 어떻게 반영하는지에 대한 지침이 없다.** 별도 컴포넌트? 미들웨어? 라이브러리? 판단 기준이 필요하다.

### agents/review.md

**품질**: 가장 체계적. 5개 검증 영역, 심각도 분류, 판정 기준이 잘 구조화되어 있다.

**문제점**:
- **"후속 스킬 소비 적합성" 테이블에 `impl:generate`, `qa:strategy` 등으로 참조하지만, 이 네이밍이 실제 스킬 정의와 일치하지 않는다.** skills.yaml에서 impl 스킬의 에이전트는 `generate`이고, qa 스킬의 에이전트명은 확인 필요. 참조 방식의 일관성이 부족하다.
- **ATAM "축소 적용"이라고 했지만, ATAM의 핵심인 "sensitivity point"와 "tradeoff point" 식별이 없다.** ATAM을 참조하려면 그 핵심 개념을 반영해야 하고, 그렇지 않다면 ATAM을 언급하지 않는 것이 낫다. 이름만 빌려오는 것은 오히려 혼란을 준다.

### agents/adr.md

**품질**: 양호. Michael Nygard 형식을 충실히 따르며, 생성 프로세스가 명확하다.

**문제점**:
- **"ADR 작성 필수"와 "ADR 작성 권고"의 경계가 애매하다.** 예를 들어, "주요 기술 선택"이 필수인데, 예제(adr-output.md)에서는 AD-004(SAML 2.0 + RBAC)를 "hard 제약에 의한 필수 선택이므로 ADR 생략"이라고 했다. 인증/인가 아키텍처는 필수 항목인데 생략한 것이 원칙과 모순된다.
- **"경량 모드에서도 핵심 결정에 대한 ADR은 작성합니다"라고 했지만, 경량/중량 판별 로직이 ADR 에이전트에는 없다.** design 에이전트에서 모드 판별이 이루어지고 그 결과가 ADR 에이전트로 전달되어야 하는데, input 스키마에 모드 정보가 없다.

### agents/diagram.md

**품질**: 양호. 다이어그램 유형별 Mermaid 코드 패턴이 구체적이다.

**문제점**:
- **C4 Model의 표준 표기법을 따르지 않는다.** C4 Model은 특정 도형/색상 규칙이 있는데(Person은 원형, System은 직사각형 등), 여기서는 일반 Mermaid `graph TB`를 사용한다. 실제 C4 다이어그램을 Mermaid로 구현하려면 `C4Context`, `C4Container` 등의 Mermaid C4 확장 문법이 있는데, 이를 무시하고 일반 graph 문법을 사용한다. "C4"라고 부르면서 C4의 시각적 규칙을 따르지 않는 것은 혼란을 준다.
- **데이터 흐름 다이어그램(DFD)이 정의되어 있지만, 예제에서는 한 번도 사용되지 않는다.** 실제 사용 사례가 없는 기능 정의는 over-engineering이다.
- **"노드 15개 이하" 규칙의 근거가 없다.** 왜 15인가? Mermaid 렌더링의 실제 한계인가, 가독성 기준인가?

---

## 4. 프롬프트 분석

### prompts/design.md

**문제점**:
- **agents/design.md와 80% 이상 내용이 중복된다.** "Step 1~7"이 agents의 "단계 1~5"의 확장판인데, 두 문서 모두 프로세스, 출력 형식, 주의사항을 반복한다. LLM에게 system prompt와 user prompt를 함께 전달할 때 이 중복은 토큰 낭비이며, 지시사항이 미세하게 다를 경우 LLM이 어느 것을 따를지 모호하다.
- **입력 변수 바인딩이 `{{variable_name}}` 형식인데, 실제 템플릿 엔진이 무엇인지 정의되지 않았다.** Jinja2인가, Mustache인가, 자체 구현인가? 런타임에서 이 변수가 어떻게 치환되는지 알 수 없다.

### prompts/review.md

agents/review.md와의 중복이 심각하다. Step 1~8이 agents의 검증 영역 1~5 + 프로세스 단계 1~4를 재구성한 것인데, 동일한 내용을 다른 번호 체계로 다시 쓴 것이다.

### prompts/adr.md

상대적으로 깔끔하다. agents/adr.md의 프로세스를 축약하여 실행 지시로 변환했다. 하지만 체크리스트가 agents에서 복사한 것이고, 이를 두 곳에서 관리하는 문제는 동일하다.

### prompts/diagram.md

- **`{{mode}}` 변수가 입력에 포함되어 있지만, skills.yaml의 diagram 에이전트 input 스키마에는 mode 필드가 없다.** 이 변수가 어디서 오는지 알 수 없다. 스키마와 프롬프트 간의 불일치다.

---

## 5. 예제 분석

### design-input.md / design-output.md

**품질**: 우수. 휴가 관리 시스템이라는 현실적인 도메인으로 RE 산출물 3섹션(FR 8개, NFR 3개, 제약 5개, 품질속성 4개)과 기술적 맥락까지 완전한 입력을 제공하고, 출력에서 3섹션(AD 5개, COMP 5개, 기술스택 8개)을 구체적으로 보여준다.

**문제점**:
- **경량 모드 예제가 없다.** 모든 예제가 중량 모드 하나뿐이다. 적응적 깊이가 핵심 기능인데, 경량 모드의 동작을 보여주는 예제가 없으면 경량 모드가 실제로 어떤 출력을 내는지 알 수 없다.
- **design-input.md에 "기술적 맥락" 섹션이 포함되어 있는데, 이는 design 에이전트가 사용자와의 대화로 파악해야 하는 정보이다.** 입력 예제에 이미 포함되어 있으면 multi-turn 대화 시뮬레이션이 아니라 단일 입력 예제가 되어버린다. multi-turn의 어떤 시점에서 이 정보가 수집되는지를 보여주는 대화 흐름 예제가 필요하다.

### adr-input.md / adr-output.md

- **adr-input.md는 "design-output.md를 참조하라"는 한 줄짜리 포인터이다.** 독립적인 예제가 아니다. design-output.md를 열어봐야 입력을 알 수 있다.
- **adr-output.md에서 AD-004를 "ADR 생략"한 것이 agents/adr.md의 "인증/인가 아키텍처는 필수" 규칙과 모순된다.** 예제가 원칙을 위반하고 있다.
- **ADR 3건만 생성했는데, 그 중 ADR 간 관계가 모두 `relates-to`이다.** `supersedes`나 `amends`의 사용 예가 없어, 관계 설정 기능의 실질적인 예제가 부족하다.

### diagram-input.md / diagram-output.md

- **diagram-input.md도 포인터 파일이다.**
- **diagram-output.md의 Mermaid 코드에서 `mail` 노드가 두 번 정의된다.** c4-container 다이어그램에서 `worker -->|"SMTP"| mail["사내 메일 서버"]`와 `api -->|"SAML"| sso["사내 SSO"]`가 subgraph 밖에서 inline으로 정의되는데, 이미 외부에 동일 ID의 노드가 있을 수 있어 Mermaid 렌더링 에러를 유발할 수 있다.
- **시퀀스 다이어그램에서 Nginx가 참여자로 포함되어 있다.** 아키텍처적으로는 맞지만, Nginx는 투명한 프록시이므로 시퀀스에서 생략하면 더 간결하다. 이런 판단 기준에 대한 가이드가 agents/diagram.md에 없다.

### review-input.md / review-output.md

- **review-input.md도 포인터 파일이다.** (3개 입력 파일이 전부 포인터.)
- **review-output.md는 가장 완성도 높은 예제이다.** 시나리오 검증, 제약 준수, 추적성 매트릭스, 리스크, 후속 스킬 적합성, 에스컬레이션, 최종 판정까지 모든 출력 섹션을 보여준다.
- **다만, 너무 "좋은 결과"만 보여준다.** 모든 제약이 COMPLIANT, 모든 요구사항이 COVERED. REJECTED 판정이나 Critical 이슈가 있는 예제가 없어, 부정적 케이스에서의 행동이 불명확하다.

---

## 6. 일관성 검토

### 용어 불일치

| 위치 | 표현 A | 표현 B | 문제 |
|------|--------|--------|------|
| skills.yaml consumers | `security`, `deployment`, `operation` | 실제 리포지토리 | `sec`, `devops` (operation은 부재) |
| skills.yaml | `interaction_mode: multi-turn` | impl skills.yaml | `interaction_mode: auto-execute` |
| agents/design.md | "단계 1~5" | prompts/design.md | "Step 1~7" |
| agents/review.md | "검증 영역 1~5" | prompts/review.md | "Step 1~8" |
| 에이전트 참조 | `impl:generate`, `qa:strategy` | 실제 에이전트명 | qa에 strategy 에이전트가 있는지 미확인 |

### 네이밍 불일치

- skills.yaml의 output에서 `architecture_decisions`라 정의하고, impl 스킬에서도 `architecture_decisions`로 소비한다. 이 부분은 일관적이다.
- 하지만 review 에이전트의 input은 `design_output`이라는 래퍼 객체를 사용하여 한 단계 더 감싸는데, 다른 에이전트들은 직접 참조한다. 래핑 수준이 불일치한다.

### ID 체계 불일치

- `AD-XXX` (아키텍처 결정) vs `ADR-XXX` (ADR 문서): 둘 다 아키텍처 결정에 대한 것인데 별도 ID 체계를 사용한다. AD-001 → ADR-001 매핑이 필요한데, 이 매핑을 누가 관리하는지 불명확하다. ADR 에이전트가 AD-001을 ADR-001로 변환하는 것은 이해하지만, 향후 AD-006이 추가되면 ADR 번호는 003에서 이어가야 하는지 001부터 다시 매기는지 규칙이 모호하다.

---

## 7. 주요 문제점 (심각도 순)

### Critical

1. **agents/와 prompts/의 대규모 내용 중복 — 동기화 실패 리스크가 높다.** 이미 단계 수가 다르고(design: 5단계 vs 7단계), 일부 규칙이 한쪽에만 존재한다(재질문 금지 규칙). 이는 LLM에게 상충되는 지시를 전달할 수 있는 구조적 결함이다.

2. **파이프라인 순서의 논리적 모순.** review가 마지막인데 ADR/다이어그램을 검증하지 않는다. review는 design 출력만 검증하므로, design 직후에 위치하는 것이 맞다. 현재 순서는 ADR/다이어그램에 오류가 있어도 파이프라인이 APPROVED로 통과할 수 있다.

3. **3개 입력 예제(adr, diagram, review)가 실질적으로 비어있다.** 독립적으로 실행/검증할 수 없는 예제는 무가치하다.

### Major

4. **경량 모드 예제 전무.** 적응적 깊이가 핵심 차별점인데, 경량 모드의 예제가 하나도 없다.

5. **prompts/diagram.md의 `{{mode}}` 변수가 skills.yaml input 스키마에 정의되지 않았다.** 런타임 오류 가능성.

6. **skills.yaml consumers의 스킬명이 실제 리포지토리와 불일치한다.** `security` ≠ `sec`, `deployment` ≠ `devops`, `operation`은 부재.

7. **review 에이전트의 input 스키마가 `type: object`로만 되어있어 계약이 느슨하다.** 다른 에이전트의 output이 변경되면 review가 깨질 수 있지만, 스키마 수준에서 감지할 수 없다.

### Minor

8. **adr-output.md 예제가 agents/adr.md의 "인증/인가는 필수" 규칙을 위반한다.** 예제가 원칙과 모순되면 LLM이 어느 것을 따를지 불확실하다.

9. **C4 다이어그램이 실제 C4 Model의 시각적 규칙을 따르지 않는다.** "C4"라는 이름의 오용.

10. **architecture_patterns 카탈로그가 skills.yaml과 agents/design.md에 중복 정의된다.**

---

## 8. 개선 제안

### 구조 개선

1. **agents/와 prompts/의 역할을 엄격히 분리하라.**
   - `agents/*.md` (system prompt): 역할 정의, 핵심 원칙, 제약 조건, 출력 형식 스키마만 포함.
   - `prompts/*.md` (prompt template): 입력 변수 바인딩, 실행 단계(Step), 사용자 상호작용 스크립트만 포함.
   - 프로세스/단계 정의는 한 곳에만. 다른 곳에서는 참조만.

2. **파이프라인 순서를 재조정하라.** design → review → (APPROVED일 때만) adr → diagram. 또는 review의 input에 ADR/다이어그램을 포함시켜 전체를 검증하게 하라.

3. **빈 input 예제를 실제 데이터로 채우라.** 최소한 design-output.md에서 해당 에이전트가 소비하는 부분을 복사하여 독립적인 예제로 만들어라.

### 스키마 개선

4. **review 에이전트의 input 스키마를 상세화하라.** `design_output` 내부에 `architecture_decisions`, `component_structure`, `technology_stack`의 구조를 명시하라.

5. **diagram 에이전트의 input에 `mode` 필드를 추가하라.** 또는 prompts/diagram.md에서 `{{mode}}`를 제거하고, 입력 데이터의 복잡도를 보고 에이전트가 자체 판별하게 하라(현재 design 에이전트가 하는 방식처럼).

6. **consumers 섹션의 스킬명을 실제 리포지토리 디렉토리명과 일치시키라.** `security` → `sec`, `deployment` → `devops`.

### 예제 개선

7. **경량 모드 예제를 추가하라.** FR 3개, NFR 1개 수준의 간단한 프로젝트에 대한 입출력 예제.

8. **부정적 시나리오 예제를 추가하라.** review에서 REJECTED 판정이 나오는 케이스, hard 제약 위반이 발견되는 케이스.

9. **multi-turn 대화 예제를 추가하라.** 현재 예제는 모두 단일 입출력 쌍인데, 에이전트의 `interaction_mode`가 `multi-turn`이다. 실제 대화 흐름(질문-응답-수정-확정)을 보여주는 예제가 있어야 한다.

### 내용 개선

10. **ADR 작성 필수/권고 기준을 명확히 하라.** "인증/인가 아키텍처는 필수"인데 hard 제약에 의한 선택이면 생략 가능한지, 불가능한지 규칙을 확정하라. 예제를 규칙에 맞게 수정하라.

11. **C4 다이어그램 표기를 실제 C4 규칙에 맞추거나, "C4-style"이라는 표현을 제거하라.** Mermaid의 C4 확장 문법(`C4Context`, `C4Container`)을 사용하거나, 단순히 "시스템 컨텍스트 다이어그램"으로 명칭을 변경하라.

12. **adr 에이전트의 input에 RE 산출물(최소한 constraints와 quality_attribute_priorities)을 추가하라.** ADR의 "RE 근거" 섹션을 작성하려면 RE 원본 데이터가 필요하다.
