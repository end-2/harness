# Impl (Implementation) Skill 구현 계획

## 개요

Arch 스킬의 산출물(아키텍처 결정, 컴포넌트 구조, 기술 스택, 다이어그램)을 입력으로 받아, **설계를 실제 코드로 변환**하는 스킬입니다.

Arch가 "어떻게 구조를 잡을 것인가"를 결정했다면, Impl은 "그 구조를 코드로 어떻게 구현할 것인가"를 실행합니다. 이 과정에서 Arch가 다루지 않는 **코드 레벨 맥락**(기존 코드베이스 컨벤션, 의존성 관리 정책, 빌드 환경 등)을 **기존 코드베이스 자동 분석과 기술 스택의 관용적 관행**으로 파악하고, 이를 근거로 구현 결정을 내립니다.

RE와 Arch에서 이미 의사결정이 완료된 상태이므로, Impl은 **자동 실행 + 예외 에스컬레이션** 모델을 채택합니다. Arch 결정을 기계적으로 코드로 변환하는 것이 핵심이며, **Arch 결정이 코드 레벨에서 실현 불가능한 경우에만 사용자에게 에스컬레이션**합니다.

### 전통적 구현 vs AI 컨텍스트 구현

| 구분 | 전통적 구현 | AI 컨텍스트 구현 |
|------|------------|-----------------|
| 수행자 | 개발자가 설계를 해석하여 직접 코딩 | 개발자가 AI에게 설계 기반 코드 생성을 위임 |
| 입력 | 설계 문서 + 개발자의 암묵적 경험 | **Arch 스킬의 구조화된 4섹션 산출물** + 기존 코드베이스 자동 분석 |
| 코드 품질 | 리뷰어의 주관적 판단에 의존 | **Arch 결정 준수 여부를 기계적으로 검증** 가능 |
| 산출물 | 코드 + PR 설명 | **Arch 추적성이 내장된 코드** + 구현 맵 + 구현 결정 기록 |
| 리팩토링 | 개발자 감각에 의존 | **코드 스멜 카탈로그 기반 체계적 탐지** + 안전한 변환 보장 |
| 패턴 적용 | 개발자 경험에 따라 편차 큼 | **문제 상황 분석 기반 패턴 추천** + 적용 전후 트레이드오프 제시 |
| 일관성 | 팀원 간 스타일 편차 발생 | **기존 코드베이스 컨벤션 자동 감지 및 일관 적용** |

## Arch 산출물 소비 계약

Impl 스킬은 Arch 워크플로우의 최종 산출물(4섹션)을 직접 소비합니다. RE 산출물은 Arch의 `re_refs`/`constraint_ref`를 통해 간접 참조합니다.

### Arch 출력 → Impl 소비 매핑

| Arch 산출물 섹션 | 주요 필드 | Impl에서의 소비 방법 |
|-----------------|-----------|---------------------|
| **아키텍처 결정 요약** | `id`, `decision`, `rationale`, `trade_offs`, `re_refs` | `decision`으로 코드 구조 결정의 근거 확보. `trade_offs`를 구현 시 주석/문서로 보존. `re_refs`를 통해 RE까지 추적성 유지 |
| **컴포넌트 구조** | `id`, `name`, `responsibility`, `type`, `interfaces`, `dependencies` | `name` + `type`으로 모듈/패키지 스캐폴딩. `responsibility`로 클래스/모듈의 단일 책임 경계 설정. `interfaces`로 API 계약 코드 생성. `dependencies`로 의존성 방향 및 import 구조 결정 |
| **기술 스택** | `category`, `choice`, `rationale`, `decision_ref`, `constraint_ref` | `choice`로 언어/프레임워크/DB 선택 확정. `constraint_ref`로 RE 제약 조건 준수 확인. 기술별 관용구(idiom)와 베스트 프랙티스 적용 |
| **다이어그램** | `type`, `code`, `description` | `c4-container`로 모듈 경계 확인. `sequence`로 메서드 호출 흐름 구현. `data-flow`로 데이터 변환 로직 구현 |

### RE 산출물 간접 참조

Impl은 RE 산출물을 직접 소비하지 않으나, Arch 산출물의 `re_refs`와 `constraint_ref`를 통해 간접 참조합니다.

| RE 산출물 | 간접 참조 경로 | Impl에서의 영향 |
|-----------|---------------|----------------|
| **요구사항 명세** | Arch `components.re_refs` → `FR-xxx`, `NFR-xxx` | 컴포넌트가 담당하는 FR의 `acceptance_criteria`를 구현 완전성 체크에 사용 |
| **제약 조건** | Arch `tech-stack.constraint_ref` → `CON-xxx` | `hard` 제약(특정 언어/프레임워크 강제 등)을 구현 시 비협상 조건으로 준수 |
| **품질 속성 우선순위** | Arch `decisions.re_refs` → `QA:xxx` | 성능/보안 등 품질 속성에 따른 구현 패턴 선택 (예: 캐싱, 입력 검증 강화) |

### 적응적 깊이

Arch의 모드에 연동하여 Impl의 산출물 수준을 자동 조절합니다.

| Arch 모드 | 판별 기준 | Impl 모드 | 산출물 수준 |
|-----------|-----------|-----------|------------|
| 경량 | Arch가 스타일 추천 + 디렉토리 가이드 수준 | 경량 | 단일 프로젝트 스캐폴딩 + 핵심 모듈 구현 + 인라인 구현 가이드 |
| 중량 | Arch가 컴포넌트 정의 + C4 다이어그램 수준 | 중량 | 멀티 모듈 프로젝트 구조 + 컴포넌트별 구현 + 인터페이스 계약 코드 + 구현 결정 기록(IDR) |

모드는 Arch 산출물 로드 시점에 자동 판별되며, 사용자가 명시적으로 재지정할 수도 있습니다. 경량 모드에서는 패턴/리팩토링 단계의 일부를 생략할 수 있습니다.

## 최종 산출물 구조

Impl 스킬의 최종 산출물은 다음 **네 가지 섹션**으로 구성됩니다. 코드 레벨 구현까지를 범위로 하며, 테스트 작성이나 배포 설정은 후속 스킬(`qa`, `deployment`)의 영역입니다. 또한 실제 소스 코드(`src/**/*`)는 본 4섹션과 별개의 산출물로 생성되며, 4섹션은 그 코드를 추적·관리하기 위한 **문서성 산출물**입니다.

### 1. 구현 맵 (Implementation Map)

Arch 컴포넌트와 실제 코드 모듈/파일 간의 매핑을 정의합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `IM-001`) |
| `component_ref` | 매핑 대상 Arch 컴포넌트 ID (`COMP-001` 등) |
| `module_path` | 실제 코드 모듈/패키지 경로 (예: `src/auth/`) |
| `entry_point` | 모듈의 진입점 파일 |
| `internal_structure` | 모듈 내부 구조 요약 (디렉토리, 주요 파일 목록) |
| `interfaces_implemented` | 구현한 인터페이스 목록 (Arch `interfaces`와의 매핑) |
| `re_refs` | 추적 가능한 RE 요구사항 ID (Arch 경유) |

### 2. 코드 구조 (Code Structure)

생성된 프로젝트의 전체 구조와 의존성을 정의합니다.

| 필드 | 설명 |
|------|------|
| `project_root` | 프로젝트 루트 경로 |
| `directory_layout` | 디렉토리 구조 트리 |
| `module_dependencies` | 모듈 간 의존성 그래프 (방향, 유형) |
| `external_dependencies` | 외부 라이브러리/패키지 목록 (이름, 버전, 용도) |
| `build_config` | 빌드 설정 파일 목록 및 설명 |
| `environment_config` | 환경 변수 및 설정 파일 목록 |

### 3. 구현 결정 (Implementation Decisions)

코드 레벨에서 내려진 주요 기술적 결정과 그 근거를 기록합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `IDR-001`) |
| `title` | 결정 제목 |
| `decision` | 선택한 구현 방식 |
| `rationale` | 결정 근거 (Arch 결정/RE 제약 참조 포함) |
| `alternatives_considered` | 고려한 대안 및 기각 사유 |
| `pattern_applied` | 적용한 디자인 패턴 (있는 경우) |
| `arch_refs` | 근거가 된 Arch 산출물 ID (`AD-001`, `COMP-001` 등) |
| `re_refs` | 근거가 된 RE 산출물 ID (`NFR-001`, `CON-001` 등) |

### 4. 구현 가이드 (Implementation Guide)

코드를 빌드, 실행, 확장하기 위한 가이드입니다.

| 필드 | 설명 |
|------|------|
| `prerequisites` | 사전 요구사항 (런타임, 도구, 계정 등) |
| `setup_steps` | 프로젝트 설정 절차 |
| `build_commands` | 빌드 명령어 |
| `run_commands` | 실행 명령어 |
| `conventions` | 적용된 코딩 컨벤션 요약 |
| `extension_points` | 확장 가능 지점 설명 (새 기능 추가 시 어디를 수정해야 하는지) |

### 산출물 파일 구성: 메타데이터 + 문서 분리

위 4섹션의 산출물은 **메타데이터 파일과 문서 markdown 파일을 분리**하여 저장합니다. 메타데이터는 구조화된 상태/추적 정보를 담고, markdown은 사람이 읽을 서술형 본문을 담습니다. 실제 소스 코드는 본 분리 원칙의 대상이 아니며, 에이전트가 직접 생성·편집합니다.

| 파일 유형 | 형식 | 역할 |
|----------|------|------|
| 메타데이터 파일 | **YAML** (`*.meta.yaml`) | 진행 상태, 승인 상태, 추적성(refs), 4섹션의 구조화 필드 저장. 스크립트가 읽고 쓰는 단일 진실 공급원(SSoT) |
| 문서 파일 | Markdown (`*.md`) | 구현 맵 서술, 코드 구조 설명, 구현 결정 근거, 구현 가이드 본문 |
| 실제 소스 코드 | 언어별 소스 | 빌드/실행 대상 코드 — 메타/문서 분리 원칙 대상 아님, 에이전트가 직접 생성·편집 |

**YAML을 채택한 이유**:

- **주석 지원**: 결정 근거나 임시 메모를 인라인 주석으로 남길 수 있어 사람이 작성/편집 시 맥락 전달이 용이
- **사람이 읽기 쉬움**: 들여쓰기 기반 구조로 JSON 대비 시각적 가독성이 높음 — Impl 산출물처럼 사용자가 직접 검토하는 문서에 적합
- **스크립트 파싱 용이**: PyYAML 등 표준 라이브러리로 손쉽게 로드/덤프 가능하며, 키 순서 보존도 지원

### 메타데이터 스키마 (공통 필드)

각 산출물 메타데이터 파일은 4섹션의 구조화 필드 외에 다음 공통 필드를 포함합니다.

| 필드 | 설명 |
|------|------|
| `artifact_id` | 산출물 고유 식별자 (예: `IMPL-map-001`) |
| `phase` | 현재 단계 (`draft` / `in_review` / `revising` / `approved` / `superseded`) |
| `progress` | 진행률 정보 (`section_completed`, `section_total`, `percent`) |
| `approval.state` | 승인 상태 (`pending` / `approved` / `rejected` / `changes_requested`) |
| `approval.approver` | 승인자 식별자 (사용자명/역할) |
| `approval.approved_at` | 승인 시각 (ISO 8601) |
| `approval.notes` | 승인/반려 코멘트 |
| `upstream_refs` | 상위 산출물 ID 목록 (Arch의 `AD-xxx`, `COMP-xxx`, RE의 `FR-xxx`/`NFR-xxx`/`CON-xxx`) |
| `downstream_refs` | 이 산출물을 소비하는 후속 산출물 ID 목록 (`qa`, `security`, `deployment`, `operation`, `management` 등) |
| `document_path` | 짝을 이루는 markdown 문서의 상대 경로 |
| `updated_at` | 최종 수정 시각 |

### 스크립트 기반 메타데이터 조작 (필수)

에이전트는 **YAML 메타데이터 파일을 직접 편집하지 않습니다**. 모든 상태 갱신은 `scripts/` 디렉토리의 스크립트 커맨드를 통해서만 수행하며, 이는 다음을 보장합니다.

- 스키마 검증 (잘못된 phase 값, 누락 필드 차단)
- `updated_at` 등 자동 필드의 일관된 갱신
- 추적성 ref의 양방향 무결성 (upstream/downstream 동기화)
- 승인 상태 전이 규칙 적용 (예: `draft → approved` 직행 금지)

핵심 스크립트(예시):

| 스크립트 커맨드 | 용도 |
|----------------|------|
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py init --section <name>` | 메타데이터 + markdown 템플릿 쌍을 새로 생성 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py set-phase <id> <phase>` | 진행 단계 전이 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py set-progress <id> --completed N --total M` | 진행률 갱신 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py approve <id> --approver <name> [--notes ...]` | 승인 상태 전이 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py link <id> --upstream <ref>` / `--downstream <ref>` | 추적성 ref 추가 |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py show <id>` | 메타데이터 조회 (사람이 읽기 좋은 형태) |
| `${CLAUDE_SKILL_DIR}/scripts/artifact.py validate [<id>]` | 스키마/추적성 검증 |

### 문서 템플릿 (`assets/templates/`)

markdown 문서 또한 자유 양식이 아니라, `assets/templates/` 디렉토리에 4섹션별 템플릿을 사전에 정의합니다. `scripts/artifact.py init` 실행 시 해당 템플릿이 복사되어 **섹션 헤더, 플레이스홀더, Arch/RE 참조 위치가 채워진 골격**이 생성되며, 에이전트는 이 골격 안의 플레이스홀더를 채우는 방식으로 본문을 작성합니다.

| 템플릿 파일 | 대상 섹션 |
|------------|----------|
| `assets/templates/implementation-map.md.tmpl` | 구현 맵 |
| `assets/templates/code-structure.md.tmpl` | 코드 구조 |
| `assets/templates/implementation-decisions.md.tmpl` | 구현 결정 (IDR) |
| `assets/templates/implementation-guide.md.tmpl` | 구현 가이드 |
| `assets/templates/*.meta.yaml.tmpl` | 각 섹션 메타데이터의 초기 골격 |

### 후속 스킬 연계

```
impl 산출물 구조:
┌─────────────────────────────────────────┐
│  구현 맵 (Implementation Map)            │──→ qa:strategy (테스트 대상 모듈 식별)
│  - IM-001: COMP-001 → src/auth/         │──→ security:threat-model (코드 레벨 공격 표면)
│  - IM-002: COMP-002 → src/api/          │──→ operation:runbook (운영 대상 모듈)
├─────────────────────────────────────────┤
│  코드 구조 (Code Structure)              │──→ qa:strategy (테스트 구조/커버리지 경계)
│  - directory_layout                     │──→ deployment:strategy (빌드/패키징 단위)
│  - module_dependencies                  │──→ security:scan (의존성 취약점 스캔 대상)
├─────────────────────────────────────────┤
│  구현 결정 (Implementation Decisions)    │──→ qa:strategy (패턴별 테스트 전략)
│  - IDR-001: Repository 패턴 적용         │──→ management:plan (기술 부채 추적)
│  - IDR-002: JWT 기반 인증 구현           │──→ security:threat-model (구현 수준 보안 함의)
├─────────────────────────────────────────┤
│  구현 가이드 (Implementation Guide)      │──→ deployment:strategy (빌드/실행 환경)
│  - setup, build, run                    │──→ operation:runbook (운영 절차 기반)
│  - conventions, extension_points        │──→ management:plan (온보딩/유지보수 가이드)
└─────────────────────────────────────────┘
```

## 목표 구조 (Claude Code Skill 표준 준수)

본 스킬은 Claude Code Skill 공식 표준(https://code.claude.com/docs/ko/skills)을 따릅니다. 단일 진입점은 `impl/SKILL.md` 이며, `skills.yaml`, `agents/`, `prompts/` 디렉토리는 사용하지 않습니다. 상세 행동 규칙과 단계별 가이드는 `references/`에, 템플릿은 `assets/`에 분리합니다.

```
impl/
├── SKILL.md                              # 필수 진입점 (YAML frontmatter + 4단계 워크플로우 요약, 500줄 이내)
├── scripts/
│   └── artifact.py                       # 메타데이터 init/set-phase/set-progress/approve/link/show/validate
├── assets/
│   └── templates/
│       ├── implementation-map.md.tmpl
│       ├── implementation-map.meta.yaml.tmpl
│       ├── code-structure.md.tmpl
│       ├── code-structure.meta.yaml.tmpl
│       ├── implementation-decisions.md.tmpl
│       ├── implementation-decisions.meta.yaml.tmpl
│       ├── implementation-guide.md.tmpl
│       └── implementation-guide.meta.yaml.tmpl
└── references/
    ├── workflow/
    │   ├── generate.md                   # 코드 생성 단계 상세 행동 규칙 (on-demand 로드)
    │   ├── pattern.md                    # 패턴 적용 단계 상세 행동 규칙
    │   ├── review.md                     # 리뷰 단계 상세 행동 규칙
    │   └── refactor.md                   # 리팩토링 단계 상세 행동 규칙
    ├── contracts/
    │   ├── arch-input-contract.md        # Arch 4섹션 소비 계약
    │   └── downstream-contract.md        # qa/security/deployment/operation/management 소비 계약
    ├── schemas/
    │   ├── meta-schema.md                # 메타데이터 공통 필드 설명
    │   └── section-schemas.md            # 4섹션 필드 명세
    ├── adaptive-depth.md                 # 경량/중량 분기 규칙
    └── examples/
        ├── light/
        │   ├── arch-input.md
        │   ├── generate-output.md
        │   └── generate-output.meta.yaml
        └── heavy/
            ├── arch-input.md
            ├── generate-output.md
            ├── generate-output.meta.yaml
            ├── pattern-output.md
            ├── review-report.md
            └── refactor-output.md
```

요점:
- `SKILL.md`가 유일한 필수 진입점이며, 4개의 워크플로우 단계(generate/pattern/review/refactor)는 **동일 SKILL.md 안에 짧게 요약**하고, 상세 규칙은 `references/workflow/*.md`로 분리하여 **on-demand 로드**합니다.
- `templates/` 대신 표준 명칭인 `assets/templates/`, `examples/` 대신 `references/examples/`를 사용합니다.
- `skills.yaml`, `agents/`, `prompts/`는 폐기합니다.

## 워크플로우 단계 (SKILL.md 내부 단일 진입점)

표준 스킬 모델을 따르기 위해, 기존에 "4개의 내부 에이전트"로 구상했던 generate/pattern/review/refactor는 **별도의 시스템 프롬프트 파일이 아니라**, SKILL.md가 순차적으로 수행하는 **4개의 워크플로우 단계**로 재정의합니다. 각 단계의 상세 행동 규칙은 `references/workflow/*.md`에 분리되어 필요 시점에 Read로 로드됩니다.

```
Arch:design 산출물 (4섹션, $ARGUMENTS[0])
    │
    ▼
[Stage 1] generate ─────────────────────────┐
    │  references/workflow/generate.md 로드  │
    │  (기존 코드 자동 분석 → 스캐폴딩 →       │
    │   전체 모듈 구현 → 자동 완료)            │
    │                                        │
    ▼                                        │
[Stage 2] pattern ──────────────────────────┤
    │  references/workflow/pattern.md 로드   │
    │  (generate 과정에서 식별된 패턴을       │
    │   자동 평가·적용, IDR 기록)              │
    │                                        │
    ▼                                        │
[Stage 3] review ◄──────────────────────────┘
    │  references/workflow/review.md 로드
    │  (생성된 코드를 Arch 결정 준수 +
    │   클린 코드 원칙 기반으로 자동 리뷰)
    │
    ├── 자동 수정 가능 ──→ [Stage 4] refactor
    │   이슈 발견 시        references/workflow/refactor.md 로드
    │                       (Arch 경계 내에서
    │                        코드 스멜 자동 제거)
    │                            │
    │                            ▼
    │                       [Stage 3] review (재수행)
    │
    ├── Arch 결정 실현 불가 ──→ 사용자 에스컬레이션
    │   발견 시
    │
    ▼
최종 산출물 (4섹션) → 사용자에게 결과 보고
```

### `references/workflow/generate.md` — 코드 생성 단계 상세 규칙

- **역할**: Arch 산출물을 기반으로 설계를 **자동으로** 실제 코드로 변환
- **핵심 역량**:
  - **Arch 산출물 해석**: Arch의 4섹션을 코드 생성 지시로 변환
    - `components`의 `name` + `type` → 모듈/패키지 스캐폴딩
    - `components`의 `interfaces` → API 계약 코드 (인터페이스, 타입 정의)
    - `components`의 `dependencies` → import 구조 및 의존성 방향
    - `decisions`의 `decision` → 코드 구조 패턴 결정
    - `tech-stack`의 `choice` → 언어/프레임워크별 관용구 적용
    - `diagrams`의 `sequence` → 메서드 호출 흐름 구현
  - **코드 레벨 맥락 자동 감지**: 사용자에게 질문하지 않고 자동으로 파악
    - 기존 코드베이스가 있는 경우: 코드 분석을 통한 컨벤션, 디렉토리 구조, 네이밍 규칙 자동 감지
    - 의존성 관리 정책: `package.json`, `go.mod`, `requirements.txt` 등 매니페스트 파일 분석
    - 빌드/실행 환경: 기존 설정 파일(`Dockerfile`, `Makefile`, CI 설정 등) 분석
    - 에러 처리 전략: 기술 스택의 관용적 방식 적용 (Go → error return, Rust → Result, Java → exceptions)
    - 로깅/관측성: RE NFR에서 도출된 요구사항 + 기술 스택의 표준 라이브러리 적용
  - 아키텍처 설계로부터 프로젝트 구조 스캐폴딩
  - 인터페이스/타입 정의 → 구현체 생성
  - 보일러플레이트 코드 최소화
- **입력**: Arch 산출물 (`decisions`, `components`, `tech-stack`, `diagrams`) + 기존 코드베이스 스냅샷
- **출력**:
  - 구현 맵 (Arch 컴포넌트 → 코드 모듈 매핑)
  - 코드 구조 (디렉토리 레이아웃, 의존성 그래프)
  - 생성된 실제 소스 코드 파일들
  - 구현 가이드 초안 (빌드, 실행, 컨벤션)
- **상호작용 모델**: Arch 산출물 수신 → 기존 코드베이스 자동 분석 → 전체 구현 생성 → 결과 보고. 사용자 개입 없이 자동 실행
- **에스컬레이션 조건**: Arch 결정이 코드 레벨에서 실현 불가능한 경우에만 사용자에게 질문 (예: Arch가 선택한 프레임워크가 요구하는 인터페이스를 실현할 수 없는 경우, 기존 코드베이스와 Arch 결정 간 해소 불가능한 충돌)

### `references/workflow/pattern.md` — 패턴 적용 단계 상세 규칙

- **역할**: `generate` 과정에서 식별된 패턴 적용 기회를 평가하고 적용
- **핵심 역량**:
  - **Arch 결정 연계**: `decisions`에서 명시된 패턴은 필수 적용, 명시되지 않은 패턴은 추천 레벨
  - 문제 상황에 맞는 GoF/기타 패턴 추천
  - 패턴 적용 전후 코드 비교
  - 패턴의 장단점 및 적용 조건 설명 (과도한 패턴 적용 경고 포함)
  - 안티패턴 탐지 및 교정
  - **구현 결정 기록**: 패턴 적용 시 `IDR-xxx`로 결정 근거 기록 (Arch/RE 참조 포함)
- **입력**: generate 단계의 코드 + Arch 산출물 (결정된 패턴 참조)
- **출력**: 적용된 패턴 목록, 변환된 코드, 트레이드오프 분석, IDR 기록
- **상호작용 모델**: Arch `decisions`에서 명시된 패턴은 자동 적용. 명시되지 않은 패턴은 문제 상황 분석 후 자동 적용하되, IDR에 근거를 기록. 사용자 개입 없음
- **에스컬레이션 조건**: 없음 — Arch 명시 패턴은 필수, 비명시 패턴은 자동 판단하여 IDR로 근거 기록

### `references/workflow/review.md` — 리뷰 단계 상세 규칙

- **역할**: 생성된 코드를 **Arch 결정 준수 여부**와 **클린 코드 원칙** 두 축으로 자동 리뷰
- **핵심 역량**:
  - **Arch 결정 준수 검증**:
    - 코드 구조가 `components`의 경계를 지키는지 확인
    - `decisions`에서 정한 패턴이 코드에 반영되었는지 확인
    - `tech-stack`에서 선정된 기술만 사용되었는지 확인
    - `interfaces`에서 정의한 계약이 구현에서 충실히 구현되었는지 확인
  - **RE 제약 조건 준수 검증**: Arch `constraint_ref` 경유로 `hard` 제약이 코드에 반영되었는지 확인
  - **클린 코드 원칙 검증**:
    - SOLID 원칙 준수 여부 검증
    - 가독성, 유지보수성, 테스트 용이성 평가
    - 네이밍 컨벤션 및 코드 스타일 일관성 검사
    - 복잡도 분석 (순환 복잡도, 인지 복잡도)
    - 잠재적 버그 및 엣지 케이스 식별
  - **보안 기본 검증**: OWASP Top 10 수준의 코드 레벨 보안 이슈 탐지 (상세 보안 분석은 `security` 스킬 영역)
- **입력**: 생성된 코드 + Arch 산출물 (검증 기준)
- **출력**: 리뷰 리포트 (Arch 준수 여부, 클린 코드 이슈, 보안 이슈, 라인별 피드백, 심각도, 개선 제안)
- **상호작용 모델**: 자동 리뷰 수행 → 자동 수정 가능한 이슈는 refactor 단계로 직접 전달 → **Arch 결정과의 구조적 편차**가 발견된 경우에만 사용자 에스컬레이션
- **에스컬레이션 조건**: Arch `components` 경계 위반, `decisions` 패턴 미반영, `tech-stack` 외 기술 사용 등 **Arch 계약 위반** 수준의 이슈만 에스컬레이션. 클린 코드 이슈는 자동 수정

### `references/workflow/refactor.md` — 리팩토링 단계 상세 규칙

- **역할**: 코드 스멜 탐지 및 **Arch 결정을 유지하면서** 안전한 리팩토링 수행
- **핵심 역량**:
  - Martin Fowler의 코드 스멜 카탈로그 기반 체계적 탐지
  - 리팩토링 기법 추천 (Extract Method, Move Field, Replace Conditional 등)
  - **Arch 경계 존중**: 리팩토링이 `components`의 모듈 경계를 위반하지 않는지 검증
  - **추적성 유지**: 리팩토링 후에도 `구현 맵`의 매핑이 유효한지 확인 및 갱신
  - 단계별 리팩토링 절차 제시 (안전한 변환 보장)
  - 리팩토링 전후 비교 제시
- **입력**: review 리포트 (이슈 목록) + 리팩토링 대상 코드 + Arch 산출물 (경계 기준)
- **출력**: 변환된 코드, 갱신된 구현 맵, 리팩토링 결정 기록(IDR)
- **상호작용 모델**: review 리포트 수신 → Arch 경계 내에서 자동 리팩토링 수행 → 갱신된 코드와 구현 맵 출력 → review 단계로 재진입
- **에스컬레이션 조건**: 리팩토링이 Arch `components` 경계를 넘어야 해결 가능한 경우(모듈 간 책임 재분배가 필요한 수준)에만 사용자에게 에스컬레이션

## 구현 단계

### 1단계: `SKILL.md` 작성 (필수 진입점 + frontmatter)

표준에서 메타데이터의 단일 출처는 `impl/SKILL.md`의 YAML frontmatter입니다. `skills.yaml`은 표준 사양에 존재하지 않으므로 사용하지 않습니다. Claude Code Skill 표준(https://code.claude.com/docs/ko/skills)에 따라 frontmatter는 `name`과 `description`만 필수로 두고, 나머지 옵션 필드는 기본 동작으로 스킬 목적을 달성할 수 없음이 입증된 경우에만 추가합니다.

**권장 frontmatter 초안**:

```yaml
---
name: impl
description: Arch 산출물(아키텍처 결정·컴포넌트·기술 스택·다이어그램 4섹션)을 입력으로 받아 실제 소스 코드와 4섹션 구현 산출물(구현 맵·코드 구조·구현 결정·구현 가이드)을 자동 생성하고, scripts/artifact.py로 메타데이터·추적성을 관리한다. Arch 완료 후 qa/security/deployment 진입 직전 코드 스캐폴딩·생성·자동 리뷰·리팩토링이 필요할 때 사용.
---
```

**설계 원칙**:

- **`name`**: 스킬 디렉토리명과 일치시켜 `impl`로 고정합니다. 표준에서 요구하는 두 필수 필드 중 하나입니다.
- **`description` 작성 규칙 (자동 호출 품질 결정)**: 첫 200자 안에 반드시 다음 두 요소를 포함합니다.
  - *무엇을 하는가*: "Arch 4섹션 → 실제 코드 + Impl 4섹션 산출물 자동 생성"
  - *언제 사용하는가*: "Arch 완료 후 / qa·security·deployment 투입 직전 / 코드 스캐폴딩·자동 리뷰·리팩토링 시"
  - 250자 경계에서 잘릴 수 있음을 가정하여 핵심 키워드를 앞에 배치합니다.
- **그 외 옵션 필드(`argument-hint`, `allowed-tools`, `effort`, `model`, `disable-model-invocation`, `paths`, `hooks`, `context`, `agent` 등)는 기본값으로 두고 추가하지 않습니다.** 표준 동작으로 스킬이 동작 불가능하다는 점이 실제로 입증된 경우에만 해당 필드를 도입하고, 그 근거를 PLAN/SKILL 본문에 명시합니다.

**SKILL.md 본문 구성 (500줄 이내)**:

1. 스킬 개요 (Arch 4섹션 → 실제 코드 + Impl 4섹션)
2. 입력/출력 계약 요약 (상세는 `references/contracts/*.md`로 분리)
3. 적응적 깊이 분기 로직 (Arch 모드 연동 → 경량/중량 모드 결정)
4. 4단계 워크플로우 요약 (generate → pattern → review → refactor)
   - 각 단계는 **상세 규칙을 `references/workflow/<stage>.md`에서 로드**하도록 명시
   - 예: "review 단계 진입 시 `${CLAUDE_SKILL_DIR}/references/workflow/review.md`를 Read로 로드한 뒤 지시를 따른다"
5. 스크립트 호출 규약: 모든 메타데이터 조작은 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 를 통해서만 수행
6. 시작 시 현재 상태 주입: SKILL.md 상단에서 `` !`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate` ``를 사용해 현재 산출물 상태를 동적 컨텍스트로 주입
7. 의존성 정보(선행: `arch`, 간접: `re`, 후속: `qa`/`security`/`deployment`/`operation`/`management`)는 frontmatter가 아니라 본문 또는 `references/contracts/downstream-contract.md`에 기술

**치환자 활용**:

- 모든 스크립트 경로는 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 로 작성하여 사용자 호출 위치에 관계없이 동작하도록 합니다.
- 사용자 인자(Arch 산출물 경로 등)는 `$ARGUMENTS`로 받아 generate 단계의 시작점으로 사용합니다.

**문서 길이 관리**:

- `SKILL.md`는 500줄 이내를 유지합니다.
- 초과 위험이 있는 상세 내용은 모두 `references/` 하위로 분리하고, SKILL.md는 "언제 어떤 reference를 로드할지"만 명시합니다.

### 2단계: 워크플로우 단계별 상세 규칙 분리 (`references/workflow/`)

기존 PLAN의 "4개 내부 에이전트" 개념은 표준 스킬 모델과 직접 매핑되지 않습니다. 대신 각 단계의 상세 행동 규칙을 `references/workflow/`에 markdown 파일로 분리하고, SKILL.md가 단계 진입 시 on-demand로 Read합니다. 이는 별도의 시스템 프롬프트 파일이나 서브스킬 분할 없이, 단일 진입점을 유지하면서 단계별 로직을 캡슐화하는 표준 호환 방식입니다.

각 workflow 파일에는 해당 단계의 **역할, 핵심 역량, 입력/출력, 상호작용 모델, 에스컬레이션 조건, 스크립트 호출 시점, CoT 가이드, few-shot 예시 참조**를 담습니다. 500줄을 초과하면 few-shot을 `references/examples/`로 분리합니다.

### 3단계: 참조 문서 작성 (`references/`)

프롬프트 템플릿을 별도 `prompts/` 디렉토리로 분리하던 기존 계획은 폐기하고, 모든 가이드 문서를 표준 `references/` 디렉토리로 통합합니다. SKILL.md가 필요한 시점에 해당 파일을 Read합니다.

- `references/workflow/*.md` (4개): 단계별 상세 행동 규칙 — 2단계에서 작성
- `references/contracts/arch-input-contract.md`: Arch 4섹션 → Impl 코드 생성 지시 매핑 가이드 (각 Arch 필드가 코드 생성 지시로 어떻게 변환되는지)
- `references/contracts/downstream-contract.md`: 후속 스킬(`qa`, `security`, `deployment`, `operation`, `management`) 소비 계약
- `references/schemas/meta-schema.md`: 메타데이터 공통 필드(`artifact_id`, `phase`, `approval`, `upstream_refs`, `downstream_refs` 등) 명세
- `references/schemas/section-schemas.md`: 4섹션(`implementation-map`, `code-structure`, `implementation-decisions`, `implementation-guide`) 필드 명세
- `references/adaptive-depth.md`: Arch 모드 연동 경량/중량 판별 규칙과 모드별 스킵 단계 정의

**스크립트 호출 규약 배치**: "에이전트가 YAML을 직접 편집하지 않고 `scripts/artifact.py` 커맨드만 호출한다"는 행동 규약은 `references/workflow/*.md`에 반복 명시하고, 각 단계(generate → pattern → review → refactor)에서 어떤 커맨드를 어떤 순서로 호출해야 하는지 시퀀스로 기술합니다.

### 4단계: 문서 템플릿 작성 (`assets/templates/`)

표준 디렉토리 명칭은 `assets/`입니다(기존 `templates/`는 폐기).

- 4섹션(`implementation-map`, `code-structure`, `implementation-decisions`, `implementation-guide`)별 markdown 템플릿(`*.md.tmpl`)을 `assets/templates/`에 작성. 각 템플릿은 섹션 헤더, 표 골격, Arch/RE 참조 슬롯, 플레이스홀더를 포함하여 에이전트가 본문만 채우도록 유도
- 각 섹션의 메타데이터 초기 골격(`*.meta.yaml.tmpl`)을 작성. `phase: draft`, `approval.state: pending`, 빈 `upstream_refs`/`downstream_refs` 등 기본값을 포함
- `implementation-decisions.md.tmpl`은 IDR 항목별 표 슬롯과 Arch/RE 참조 위치를 미리 배치. `code-structure.md.tmpl`은 디렉토리 트리 코드 펜스 슬롯을 포함

**적응적 깊이 → 내부 분기**:

- 하나의 스킬 안에서 경량/중량 모드를 내부 분기로 처리하며, 스킬 자체를 `impl-light`/`impl-full`로 분할하지 않습니다(단일 진입점 유지). SKILL.md 본문의 분기 로직이 `references/adaptive-depth.md`의 판별 기준에 따라 경량 조건이면 pattern/refactor 단계의 일부를 스킵합니다.

### 5단계: 메타데이터 조작 스크립트 구현 (`scripts/`)

- `scripts/artifact.py` 를 단일 진입점으로 구현하며, 다음 서브커맨드를 제공:
  - `init` — `assets/templates/`에서 템플릿을 복사해 메타데이터 + markdown 쌍을 생성. 템플릿 경로는 `${CLAUDE_SKILL_DIR}/assets/templates/`를 기준으로 해석
  - `set-phase`, `set-progress` — 진행 상태/진행률 갱신
  - `approve` — 승인 상태 전이 (전이 규칙 검증 포함)
  - `link` — `upstream_refs`/`downstream_refs` 추가 및 양방향 무결성 유지
  - `show`, `validate` — 조회 및 스키마/추적성 검증
- 모든 쓰기 커맨드는 `updated_at`을 자동 갱신하고, 잘못된 상태 전이/누락 필드를 차단

**스크립트 호출 강제 (다층 방어)**:

행동 규약만으로는 우회될 수 있으므로 다층 방어를 구성합니다.

1. **행동 규약 (가장 약함)**: `references/workflow/*.md` 및 SKILL.md 본문에서 "메타데이터 갱신은 반드시 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 를 호출한다"를 반복 명시
2. **도구 권한 (중간)**: frontmatter `allowed-tools` 설계 시 `*.meta.yaml` 파일에 대한 직접 편집을 최소화하기 위해, Edit/Write가 필요한 대상은 markdown 본문과 실제 소스 코드로 한정하도록 워크플로우 가이드에서 명시. (도구 단위 화이트리스트만 표준에 존재하므로, 파일 단위 차단은 아래 hooks로 보완)
3. **PreToolUse hooks (가장 강함)**: 가능하다면 `*.meta.yaml`에 대한 Edit/Write 시도를 차단하는 PreToolUse hook을 등록하여, 행동 규약을 우회한 직접 편집을 원천 차단
4. **시작 시 상태 주입**: SKILL.md 상단에서 `` !`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate` ``를 사용해 현재 산출물 상태·추적성 무결성을 동적으로 주입. 이를 통해 에이전트가 자연스럽게 스크립트 기반 흐름을 따르도록 유도

### 6단계: 입출력 예시 작성 (`references/examples/`)

- Arch 경량 출력 → Impl 경량 구현 예시 (간단한 CRUD API 스캐폴딩)
- Arch 중량 출력 → Impl 중량 구현 예시 (멀티 모듈 프로젝트 + 인터페이스 계약)
- 기존 코드베이스 자동 분석을 통한 컨벤션 감지 예시
- Arch 결정 준수 기반 자동 리뷰 → 자동 리팩토링 예시
- 패턴 자동 적용 예시 (Arch 결정 연계 + IDR 기록)
- 구현 맵 + IDR 생성 예시 (Arch/RE 추적성 확인)
- **메타데이터 + 문서 쌍 예시**: 각 산출물 예시는 markdown 본문(`*-output.md`)과 그에 대응하는 메타데이터(`*-output.meta.yaml`)를 함께 포함하여, `phase`, `approval`, `upstream_refs`/`downstream_refs` 가 채워진 실제 모습을 보여줄 것
- 에스컬레이션 예시 (Arch 결정과 코드 현실 간 해소 불가능한 괴리 발견 시)
- 정상 완료 예시 (에스컬레이션 없이 전체 자동 생성 후 결과 보고)

## 핵심 설계 원칙

1. **Arch 산출물 기반 (Arch-Driven)**: 모든 코드 생성은 Arch의 4섹션 산출물에 근거하며, `arch_refs`/`re_refs`로 추적성을 유지합니다. Arch가 확정한 컴포넌트 경계와 기술 스택은 재질문하지 않고 전제로 수용하며, 자동 실행 + 예외 에스컬레이션 모델을 채택하여 Arch 결정이 코드 레벨에서 실현 불가능한 경우에만 사용자에게 질문합니다.
2. **클린 코드 원칙 (Clean Code Principles)**: SOLID 원칙, 가독성, 유지보수성, 테스트 용이성, 일관된 네이밍 및 컨벤션을 모든 생성 코드에 적용합니다. 기존 코드베이스가 있는 경우 그 컨벤션을 자동 감지하여 일관성을 유지하며, 사용자에게 컨벤션을 질문하지 않습니다.
3. **적응적 깊이 (Adaptive Depth)**: Arch 모드에 연동하여 경량(단일 스캐폴딩 + 인라인 가이드)/중량(멀티 모듈 + 인터페이스 계약 + IDR) 모드를 자동 전환합니다. 패턴/리팩토링 단계의 깊이도 모드에 따라 자동 조절합니다.
4. **패턴 적용 (Pattern Application)**: generate 과정에서 식별된 패턴 적용 기회를 평가하여 적용합니다. Arch `decisions`에서 명시된 패턴은 필수 적용, 명시되지 않은 패턴은 문제 상황 분석 후 자동 판단하며, 모든 적용은 IDR로 근거를 기록하여 Arch 결정과 연계합니다.
5. **추적성 (Traceability via re_refs/arch_refs)**: 모든 코드 모듈과 구현 결정은 `arch_refs`로 Arch 산출물을, `re_refs`로 RE 산출물을 (Arch 경유로) 참조합니다. 이를 통해 "왜 이렇게 구현했는가"를 설계와 요구사항까지 양방향 추적할 수 있으며, 사용자 개입 없이 내린 자동 결정도 IDR에 근거를 기록하여 투명성을 확보합니다.
6. **4섹션 산출물 표준화 (Standardized Output)**: 최종 산출물을 **구현 맵 / 코드 구조 / 구현 결정 / 구현 가이드** 4섹션으로 고정하여, 후속 스킬(`qa`, `security`, `deployment`, `operation`, `management`)이 자연어 파싱 없이 직접 소비 가능한 계약(contract) 역할을 수행합니다.
7. **메타데이터-문서 분리 및 스크립트 경유 원칙 (Metadata/Document Separation via Scripts)**: 산출물은 YAML 메타데이터 파일과 markdown 문서 파일을 분리하여 관리하고, 메타데이터(진행 상태·승인 상태·추적성 ref)는 에이전트가 직접 편집하지 않고 오직 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 커맨드를 통해서만 갱신합니다. markdown 본문은 `assets/templates/` 의 사전 정의 템플릿으로 골격을 생성한 뒤 에이전트가 플레이스홀더를 채움으로써, 상태 일관성과 서식 표준을 동시에 보장합니다. 본 원칙은 문서성 산출물에 한정되며, 실제 소스 코드 파일과는 무관합니다.
