# Impl 스킬 코드/설계 리뷰

## 1. 구조 분석

### 디렉토리 구조

```
impl/
├── skills.yaml
├── agents/
│   ├── generate.md
│   ├── pattern.md
│   ├── refactor.md
│   └── review.md
├── prompts/
│   ├── generate.md
│   ├── pattern.md
│   ├── refactor.md
│   └── review.md
└── examples/
    ├── generate-input.md
    ├── generate-output.md
    ├── pattern-input.md
    ├── pattern-output.md
    ├── refactor-input.md
    ├── refactor-output.md
    ├── review-input.md
    └── review-output.md
```

**양호한 점**: agents/prompts/examples가 1:1:1로 대응되어 파일 구성이 깔끔하다. 네이밍도 일관적이다.

**문제점**:

- **agents/와 prompts/의 역할 분리가 모호하다.** `agents/generate.md`와 `prompts/generate.md`를 비교하면, agents 파일이 "시스템 프롬프트"이고 prompts 파일이 "유저 프롬프트 템플릿"인 것으로 보이는데, 실질적으로 내용이 상당 부분 중복된다. 예를 들어 generate의 경우 agents 파일(160줄)과 prompts 파일(176줄) 모두 "실행 절차"를 단계별로 기술하고 있어, 어디가 권위적 정의인지 불분명하다. 둘 사이에 충돌이 생기면 어느 쪽을 따라야 하는지 정의되어 있지 않다.
- **에이전트 간 공유 정의가 없다.** 에스컬레이션 형식, ID 체계(IM-xxx, IDR-xxx), Arch 산출물 해석 규칙 등이 여러 에이전트에 걸쳐 반복적으로 기술되어 있다. 공통 정의를 별도 파일(예: `shared/conventions.md`)로 분리하면 유지보수성이 올라간다.

---

## 2. skills.yaml 분석

### 완성도

skills.yaml은 287줄로 상당히 상세하게 정의되어 있다. 4개 에이전트(generate, review, refactor, pattern), 파이프라인, 의존성, 소비자를 모두 기술하고 있다.

### 문제점

1. **input/output 스키마 정의의 깊이가 에이전트마다 불균등하다.**
   - `generate`: input 68줄, output 48줄 -- 필드 레벨까지 상세하게 정의
   - `review`: input 8줄, output 20줄 -- `generated_code: type: object`로 뭉뚱그려 놓음
   - `refactor`: input 10줄, output 18줄 -- 역시 `target_code: type: object`
   - `pattern`: input 8줄, output 16줄

   generate를 제외한 3개 에이전트의 input이 `type: object`로만 정의되어 있어, 실제로 어떤 구조의 데이터가 들어오는지 스키마만으로는 알 수 없다. 이는 파이프라인에서 에이전트 간 데이터를 자동으로 연결할 때 검증이 불가능하다는 뜻이다.

2. **pipeline의 condition 표현이 비일관적이다.**
   - 3번째 스테이지: `condition: "review.verdict == 'FIX_REQUIRED'"` -- 프로그래밍 스타일
   - 4번째 스테이지: `condition: "refactor 수행 시 재리뷰"` -- 자연어 스타일
   
   하나의 DSL이면 일관된 표현 체계를 써야 한다. 자연어와 코드를 섞으면 파서가 처리할 수 없다.

3. **pipeline에서 pattern 에이전트가 빠져 있다.** skills.yaml의 agents 섹션에 pattern이 정의되어 있고, generate 에이전트 문서에서 "필요시 pattern 에이전트를 호출"한다고 기술하지만, pipeline.stages에는 pattern이 등장하지 않는다. pattern이 generate의 서브루틴으로 호출되는 것이라면, 그 관계를 pipeline 정의에서 명시해야 한다.

4. **checkpoint가 모두 false이다.** 4개 스테이지 전부 `checkpoint: false`인데, 이 필드가 왜 존재하는지 설명이 없다. 만약 사용자 확인 지점을 의미한다면, ESCALATE 상황에서는 checkpoint가 필요할 텐데 이것이 escalation 섹션과 어떻게 연동되는지 불분명하다.

5. **consumers 섹션의 skill 이름이 프로젝트 내 실제 디렉토리와 불일치한다.**
   - `security` -> 프로젝트에는 `sec/`로 존재
   - `deployment`, `operation`, `management` -> 프로젝트에 `devops/`는 있지만 이 세 개는 각각 존재하지 않음
   
   아직 미구현 스킬을 선제적으로 참조하는 것인지, 이름이 잘못된 것인지 판단할 수 없다. 실제 디렉토리 구조(`re`, `arch`, `impl`, `qa`, `devops`, `sec`, `ex`, `orch`)와 매핑이 안 된다.

6. **adaptive_depth가 generate에만 정의되어 있다.** review, refactor, pattern에는 adaptive_depth가 없는데, generate가 경량/중량 모드로 나뉘면 후속 에이전트들의 동작도 달라져야 하지 않는가? review가 경량 모드 산출물을 리뷰할 때와 중량 모드 산출물을 리뷰할 때 기준이 같다면, 중량 모드에서 "IDR 기록"이 없는 경량 모드 산출물에 "IDR 미기록"을 이슈로 잡을 수 있다.

7. **version이 1.0.0인데 실제로는 초기 설계 단계이다.** 스키마 검증도 안 되고, 파이프라인 condition이 자연어로 쓰여 있는 상태를 1.0.0이라고 부르는 것은 과대 표기이다.

---

## 3. 에이전트 정의 분석

### generate (agents/generate.md)

**양호한 점**: Arch 산출물 필드별 코드 변환 규칙을 표로 정리한 것은 좋다. 적응적 깊이 모드, 에스컬레이션 조건, 실행 절차가 체계적이다.

**문제점**:

- **"코드 레벨 맥락 자동 감지" 섹션이 실현 가능성이 의심스럽다.** "기존 코드의 네이밍 규칙(camelCase/snake_case), 들여쓰기, 파일 구조 패턴 감지"라고 했는데, LLM이 파일 시스템을 탐색하여 이를 자동으로 수행하는 구체적 메커니즘이 없다. 어떤 도구를 쓰는지, 어떤 순서로 탐색하는지, 분석 결과를 어떤 형식으로 보관하는지 정의가 없다. 희망 사항(wishful thinking)에 가깝다.
- **"일괄 구현" 원칙의 비현실성.** "전체 코드를 일괄 생성한 뒤 결과를 보고한다"고 했는데, 중량 모드에서 6개 이상 컴포넌트의 완전한 구현을 일괄 생성하면 LLM의 컨텍스트 윈도우를 초과할 가능성이 높다. 배치 전략이나 분할 생성에 대한 고려가 전혀 없다.
- **"pattern 에이전트를 호출하여 패턴 적용"** -- 에이전트 간 호출 메커니즘이 정의되어 있지 않다. 단순히 "호출한다"고만 써놓았을 뿐, 어떤 프로토콜로 호출하는지 불분명하다.

### review (agents/review.md)

**양호한 점**: Arch 준수 / 클린 코드 / 보안 3축 리뷰 구조는 명확하다. 이슈 분류(critical/high/medium/low/info)와 판정(PASS/FIX_REQUIRED/ESCALATE) 기준도 잘 정의되어 있다.

**문제점**:

- **"리뷰 축 3: 보안 기본 검증"이 agents 파일에만 있고 prompts 파일의 Step 4와 미묘하게 다르다.** agents에서는 "OWASP Top 10 수준"이라 했고, prompts에서는 SQL 인젝션/XSS/하드코딩 자격증명/로그 민감정보/입력 검증 5개만 나열했다. OWASP Top 10은 10개인데 5개만 체크하는 것은 부족하다.
- **review_report의 output 스키마에 `line_feedback` 필드가 skills.yaml에 정의되어 있지만**, agents 파일과 prompts 파일의 출력 형식에서는 한 번도 언급되지 않는다. 스키마에만 존재하고 실제 사용되지 않는 유령 필드이다.
- **심각도 체계가 불일치한다.** skills.yaml의 review output에는 severity 필드가 없고, agents/review.md에서는 `high | medium | low`를 쓰고, prompts/review.md에서는 `critical | high | medium | low | info`를 쓴다. critical과 info가 agents 파일에는 없다.

### refactor (agents/refactor.md)

**양호한 점**: Martin Fowler의 코드 스멜 카탈로그를 체계적으로 분류한 것은 참고 가치가 있다. Arch 경계 검증 절차도 구체적이다.

**문제점**:

- **"동작을 보존하는 리팩토링만 수행한다"고 했지만, 동작 보존을 어떻게 검증하는지 정의하지 않았다.** 테스트를 돌린다? 타입 체크만 한다? LLM이 "안전성: 동작 보존"이라고 자기 선언하는 것으로 충분한가? 이는 refactor 에이전트의 핵심 약속인데 검증 수단이 없다.
- **코드 스멜 탐지 기준이 정적 분석 도구 수준의 구체성을 갖고 있지만, 실행 주체가 LLM이다.** "함수 20줄 이상 또는 순환 복잡도 10 이상"이라는 기준을 LLM이 정확히 측정할 수 있는가? 줄 수를 세는 것조차 LLM은 부정확할 수 있다. 실제 정적 분석 도구 연동 없이 이 기준은 허울이다.

### pattern (agents/pattern.md)

**양호한 점**: 의사결정 트리가 ASCII 트리로 명확하게 제시되어 있다. YAGNI 경계가 잘 설정되어 있다. "에스컬레이션하지 않는다"는 결정도 합리적이다.

**문제점**:

- **의사결정 트리가 GoF 패턴에 편향되어 있다.** "기술 스택의 관용적 패턴이 GoF 패턴보다 우선한다"고 prompts에서 언급하면서도, 의사결정 트리 자체는 GoF 패턴만 나열한다. Go의 functional options, Rust의 builder derive, Python의 decorator syntax 등 언어별 관용적 패턴에 대한 의사결정 트리가 없다.
- **"안티패턴 탐지" 섹션이 generate와 pattern 사이에서 책임이 중복된다.** generate가 코드를 생성할 때 안티패턴을 만들고, pattern이 안티패턴을 탐지하고, review가 또 코드 스멜을 탐지한다. 세 에이전트가 유사한 검증을 중복 수행하는 구조이다.

---

## 4. 프롬프트 분석

### 공통 문제

- **agents 파일과 prompts 파일의 지시사항이 중복된다.** agents 파일의 "실행 절차"와 prompts 파일의 "Step 1~N"이 동일한 내용을 다른 표현으로 반복한다. 예를 들어 generate의 경우:
  - agents: "단계 1: Arch 산출물 파싱 ... 단계 5: 산출물 구성"
  - prompts: "Step 1: 적응적 깊이 판별 ... Step 8: 에스컬레이션 또는 결과 보고"
  
  agents는 5단계, prompts는 8단계로 분할 방식이 다르다. 실행 시 LLM에게 system prompt + user prompt가 동시에 제공된다면, "단계 1"과 "Step 1"이 같은 것인지 다른 것인지 혼란을 줄 수 있다.

- **프롬프트 템플릿 변수가 실제 input 스키마와 불일치한다.**
  - `prompts/review.md`: `{{generated_code}}`, `{{implementation_map}}`, `{{implementation_decisions}}`를 참조하지만, skills.yaml의 review input에는 `generated_code`와 `arch_output` 두 필드만 정의되어 있다. `implementation_map`과 `implementation_decisions`는 `generated_code` 내부에 포함된 것인가? 그렇다면 `generated_code.implementation_map`으로 접근해야 하는데 템플릿에서는 최상위 변수처럼 쓰고 있다.
  - `prompts/refactor.md`: `{{implementation_map}}`, `{{component_structure}}`, `{{architecture_decisions}}`를 참조하지만, skills.yaml의 refactor input에는 `target_code`, `review_report`, `arch_output` 세 필드만 있다. `implementation_map`은 어디서 오는가?

### 개별 프롬프트

- **prompts/generate.md**: 상대적으로 가장 완성도가 높다. Step별 체크리스트, 구체적 YAML 예시, 주의사항이 잘 구성되어 있다. 다만 "Step 1: 적응적 깊이 판별"의 기준이 "컴포넌트 5개 이하 = 경량"인데, 이 기준이 agents 파일에는 명시되지 않았다. agents 파일에서는 "Arch가 스타일 추천 + 디렉토리 가이드 수준"이라는 정성적 기준을 쓴다.
- **prompts/pattern.md**: Step 3의 "적용하지 않아야 하는 경우"와 "적용해야 하는 경우"가 실용적이다. 그러나 input 변수에 `{{architecture_decisions}}`와 `{{component_structure}}`와 `{{technology_stack}}`을 따로 받는데, skills.yaml에서는 `arch_output: type: object`로 하나로 뭉쳐져 있다.
- **prompts/refactor.md**: "Step 4: 리팩토링 실행"에서 제시하는 예시가 Go 특정적이다. 다른 언어에 대한 고려가 없다.
- **prompts/review.md**: PASS 판정 기준이 agents 파일과 다르다. agents: "이슈 없음 또는 참고 사항만 존재", prompts: "critical/high/medium 이슈 없음". agents 기준이면 low 이슈가 있어도 PASS이지만, prompts 기준이면 low만 있어도 PASS이다. 이 둘은 일치하지만, medium에 대해서는 다르다: agents에서 "자동 수정 가능 이슈 존재 -> FIX_REQUIRED"이므로 medium auto_fixable이면 FIX_REQUIRED인데, prompts에서도 동일하다. 결과적으로 일치하나, info 등급이 agents에는 언급되지 않아 혼동의 여지가 있다.

---

## 5. 예제 분석

### 양호한 점

- 4개 에이전트 모두 input/output 예제가 존재한다.
- 예제가 하나의 일관된 도메인(휴가 관리 시스템)을 사용하여 파이프라인 흐름을 추적할 수 있다.
- Go + Echo + PostgreSQL이라는 구체적 기술 스택으로 현실감이 있다.

### 문제점

1. **예제가 단일 기술 스택(Go)에만 치우쳐 있다.** 스킬 설명에서는 Java, TypeScript, Python, Rust 등을 언급하면서 예제는 전부 Go이다. 다른 언어에서의 관용적 구현이 어떻게 다른지 보여주는 예제가 없다.

2. **경량 모드 예제가 전혀 없다.** generate의 adaptive_depth에 경량/중량 모드가 정의되어 있지만, 예제는 전부 중량 모드이다. 경량 모드의 입력이 어떤 형태이고 출력이 어떻게 줄어드는지 예시가 없어서, 실행 시 경량 모드가 제대로 동작할지 검증할 수 없다.

3. **에스컬레이션 예제가 없다.** 모든 에이전트에서 에스컬레이션 조건과 형식을 정의해놓고, 예제에서는 "에스컬레이션 없음"으로만 끝난다. 에스컬레이션이 실제로 발생했을 때의 입출력 예제가 필요하다.

4. **review-output의 예제에 모순이 있다.**
   - summary에 `issues_found: 7`, `auto_fixable: 5`, `escalations: 2`라 했는데, 실제 나열된 clean_code_issues는 5건, security_issues 1건, arch_compliance deviation 3건이다. 7 = 5(clean) + 1(security) + 3(arch) = 9가 아니라 7이라 수가 맞지 않는다. arch_compliance의 3건 중 2건이 escalation이면 `escalations: 2`는 맞지만, 3건을 issues_found에 포함하는지 제외하는지 기준이 불명확하다.

5. **refactor-input과 review-output 사이의 데이터 흐름이 예제에서 단절된다.** review-output에서 verdict가 ESCALATE인데, refactor-input은 auto_fixable 이슈만 받아서 처리한다. 파이프라인 정의에 따르면 ESCALATE면 사용자에게 에스컬레이션되어야 하고, FIX_REQUIRED일 때만 refactor가 실행되어야 한다. 그런데 예제에서는 review가 ESCALATE를 내놓고, refactor가 바로 동작하는 것처럼 보인다. 파이프라인 흐름과 예제가 모순된다.

6. **pattern-output에서 `calculators` 전역 변수가 동시성 안전하지 않다.** `var calculators = map[string]BalanceCalculator{...}`와 `RegisterCalculator` 함수가 동시성 보호 없이 전역 map을 수정한다. Go에서 이는 data race이다. 예제가 기술 스택의 관용적 관행을 따른다고 하면서 동시성 안전을 무시하는 것은 자기모순이다.

7. **pattern-output에서 `AnnualCalculator{}`의 `repo` 필드가 초기화되지 않는다.** `calculators` map에서 `&AnnualCalculator{}`로 생성하면서 `repo` 필드를 주입하지 않는다. 이후 `c.repo.GetUsedDays()`를 호출하면 nil pointer dereference가 발생한다.

---

## 6. 일관성 검토

### 용어 불일치

| 항목 | 위치 A | 위치 B | 불일치 |
|------|--------|--------|--------|
| 심각도 등급 | agents/review.md: `high/medium/low` | prompts/review.md: `critical/high/medium/low/info` | `critical`과 `info` 누락 |
| 적응적 깊이 경량 기준 | agents/generate.md: "스타일 추천 + 디렉토리 가이드 수준" | prompts/generate.md: "컴포넌트 5개 이하" | 정성적 vs 정량적 |
| Arch 산출물 입력 | prompts/pattern.md: 개별 필드(`{{architecture_decisions}}`, `{{component_structure}}`, `{{technology_stack}}`) | skills.yaml pattern input: `arch_output: type: object` | 템플릿 변수와 스키마 불일치 |
| 실행 단계 수 | agents/generate.md: 5단계 | prompts/generate.md: 8단계 | 분할 방식 불일치 |
| interaction_mode | skills.yaml generate: `auto-execute` | skills.yaml qa strategy: `auto` | 같은 개념인데 다른 이름 (프로젝트 전체 차원의 문제) |

### 네이밍

- 에이전트 이름은 영어(generate, review, refactor, pattern)인데, `name` 필드는 한국어(코드 생성, 코드 리뷰, 리팩토링, 디자인 패턴)이다. 이 자체는 문제가 아니나, description이 한국어와 영어 약어를 혼용한다.
- ID 체계(AD-xxx, COMP-xxx, IM-xxx, IDR-xxx, FR-xxx, NFR-xxx, CON-xxx)는 전체적으로 일관적이다. 이 부분은 잘 설계되었다.

### 형식

- agents 파일들의 마크다운 구조는 일관적이다: 역할 -> 핵심 원칙 -> 세부 내용 -> 에스컬레이션 -> 출력 형식.
- prompts 파일들도 일관적이다: 입력 -> 지시사항 -> Step N -> 주의사항.
- 예제 파일들은 형식이 약간 다르다: generate-output은 YAML 코드 블록 위주, review-output은 YAML + 요약 표 혼합.

---

## 7. 주요 문제점 (심각도 순)

### Critical

1. **프롬프트 템플릿 변수와 skills.yaml input 스키마의 불일치.** review와 refactor 프롬프트가 skills.yaml에 정의되지 않은 변수를 참조한다. 실행 시 변수가 바인딩되지 않아 빈 값이 들어가거나 에러가 발생할 수 있다. 이는 시스템이 실제로 동작하지 않음을 의미한다.

2. **파이프라인 condition 표현의 비일관성.** 코드 스타일(`review.verdict == 'FIX_REQUIRED'`)과 자연어 스타일(`refactor 수행 시 재리뷰`)이 혼재하여, 이를 자동으로 파싱/실행하는 오케스트레이터가 구현 불가능하다.

3. **review-output 예제와 파이프라인 흐름의 모순.** ESCALATE verdict인데 refactor 예제로 이어지는 것은 정의된 파이프라인 로직(`condition: review.verdict == 'FIX_REQUIRED'`)과 모순된다.

### High

4. **agents 파일과 prompts 파일 간 지시사항 중복 및 미묘한 차이.** 동일한 내용이 두 곳에서 약간 다르게 기술되어, LLM이 어느 쪽을 따를지 예측 불가능하다. 유지보수 시 한쪽만 수정하면 불일치가 악화된다.

5. **review, refactor, pattern의 input 스키마가 `type: object`로만 정의.** 스키마의 존재 의의가 없다. generate의 상세한 스키마와 대비되어 설계 미완성 상태가 명확하다.

6. **consumers 섹션의 스킬명이 실제 프로젝트 구조와 불일치.** `security`, `deployment`, `operation`, `management`는 프로젝트에 존재하지 않는 이름이다.

### Medium

7. **경량 모드 예제 부재.** 적응적 깊이가 핵심 설계 요소인데 절반(경량)에 대한 검증이 불가능하다.

8. **에스컬레이션 예제 부재.** 에스컬레이션이 발생하는 시나리오의 end-to-end 예제가 없다.

9. **코드 예제의 버그.** pattern-output의 전역 map 동시성 문제와 nil pointer 문제는, 예제가 "이상적 출력"으로서의 역할을 하지 못하게 만든다.

10. **"동작 보존" 검증 수단 부재.** refactor 에이전트의 핵심 약속이지만, 어떻게 보장하는지 정의가 없다.

### Low

11. **단일 기술 스택(Go) 편향.** 다양한 기술 스택 지원을 표방하면서 예제와 구체적 기술은 전부 Go이다.

12. **안티패턴 탐지 책임이 pattern, review, refactor 3곳에 분산.** 역할 경계가 불명확하다.

---

## 8. 개선 제안

### 즉시 수정 가능 (빠른 승리)

1. **프롬프트 템플릿 변수를 skills.yaml input 스키마와 일치시키라.** review와 refactor의 input 스키마를 확장하거나, 프롬프트 템플릿의 변수를 스키마에 맞게 수정하라.

2. **pipeline condition을 일관된 표현 체계로 통일하라.** 4번째 스테이지의 `"refactor 수행 시 재리뷰"`를 `"stages[2].executed == true"`와 같은 형식으로 바꾸라.

3. **review-output 예제의 verdict를 FIX_REQUIRED로 수정하거나, 별도의 ESCALATE 시나리오 예제를 추가하라.** 현재 예제 세트가 하나의 일관된 파이프라인 흐름을 보여주도록 수정하라.

4. **pattern-output의 코드 버그를 수정하라.** `sync.RWMutex`를 추가하고, calculator 생성자에 repo를 주입하는 패턴으로 수정하라.

5. **consumers의 스킬명을 실제 프로젝트 구조와 맞추거나, 미구현 상태임을 명시하라.**

### 구조적 개선 (중기)

6. **agents 파일은 "역할 정의 + 제약 조건"에 집중하고, prompts 파일은 "실행 절차 + 출력 형식"에 집중하도록 책임을 분리하라.** 현재 두 파일이 모두 "실행 절차"를 기술하여 중복이 발생한다. 원칙: agents = "당신은 누구이며 무엇을 하면 안 되는가", prompts = "이 입력으로 이 순서로 이것을 하라".

7. **review, refactor, pattern의 input/output 스키마를 generate 수준으로 상세화하라.** 최소한 필수 필드와 타입은 정의되어야 한다.

8. **경량 모드 예제 세트를 추가하라.** 경량 모드의 generate-input, generate-output, review-input, review-output 4개 파일을 추가하라.

9. **에스컬레이션 시나리오 예제를 추가하라.** generate 에스컬레이션(기술적 실현 불가), review 에스컬레이션(Arch 계약 위반), refactor 에스컬레이션(경계 간 리팩토링) 각 1건씩.

10. **공통 정의를 분리하라.** ID 체계, 에스컬레이션 형식, Arch 산출물 참조 규칙을 `shared/conventions.md`로 추출하고, 각 에이전트 파일에서 참조하라.

### 장기 개선

11. **pipeline 정의를 실행 가능한 형태로 발전시키라.** condition을 파싱 가능한 DSL로 정의하고, agent 간 데이터 연결(wire)을 명시적으로 기술하라. pattern 에이전트의 호출 관계도 pipeline에 반영하라.

12. **다양한 기술 스택의 예제를 추가하라.** 최소한 TypeScript + Next.js, Java + Spring Boot 예제 1세트씩 추가하여 "기술 스택 관용구 적용"이 실제로 어떻게 달라지는지 보여주라.

13. **정적 분석 도구 연동을 설계하라.** refactor의 코드 스멜 탐지와 review의 순환 복잡도 측정을 LLM에 의존하지 말고, 실제 도구(golangci-lint, eslint, sonarqube 등)의 출력을 입력으로 받는 구조를 검토하라.
