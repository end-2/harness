# Ex (Exploration) Skill 구현 계획

## 개요

기존 코드베이스를 자동 분석하여, **LLM 컨텍스트 윈도우에 최적화된 4섹션 프로젝트 맵**(프로젝트 구조 맵, 기술 스택 탐지, 컴포넌트 관계, 아키텍처 추론)을 생성하는 스킬입니다.

RE가 "무엇을 만들 것인가"를, Arch가 "어떻게 구조를 잡을 것인가"를 결정하는 **순방향 스킬**이라면, Ex는 방향을 뒤집어 **이미 존재하는 코드가 무엇이고 어떻게 구성되어 있는가**를 코드 그 자체에서 추출합니다. 따라서 Ex는 harness 스킬 체인의 다른 스킬과 달리 상위 스킬의 산출물을 입력으로 받지 않고, **코드베이스 경로**를 유일한 입력으로 삼습니다. 산출된 4섹션 맵은 후속 순방향 스킬(`re`/`arch`/`impl`/`qa`/`sec`)에 **컨텍스트로 주입**되어, 신규 작업이 기존 코드 위에서 일관성 있게 수행되도록 합니다.

코드에서 구조화된 컨텍스트를 추출하는 것이 핵심이므로, **자동 실행 + 결과 보고** 모델을 채택합니다. 사용자에게 질문하지 않고 코드베이스를 기계적으로 분석하며, 분석이 물리적으로 불가능한 상황(접근 불가, 심볼릭 링크 순환, 바이너리 전용 등)에서만 에스컬레이션합니다.

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
| 방향 | 정해진 방향 없음 | **역방향**: 코드 → 컨텍스트 → 후속 순방향 스킬에 주입 |

## 입력 수집 방식 (코드베이스 스캔)

Ex 스킬은 harness의 다른 스킬과 달리 **선행 스킬의 산출물을 소비하지 않습니다**. 입력은 분석 대상 코드베이스의 경로와 동작 옵션이며, 코드베이스 그 자체가 유일한 진실의 원천(SSoT)입니다.

### 입력 인자

| 인자 | 필수 여부 | 설명 |
|------|----------|------|
| `$1` (`project_root`) | 필수 | 분석 대상 프로젝트의 루트 디렉토리 절대/상대 경로. 사전 검사에서 부재 시 즉시 에스컬레이션 |
| `--depth lite|heavy` | 선택 | 경량/중량 모드 수동 지정. 미지정 시 복잡도 자동 판별 |
| `--budget N` | 선택 | 최종 산출물의 목표 토큰 수 (기본 4000) |
| `--focus <path>` | 선택 | 특정 디렉토리/컴포넌트 집중 분석 |
| `--out <dir>` | 선택 | 출력 디렉토리. 미지정 시 `${CLAUDE_SKILL_DIR}/out/${CLAUDE_SESSION_ID}/` |
| `--exclude <glob,...>` | 선택 | 추가 제외 패턴 (기본: `.gitignore` + `node_modules`, `.git`, `__pycache__` 등) |

### Pre-scan 동적 컨텍스트 주입

SKILL.md 상단에서 표준 `` !`...` `` 구문으로 사전 컨텍스트를 로딩 시점에 주입하여 본 분석 단계의 토큰 소비를 사전 절감합니다.

```markdown
## Pre-scan context
- Working dir: !`pwd`
- Target root: !`test -d "$1" && echo "OK: $1" || echo "MISSING: $1"`
- Top-level:   !`ls -la "$1" 2>/dev/null | head -30`
- Manifests:   !`fd -t f -d 2 '(package\.json|go\.mod|Cargo\.toml|pyproject\.toml|requirements\.txt|pom\.xml|build\.gradle|Gemfile)$' "$1" 2>/dev/null`
- Git branch:  !`git -C "$1" rev-parse --abbrev-ref HEAD 2>/dev/null`
- Skill dir:   ${CLAUDE_SKILL_DIR}
- Session:     ${CLAUDE_SESSION_ID}
```

이 사전 컨텍스트는 단순한 진단 출력이 아니라, Phase 1(Scan)이 매니페스트 위치/디렉토리 깊이/Git 상태를 미리 알고 시작할 수 있도록 하는 **컨텍스트 워밍**입니다.

### 비파괴적 분석 원칙

Ex 스킬은 분석 대상 프로젝트(`project_root`) 안에 어떠한 파일도 쓰지 않습니다. 모든 산출물은 `--out` 으로 지정된 디렉토리(기본값: `${CLAUDE_SKILL_DIR}/out/${CLAUDE_SESSION_ID}/`)에만 기록되며, 분석 대상은 읽기 전용으로만 접근합니다.

## 적응적 깊이 (경량/중량 모드)

프로젝트 복잡도를 자동 판별하여 분석 깊이를 조절합니다. 동일한 SKILL.md 본문 안에서 분기 처리하며, 스킬 자체를 `ex-light`/`ex-full`로 분할하지 않습니다(단일 진입점 유지).

| 프로젝트 복잡도 | 판별 기준 | Ex 모드 | 산출물 수준 |
|---------------|-----------|---------|------------|
| 경량 | 파일 수 ≤ 50개, 언어 1개, 프레임워크 ≤ 1개, 디렉토리 깊이 ≤ 3 | 경량 | 디렉토리 트리 + 기술 스택 요약 + 진입점 목록 + 간략 의존성 |
| 중량 | 파일 수 > 50개 또는 언어 > 1개 또는 프레임워크 > 1개 또는 디렉토리 깊이 > 3 | 중량 | 전체 구조 맵 + 컴포넌트 관계 그래프 + API 경계 분석 + 의존성 트리 + 패턴 탐지 + 아키텍처 추론 |

상세 분기 규칙과 모드별 스킵 단계 정의는 `references/adaptive-depth.md` 에 분리합니다.

## 토큰 예산 관리

LLM 컨텍스트 윈도우는 유한한 자원이므로, Ex의 최종 산출물은 지정된 토큰 예산(기본 4000) 내에서 최대 정보 밀도를 달성하도록 설계합니다.

- **우선순위 기반 선별**: 진입점/API > 컴포넌트 구조 > 기술 스택 > 상세 의존성
- **반복 패턴 축약**: 유사 파일 그룹화 (예: `components/{Header,Footer,Nav,...12 more}/index.tsx`)
- **계층적 상세화**: 중요 모듈은 상세히, 유틸/설정은 요약
- **트리 표현 압축**: `.gitignore` 패턴 존중, 빌드 산출물 자동 제외

상세 축약 규칙은 `references/token-budget.md` 에 분리합니다.

## 최종 산출물 구조

Ex 스킬의 최종 산출물은 다음 **네 가지 섹션**으로 구성됩니다. 기존 코드베이스의 구조와 특성을 LLM이 소비할 수 있는 형태로 추출하며, 코드 품질 평가나 개선 제안은 포함하지 않습니다.

### 1. 프로젝트 구조 맵 (Project Structure Map)

| 필드 | 설명 |
|------|------|
| `project_root` | 프로젝트 루트 경로 |
| `directory_tree` | 디렉토리 트리 (토큰 효율적 축약 형식, `.gitignore` 패턴 제외) |
| `file_count` | 총 파일 수 (유형별 분류) |
| `directory_conventions` | 탐지된 디렉토리 규칙 (예: "src/ 하위에 도메인별 분리", "tests/ 미러링 구조") |
| `entry_points` | 진입점 파일 목록 (main, index, app, server 등) 및 역할 추론 |
| `config_files` | 설정 파일 목록 (빌드, 린트, CI, 환경 변수 등) 및 역할 |
| `ignored_patterns` | `.gitignore` 및 분석 제외 패턴 |

### 2. 기술 스택 탐지 (Technology Stack Detection)

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `TS-001`) |
| `category` | 카테고리 (`language` / `framework` / `database` / `messaging` / `build` / `test` / `lint` / `ci` / `container` / `infra`) |
| `name` | 기술 이름 |
| `version` | 탐지된 버전 (매니페스트 파일 기반) |
| `evidence` | 탐지 근거 (어떤 파일에서 탐지했는지) |
| `role` | 프로젝트 내 역할 추론 (예: "주 언어", "테스트 프레임워크", "ORM") |
| `config_location` | 관련 설정 파일 경로 |

### 3. 컴포넌트 관계 (Component Relationships)

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

### 산출물 파일 구성: 메타데이터 + 문서 분리

위 4섹션의 산출물은 **메타데이터 파일과 문서 markdown 파일을 분리**하여 저장합니다. 메타데이터는 구조화된 상태/추적 정보를 담고, markdown은 사람이 읽을 서술형 본문을 담습니다.

| 파일 유형 | 형식 | 역할 |
|----------|------|------|
| 메타데이터 파일 | **YAML** (`*.meta.yaml`) | 진행 상태, 승인 상태, 추적성(refs), 4섹션의 구조화 필드 저장. 스크립트가 읽고 쓰는 단일 진실 공급원(SSoT) |
| 문서 파일 | Markdown (`*.md`) | 디렉토리 트리, 기술 스택 표, 컴포넌트 설명, 아키텍처 추론 서술 본문 |

**YAML을 채택한 이유**:

- **주석 지원**: 탐지 근거나 임시 메모를 인라인 주석으로 남길 수 있어 사람이 검토 시 맥락 전달이 용이
- **사람이 읽기 쉬움**: 들여쓰기 기반 구조로 JSON 대비 시각적 가독성이 높음
- **스크립트 파싱 용이**: PyYAML 등 표준 라이브러리로 손쉽게 로드/덤프 가능하며, 키 순서 보존도 지원

각 섹션은 다음 한 쌍을 가집니다:

| 섹션 | 메타데이터 파일 | 문서 파일 |
|------|---------------|----------|
| 프로젝트 구조 맵 | `structure-map.meta.yaml` | `structure-map.md` |
| 기술 스택 탐지 | `tech-stack.meta.yaml` | `tech-stack.md` |
| 컴포넌트 관계 | `components.meta.yaml` | `components.md` |
| 아키텍처 추론 | `architecture.meta.yaml` | `architecture.md` |

### 메타데이터 스키마 (공통 필드)

각 산출물 메타데이터 파일은 4섹션의 구조화 필드 외에 다음 공통 필드를 포함합니다.

| 필드 | 설명 |
|------|------|
| `artifact_id` | 산출물 고유 식별자 (예: `EX-structure-001`) |
| `phase` | 현재 단계 (`draft` / `in_review` / `revising` / `approved` / `superseded`) |
| `progress` | 진행률 정보 (`section_completed`, `section_total`, `percent`) |
| `approval.state` | 승인 상태 (`pending` / `approved` / `rejected` / `changes_requested`) |
| `approval.approver` | 승인자 식별자 (사용자명/역할) |
| `approval.approved_at` | 승인 시각 (ISO 8601) |
| `approval.notes` | 승인/반려 코멘트 |
| `upstream_refs` | 상위 산출물 ID 목록 (Ex의 경우 일반적으로 비어 있음 — 코드베이스가 입력) |
| `downstream_refs` | 이 산출물이 주입되는 후속 스킬 식별자 목록 (`re`, `arch`, `impl`, `qa`, `sec` 등) |
| `document_path` | 짝을 이루는 markdown 문서의 상대 경로 |
| `updated_at` | 최종 수정 시각 |

### 스크립트 기반 메타데이터 조작 (필수)

에이전트는 **YAML 메타데이터 파일을 직접 편집하지 않습니다**. 모든 상태 갱신은 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 를 통해서만 수행하며, 이는 다음을 보장합니다.

- 스키마 검증 (잘못된 phase 값, 누락 필드 차단)
- `updated_at` 등 자동 필드의 일관된 갱신
- 추적성 ref 의 양방향 무결성 (downstream 주입 대상 동기화)
- 승인 상태 전이 규칙 적용

핵심 스크립트(예시):

| 스크립트 커맨드 | 용도 |
|----------------|------|
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section <name>` | 메타데이터 + markdown 템플릿 쌍을 새로 생성 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py set-phase <id> <phase>` | 진행 단계 전이 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py set-progress <id> --completed N --total M` | 진행률 갱신 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py approve <id> --approver <name> [--notes ...]` | 승인 상태 전이 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py link <id> --downstream <ref>` | 주입 대상 후속 스킬 ref 추가 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py show <id>` | 메타데이터 조회 (사람이 읽기 좋은 형태) |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py validate [<id>]` | 스키마/추적성 검증 |

### 문서 템플릿 (`assets/templates/`)

markdown 문서 또한 자유 양식이 아니라, `assets/templates/` 디렉토리에 4섹션별 템플릿을 사전에 정의합니다. `artifact.py init` 실행 시 해당 템플릿이 복사되어 **섹션 헤더, 표 골격, 플레이스홀더가 채워진 골격**이 생성되며, 에이전트는 이 골격 안의 플레이스홀더를 채우는 방식으로 본문을 작성합니다.

| 템플릿 파일 | 대상 섹션 |
|------------|----------|
| `assets/templates/structure-map.md.tmpl` | 프로젝트 구조 맵 (디렉토리 트리/진입점/설정 파일 골격) |
| `assets/templates/tech-stack.md.tmpl` | 기술 스택 탐지 (카테고리별 표 골격 + 탐지 근거) |
| `assets/templates/components.md.tmpl` | 컴포넌트 관계 (컴포넌트 카드 + 의존성 mermaid 자리) |
| `assets/templates/architecture.md.tmpl` | 아키텍처 추론 (스타일/계층/횡단 관심사 골격) |
| `assets/templates/*.meta.yaml.tmpl` | 각 섹션 메타데이터의 초기 골격 |

### 후속 스킬 연계 (역방향 주입)

Ex는 다른 스킬과 달리 **자신이 후속 스킬에 컨텍스트를 주입**합니다. 화살표는 "Ex의 산출물이 후속 스킬의 작업에 컨텍스트로 들어간다"는 의미이며, 후속 스킬이 Ex 산출물을 능동적으로 가져오는 것이 아니라 Ex가 push 방식으로 제공합니다.

```
ex 산출물 (역방향 주입):
┌─────────────────────────────────────────┐
│  프로젝트 구조 맵 (Structure Map)        │──→ re   (기존 기능/도메인 맥락 주입)
│  - directory_tree                       │──→ impl (디렉토리 컨벤션 준수 컨텍스트)
│  - entry_points, config_files           │──→ qa   (테스트 진입점 맥락)
├─────────────────────────────────────────┤
│  기술 스택 (Tech Stack)                  │──→ arch (기존 기술 제약을 설계 입력으로)
│  - TS-001: language: TypeScript         │──→ impl (관용구/프레임워크 맥락)
│  - TS-002: framework: Next.js           │──→ qa   (테스트 프레임워크 결정 컨텍스트)
├─────────────────────────────────────────┤
│  컴포넌트 관계 (Components)              │──→ arch (기존 컴포넌트 경계 컨텍스트)
│  - CM-001: API Handler                  │──→ impl (기존 모듈 구조 컨텍스트)
│  - CM-002: Data Access Layer            │──→ sec  (공격 표면 식별 컨텍스트)
├─────────────────────────────────────────┤
│  아키텍처 추론 (Architecture Inference)  │──→ arch (기존 아키텍처 전제로 수용)
│  - style: modular-monolith              │──→ re   (기존 시스템 제약 도출 컨텍스트)
│  - patterns, test_patterns              │──→ qa   (기존 테스트 패턴 컨텍스트)
└─────────────────────────────────────────┘

주요 주입 시나리오:

1. 기존 프로젝트에 새 기능 추가:
   ex → re (기존 맥락 주입) → arch → impl
2. 기존 프로젝트의 아키텍처 리뷰:
   ex → arch (기존 구조 컨텍스트로 리뷰)
3. 기존 프로젝트의 보안 감사:
   ex → sec (공격 표면 컨텍스트 → threat-model)
4. 기존 프로젝트의 테스트 전략 수립:
   ex → qa (기존 테스트 패턴 컨텍스트)
```

이 주입 계약은 `references/contracts/downstream-injection-contract.md` 에 상세 기술됩니다.

## 목표 구조 (Claude Code Skill 표준 준수)

본 스킬은 Claude Code Skill 공식 표준(https://code.claude.com/docs/ko/skills)을 따릅니다. 단일 진입점은 `ex/SKILL.md` 이며, `skills.yaml`, `agents/`, `prompts/` 디렉토리는 사용하지 않습니다. 상세 행동 규칙과 단계별 가이드는 `references/` 에, 템플릿은 `assets/` 에 분리합니다.

```
ex/
├── SKILL.md                              # 필수 진입점 (YAML frontmatter + 4단계 워크플로우 요약, 500줄 이내)
├── scripts/
│   └── artifact.py                       # 메타데이터 init/set-phase/set-progress/approve/link/show/validate
├── assets/
│   └── templates/
│       ├── structure-map.md.tmpl
│       ├── structure-map.meta.yaml.tmpl
│       ├── tech-stack.md.tmpl
│       ├── tech-stack.meta.yaml.tmpl
│       ├── components.md.tmpl
│       ├── components.meta.yaml.tmpl
│       ├── architecture.md.tmpl
│       └── architecture.meta.yaml.tmpl
└── references/
    ├── workflow/
    │   ├── scan.md                       # 스캔 단계 상세 행동 규칙 (on-demand 로드)
    │   ├── detect.md                     # 기술 탐지 단계 상세 행동 규칙
    │   ├── analyze.md                    # 관계 분석 단계 상세 행동 규칙
    │   └── map.md                        # 통합 맵 생성 단계 상세 행동 규칙
    ├── contracts/
    │   └── downstream-injection-contract.md  # re/arch/impl/qa/sec 주입 계약
    ├── schemas/
    │   ├── meta-schema.md                # 메타데이터 공통 필드 설명
    │   └── section-schemas.md            # 4섹션 필드 명세
    ├── adaptive-depth.md                 # 경량/중량 분기 규칙
    ├── detect-patterns.md                # 프레임워크/언어/DB/CI 탐지 시그니처 카탈로그
    ├── analyze-heuristics.md             # 의존성/컴포넌트 경계/아키텍처 스타일 추론 휴리스틱
    ├── token-budget.md                   # 축약/우선순위/계층적 상세화 규칙
    ├── escalation.md                     # 분석 불가 케이스 카탈로그
    └── examples/
        ├── light/
        │   ├── structure-map.md
        │   ├── structure-map.meta.yaml
        │   ├── tech-stack.md
        │   ├── tech-stack.meta.yaml
        │   ├── components.md
        │   ├── components.meta.yaml
        │   ├── architecture.md
        │   └── architecture.meta.yaml
        └── heavy/
            ├── structure-map.md
            ├── structure-map.meta.yaml
            ├── tech-stack.md
            ├── tech-stack.meta.yaml
            ├── components.md
            ├── components.meta.yaml
            ├── architecture.md
            └── architecture.meta.yaml
```

요점:
- `SKILL.md`가 유일한 필수 진입점이며, 4개의 워크플로우 단계(scan/detect/analyze/map)는 **동일 SKILL.md 안에 짧게 요약**하고, 상세 규칙은 `references/workflow/*.md` 로 분리하여 **on-demand 로드**합니다.
- 표준 명칭인 `assets/templates/`, `references/examples/` 를 사용합니다.
- `skills.yaml`, `agents/`, `prompts/` 는 폐기합니다.

## 워크플로우 단계 (SKILL.md 내부 단일 진입점)

표준 스킬 모델을 따르기 위해, 기존에 "4개의 내부 에이전트(scan/detect/analyze/map)"로 구상했던 파이프라인은 **별도의 시스템 프롬프트 파일이 아니라**, SKILL.md가 순차적으로 수행하는 **4개의 워크플로우 단계**로 재정의됩니다. 각 단계의 상세 행동 규칙은 `references/workflow/*.md` 에 분리되어 필요 시점에 Read로 로드됩니다.

```
$1 = project_root (코드베이스 경로)
    │
    ▼
[Stage 1] scan ────────────────────────────┐
    │  references/workflow/scan.md 로드     │
    │  (디렉토리 트리 → 파일 분류 →           │
    │   진입점 식별 → 복잡도 판별 →           │
    │   경량/중량 모드 결정)                  │
    │                                      │
    ▼                                      │
[Stage 2] detect                           │
    │  references/workflow/detect.md +     │
    │  references/detect-patterns.md       │
    │  (매니페스트 분석 → 언어/프레임워크/    │
    │   DB/테스트/CI/컨테이너 탐지 →          │
    │   탐지 근거 기록)                      │
    │                                      │
    ▼                                      │
[Stage 3] analyze                          │
    │  references/workflow/analyze.md +    │
    │  references/analyze-heuristics.md    │
    │  (import 분석 → 의존성 그래프 →        │
    │   컴포넌트 경계 → API 표면 →           │
    │   아키텍처 스타일 추론)                 │
    │                                      │
    ▼                                      │
[Stage 4] map ◄────────────────────────────┘
    references/workflow/map.md +
    references/token-budget.md 로드
    (Stage 1~3 결과를 토큰 예산 내에서
     4섹션 산출물로 통합 →
     downstream 주입 ref 등록)
    │
    ▼
re / arch / impl / qa / sec 에 컨텍스트 주입
```

### `references/workflow/scan.md` — 스캔 단계 상세 규칙

- **역할**: 프로젝트 디렉토리 구조를 스캔하고, 파일을 분류하며, 적응적 깊이 모드를 결정
- **핵심 역량**:
  - **디렉토리 트리 구축**: `.gitignore` 패턴 존중, 불필요 파일(`node_modules`, `.git`, build 산출물) 자동 제외
  - **파일 분류**: 소스 코드, 설정, 테스트, 문서, 빌드 산출물, 정적 자원 등
  - **진입점 식별**: `main`, `index`, `app`, `server`, `bootstrap` 등 관용 진입점 탐지
  - **설정 파일 매핑**: `package.json`, `go.mod`, `Cargo.toml`, `pyproject.toml`, `Makefile`, `Dockerfile`, `.env.example` 등의 역할 태깅
  - **복잡도 판별**: 파일 수/언어 수/프레임워크 수/디렉토리 깊이를 기준으로 경량/중량 모드 자동 결정
  - **토큰 효율적 트리 표현**: 반복 패턴 축약 (예: `components/{Header,Footer,Nav,...12 more}/index.tsx`)
- **입력**: `project_root`, 제외 패턴
- **출력**: 디렉토리 트리(축약), 파일 분류 결과, 진입점 목록, 설정 파일 목록, 적응적 깊이 모드 판정과 근거
- **상호작용 모델**: 자동 스캔 → 결과를 다음 단계로 전달 (사용자 개입 없음)

### `references/workflow/detect.md` — 기술 탐지 단계 상세 규칙

- **역할**: 매니페스트 파일과 코드 패턴을 분석하여 사용된 기술 스택을 자동 탐지
- **핵심 역량**:
  - **매니페스트 파일 분석**: `package.json`/`go.mod`/`Cargo.toml`/`pyproject.toml`/`requirements.txt`/`Pipfile`/`pom.xml`/`build.gradle`/`Gemfile` 등에서 의존성과 버전 추출
  - **프레임워크 탐지**: 의존성 + 코드 패턴(import, 데코레이터, 설정 파일)으로 식별
    - Next.js: `next.config.js` + `import from 'next'`
    - Express: `require('express')` + 라우트 패턴
    - Spring Boot: `@SpringBootApplication` + `pom.xml`
    - Django: `settings.py` + `INSTALLED_APPS`
    - FastAPI: `from fastapi import` + `uvicorn` 설정
  - **데이터베이스 탐지**: ORM 설정(prisma/typeorm/gorm/sqlalchemy), 마이그레이션 디렉토리, `DATABASE_URL` 환경 변수
  - **테스트/빌드/CI/컨테이너 탐지**: `jest.config`, `pytest.ini`, `_test.go`, webpack/vite/esbuild, `.github/workflows/`, Dockerfile, k8s manifests 등
  - **탐지 근거 기록**: 각 기술에 대해 "어떤 파일의 어떤 패턴에서 탐지했는가" 를 evidence 필드에 보존
- **입력**: scan 단계의 파일 분류 결과 + 설정 파일 목록
- **출력**: 카테고리/이름/버전/근거/역할/설정 위치를 갖춘 기술 스택 목록, 기술 간 관계
- **상호작용 모델**: 자동 탐지 → 결과를 다음 단계로 전달

### `references/workflow/analyze.md` — 관계 분석 단계 상세 규칙

- **역할**: import/require 구문을 분석하여 모듈 의존성 그래프를 구축하고, 컴포넌트 경계와 아키텍처 스타일을 추론
- **핵심 역량**:
  - **Import 분석**: 언어별 import/require/use 구문을 파싱
    - TypeScript/JavaScript: `import from`, `require()`
    - Python: `import`, `from ... import`
    - Go: `import (...)`
    - Java: `import ...`
    - Rust: `use ...`, `mod ...`
  - **컴포넌트 경계 추론**: 높은 내부 응집도 + 낮은 외부 결합도 = 컴포넌트 경계
  - **API 표면 식별**: HTTP 라우트, gRPC 서비스, 이벤트 핸들러 등 외부 인터페이스
  - **아키텍처 스타일 추론**: layered, hexagonal, monolithic, microservices, event-driven 등의 시그니처 매칭
  - **횡단 관심사 탐지**: 인증 미들웨어, 로깅 설정, 에러 처리 패턴
  - **순환 의존성 탐지**: 모듈 간 순환 참조 식별
  - **경량 모드 동작**: 경량 모드에서는 import 분석/아키텍처 추론을 생략하고 디렉토리 기반 분류만 수행
- **입력**: scan + detect 단계의 결과
- **출력**: 모듈/컴포넌트 목록(이름, 경로, 유형, 책임, 의존 관계), API 표면, 아키텍처 스타일 추론, 횡단 관심사, 순환 의존성 경고
- **상호작용 모델**: 자동 분석 → 결과를 다음 단계로 전달

### `references/workflow/map.md` — 통합 맵 생성 단계 상세 규칙

- **역할**: scan, detect, analyze 결과를 통합하여 LLM 토큰 효율에 최적화된 최종 4섹션 산출물 생성 및 후속 스킬 주입 ref 등록
- **핵심 역량**:
  - **토큰 예산 관리**: 지정된 예산(기본 4000) 내에서 최대 정보 밀도 달성
  - **4섹션 통합 매핑**: scan → 프로젝트 구조 맵, detect → 기술 스택, analyze → 컴포넌트 관계 + 아키텍처 추론
  - **후속 스킬 최적화**: 각 산출물 필드가 어떤 후속 스킬에서 어떻게 소비되는지를 고려해 정보 선별 (re의 도메인 힌트, arch의 기존 구조 제약, impl의 컨벤션 등)
  - **일관성 검증**: 4섹션 간 상호 참조(ID/경로) 일관성 확인
  - **메타데이터 갱신**: `artifact.py` 로 각 섹션을 `init` → `set-phase` 전이 → `link --downstream re,arch,impl,qa,sec` 로 주입 대상 등록
- **입력**: scan + detect + analyze 단계의 전체 결과
- **출력**: 최종 4섹션 산출물 + downstream 주입 ref 가 채워진 메타데이터
- **상호작용 모델**: 통합 → 산출물 출력 + 결과 보고 (출력 절대 경로 포함)

## 구현 단계

### 1단계: `SKILL.md` 작성 (필수 진입점 + frontmatter)

표준에서 메타데이터의 단일 출처는 `ex/SKILL.md` 의 YAML frontmatter 입니다. `skills.yaml` 은 표준 사양에 존재하지 않으므로 사용하지 않습니다. frontmatter 는 `name` 과 `description` 만 필수로 두고, 나머지 옵션 필드는 기본 동작으로 스킬 목적을 달성할 수 없음이 입증된 경우에만 추가합니다. Ex는 이미 `${CLAUDE_SKILL_DIR}` 치환자를 적극 활용하는 강점을 그대로 유지합니다.

**권장 frontmatter 초안**:

```yaml
---
name: ex
description: 기존 코드베이스를 자동 분석하여 LLM 컨텍스트 윈도우에 최적화된 4섹션 프로젝트 맵(구조/기술 스택/컴포넌트/아키텍처)을 생성하고 re/arch/impl/qa/sec에 컨텍스트로 주입한다. 문서가 없거나 부실한 기존 프로젝트의 맥락을 harness 스킬 체인 시작점에 주입해야 할 때 사용.
---
```

**설계 원칙**:

- **`name`**: 디렉토리명과 일치하는 `ex`. lowercase/digit/hyphen 규칙 준수.
- **`description` 작성 규칙**: 250자 절단 한도 안에 (1) 무엇을 만드는지, (2) 언제 호출되어야 하는지를 앞쪽에 배치합니다. "기존 코드베이스", "프로젝트 맵", "컨텍스트 주입" 같은 핵심 키워드를 250자 안에 배치합니다.
- 그 외 옵션 필드(`argument-hint`, `allowed-tools`, `effort`, `paths`, `hooks`, `context`, `agent` 등)는 기본값으로 두고 추가하지 않습니다. 단, "기존 프로젝트를 절대 수정하지 않는다" 는 비파괴 원칙을 기술적으로 강제할 필요가 있다면, `Write` 를 제외한 `allowed-tools: Read Glob Grep Bash` 를 명시적 보안 가드로 추가하는 것이 정당화됩니다.

**SKILL.md 본문 구성 (500줄 이내)**:

1. 스킬 개요 (코드베이스 → 4섹션 맵 → 후속 스킬 주입)
2. Pre-scan 동적 컨텍스트 주입 (`` !`...` `` 구문)
3. Argument parsing (`$1` + 플래그 해석)
4. 적응적 깊이 분기 로직 (복잡도 판별 → 경량/중량 모드 결정)
5. 4단계 워크플로우 요약 (scan → detect → analyze → map)
   - 각 단계는 **상세 규칙을 `${CLAUDE_SKILL_DIR}/references/workflow/<stage>.md` 에서 로드**하도록 명시
6. 스크립트 호출 규약: 모든 메타데이터 조작은 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 를 통해서만 수행
7. 시작 시 상태 주입: `` !`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate` `` 로 현재 산출물 상태를 동적 컨텍스트로 주입
8. 에스컬레이션 규칙 (`references/escalation.md` 참조)
9. Reporting format: 출력 절대 경로를 반드시 포함

**치환자 활용**:

- 모든 스크립트 경로는 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 로 작성하여 호출 위치에 무관하게 동작하도록 합니다.
- 기본 출력 위치는 `${CLAUDE_SKILL_DIR}/out/${CLAUDE_SESSION_ID}/` 로 구성합니다.
- 사용자 인자는 `$ARGUMENTS` 로 받아 파싱합니다.

**문서 길이 관리**:

- `SKILL.md` 는 500줄 이내를 유지합니다.
- 초과 위험이 있는 상세 내용은 모두 `references/` 하위로 분리하고, SKILL.md 는 "언제 어떤 reference 를 로드할지" 만 명시합니다.

### 2단계: 워크플로우 단계별 상세 규칙 분리 (`references/workflow/`)

기존 PLAN 의 "4개 내부 에이전트(scan/detect/analyze/map)" 개념은 표준 스킬 모델과 직접 매핑되지 않습니다. 대신 각 단계의 상세 행동 규칙을 `references/workflow/` 에 markdown 파일로 분리하고, SKILL.md 가 단계 진입 시 on-demand 로 Read 합니다. 이는 별도의 시스템 프롬프트 파일이나 서브스킬 분할 없이, 단일 진입점을 유지하면서 단계별 로직을 캡슐화하는 표준 호환 방식입니다.

작성 대상은 위 "워크플로우 단계" 절의 4개 파일(`scan.md`, `detect.md`, `analyze.md`, `map.md`)이며, 각각 역할/핵심 역량/입력/출력/상호작용 모델을 동일한 형식으로 기술합니다.

### 3단계: 참조 문서 작성 (`references/`)

프롬프트 템플릿을 별도 `prompts/` 디렉토리로 분리하던 기존 계획은 폐기하고, 모든 가이드 문서를 표준 `references/` 디렉토리로 통합합니다. SKILL.md 가 필요한 시점에 해당 파일을 Read 합니다.

- `references/workflow/*.md` (4개): 단계별 상세 행동 규칙 — 2단계에서 작성
- `references/contracts/downstream-injection-contract.md`: ex 산출물이 `re`/`arch`/`impl`/`qa`/`sec` 에 어떻게 주입되는지의 계약. Ex는 다른 스킬과 달리 push 방식이므로 "downstream injection" 명칭을 사용
- `references/schemas/meta-schema.md`: 메타데이터 공통 필드 명세
- `references/schemas/section-schemas.md`: 4섹션(`structure-map`, `tech-stack`, `components`, `architecture`) 필드 명세
- `references/adaptive-depth.md`: 경량/중량 모드 판별 규칙과 모드별 스킵 단계 정의
- `references/detect-patterns.md`: 프레임워크/언어/DB/CI/컨테이너 탐지 시그니처 카탈로그
- `references/analyze-heuristics.md`: 의존성/컴포넌트 경계/아키텍처 스타일 추론 휴리스틱
- `references/token-budget.md`: 축약/우선순위 기반 선별/계층적 상세화 규칙
- `references/escalation.md`: 분석 불가 케이스 카탈로그(접근 불가, 심볼릭 링크 순환, 매니페스트 부재, 바이너리 전용 등)와 에스컬레이션 메시지 템플릿
- `references/examples/` 하위: 경량/중량 시나리오 예시

**스크립트 호출 규약 배치**: "에이전트가 YAML 을 직접 편집하지 않고 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 커맨드만 호출한다" 는 행동 규약은 `references/workflow/*.md` 에 반복 명시하고, 각 단계에서 어떤 커맨드를 어떤 순서로 호출해야 하는지 시퀀스로 기술합니다.

### 4단계: 문서 템플릿 작성 (`assets/templates/`)

표준 디렉토리 명칭은 `assets/` 입니다.

- 4섹션(`structure-map`, `tech-stack`, `components`, `architecture`)별 markdown 템플릿(`*.md.tmpl`)을 `assets/templates/` 에 작성. 각 템플릿은 섹션 헤더, 표 골격, 플레이스홀더(`<!-- TODO: ... -->`), 다이어그램 자리(mermaid 코드 블록)를 포함하여 에이전트가 본문만 채우도록 유도
- 각 섹션의 메타데이터 초기 골격(`*.meta.yaml.tmpl`)을 작성. `phase: draft`, `approval.state: pending`, 빈 `upstream_refs`/`downstream_refs` 등 기본값 포함
- `components.md.tmpl` 은 의존성 mermaid 코드 펜스 슬롯을 미리 배치

**적응적 깊이 분기**:

- SKILL.md 본문의 분기 로직에서 `references/adaptive-depth.md` 의 판별 기준에 따라 경량 조건이면 analyze 단계의 일부(import 분석, 아키텍처 추론)를 생략합니다.
- 단일 진입점 유지: 스킬 자체를 `ex-light`/`ex-full` 로 분할하지 않고, 한 SKILL.md 안에서 분기 처리합니다.

### 5단계: 메타데이터 조작 스크립트 구현 (`scripts/`)

- `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 를 단일 진입점으로 구현하며, 다음 서브커맨드를 제공:
  - `init` — `assets/templates/` 에서 템플릿을 복사해 메타데이터 + markdown 쌍을 생성. 템플릿 경로는 `${CLAUDE_SKILL_DIR}/assets/templates/` 기준으로 해석
  - `set-phase`, `set-progress` — 진행 상태/진행률 갱신
  - `approve` — 승인 상태 전이 (전이 규칙 검증 포함)
  - `link` — `downstream_refs` 추가 (Ex의 후속 스킬 주입 대상 등록 용도가 핵심)
  - `show`, `validate` — 조회 및 스키마/추적성 검증
- 모든 쓰기 커맨드는 `updated_at` 을 자동 갱신하고, 잘못된 상태 전이/누락 필드를 차단
- **출력 위치**: 기본값은 `${CLAUDE_SKILL_DIR}/out/${CLAUDE_SESSION_ID}/`, `--out <dir>` 로 오버라이드 가능. 분석 대상 프로젝트(`project_root`) 안에는 어떠한 파일도 쓰지 않음 (비파괴적 분석 원칙)

**스크립트 호출 강제 (다층 방어)**:

행동 규약만으로는 우회될 수 있으므로 다층 방어를 구성합니다.

1. **행동 규약 (가장 약함)**: `references/workflow/*.md` 및 SKILL.md 본문에서 "메타데이터 갱신은 반드시 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 를 호출한다" 를 반복 명시
2. **도구 권한 (중간)**: Edit/Write 가 필요한 대상은 markdown 본문으로 한정하도록 워크플로우 가이드에서 명시. 분석 대상 프로젝트 보호를 위해 `Write` 자체를 frontmatter `allowed-tools` 에서 제거하는 옵션도 고려
3. **PreToolUse hooks (가장 강함)**: 가능하다면 `*.meta.yaml` 에 대한 Edit/Write 시도를 차단하는 PreToolUse hook 을 등록하여, 행동 규약을 우회한 직접 편집을 원천 차단
4. **시작 시 상태 주입**: SKILL.md 상단에서 `` !`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate` `` 를 사용해 현재 산출물 상태/추적성 무결성을 동적으로 주입. 에이전트가 자연스럽게 스크립트 기반 흐름을 따르도록 유도

### 6단계: 입출력 예시 작성 (`references/examples/`)

- `references/examples/light/` — **경량 시나리오**: 단순 Express API 등 ~20 파일 규모. 자동으로 경량 모드가 선택됨을 보임. 4섹션 메타데이터/문서 쌍 모두 포함
- `references/examples/heavy/` — **중량 시나리오**: Next.js + Prisma + Docker 등 ~200 파일 규모. 컴포넌트 관계 그래프와 아키텍처 추론까지 완결. 4섹션 메타데이터/문서 쌍 모두 포함
- 각 예시는 markdown 본문(`*.md`)과 그에 대응하는 메타데이터(`*.meta.yaml`)를 함께 포함하여, `phase`, `approval`, `downstream_refs` 가 채워진 실제 모습을 보여줄 것
- 토큰 예산 내 축약 결과와 축약 근거를 명시하여, 후속 스킬 작성자가 예시를 참조해 산출물 품질을 가늠할 수 있게 함

## 핵심 설계 원칙

1. **코드베이스 기반 (Codebase-Driven)**: 문서나 사용자 설명이 아닌, 코드베이스 자체를 유일한 진실의 원천(SSoT)으로 사용. 모든 산출물 필드는 코드에서 자동 추출되며, Ex 는 상위 스킬 산출물을 입력으로 받지 않습니다.
2. **역방향 주입 (Reverse Injection)**: 다른 harness 스킬이 상위 산출물을 소비하는 순방향 흐름과 달리, Ex 는 자신의 산출물을 후속 스킬(`re`/`arch`/`impl`/`qa`/`sec`)에 컨텍스트로 push 주입합니다. `downstream_refs` 가 추적성의 핵심입니다.
3. **적응적 깊이 (Adaptive Depth)**: 프로젝트 복잡도(파일 수/언어 수/프레임워크 수/디렉토리 깊이)를 자동 판별하여 경량/중량 모드 자동 전환. 단일 진입점 안에서 분기 처리합니다.
4. **토큰 예산 관리 (Token Budget Management)**: LLM 컨텍스트 윈도우는 유한한 자원이므로, 최종 산출물은 지정된 토큰 예산 내에서 최대 정보 밀도를 달성하도록 우선순위 기반 선별, 반복 패턴 축약, 계층적 상세화를 적용합니다.
5. **증거 기반 탐지 (Evidence-based Detection)**: 모든 탐지·추론에 evidence 를 명시. "어떤 파일의 어떤 패턴(framework signature, manifest entry, 디렉토리 구조)에서 이 결론을 도출했는가" 를 추적 가능하게 기록합니다.
6. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **프로젝트 구조 맵 / 기술 스택 / 컴포넌트 관계 / 아키텍처 추론** 4섹션으로 고정하여, 후속 스킬이 직접 소비할 수 있는 계약(contract) 역할을 수행합니다. 비파괴적 분석 원칙에 따라 분석 대상 프로젝트 안에는 어떠한 파일도 쓰지 않습니다.
7. **메타데이터-문서 분리 및 스크립트 경유 원칙 (Metadata/Document Separation via Scripts)**: 산출물은 YAML 메타데이터 파일과 markdown 문서 파일을 분리하여 관리하고, 메타데이터(진행 상태·승인 상태·추적성 ref)는 에이전트가 직접 편집하지 않고 오직 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 커맨드를 통해서만 갱신. markdown 본문은 `assets/templates/` 의 사전 정의 템플릿으로 골격을 생성한 뒤 에이전트가 플레이스홀더를 채움으로써, 상태 일관성과 서식 표준을 동시에 보장합니다.
