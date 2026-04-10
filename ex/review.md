# Ex (Execution) 스킬 코드/설계 리뷰

---

## 1. 구조 분석

### 디렉토리 구조

```
ex/
├── skills.yaml
├── agents/
│   ├── scan.md
│   ├── detect.md
│   ├── analyze.md
│   └── map.md
├── prompts/
│   ├── scan.md
│   ├── detect.md
│   ├── analyze.md
│   └── map.md
└── examples/
    ├── scan-input.md / scan-output.md
    ├── detect-input.md / detect-output.md
    ├── analyze-input.md / analyze-output.md
    └── map-input.md / map-output.md
```

**양호한 점**: agents/prompts/examples 3계층 분리는 관심사 분리 원칙에 부합한다. 4개 에이전트에 대해 일관된 파일 네이밍 패턴을 사용하고 있다.

**문제점**:

- **agents/와 prompts/의 역할 경계가 불명확하다.** agents/*.md는 "시스템 프롬프트"로, prompts/*.md는 "프롬프트 템플릿"으로 분류되어 있으나, 실질적으로 두 파일의 내용이 상당 부분 중복된다. 예를 들어 agents/scan.md와 prompts/scan.md 모두 파일 분류 기준, 진입점 식별 규칙, 적응적 깊이 판별 로직을 설명한다. 이 중복은 유지보수 시 불일치를 유발할 위험이 크다.
- **examples/ 파일명이 실제 참조 관계와 불일치한다.** analyze-input.md 내에서 `scan-output.md`와 `detect-output.md`를 참조하지만, 실제 파일명은 `scan-output.md`가 아니라 `scan-output.md`이다. 이는 우연히 일치할 뿐, detect-input.md에서도 `scan-output.md`를 참조하는 등 예제 간 참조 체계가 파일 시스템과 정확히 대응하는지 검증이 필요하다.

---

## 2. skills.yaml 분석

### 완성도

skills.yaml은 317줄로, 4개 에이전트, 파이프라인, 의존성, 에스컬레이션 조건, 설계 원칙까지 포괄적으로 정의하고 있다. 구조 자체는 잘 설계되어 있다.

### 문제점

1. **`file_classification.other` 카테고리 누락**: 47줄에서 "source, config, test, doc, build, static, other"로 설명하면서 `properties`에는 `other`를 정의하지 않았다. 스키마와 설명이 불일치한다.

2. **scan 에이전트의 `escalation_only: true`가 의미적으로 모순**: scan은 파이프라인의 최초 진입점이다. `escalation_only: true`는 "에스컬레이션이 있을 때만 호출"이라는 의미로 해석될 수 있는데, 이 경우 파이프라인 자체가 동작하지 않는다. 이 필드의 의미가 명확하게 정의되어 있지 않다면 혼란을 초래한다.

3. **detect의 `escalation_only: true` vs analyze의 `escalation_only: false` 불일치**: detect도 파이프라인에서 자동 실행되는 에이전트인데 escalation_only가 true이다. 반면 analyze와 map은 false이다. 이 차이에 대한 설명이 없다. 이것이 의도적 설계인지, 복사 오류인지 판단할 수 없다.

4. **adaptive_depth가 scan과 analyze에만 정의**: detect와 map에는 adaptive_depth가 없다. 그러나 detect는 scan의 depth_mode를 입력으로 받지 않으면서, analyze는 받는다. detect가 경량/중량에 따라 행동이 달라지지 않는 것이 의도적인지 불명확하다. 실제로 경량 프로젝트에서 detect가 전체 시그니처 매칭을 수행하는 것은 과잉 분석일 수 있다.

5. **scan output의 `depth_mode.evidence.file_count` 정의 혼란**: skills.yaml에서는 `file_count: { type: integer }`로 정의하지만, scan-output 예제에서는 `file_count: 38  # 소스 파일 21 + 테스트 6 + ...`로 총 파일 수를 기록한다. 그런데 scan agent 프롬프트에서는 "소스 파일 수 <= 50"을 기준으로 사용한다. 어떤 파일 수인지(소스만? 전체?) 정의가 모호하다.

6. **map output에서 `test_patterns`과 `build_deploy_patterns`가 skills.yaml에만 존재**: 이 필드들은 analyze의 output에는 없고, map의 output에서 처음 등장한다. 즉 map 에이전트가 detect 출력에서 정보를 가져와 새로운 필드를 조합해야 하는데, 이 데이터 흐름이 skills.yaml에 명시되어 있지 않다.

7. **`token_budget_summary`가 map의 output에 nested되어 있으나 독립 메타데이터처럼 동작**: 이것이 architecture_inference의 하위인 것은 의미적으로 부자연스럽다. 분석 메타데이터에 속해야 한다.

8. **dependencies.consumers 목록이 검증 불가**: re, arch, impl, qa, sec, devops 스킬이 harness 프로젝트에 존재하나, 실제로 이 스킬들이 ex의 출력을 어떻게 소비하는지에 대한 인터페이스 계약이 없다. 단방향 선언에 불과하다.

---

## 3. 에이전트 정의 분석

### agents/scan.md

**양호한 점**: 파일 분류 기준, 진입점 패턴, 설정 파일 매핑이 구체적인 테이블로 정리되어 있다. .gitignore 해석 로직과 기본 제외 패턴이 명확하다.

**문제점**:
- **언어 확장자 목록이 불완전하다**: `.tsx`, `.jsx`, `.vue`, `.svelte` 등 프레임워크 확장자가 source 분류 기준에 없다. `.c`, `.cpp`, `.h` 등 C/C++ 계열도 빠져 있다.
- **분류 우선순위 규칙이 프롬프트에는 있으나 에이전트에는 없다**: `jest.config.ts`를 test가 아닌 config로 분류하라는 규칙이 prompts/scan.md에만 있고 agents/scan.md에는 없다.
- **"대규모 프로젝트(파일 1000개 이상)"라는 기준이 임의적이다**: 1000개는 어떤 근거에서 나온 수치인지 불명확하며, 500개와 1000개 사이의 프로젝트에 대한 가이드가 없다.

### agents/detect.md

**양호한 점**: 매니페스트별, 프레임워크별, 도구별 탐지 시그니처가 매우 구체적이고 포괄적이다. 현실적인 기술 스택을 잘 커버한다.

**문제점**:
- **시그니처 테이블이 사실상 하드코딩된 룩업 테이블이다**: 새로운 기술(예: Bun, Deno, Remix, tRPC, Drizzle 등)이 등장하면 에이전트 정의를 직접 수정해야 한다. 시그니처 확장 메커니즘이 없다.
- **Deno, Bun 런타임이 빠져 있다**: 현재 JavaScript/TypeScript 생태계에서 Node.js만 가정하고 있다.
- **Drizzle은 데이터베이스/ORM 테이블에 있지만, 프레임워크 탐지 시그니처에는 Remix, Astro, Qwik 등 최신 프레임워크가 없다.**
- **`messaging` 카테고리가 skills.yaml의 tech_stack.category enum에 있지만, detect 에이전트에서 메시징 기술(Kafka, RabbitMQ, Redis Pub/Sub 등) 탐지 시그니처가 독립 섹션으로 정리되어 있지 않다.** analyze 에이전트의 통신 패턴 탐지에서 언급될 뿐이다.

### agents/analyze.md

**양호한 점**: import 분석의 언어별 구문, 컴포넌트 경계 추론 규칙, 아키텍처 스타일 추론 테이블이 체계적이다. 순환 의존성 탐지와 횡단 관심사 탐지까지 포함한 것은 높은 수준의 분석이다.

**문제점**:
- **"핵심 모듈(진입점에서 2홉 이내)에 집중"이라는 규칙이 모호하다**: "2홉"이 import 그래프에서의 거리인지, 디렉토리 깊이인지 불명확하다. 또한 대규모 프로젝트에서 2홉이면 사실상 대부분의 모듈이 포함된다.
- **아키텍처 스타일이 상호 배타적이지 않다**: 하나의 프로젝트가 layered이면서 동시에 event-driven일 수 있다. 그러나 스키마에서는 단일 값(`architecture_style: string`)만 허용한다.
- **Rust의 `use`/`mod` 분석이 피상적이다**: `crate::`만으로 내부/외부를 구분하는데, `use super::`, `use self::`, re-export 패턴 등이 누락되어 있다.
- **C/C++, Swift, Kotlin의 import 분석이 완전히 빠져 있다**: agents/scan.md에서는 `.swift`, `.kt` 등을 소스 파일로 분류하면서, analyze에서는 이 언어들의 import 구문을 다루지 않는다.

### agents/map.md

**양호한 점**: 토큰 예산 관리의 우선순위 테이블과 축약 전략이 구체적이다. 후속 스킬 연계 최적화 테이블도 실용적이다.

**문제점**:
- **토큰 수 추정 방법이 정의되어 있지 않다**: "estimated_tokens"를 산출해야 하지만, 어떤 토크나이저를 기준으로 몇 토큰인지 계산하는 방법이 없다. LLM이 자체적으로 토큰 수를 정확히 추정하는 것은 불가능에 가깝다.
- **"기본값 4000 토큰"의 근거가 없다**: 왜 4000인가? 어떤 모델의 컨텍스트 윈도우를 기준으로 한 것인지 설명이 없다. Claude의 200K 컨텍스트에서 4000은 극히 작은 비율이다.
- **일관성 검증을 LLM에게 위임하는 것이 비현실적이다**: ID 상호 참조, 경로 일관성 등을 LLM이 실시간으로 완벽하게 검증하는 것은 기대하기 어렵다. 프로그래매틱 검증이 필요한 영역이다.

---

## 4. 프롬프트 분석

### 공통 문제

1. **에이전트 정의와의 내용 중복이 심각하다**: 모든 프롬프트가 에이전트 정의의 내용을 거의 그대로 반복하면서 Step 형태로 재구성한 것이다. 예를 들어:
   - agents/scan.md의 "파일 분류 기준" 테이블 ≈ prompts/scan.md의 "Step 3: 파일 분류"
   - agents/detect.md의 "프레임워크 탐지 시그니처" ≈ prompts/detect.md의 "Step 2: 프레임워크 탐지"
   
   이 중복은 유지보수 비용을 2배로 만든다. 한쪽을 수정하고 다른 쪽을 빠뜨리면 불일치가 발생한다.

2. **템플릿 변수 바인딩 메커니즘이 정의되어 있지 않다**: `{{scan_output}}`, `{{detect_output}}`, `{{token_budget}}` 등의 변수가 사용되지만, 이 변수들이 어떻게 주입되는지(어떤 런타임? 어떤 포맷?) 정의가 없다.

3. **출력 형식이 "YAML 형식으로 출력하세요"로만 지정**: 실제로 YAML을 코드 블록으로 감싸야 하는지, 순수 YAML이어야 하는지, 마크다운 내 YAML인지 명확하지 않다. 후속 에이전트가 이 출력을 파싱해야 한다면 형식이 엄밀해야 한다.

### prompts/scan.md

- Step이 8개로 세분화되어 있어 지시가 명확한 편이다.
- 다만 **Step 7(디렉토리 규칙 탐지)가 중량 모드에서만 수행되는데, Step 6(적응적 깊이 판별) 이후에 배치되어 순서는 적절하다.**

### prompts/detect.md

- Step 7개가 논리적 순서대로 잘 배치되어 있다.
- **카테고리 순서(`language → framework → ... → infra`)가 프롬프트에서만 명시되고 skills.yaml에는 없다.** 이 정렬 규칙이 후속 처리에 영향을 미치는지 불명확하다.

### prompts/analyze.md

- **경량/중량 모드에 따른 분기가 프롬프트 상단에 명시된 것은 좋다.**
- 그러나 **"Step 1 → Step 2(간략) → Step 7로 건너뛰기"라는 지시에서 "Step 2(간략)"의 의미가 모호하다.** 경량 모드에서 Step 2를 수행하라는 것인지, 생략하라는 것인지 혼동된다. 실제로 하단의 "경량 모드" 설명에서는 "Step 1에서 간략 의존성 요약만 추가하고 Step 7로"라고 하여 Step 2를 건너뛰라고 한다. 상단과 하단의 지시가 모순된다.

### prompts/map.md

- 8단계 중 Step 7(일관성 검증)과 Step 8(토큰 예산 최종 조정)은 현실적으로 LLM이 수행하기 어려운 작업이다. 특히 토큰 수 계산은 LLM의 능력 밖이다.

---

## 5. 예제 분석

### 공통 문제

1. **모든 예제가 동일한 프로젝트(Task Manager API)를 사용한다**: Express + TypeScript + Prisma라는 매우 전형적인 스택 하나만 커버하며, 다음과 같은 중요한 시나리오가 완전히 누락되어 있다:
   - 경량 모드 예제 (소규모 프로젝트)
   - 모노레포 프로젝트
   - Python/Go/Rust 등 비-Node.js 프로젝트
   - 마이크로서비스 아키텍처
   - 매니페스트가 없는 레거시 프로젝트
   - 에스컬레이션이 발생하는 경우

2. **예제 간 데이터 일관성 문제**: 
   - scan-input.md에서 "파일 약 65개"라고 했는데, scan-output.md의 depth_mode.evidence.file_count는 38이다. 65와 38의 차이가 설명되지 않는다. (제외된 파일 포함 시 65? 소스 파일만 38? 불명확)
   - scan-input.md에서 "프레임워크 2개(Express, Prisma)"라고 했는데, Prisma를 프레임워크로 분류하는 것은 일반적이지 않다. detect-output.md에서도 Prisma의 카테고리는 `database`이다.

3. **입력 예제가 비현실적이다**: analyze-input.md와 map-input.md는 "scan-output.md 참조"와 "detect-output.md 참조"라는 간접 참조만 있고, 실제 입력 데이터의 전문을 포함하지 않는다. 이는 예제로서의 실용성을 크게 떨어뜨린다.

4. **detect-input.md가 지나치게 간략하다**: scan 출력의 극히 일부만 "핵심 참조 포인트"로 보여주고 있어, 실제 detect 에이전트가 어떤 입력을 받는지 파악하기 어렵다.

### scan-output 예제

- `file_count: 38`인데, file_classification을 합산하면 source(21) + config(7) + test(6) + doc(1) + build(3) + static(0) = 38로 일치한다. 양호하다.
- 그러나 `.gitignore` 파일 자체가 file_classification 어느 카테고리에도 속하지 않는다. 디렉토리 트리에는 `.gitignore`가 있지만 분류에서 누락되었다. `other` 카테고리가 필요한 이유를 보여주는 사례다.

### detect-output 예제

- TS-003(Prisma)의 카테고리가 `database`인데, Prisma는 ORM이지 데이터베이스가 아니다. `orm` 카테고리를 추가하거나, 최소한 별도 분류가 필요하다. 현재 skills.yaml의 category enum에 `orm`이 없다.
- TS-007(Supertest)의 `config_location: null`은 YAML에서 null로 표현되었지만, skills.yaml의 output 정의에서 이 필드가 nullable인지 명시되지 않았다.

### analyze-output 예제

- CM-004(Repositories)의 type이 `library`인데, 실제로는 data access layer로서 `service`에 더 가깝다. 또는 별도의 `repository` 타입이 필요하다. 현재 7개 타입(`service, library, handler, model, config, util, test`) 중 repository 패턴에 정확히 맞는 것이 없다.
- CM-006(Models)의 dependents에 `[CM-003, CM-004]`가 있는데, CM-004(Repositories)가 Models에 의존한다는 것은 Prisma 기반에서는 부자연스럽다. Prisma는 schema.prisma에서 모델을 정의하며, TypeScript 타입과 별도이다. 이 의존 관계가 실제 코드에서 성립하는지 의문이다.

### map-output 예제

- detect-output.md에서 기술이 12개(TS-001~TS-012)였는데, map-output.md에서는 7개(TS-001~TS-007)로 병합되었다. TS-003에서 Prisma와 PostgreSQL을 "Prisma + PostgreSQL"로 합치고, TS-005에서 ESLint와 Prettier를 병합한 것은 토큰 축약 전략으로 이해되나, **ID 체계가 완전히 재번호화되었다.** 원본의 TS-003(Prisma)과 map의 TS-003(Prisma + PostgreSQL)은 다른 엔티티이다. 이는 후속 스킬이 ID로 참조할 때 혼란을 일으킨다.
- `tech_relationships`가 `technology_stack_detection` 배열 내에 들어가 있는데, YAML 구조상 배열의 마지막 항목 뒤에 `tech_relationships` 키가 오는 것은 문법적으로 부정확하다. 이것은 배열이 아닌 객체 내의 두 필드여야 한다.

---

## 6. 일관성 검토

### 용어 불일치

| 위치 | 용어 A | 용어 B | 문제 |
|------|--------|--------|------|
| skills.yaml vs agents/scan.md | `file_classification.other` (설명에만 존재) | 스키마에는 `other` 없음 | 스키마-설명 불일치 |
| skills.yaml line 69 | `category: other` (config_files) | prisma/schema.prisma | Prisma 스키마가 `other`로 분류되는 것이 적절한지 의문. `orm` 또는 `database` 카테고리가 없다 |
| scan agent | "소스 파일 수 ≤ 50개" | scan prompt | "소스 파일 수 ≤ 50개" | 일치하나, scan-output 예제의 file_count(38)는 전체 파일 수이며 소스만의 수(21)와 다르다 |
| skills.yaml | `interaction_mode: auto-execute` | 모든 에이전트 동일 | 이 필드의 의미와 다른 옵션이 정의되어 있지 않다 |
| detect agent | `category: database` | Prisma (ORM) | ORM을 database로 분류 |

### 네이밍 불일치

- skills.yaml에서 스킬 이름은 `ex`이지만, 설명에서는 "Explorer"라고 부른다. 약어와 전체 이름의 매핑이 명시적이지 않다.
- `depth_mode`와 `adaptive_depth`라는 두 가지 용어가 혼용된다. skills.yaml에서는 `adaptive_depth`를 에이전트 속성으로, `depth_mode`를 출력 필드로 사용하는데, 같은 개념에 대해 두 가지 이름을 쓰고 있다.

### 형식 불일치

- scan-output 예제에서 `directory_conventions`가 별도의 YAML 블록으로 분리되어 있지만, map-output에서는 `project_structure_map.directory_conventions`에 인라인으로 포함된다. 같은 데이터가 서로 다른 구조로 표현된다.
- detect-output에서 `tech_relationships`는 `tech_stack`과 같은 레벨이지만, map-output에서는 `technology_stack_detection` 배열 내부에 들어가 있다.

---

## 7. 주요 문제점 (심각도 순)

### 심각 (구조적 문제)

1. **agents/와 prompts/의 대규모 내용 중복**: 4개 에이전트 x 2개 파일 = 8개 파일에 걸쳐 동일한 규칙이 반복 기술된다. 불일치 위험이 높고, 수정 비용이 2배이다. 에이전트 정의는 "무엇을 하는가(What)"에, 프롬프트는 "어떻게 하는가(How)"에 집중해야 하는데, 현재는 두 파일 모두 "무엇을 어떻게" 전부를 담고 있다.

2. **LLM에게 비현실적인 작업을 요구한다**: 토큰 수 정확한 추정, ID 일관성 검증, YAML 구조의 엄밀한 생성 등은 LLM의 약점 영역이다. 프로그래매틱 후처리 파이프라인이 없다면 산출물의 신뢰성이 보장되지 않는다.

3. **escalation_only 필드의 의미 모호성**: scan과 detect가 `escalation_only: true`인데, 파이프라인에서 자동 실행되어야 한다. 이 필드가 "다른 스킬에서 직접 호출 불가, 파이프라인 내에서만 실행"이라는 의미라면, 그 정의가 어디에도 없다.

### 높음 (기능적 문제)

4. **예제 커버리지 부족**: 단일 프로젝트 유형(TypeScript/Express)만 예제로 제공. 경량 모드, 다른 언어, 에스컬레이션 시나리오 등의 예제가 전무하다.

5. **map-output에서 ID 재번호화로 인한 참조 무결성 파괴**: detect가 부여한 TS-001~TS-012와 map이 출력한 TS-001~TS-007은 서로 다른 엔티티를 가리킨다.

6. **file_classification에서 `other` 카테고리의 스키마 누락**: 실제로 .gitignore, prisma/schema.prisma 등 기존 카테고리에 깔끔하게 맞지 않는 파일이 존재함에도 other가 스키마에 없다.

### 보통 (설계 개선 필요)

7. **아키텍처 스타일이 단일 값으로 제한**: 현실 프로젝트는 복수 아키텍처 특성을 동시에 가질 수 있다.

8. **detect의 기술 탐지 시그니처가 하드코딩**: 확장성이 없다.

9. **토큰 예산 기본값 4000의 근거 부재**: 이 값이 적절한지 판단할 근거가 없다.

10. **analyze-prompt의 경량 모드 분기 지시가 모순적**: 상단에서 "Step 2(간략)"이라 했다가, 하단에서는 Step 2를 건너뛰라고 한다.

---

## 8. 개선 제안

### 즉시 수행 가능

1. **agents/와 prompts/ 간 역할을 엄밀하게 분리한다.**
   - `agents/*.md`: 역할 정의, 핵심 원칙, 산출물 스키마, 주의사항만 포함 (What + Why)
   - `prompts/*.md`: 구체적인 Step-by-step 실행 지시, 예제 포맷, 조건부 분기만 포함 (How)
   - 공통 규칙(파일 분류 기준, 탐지 시그니처 등)은 별도 참조 파일로 분리하여 양쪽에서 참조

2. **skills.yaml의 file_classification에 `other` 프로퍼티를 추가한다.**

3. **escalation_only 필드의 의미를 skills.yaml 상단이나 별도 스키마 문서에 명확히 정의한다.**

4. **analyze-prompt의 경량 모드 분기 지시 모순을 수정한다.** "Step 1 → Step 7"로 명확하게 건너뛰기를 지시하고, "Step 2(간략)"이라는 모호한 표현을 제거한다.

5. **map-output 예제에서 ID 재번호화를 하지 않도록 수정한다.** detect의 원본 ID를 유지하고, 병합된 항목은 별도 표기한다.

### 중기 개선

6. **경량 모드 프로젝트, Python 프로젝트, 모노레포, 에스컬레이션 발생 시나리오에 대한 예제를 추가한다.** 최소 3~4가지 프로젝트 유형을 커버해야 한다.

7. **아키텍처 스타일을 배열로 변경하여 복수 스타일을 허용한다.** 각 스타일에 confidence score를 부여하는 것도 고려한다.
   ```yaml
   architecture_styles:
     - style: layered
       confidence: 0.9
       evidence: [...]
     - style: modular-monolith
       confidence: 0.6
       evidence: [...]
   ```

8. **토큰 예산 관리를 LLM 단독이 아닌 프로그래매틱 파이프라인으로 보완한다.** 산출물 생성 후 실제 토큰 수를 tiktoken 등으로 계산하여 재조정하는 후처리 단계를 추가한다.

### 장기 개선

9. **detect의 기술 탐지 시그니처를 외부 데이터 파일(예: `signatures.yaml`)로 분리한다.** 새로운 기술 추가 시 에이전트 정의를 수정하지 않아도 되도록 한다.

10. **산출물의 일관성 검증(ID 참조, 경로 일관성 등)을 프로그래매틱으로 수행하는 검증 단계를 파이프라인에 추가한다.** LLM에게 맡기지 않는다.

11. **C/C++, Swift, Kotlin, Dart 등 현재 누락된 언어에 대한 import 분석 규칙을 추가한다.**

---

## 총평

Ex 스킬의 설계 의도와 전체 구조는 우수하다. 4단계 파이프라인(scan -> detect -> analyze -> map), 적응적 깊이, 토큰 예산 관리, 후속 스킬 연계 등의 개념은 잘 설계되어 있다.

그러나 실제 구현 수준에서는 **agents/와 prompts/ 간의 대규모 내용 중복**, **LLM에게 비현실적인 작업(토큰 정밀 계산, 일관성 검증) 위임**, **단일 예제 프로젝트에 의존한 불충분한 커버리지**, **스키마와 실제 사용 간의 불일치(other 누락, ID 재번호화, escalation_only 의미 모호)**가 핵심 약점이다.

현재 상태로는 "잘 작성된 설계 문서"이지 "실행 가능한 스킬 정의"라고 보기는 어렵다. 프로그래매틱 검증/후처리 파이프라인 없이 LLM만으로 일관된 산출물을 기대하기는 어려우며, agents/와 prompts/의 중복은 유지보수 부채로 빠르게 누적될 것이다.
