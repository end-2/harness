# Ex (Explorer) Skill 구현 계획

## 개요

기존 프로젝트의 코드베이스를 자동 분석하여, **LLM 컨텍스트 윈도우에 최적화된 프로젝트 맵(Project Map)**을 생성하는 스킬입니다.

RE가 "무엇을 만들 것인가"를, Arch가 "어떻게 구조를 잡을 것인가"를 결정하는 **순방향 스킬**이라면, Ex는 **역방향 스킬**로서 "이미 존재하는 코드가 무엇이고 어떻게 구성되어 있는가"를 추출합니다. 기존 코드베이스에 대한 문서가 없거나 부실한 경우, 또는 harness 스킬 체인의 시작점으로 기존 프로젝트의 맥락을 주입해야 하는 경우에 사용합니다.

코드에서 구조화된 컨텍스트를 추출하는 것이 핵심이므로, **자동 실행 + 결과 보고** 모델을 채택합니다. 사용자에게 질문하지 않고 코드베이스를 기계적으로 분석하며, **분석 불가능한 상황(암호화된 바이너리, 접근 불가 파일 등)에서만 에스컬레이션**합니다.

### 전통적 코드 분석 vs AI 컨텍스트 탐색

| 구분 | 전통적 코드 분석 | AI 컨텍스트 탐색 |
|------|----------------|-----------------|
| 수행자 | 시니어 개발자가 수동으로 코드 리딩 | AI가 자동으로 코드베이스 전체 분석 |
| 입력 | 코드베이스 + 개발자의 시간과 경험 | **프로젝트 루트 경로** (최소 입력) |
| 목적 | 개발자 본인의 이해 | **LLM이 소비할 수 있는 구조화된 컨텍스트 생성** |
| 산출물 | 비정형 메모, 화이트보드 스케치 | **후속 스킬이 직접 소비 가능한 표준화된 4섹션 산출물** |
| 깊이 | 분석자 역량에 의존 | **프로젝트 복잡도에 따라 적응적 조절** |
| 토큰 효율 | 해당 없음 | **LLM 컨텍스트 윈도우 예산 내에서 최대 정보 밀도** |
| 갱신 | 코드 변경 시 수동 재분석 | **프로젝트 루트만 지정하면 자동 재생성** |

## 적응적 깊이

프로젝트 복잡도를 자동 판별하여 분석 깊이를 조절합니다.

| 프로젝트 복잡도 | 판별 기준 | Ex 모드 | 산출물 수준 |
|---------------|-----------|---------|------------|
| 경량 | 파일 수 ≤ 50개, 언어 1개, 프레임워크 ≤ 1개, 디렉토리 깊이 ≤ 3 | 경량 | 디렉토리 트리 + 기술 스택 요약 + 진입점 목록 + 간략 의존성 |
| 중량 | 파일 수 > 50개 또는 언어 > 1개 또는 프레임워크 > 1개 또는 디렉토리 깊이 > 3 | 중량 | 전체 구조 맵 + 컴포넌트 관계 그래프 + API 경계 분석 + 의존성 트리 + 패턴 탐지 + 아키텍처 추론 |

## 최종 산출물 구조

Ex 스킬의 최종 산출물은 다음 **네 가지 섹션**으로 구성됩니다. 기존 코드베이스의 구조와 특성을 LLM이 소비할 수 있는 형태로 추출하며, 코드 품질 평가나 개선 제안은 포함하지 않습니다.

### 산출물 파일 레이아웃 (메타데이터/문서 분리)

각 섹션의 산출물은 **메타데이터 파일과 사람이 읽는 markdown 문서를 분리**하여 한 쌍으로 관리합니다. 메타데이터는 진행 상태/승인 상태/추적성 같은 구조화된 필드를 담고, markdown은 서술적 설명과 다이어그램을 담습니다.

| 파일 유형 | 형식 | 역할 | 편집 주체 |
|----------|------|------|---------|
| 메타데이터 | **YAML** (권장) | 진행 상태, 승인 상태, 추적성 ref, 섹션별 구조화 필드 | **스크립트만** (`scripts/artifact.py`) |
| 문서 | Markdown | 서술 설명, 표, 다이어그램, 근거 | 에이전트가 직접 편집 |

**YAML을 채택한 이유**:
- 주석 지원으로 필드 설명과 추적성 메모를 인라인으로 남길 수 있음
- 들여쓰기 기반 표현이 사람이 읽고 검토하기에 JSON보다 친화적
- PyYAML/ruamel.yaml 등 표준 라이브러리로 스크립트 파싱이 용이하며 라운드트립 보존 가능
- harness 다른 스킬(`skills.yaml`)과의 형식 일관성

**비파괴적 분석 원칙과의 관계**: 메타데이터 파일과 문서 markdown은 **분석 대상 프로젝트(`project_root`) 안에 절대 생성되지 않습니다**. Ex 스킬 자체의 산출물 저장소(`ex/out/<run-id>/` 등 호출자가 지정한 출력 디렉토리)에만 기록되며, 분석 대상은 읽기 전용으로만 접근합니다.

각 섹션은 다음 한 쌍을 가집니다:

| 섹션 | 메타데이터 파일 | 문서 파일 |
|------|---------------|----------|
| 프로젝트 구조 맵 | `structure-map.yaml` | `structure-map.md` |
| 기술 스택 탐지 | `tech-stack.yaml` | `tech-stack.md` |
| 컴포넌트 관계 분석 | `components.yaml` | `components.md` |
| 아키텍처 추론 | `architecture.yaml` | `architecture.md` |

### 메타데이터 공통 스키마

모든 섹션의 YAML 메타데이터는 다음 공통 헤더를 포함합니다. 이 필드들은 **스크립트(`scripts/artifact.py`)를 통해서만 갱신**되며, 에이전트가 직접 YAML/JSON을 편집해서는 안 됩니다.

| 필드 | 설명 |
|------|------|
| `artifact_id` | 산출물 고유 ID (예: `EX-STRUCT-001`) |
| `section` | 4섹션 중 하나 (`structure_map` / `tech_stack` / `components` / `architecture`) |
| `phase` | 현재 진행 단계 (`pending` / `scanning` / `drafting` / `review` / `finalized`) |
| `progress` | 0–100 정수, 해당 섹션 내부 진행률 |
| `approval.state` | 승인 상태 (`unreviewed` / `approved` / `changes_requested` / `rejected`) |
| `approval.approver` | 승인자 식별자 (사용자 또는 후속 스킬) |
| `approval.approved_at` | 승인 타임스탬프 |
| `approval.notes` | 승인 메모 |
| `traceability.upstream_refs` | 이 산출물이 의존하는 상류 ref (예: scan 에이전트 출력 ID) |
| `traceability.downstream_refs` | 이 산출물을 소비하는 하류 ref (예: `re:elicit`, `arch:design` 입력 ID) |
| `document_path` | 짝이 되는 markdown 문서의 상대 경로 |
| `generated_at` / `updated_at` | 생성/갱신 타임스탬프 |

### 1. 프로젝트 구조 맵 (Project Structure Map)

프로젝트의 디렉토리 구조와 파일 구성을 정리합니다.

| 필드 | 설명 |
|------|------|
| `project_root` | 프로젝트 루트 경로 |
| `directory_tree` | 디렉토리 트리 (토큰 효율적 축약 형식, .gitignore 패턴 제외) |
| `file_count` | 총 파일 수 (유형별 분류) |
| `directory_conventions` | 탐지된 디렉토리 규칙 (예: "src/ 하위에 도메인별 분리", "tests/ 미러링 구조") |
| `entry_points` | 진입점 파일 목록 (main, index, app, server 등) 및 역할 추론 |
| `config_files` | 설정 파일 목록 (빌드, 린트, CI, 환경 변수 등) 및 역할 |
| `ignored_patterns` | .gitignore 및 분석 제외 패턴 |

### 2. 기술 스택 탐지 (Technology Stack Detection)

사용된 언어, 프레임워크, 도구를 자동 탐지합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `TS-001`) |
| `category` | 카테고리 (`language` / `framework` / `database` / `messaging` / `build` / `test` / `lint` / `ci` / `container` / `infra`) |
| `name` | 기술 이름 |
| `version` | 탐지된 버전 (매니페스트 파일 기반) |
| `evidence` | 탐지 근거 (어떤 파일에서 탐지했는지) |
| `role` | 프로젝트 내 역할 추론 (예: "주 언어", "테스트 프레임워크", "ORM") |
| `config_location` | 관련 설정 파일 경로 |

### 3. 컴포넌트 관계 분석 (Component Relationship Analysis)

모듈/컴포넌트 간 의존성과 통신 패턴을 분석합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `CM-001`) |
| `name` | 컴포넌트/모듈 이름 |
| `path` | 파일 시스템 경로 |
| `type` | 추론된 유형 (`service` / `library` / `handler` / `model` / `config` / `util` / `test`) |
| `responsibility` | 추론된 핵심 책임 (주요 export/public 인터페이스 기반) |
| `dependencies_internal` | 내부 의존 모듈 목록 (import/require 분석) |
| `dependencies_external` | 외부 패키지 의존 목록 |
| `dependents` | 이 모듈을 의존하는 모듈 목록 (역참조) |
| `api_surface` | 외부에 노출하는 API (HTTP 라우트, gRPC 서비스, 이벤트 핸들러 등) |
| `patterns_detected` | 탐지된 디자인 패턴 (Repository, Factory, Observer 등) |

### 4. 아키텍처 추론 (Architecture Inference)

코드에서 추론된 아키텍처 특성과 패턴을 요약합니다.

| 필드 | 설명 |
|------|------|
| `architecture_style` | 추론된 아키텍처 스타일 (`monolithic` / `modular-monolith` / `microservices` / `serverless` / `layered` / `hexagonal`) |
| `style_evidence` | 스타일 추론 근거 (디렉토리 구조, 의존성 패턴, 설정 파일 등) |
| `layer_structure` | 탐지된 계층 구조 (presentation → business → data 등) |
| `communication_patterns` | 탐지된 통신 패턴 (REST, gRPC, 이벤트 버스, DB 공유 등) |
| `data_stores` | 탐지된 데이터 저장소 및 접근 패턴 |
| `cross_cutting_concerns` | 탐지된 횡단 관심사 (인증, 로깅, 에러 처리, 미들웨어 등) |
| `test_patterns` | 탐지된 테스트 패턴 (단위/통합/E2E, 테스트 프레임워크, 커버리지 설정) |
| `build_deploy_patterns` | 탐지된 빌드/배포 패턴 (Dockerfile, CI 설정, IaC 존재 여부) |
| `token_budget_summary` | 전체 산출물의 토큰 수 추정 및 축약 수준 표시 |

### 후속 스킬 연계

```
ex 산출물 구조:
┌─────────────────────────────────────────┐
│  프로젝트 구조 맵 (Structure Map)        │──→ re:elicit (기존 기능 파악, 도메인 맥락)
│  - directory_tree                       │──→ impl:generate (디렉토리 컨벤션 준수)
│  - entry_points, config_files           │──→ devops:pipeline (빌드/배포 설정 기반)
├─────────────────────────────────────────┤
│  기술 스택 탐지 (Tech Stack)             │──→ arch:design (기존 기술 제약으로 반영)
│  - TS-001: language: TypeScript         │──→ impl:generate (언어/프레임워크 관용구)
│  - TS-002: framework: Next.js           │──→ qa:strategy (테스트 프레임워크 선택)
├─────────────────────────────────────────┤
│  컴포넌트 관계 분석 (Components)          │──→ arch:design (기존 컴포넌트 경계 참조)
│  - CM-001: API Handler                  │──→ impl:generate (기존 모듈 구조 준수)
│  - CM-002: Data Access Layer            │──→ sec:threat-model (공격 표면 식별)
├─────────────────────────────────────────┤
│  아키텍처 추론 (Architecture Inference)   │──→ arch:design (기존 아키텍처 전제로 수용)
│  - style: modular-monolith              │──→ re:elicit (기존 시스템 제약 도출)
│  - patterns, test_patterns              │──→ qa:strategy (기존 테스트 패턴 준수)
└─────────────────────────────────────────┘

주요 소비 시나리오:

1. 기존 프로젝트에 새 기능 추가 시:
   ex → re:elicit (기존 맥락 주입) → re:spec → arch:design → impl:generate

2. 기존 프로젝트의 아키텍처 리뷰:
   ex → arch:review (기존 구조 기반 리뷰)

3. 기존 프로젝트의 보안 감사:
   ex → sec:threat-model (공격 표면 식별) → sec:audit

4. 기존 프로젝트의 테스트 전략 수립:
   ex → qa:strategy (기존 테스트 패턴 기반)
```

## 목표 구조 (Claude Code Skill 표준 준수)

본 스킬은 Claude Code Skill 공식 표준(https://code.claude.com/docs/ko/skills)을 따라 **단일 진입점 `SKILL.md`** + **`references/` 요구 시 로드 자료** + **`assets/` 템플릿** + **`scripts/` 보조 스크립트** 구조로 구성합니다. harness 사내 컨벤션이었던 `skills.yaml`, `agents/`, `prompts/` 디렉토리는 사용하지 않습니다.

```
ex/
├── SKILL.md                          # [필수] 단일 진입점 (≤300줄)
│                                     #   - frontmatter (name/description/argument-hint/
│                                     #     allowed-tools/context/agent)
│                                     #   - Pre-scan !`...` 동적 컨텍스트 주입
│                                     #   - Phase 1~4 실행 지시
│                                     #   - references/ 로드 가이드
│                                     #   - 에스컬레이션 규칙 / 결과 보고 형식
│
├── references/                       # [표준] 요구 시 로드되는 상세 자료
│   ├── output-schema.md              # 4섹션 필드 정의 (본 계획 "최종 산출물 구조" 이관)
│   ├── detect-patterns.md            # 프레임워크/언어/DB 시그니처 카탈로그
│   ├── analyze-heuristics.md         # 아키텍처 추론 규칙 / 휴리스틱
│   ├── token-budget.md               # 축약/우선순위 규칙 (토큰 최적화 가이드)
│   └── escalation.md                 # 분석 불가 케이스 카탈로그
│
├── scripts/                          # [표준] 실행 가능 보조 스크립트
│   ├── artifact.py                   # 메타데이터 CRUD 단일 인터페이스
│   ├── schema.py                     # YAML 스키마 정의 및 검증
│   └── render.py                     # 메타데이터 → markdown 골격 렌더링
│
├── assets/                           # [표준] 템플릿 (표준의 `assets/` 컨벤션)
│   ├── structure-map.md.tmpl
│   ├── tech-stack.md.tmpl
│   ├── components.md.tmpl
│   ├── architecture.md.tmpl
│   └── metadata.yaml.tmpl            # 공통 메타데이터 헤더 템플릿
│
├── examples/                         # 시나리오별 완성 예시 (메타데이터/문서 쌍)
│   ├── lite-express/                 # 경량 (~20 파일)
│   │   ├── structure-map.{yaml,md}
│   │   ├── tech-stack.{yaml,md}
│   │   ├── components.{yaml,md}
│   │   └── architecture.{yaml,md}
│   ├── heavy-nextjs-prisma/          # 중량 (~200 파일)
│   ├── monorepo-turbo/               # 모노레포
│   └── trace-artifact-script/        # init→drafting→approve 시퀀스 트레이스
│
└── out/                              # 런타임 산출물 (gitignore 권장)
    └── <session-id>/                 # 기본 출력 위치: ${CLAUDE_SKILL_DIR}/out/${CLAUDE_SESSION_ID}/
```

> 표준 준수 원칙: `agents/`, `prompts/`, `skills.yaml`은 표준 Skill 디렉토리에 존재하지 않으므로 완전히 제거했습니다. 과거 4개 에이전트(`scan`/`detect`/`analyze`/`map`)는 본 계획에서 **SKILL.md 본문의 Phase 1~4 단계**로 통합되고, 각 단계의 상세 카탈로그는 `references/`로 분리됩니다. 템플릿은 표준 컨벤션인 `assets/` 아래에 둡니다.

## SKILL.md 내부 실행 흐름 (Phase 1~4)

과거 `agents/*.md` 4개로 나뉘어 있던 파이프라인을, 표준 Skill 모델에 맞추어 **SKILL.md 본문의 4개 Phase 섹션**으로 통합합니다. 각 Phase는 본문에서 간결하게 지시하고, 상세 카탈로그/휴리스틱은 `references/`에서 요구 시 로드합니다.

```
$1 = project_root
    │
    ▼
Phase 1: Scan ─────────────────────────────┐
    │  (디렉토리 구조 스캔 →                  │
    │   파일 분류 → 진입점 식별 →             │
    │   복잡도 판별 → 경량/중량 모드 결정)     │
    │  상세 참조: references/detect-patterns.md
    │                                      │
    ▼                                      │
Phase 2: Detect                            │
    │  (매니페스트 파일 분석 →                 │
    │   언어/프레임워크/도구 탐지 →            │
    │   버전 및 설정 위치 매핑)                │
    │  상세 참조: references/detect-patterns.md
    │                                      │
    ▼                                      │
Phase 3: Analyze                           │
    │  (import/require 분석 →               │
    │   모듈 의존성 그래프 구축 →              │
    │   컴포넌트 경계 추론 →                  │
    │   API 표면 식별 →                     │
    │   아키텍처 스타일 추론)                  │
    │  상세 참조: references/analyze-heuristics.md
    │                                      │
    ▼                                      │
Phase 4: Map  ◄────────────────────────────┘
    (Phase 1~3 결과를 토큰 효율 최적화하여
     4섹션 최종 산출물로 통합)
    상세 참조: references/token-budget.md,
              references/output-schema.md
```

### Phase 실행 규칙

- Phase 1~3은 **`context: fork` + `agent: Explore`** 서브에이전트에서 수행되어 메인 컨텍스트를 오염시키지 않습니다. 대량 파일 스캔/의존성 추적으로 발생하는 토큰 부담을 격리하기 위한 핵심 설계 결정입니다.
- Phase 4(Map)의 결과만 메인 컨텍스트로 전달되어 사용자 보고와 후속 스킬 연계에 사용됩니다.
- 각 Phase는 SKILL.md 본문에서 "이 단계에서는 `references/<파일>`을 읽은 뒤 수행하라" 형태로 **요구 시 로드 지시**를 합니다. references 파일은 항상 로드되지 않으며 Phase가 실제 필요로 할 때만 로드됩니다.
- **전체 파이프라인은 사용자 개입 없이 자동 실행**되며, 사용자 접점은 (1) 분석 불가 상황 에스컬레이션과 (2) 최종 결과 보고 두 곳뿐입니다.

## 구현 단계

### 1단계: `SKILL.md` 작성 — 표준 Skill 진입점

SKILL.md를 디렉토리 최상단에 신설합니다. 본문은 ≤300줄을 목표로 유지하고, 상세 카탈로그는 `references/`로 분리합니다.

#### 1-1. Frontmatter (YAML)

Claude Code Skill 표준은 frontmatter에서 `name`과 `description` 두 필드만 필수로 요구합니다. ex도 이 최소 사양을 그대로 따릅니다.

```yaml
---
name: ex
description: Analyze an existing codebase and produce a token-efficient 4-section project map (structure, tech stack, components, architecture) for downstream harness skills. Use when starting from an existing project with no or poor documentation, or when injecting prior-art context into re/arch/impl/qa/sec/devops chains.
---
```

- `name`: 디렉토리명과 일치하는 `ex`. lowercase/digit/hyphen 규칙 준수.
- `description`: **자동 호출(auto-invocation) 트리거**로 사용되며 250자 절단 한도 안에 (1) 무엇을 만드는지, (2) 언제 호출되어야 하는지(`Use when ...`)를 앞쪽에 배치. "existing project", "no documentation", "inject prior-art context" 같은 키워드가 250자 안에 들어오도록 설계.
- 그 외 옵션 필드(`argument-hint`, `allowed-tools`, `context`, `agent`, `disable-model-invocation`, `user-invocable` 등)는 **기본적으로 추가하지 않으며**, 스킬이 기본 동작만으로 목적을 달성하지 못하는 구체적 이유가 있을 때에만 도입합니다. 예를 들어 ex의 "기존 프로젝트를 절대 수정하지 않는다"는 비파괴 원칙을 기술적으로 강제해야 한다면, `Write`를 제외한 `allowed-tools: Read Glob Grep Bash`를 명시적인 보안 가드로 추가하는 것이 정당화됩니다. 그 외 필드는 실제 필요가 발생한 시점에 별도 결정으로 추가합니다.

#### 1-2. Pre-scan 동적 컨텍스트 주입

SKILL.md 상단에 표준 `` !`...` `` 구문으로 사전 컨텍스트를 로딩 시점에 주입하여 Phase 1의 토큰 소비를 사전 절감합니다.

```markdown
## Pre-scan context
- Working dir: !`pwd`
- Target root: !`test -d "$1" && echo "OK: $1" || echo "MISSING: $1"`
- Top-level:  !`ls -la "$1" 2>/dev/null | head -30`
- Manifests:  !`fd -t f -d 2 '(package\.json|go\.mod|Cargo\.toml|pyproject\.toml|requirements\.txt|pom\.xml|build\.gradle|Gemfile)$' "$1" 2>/dev/null`
- Git branch: !`git -C "$1" rev-parse --abbrev-ref HEAD 2>/dev/null`
- Skill dir:  ${CLAUDE_SKILL_DIR}
- Session:    ${CLAUDE_SESSION_ID}
```

`${CLAUDE_SKILL_DIR}`, `${CLAUDE_SESSION_ID}`, `$1` 같은 표준 치환 토큰을 적극 활용하여 스크립트 절대 경로 참조(`${CLAUDE_SKILL_DIR}/scripts/artifact.py`)와 기본 출력 디렉토리(`${CLAUDE_SKILL_DIR}/out/${CLAUDE_SESSION_ID}/`)를 구성합니다.

#### 1-3. 인자 파싱 규약

- `$1`: 필수 — 분석 대상 프로젝트 루트 (`project_root`). 사전 검사에서 디렉토리 부재 시 즉시 에스컬레이션.
- `--depth lite|heavy`: 선택 — 경량/중량 모드 수동 지정 (기본: 자동 판별).
- `--budget N`: 선택 — 최종 산출물의 목표 토큰 수 (기본: 4000).
- `--focus <path>`: 선택 — 특정 디렉토리/컴포넌트 집중 분석.
- `--out <dir>`: 선택 — 출력 디렉토리. 미지정 시 기본값 `${CLAUDE_SKILL_DIR}/out/${CLAUDE_SESSION_ID}/`.
- `--exclude <glob,...>`: 선택 — 추가 제외 패턴 (기본: .gitignore + node_modules, .git, __pycache__ 등).

SKILL.md 본문 상단 "Argument parsing" 섹션에서 `$ARGUMENTS` 전체 문자열을 파싱하고, 결과를 Phase 1~4에서 참조합니다.

#### 1-4. SKILL.md 본문 구조 (≤300줄 목표)

```markdown
# ex — Explorer

## Pre-scan context     <!-- !`...` 동적 주입 -->
## Argument parsing     <!-- $1 + 플래그 해석 -->
## Output contract      <!-- 4섹션 요약. 상세는 references/output-schema.md -->
## Phase 1: Scan        <!-- 요구 시 references/detect-patterns.md 로드 -->
## Phase 2: Detect      <!-- 요구 시 references/detect-patterns.md 로드 -->
## Phase 3: Analyze     <!-- 요구 시 references/analyze-heuristics.md 로드 -->
## Phase 4: Map         <!-- 요구 시 references/token-budget.md + output-schema.md 로드 -->
## Artifact script protocol  <!-- scripts/artifact.py 호출 규약 -->
## Escalation           <!-- 요구 시 references/escalation.md 로드 -->
## Reporting format     <!-- 출력 경로를 반드시 포함한 결과 보고 형식 -->
```

각 Phase 섹션은 짧은 지시문(수행 목표, 입력, 출력, 다음 Phase로 전달할 필드)만 담고, **프레임워크 시그니처/휴리스틱/축약 규칙** 같은 상세 카탈로그는 해당 Phase에서 `references/`를 읽어오게 합니다. 이 분리가 SKILL.md 500줄 한도를 준수하는 핵심 전략입니다.

#### 1-5. 입력 유효성 / 에스컬레이션 조건

- 프로젝트 루트가 존재하지 않거나 접근 불가
- 심볼릭 링크 순환 탐지
- 매니페스트 파일이 전혀 없음 (순수 스크립트 프로젝트 — 모호한 기술 조합 탐지 포함)
- 바이너리 전용/암호화된 프로젝트

상세 케이스 카탈로그는 `references/escalation.md`에 정리.

#### 1-6. 출력 계약

- 4섹션 (`project_structure_map`, `technology_stack_detection`, `component_relationship_analysis`, `architecture_inference`) 산출물 쌍
- 기본 출력 위치: `${CLAUDE_SKILL_DIR}/out/${CLAUDE_SESSION_ID}/`
- 사용자 지정 위치: `--out <dir>`
- **출력 절대 경로는 결과 보고에 반드시 포함** (SKILL.md "Reporting format" 섹션에서 강제)
- 분석 대상 프로젝트(`project_root`) 내부에는 어떠한 파일도 쓰지 않음 (비파괴)
- 후속 소비자: `re`, `arch`, `impl`, `qa`, `sec`, `devops`

### 2단계: Phase 상세 지시 — SKILL.md 본문 + `references/` 카탈로그

과거 `agents/*.md` 4개에 담으려 했던 내용은 이제 **SKILL.md 본문의 Phase 섹션(요약)** + **`references/*.md`(상세 카탈로그)** 두 층으로 분리됩니다. 본 단계에서는 각 Phase의 역할/핵심 역량을 정의하고, 그 중 상세 카탈로그에 해당하는 부분을 references로 이관하는 대응 관계를 고정합니다.

| Phase | SKILL.md 본문 (요약) | references/ 상세 자료 |
|-------|---------------------|----------------------|
| 1. Scan | 디렉토리 트리 구축, 파일 분류, 진입점 식별, 복잡도 판별 지시 | `detect-patterns.md` (매니페스트/진입점 시그니처) |
| 2. Detect | 매니페스트 분석, 언어/프레임워크/DB/CI 탐지 지시 | `detect-patterns.md` (프레임워크 탐지 시그니처 카탈로그) |
| 3. Analyze | import 분석, 컴포넌트 경계/API 표면/아키텍처 스타일 추론 지시 | `analyze-heuristics.md` (휴리스틱 규칙) |
| 4. Map | 토큰 예산 내 통합, 4섹션 매핑, 후속 스킬 최적화 지시 | `token-budget.md` (축약/우선순위), `output-schema.md` (4섹션 필드 정의) |

#### Phase 1: Scan — 구조 스캔

- **역할**: 프로젝트 디렉토리 구조를 스캔하고, 파일을 분류하며, 적응적 깊이 모드를 결정
- **핵심 역량**:
  - **디렉토리 트리 구축**: .gitignore 패턴 존중, 불필요 파일(node_modules, .git, build 산출물) 자동 제외
  - **파일 분류**: 소스 코드, 설정, 테스트, 문서, 빌드 산출물, 정적 자원 등으로 분류
  - **진입점 식별**: main, index, app, server, bootstrap 등 관용적 진입점 파일 탐지
  - **설정 파일 매핑**: package.json, go.mod, Cargo.toml, pyproject.toml, Makefile, Dockerfile, .env.example 등 식별 및 역할 태깅
  - **복잡도 판별**: 파일 수, 언어 수, 프레임워크 수, 디렉토리 깊이를 기준으로 경량/중량 모드 자동 결정
  - **.gitignore 패턴 해석**: 프로젝트의 .gitignore를 분석하여 무시 패턴 파악
  - **토큰 효율적 트리 표현**: 반복 패턴 축약 (예: `components/{Header,Footer,Nav,...12 more}/index.tsx`)
- **입력**: 프로젝트 루트 경로, 제외 패턴
- **출력**:
  - 디렉토리 트리 (축약)
  - 파일 분류 결과
  - 진입점 목록
  - 설정 파일 목록
  - 적응적 깊이 모드 판정 (경량/중량 + 판별 근거)
- **상호작용 모델**: 프로젝트 경로 수신 → 자동 스캔 → 결과 출력 (사용자 개입 없음)
- **에스컬레이션 조건**: 프로젝트 루트가 존재하지 않거나 접근 불가한 경우, 심볼릭 링크 순환 탐지 시

#### Phase 2: Detect — 기술 스택 탐지

- **역할**: 매니페스트 파일, 설정 파일, 코드 패턴을 분석하여 사용된 기술 스택을 자동 탐지
- **핵심 역량**:
  - **매니페스트 파일 분석**: package.json (npm/yarn/pnpm), go.mod, Cargo.toml, pyproject.toml/requirements.txt/Pipfile, pom.xml/build.gradle, Gemfile 등에서 의존성과 버전 추출
  - **프레임워크 탐지**: 의존성 목록 + 코드 패턴(import 문, 데코레이터, 설정 파일)으로 프레임워크 식별
    - Next.js: next.config.js + `import from 'next'`
    - Express: `require('express')` + 라우트 패턴
    - Spring Boot: `@SpringBootApplication` + pom.xml
    - Django: settings.py + `INSTALLED_APPS`
    - FastAPI: `from fastapi import` + uvicorn 설정
  - **데이터베이스 탐지**: ORM 설정(prisma, typeorm, gorm, sqlalchemy), 마이그레이션 디렉토리, 환경 변수(DATABASE_URL) 분석
  - **테스트 프레임워크 탐지**: jest.config, pytest.ini, _test.go 패턴, 테스트 디렉토리 구조
  - **빌드 도구 탐지**: webpack, vite, esbuild, tsc, make, gradle, maven 설정 파일
  - **CI/CD 탐지**: .github/workflows/, .gitlab-ci.yml, Jenkinsfile, CircleCI 설정
  - **컨테이너/인프라 탐지**: Dockerfile, docker-compose.yml, terraform/, helm/, k8s manifests
  - **탐지 근거 기록**: 각 기술에 대해 "어떤 파일의 어떤 패턴에서 탐지했는가" 기록
- **입력**: scan 에이전트의 파일 분류 결과 + 설정 파일 목록
- **출력**:
  - 탐지된 기술 스택 목록 (카테고리, 이름, 버전, 탐지 근거, 역할, 설정 위치)
  - 기술 간 관계 (예: "TypeScript 프로젝트에서 Jest를 테스트에, Prisma를 ORM으로 사용")
- **상호작용 모델**: scan 결과 수신 → 자동 탐지 → 결과 출력 (사용자 개입 없음)
- **에스컬레이션 조건**: 매니페스트 파일이 전혀 없는 경우 (순수 스크립트 프로젝트), 모호한 기술 조합 탐지 시 (복수 프레임워크가 동시에 존재하는 비정형 구조)

#### Phase 3: Analyze — 의존성/아키텍처 분석

- **역할**: 코드의 import/require 구문을 분석하여 모듈 의존성 그래프를 구축하고, 컴포넌트 경계와 아키텍처 스타일을 추론
- **핵심 역량**:
  - **Import 분석**: 언어별 import/require/use 구문을 파싱하여 모듈 간 의존성 그래프 구축
    - TypeScript/JavaScript: `import from`, `require()`
    - Python: `import`, `from ... import`
    - Go: `import (...)`
    - Java: `import ...`
    - Rust: `use ...`, `mod ...`
  - **컴포넌트 경계 추론**: 디렉토리 구조 + 의존성 방향으로 논리적 컴포넌트 경계 식별
    - 높은 내부 응집도(intra-directory imports) + 낮은 외부 결합도(inter-directory imports) = 컴포넌트 경계
  - **API 표면 식별**: HTTP 라우트 정의, gRPC 서비스 정의, 이벤트 핸들러 등 외부 인터페이스 탐지
  - **아키텍처 스타일 추론**:
    - 레이어드: controller → service → repository 패턴
    - 헥사고날: ports/adapters 디렉토리 패턴
    - 모놀리식: 단일 진입점 + 공유 DB 접근
    - 마이크로서비스: 복수 Dockerfile/서비스 디렉토리
    - 이벤트 드리븐: 메시지 큐 의존성 + 이벤트 핸들러 패턴
  - **횡단 관심사 탐지**: 인증 미들웨어, 로깅 설정, 에러 처리 패턴, 공통 유틸리티
  - **데이터 흐름 추적**: 데이터가 진입점에서 저장소까지 어떤 경로로 흐르는지 추론
  - **순환 의존성 탐지**: 모듈 간 순환 참조 식별
  - **경량 모드 동작**: 경량 모드에서는 import 분석과 아키텍처 추론을 생략하고, 디렉토리 기반 컴포넌트 분류만 수행
- **입력**: scan 에이전트의 구조 정보 + detect 에이전트의 기술 스택 정보
- **출력**:
  - 모듈/컴포넌트 목록 (이름, 경로, 유형, 책임 추론, 의존 관계)
  - API 표면 목록
  - 아키텍처 스타일 추론 (스타일, 근거, 계층 구조, 통신 패턴)
  - 횡단 관심사 목록
  - 순환 의존성 경고 (있는 경우)
- **상호작용 모델**: scan + detect 결과 수신 → 자동 분석 → 결과 출력 (사용자 개입 없음)
- **에스컬레이션 조건**: 없음 — 분석 불가한 파일은 건너뛰고 분석 가능한 범위에서 최선의 결과 생성

#### Phase 4: Map — 컨텍스트 맵 생성

- **역할**: scan, detect, analyze의 결과를 통합하여 LLM 토큰 효율에 최적화된 최종 4섹션 산출물 생성
- **핵심 역량**:
  - **토큰 예산 관리**: 지정된 토큰 예산(기본 4000) 내에서 최대 정보 밀도 달성
    - 우선순위: 진입점/API > 컴포넌트 구조 > 기술 스택 > 상세 의존성
    - 반복 패턴 축약: 유사 파일 그룹화 (예: "12 React components in components/")
    - 계층적 상세: 중요 모듈은 상세히, 유틸/설정은 요약
  - **4섹션 통합**: scan → project_structure_map, detect → technology_stack_detection, analyze → component_relationship_analysis + architecture_inference 매핑
  - **후속 스킬 최적화**: 각 산출물 필드가 어떤 후속 스킬에서 어떻게 소비되는지를 고려하여 정보 선별
    - re:elicit가 필요로 하는 도메인 힌트 강조
    - arch:design이 필요로 하는 기존 구조 제약 강조
    - impl:generate가 필요로 하는 컨벤션/패턴 강조
  - **일관성 검증**: 4섹션 간 상호 참조(ID, 경로) 일관성 확인
  - **메타데이터 생성**: 분석 타임스탬프, 모드(경량/중량), 분석 범위, 제외 항목, 토큰 수 추정
- **입력**: scan + detect + analyze 에이전트의 전체 결과
- **출력**: 최종 4섹션 산출물 (project_structure_map, technology_stack_detection, component_relationship_analysis, architecture_inference)
- **상호작용 모델**: 세 에이전트 결과 수신 → 토큰 예산 내 최적화 통합 → 최종 산출물 출력 + 결과 보고
- **에스컬레이션 조건**: 없음
- **메타데이터/문서 운용 규칙**:
  - 4섹션 각각에 대해 `scripts/artifact.py init --section <name>`을 호출하여 YAML 메타데이터와 markdown 문서 골격을 동시에 생성
  - 통합/축약 후 `scripts/artifact.py set-phase --section <name> --phase finalized`로 진행 상태 갱신
  - 후속 스킬 연계가 결정되면 `scripts/artifact.py link --downstream re:elicit,arch:design` 형태로 추적성 ref 기록
  - 메타데이터 파일을 직접 편집하지 않고, 모든 상태 전이를 스크립트로만 수행

### 3단계: 메타데이터/템플릿/스크립트 기반 산출물 골격 (`scripts/`, `assets/`)

산출물의 구조 일관성과 추적성을 보장하기 위해, 메타데이터 갱신과 문서 골격 생성을 **스크립트와 템플릿**으로 강제합니다. 템플릿은 표준 Skill의 `assets/` 컨벤션에 따라 `assets/` 아래에 둡니다.

#### 3-1. 템플릿 (`assets/`)

- **markdown 템플릿**: 4섹션 각각의 `*.md.tmpl` 파일에 섹션 헤더, 표 골격, 플레이스홀더(`<!-- TODO: ... -->`), 다이어그램 자리(예: mermaid 코드 블록)를 미리 정의
  - `structure-map.md.tmpl`: "디렉토리 트리", "진입점 목록", "설정 파일 매핑" 헤더와 표 골격
  - `tech-stack.md.tmpl`: 카테고리별(`language`/`framework`/`database` 등) 표 골격 + 탐지 근거 섹션
  - `components.md.tmpl`: 컴포넌트 카드 섹션 + 의존성 다이어그램(mermaid) 자리
  - `architecture.md.tmpl`: 스타일 추론, 계층 구조, 횡단 관심사, 빌드/배포 패턴 섹션
- **메타데이터 템플릿**: `metadata.yaml.tmpl`에 공통 헤더(`artifact_id`, `phase`, `progress`, `approval`, `traceability`)의 기본값 정의
- 템플릿은 사람이 읽기 쉽도록 주석으로 각 플레이스홀더의 작성 가이드를 포함

#### 3-2. 스크립트 (`scripts/`)

- `artifact.py`는 에이전트가 메타데이터를 다루는 **유일한 인터페이스**이며, 다음 서브커맨드를 제공:

| 커맨드 | 역할 |
|--------|------|
| `init --section <name> --out <dir>` | 템플릿 기반으로 `<section>.yaml` + `<section>.md` 한 쌍을 생성. `phase=pending`, `approval.state=unreviewed`로 초기화 |
| `set-phase --section <name> --phase <value>` | 진행 단계 전이 (`pending → scanning → drafting → review → finalized`) |
| `set-progress --section <name> --value <0-100>` | 진행률 갱신 |
| `approve --section <name> --approver <id> [--notes <str>]` | 승인 상태를 `approved`로 전이하고 타임스탬프 기록 |
| `request-changes --section <name> --notes <str>` | 승인 상태를 `changes_requested`로 전이 |
| `link --section <name> [--upstream <refs>] [--downstream <refs>]` | 추적성 ref 추가/갱신 |
| `get --section <name> [--field <path>]` | 메타데이터 조회 (다른 에이전트가 상태를 읽을 때 사용) |
| `validate [--section <name>]` | `schema.py` 기반으로 메타데이터 무결성 검증 |

- `schema.py`: 공통 헤더 + 섹션별 페이로드 스키마를 정의하고 검증
- `render.py`: 메타데이터의 일부 필드(예: 카테고리 표, 의존성 그래프)를 markdown 골격에 주입하여 초기 문서를 생성. 이후 Phase 실행자는 markdown만 직접 편집하고 메타데이터는 스크립트로만 갱신
- **작업 규약**: YAML/JSON을 직접 열어 편집하는 행위는 금지. 모든 메타데이터 변경은 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 호출로만 수행하며, 호출 로그가 산출물 디렉토리에 남도록 함
- **출력 위치**: 기본값은 `${CLAUDE_SKILL_DIR}/out/${CLAUDE_SESSION_ID}/`이며, `--out <dir>` 플래그로 오버라이드 가능. 분석 대상 프로젝트(`project_root`) 안에는 어떠한 파일도 쓰지 않음 (비파괴적 분석 원칙)

### 4단계: `references/` 카탈로그 작성 — SKILL.md 요구 시 로드 자료

과거 `prompts/` 디렉토리에 담으려 했던 모든 상세 가이드/시그니처/휴리스틱은 **표준 Skill의 `references/` 컨벤션**에 맞춰 분리합니다. SKILL.md는 각 Phase에서 필요 시 해당 파일을 읽도록 지시하며, 항상 전체가 로드되지는 않습니다(토큰 절감). 작성 대상:

- `references/output-schema.md`: 4섹션(`project_structure_map`, `technology_stack_detection`, `component_relationship_analysis`, `architecture_inference`) 필드 정의 및 공통 메타데이터 헤더 스키마. 본 계획의 "최종 산출물 구조" 섹션에 해당하는 상세 표를 이관.
- `references/detect-patterns.md`: **기술 탐지 패턴 카탈로그** — 언어/프레임워크/DB/CI/컨테이너 탐지 시그니처 (매니페스트 파일 패턴, import 패턴, 설정 파일 패턴, 데코레이터 패턴). Phase 1/2가 로드.
- `references/analyze-heuristics.md`: **아키텍처 추론 휴리스틱** — 디렉토리 구조/의존성 패턴에서 아키텍처 스타일(layered/hexagonal/microservices/event-driven 등)을 추론하는 규칙, 컴포넌트 경계 식별 규칙, 순환 의존성 탐지 규칙. Phase 3가 로드.
- `references/token-budget.md`: **토큰 최적화 가이드** — 축약 규칙, 우선순위 기반 정보 선별, 반복 패턴 처리법, 계층적 상세화 레벨. Phase 4가 로드.
- `references/escalation.md`: 분석 불가 케이스 카탈로그 (바이너리 전용, 접근 권한 없음, 심볼릭 링크 순환, 모호한 기술 조합 등)와 각 케이스에 대한 에스컬레이션 메시지 템플릿.
- 각 references 파일은 Chain of Thought 가이드와 few-shot 예시 링크를 포함할 수 있으며, 실제 예시는 `examples/` 하위 시나리오 디렉토리에서 참조.

### 5단계: 입출력 예시 작성 (`examples/`) — 시나리오별 재편

Phase가 단일 SKILL.md 흐름으로 통합되었으므로, 과거 4 에이전트 × input/output = 8개 파일 분할은 제거하고 **시나리오별 디렉토리**로 재편합니다. 각 시나리오 디렉토리는 4섹션 메타데이터/문서 쌍을 모두 담습니다.

- `examples/lite-express/` — **경량** 시나리오: 단순 Express API (~20 파일). 자동으로 경량 모드가 선택됨을 보임.
- `examples/heavy-nextjs-prisma/` — **중량** 시나리오: Next.js + Prisma + Docker (~200 파일). 컴포넌트 관계 그래프 + 아키텍처 추론까지 완결.
- `examples/monorepo-turbo/` — **모노레포** 시나리오: turborepo/nx 복수 패키지. 패키지 경계와 공유 의존성 처리 방식을 보임.
- `examples/trace-artifact-script/` — **스크립트 호출 트레이스** 시나리오: `artifact.py init` → `set-phase drafting` → `set-progress 60` → `approve` 순으로 메타데이터가 전이되는 시퀀스. 진행/승인/추적성 필드가 어떻게 기록되는지 보임.
- (선택) `examples/downstream-handoff/` — **후속 스킬 연계** 예시: ex 산출물 → `re:elicit` 컨텍스트 주입 흐름 발췌.
- (선택) `examples/token-budget-4k/` — **토큰 예산 내 축약** 예시: 대규모 프로젝트를 4000 토큰 내로 요약한 결과와 축약 근거.

각 시나리오 디렉토리는 다음 4쌍을 포함:

```
examples/<scenario>/
├── structure-map.yaml     structure-map.md
├── tech-stack.yaml        tech-stack.md
├── components.yaml        components.md
└── architecture.yaml      architecture.md
```

SKILL.md에서는 "Phase 4의 출력 품질 판단에 어려움이 있으면 `examples/lite-express/` 또는 `examples/heavy-nextjs-prisma/`를 참고하라" 형태로 **요구 시 로드 지시**를 둡니다.

## 핵심 설계 원칙

1. **코드 기반 (Code-Driven)**: 문서나 사용자 설명이 아닌, 코드베이스 자체를 유일한 진실의 원천(single source of truth)으로 사용. 모든 산출물 필드는 코드에서 자동 추출
2. **자동 실행 + 최소 에스컬레이션 (Auto-Execute with Minimal Escalation)**: 프로젝트 루트 경로만으로 전체 분석 가능. 사용자 질문 없이 코드를 기계적으로 분석하며, 물리적으로 분석 불가능한 상황에서만 에스컬레이션
3. **토큰 효율 (Token Efficiency)**: LLM 컨텍스트 윈도우는 유한한 자원. 산출물은 지정된 토큰 예산 내에서 최대 정보 밀도를 달성하도록 설계. 반복 패턴 축약, 우선순위 기반 선별, 계층적 상세화
4. **적응적 깊이 (Adaptive Depth)**: 프로젝트 복잡도를 자동 판별하여 경량(구조 + 스택 요약)/중량(컴포넌트 그래프 + 아키텍처 추론) 모드 자동 전환
5. **역방향 호환성 (Reverse Compatibility)**: 산출물의 필드와 형식을 순방향 스킬(re, arch, impl)의 입력/산출물 스키마와 정렬하여, 후속 스킬이 파싱 없이 직접 소비 가능
6. **비파괴적 분석 (Non-destructive Analysis)**: 프로젝트 파일을 절대 수정하지 않음. 읽기 전용 분석만 수행
7. **증거 기반 추론 (Evidence-based Inference)**: 모든 탐지와 추론에 근거(evidence)를 명시. "어떤 파일의 어떤 패턴에서 이 결론을 도출했는가"를 추적 가능
8. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **프로젝트 구조 맵 / 기술 스택 탐지 / 컴포넌트 관계 분석 / 아키텍처 추론** 4섹션으로 고정하여, 후속 스킬(`re`, `arch`, `impl`, `qa`, `sec`, `devops`)이 직접 소비할 수 있는 계약(contract) 역할을 수행
9. **메타데이터/문서 분리 + 스크립트 전용 상태 관리 (Metadata-Document Split with Script-Mediated State)**: 각 섹션은 YAML 메타데이터와 markdown 문서의 한 쌍으로 존재하며, 메타데이터(진행 상태 `phase`/`progress`, 승인 상태 `approval`, 추적성 `traceability`)는 오직 `scripts/artifact.py`를 통해서만 갱신된다. 에이전트는 YAML/JSON을 직접 편집하지 않으며, 문서 markdown은 `templates/`의 골격을 스크립트로 렌더링한 후에만 편집한다. 모든 산출물 파일은 분석 대상 프로젝트가 아닌 Ex 스킬 자체의 출력 디렉토리에만 기록되어 비파괴적 분석 원칙을 보존한다
