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

Impl 스킬은 Arch `design` 에이전트의 최종 산출물 4섹션을 직접 소비합니다.

### Arch 출력 → Impl 소비 매핑

| Arch 산출물 섹션 | 주요 필드 | Impl에서의 소비 방법 |
|-----------------|-----------|---------------------|
| **아키텍처 결정** | `id`, `decision`, `rationale`, `trade_offs`, `re_refs` | `decision`으로 코드 구조 결정의 근거 확보. `trade_offs`를 구현 시 주석/문서로 보존. `re_refs`를 통해 RE까지 추적성 유지 |
| **컴포넌트 구조** | `id`, `name`, `responsibility`, `type`, `interfaces`, `dependencies` | `name` + `type`으로 모듈/패키지 스캐폴딩. `responsibility`로 클래스/모듈의 단일 책임 경계 설정. `interfaces`로 API 계약(contract) 코드 생성. `dependencies`로 의존성 방향 및 import 구조 결정 |
| **기술 스택** | `category`, `choice`, `rationale`, `decision_ref`, `constraint_ref` | `choice`로 언어/프레임워크/DB 선택 확정. `constraint_ref`로 RE 제약 조건 준수 확인. 기술별 관용구(idiom)와 베스트 프랙티스 적용 |
| **다이어그램** | `type`, `code`, `description` | `c4-container`로 모듈 경계 확인. `sequence`로 메서드 호출 흐름 구현. `data-flow`로 데이터 변환 로직 구현 |

### RE 산출물 간접 참조

Impl은 RE 산출물을 직접 소비하지 않으나, Arch 산출물의 `re_refs`와 `constraint_ref`를 통해 간접 참조합니다.

| RE 산출물 | 간접 참조 경로 | Impl에서의 영향 |
|-----------|---------------|----------------|
| **요구사항 명세** | Arch `component_structure.re_refs` → `FR-xxx`, `NFR-xxx` | 컴포넌트가 담당하는 FR의 `acceptance_criteria`를 구현 완전성 체크에 사용 |
| **제약 조건** | Arch `technology_stack.constraint_ref` → `CON-xxx` | `hard` 제약(특정 언어/프레임워크 강제 등)을 구현 시 비협상 조건으로 준수 |
| **품질 속성 우선순위** | Arch `architecture_decisions.re_refs` → `QA:xxx` | 성능/보안 등 품질 속성에 따른 구현 패턴 선택 (예: 캐싱, 입력 검증 강화) |

### 적응적 깊이 연동

Arch의 모드에 연동하여 Impl의 산출물 수준을 자동 조절합니다.

| Arch 모드 | 판별 기준 | Impl 모드 | 산출물 수준 |
|-----------|-----------|-----------|------------|
| 경량 | Arch가 스타일 추천 + 디렉토리 가이드 수준 | 경량 | 단일 프로젝트 스캐폴딩 + 핵심 모듈 구현 + 인라인 구현 가이드 |
| 중량 | Arch가 컴포넌트 정의 + C4 다이어그램 수준 | 중량 | 멀티 모듈 프로젝트 구조 + 컴포넌트별 구현 + 인터페이스 계약 코드 + 구현 결정 기록(IDR) |

## 최종 산출물 구조

Impl 스킬의 최종 산출물은 다음 **네 가지 섹션**으로 구성됩니다. 코드 레벨 구현까지를 범위로 하며, 테스트 작성이나 배포 설정은 후속 스킬(`qa`, `deployment`)의 영역입니다.

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

위 네 섹션은 **실제 소스 코드와 구분되는 "문서성 산출물"** 입니다. Impl 스킬은 실제 코드 파일(`src/**/*`)을 생성하지만, 그와 별개로 구현 맵·코드 구조·구현 결정·구현 가이드는 **상태 추적과 승인 관리가 필요한 문서성 자산**이므로 다음 규칙으로 저장·관리합니다.

| 구분 | 파일 형식 | 용도 | 편집 주체 |
|------|----------|------|----------|
| **메타데이터 파일** | YAML (`.yaml`) | 진행 상태, 승인 상태, 추적성 ID, 필드 스키마 | **스크립트 전용** — 에이전트 직접 편집 금지 |
| **문서 markdown** | Markdown (`.md`) | 사람이 읽는 본문 (섹션 헤더, 서술, 표) | 스크립트가 템플릿으로 골격 생성 → 에이전트가 본문 편집 |
| **실제 소스 코드** | 언어별 소스 | 빌드/실행 대상 코드 | 에이전트가 직접 생성·편집 |

**YAML을 메타데이터 포맷으로 채택**하는 이유:
- 주석을 지원하여 필드별 의미를 인라인으로 설명 가능
- 들여쓰기 기반 구조로 사람이 읽고 diff 리뷰하기 쉬움
- Python/Node 스크립트에서 표준 라이브러리로 파싱·직렬화 용이
- JSON 대비 중첩 구조가 많은 추적성 레퍼런스 표현에 효율적

**메타데이터 필수 필드**:

| 필드 군 | 필드 | 설명 |
|--------|------|------|
| 식별 | `id`, `kind`, `title` | 산출물 식별자와 종류 (`implementation_map` / `code_structure` / `implementation_decisions` / `implementation_guide`) |
| 진행 상태 | `phase`, `progress`, `updated_at` | `phase` ∈ {`draft`, `in_progress`, `review`, `done`}, `progress`는 0–100 정수 |
| 승인 상태 | `approval.state`, `approval.approver`, `approval.approved_at`, `approval.notes` | `state` ∈ {`pending`, `approved`, `rejected`, `changes_requested`} |
| 추적성 | `upstream_refs` (Arch/RE ID), `downstream_refs` (후속 스킬 소비 예정 ID) | 4섹션 간 상호 참조 및 선·후행 스킬 연결 |
| 문서 연결 | `document_path` | 대응하는 markdown 본문 파일의 상대 경로 |

**스크립트 전용 조작 원칙**: 에이전트는 메타데이터 YAML/JSON을 **직접 편집하지 않습니다.** 모든 상태 갱신·조회는 `scripts/` 디렉토리의 커맨드라인 스크립트(`scripts/artifact.py` 등)를 통해서만 수행합니다. 이를 통해 (1) 스키마 위반 방지, (2) 상태 전이 규칙 강제, (3) 감사 로그(타임스탬프 자동 기록) 보장을 달성합니다.

**문서 markdown 템플릿 원칙**: markdown 본문 파일은 `templates/` 디렉토리에 섹션별 템플릿으로 미리 정의합니다. 에이전트가 백지 상태에서 markdown을 작성하지 않고, 스크립트(`scripts/artifact.py init --kind implementation_map` 등)가 템플릿을 복사하여 기본 골격(섹션 헤더, 플레이스홀더, 체크리스트)을 생성한 뒤 에이전트가 본문만 채웁니다. 이로써 4섹션 간 형식 일관성을 자동 보장합니다.

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

본 스킬은 Claude Code Skill 공식 표준(https://code.claude.com/docs/ko/skills)을 따릅니다. 단일 진입점 `impl/SKILL.md`(YAML frontmatter + Markdown 본문, 500줄 이하)를 중심으로, 상세 자원은 `scripts/`·`references/`·`templates/`·`assets/`에 분리 배치합니다. 비표준 파일(`skills.yaml`, `agents/`, `prompts/`)은 사용하지 않습니다.

```
impl/
├── SKILL.md                        # ★ 단일 진입점 (frontmatter + 본문, 500줄 이하)
├── scripts/
│   ├── artifact.py                 # 메타데이터 CRUD + 템플릿 인스턴스화 CLI
│   ├── schema.py                   # 산출물 메타데이터 스키마 정의·검증
│   ├── state_machine.py            # phase/approval 상태 전이 규칙
│   ├── detect_codebase.py          # 기존 코드베이스 컨벤션 자동 감지
│   └── validate_arch_input.py      # Arch 4섹션 입력 검증
├── references/
│   ├── io-contract.md              # Arch ↔ Impl 4섹션 매핑 상세
│   ├── metadata-governance.md      # 메타데이터/문서 분리 원칙 상세
│   ├── escalation.md               # 에스컬레이션 판별 기준 및 메시지 템플릿
│   ├── supported-languages.md      # 지원 언어 목록 및 선택 기준
│   ├── phases/
│   │   ├── 1-generate.md           # Phase 1 상세 절차·체크리스트
│   │   ├── 2-pattern.md            # Phase 2 상세 절차·패턴 결정 트리
│   │   ├── 3-review.md             # Phase 3 상세 절차·리뷰 체크리스트
│   │   └── 4-refactor.md           # Phase 4 상세 절차·리팩토링 카탈로그
│   ├── languages/
│   │   ├── typescript.md
│   │   ├── python.md
│   │   ├── go.md
│   │   ├── java.md
│   │   └── rust.md
│   ├── refactor-catalog.md         # Fowler 코드 스멜 카탈로그
│   ├── pattern-decision-tree.md    # GoF 패턴 추천 결정 트리
│   └── examples/
│       ├── lite-crud/              # Arch 경량 → Impl 경량 예시
│       ├── heavy-multi-module/     # Arch 중량 → Impl 중량 예시
│       ├── escalation-case.md      # 에스컬레이션 예시
│       ├── metadata-document-pair/ # *.metadata.yaml + *.document.md 쌍
│       └── cli-usage.md            # scripts/artifact.py 호출 시퀀스 예시
├── templates/
│   ├── implementation_map.md.tmpl
│   ├── code_structure.md.tmpl
│   ├── implementation_decisions.md.tmpl
│   ├── implementation_guide.md.tmpl
│   └── metadata.yaml.tmpl          # 공통 메타데이터 골격
└── assets/
    └── (필요 시 다이어그램·아이콘 등 정적 자산)
```

**디렉토리 구조 원칙**:
- `SKILL.md`는 표준에서 요구하는 **유일한 진입점**. frontmatter는 `---`로 감싸고, 본문은 500줄을 넘지 않도록 상세는 `references/`로 분리.
- `scripts/`는 결정적(task-content) 동작 번들. 에이전트가 직접 YAML을 만지지 못하도록 강제.
- `references/`는 인라인 참조 콘텐츠. SKILL.md 본문에서 필요한 시점에 명시적으로 "see `references/...`" 형태로 참조.
- `templates/`는 표준 필수 디렉토리는 아니나 task형 스킬의 결정적 자원으로서 유지. SKILL.md에서 `${CLAUDE_SKILL_DIR}/templates/...` 형태로 명시 참조.
- `assets/`는 정적 자산 전용. 본 스킬은 최소로 사용.

## Phase 흐름 (SKILL.md 본문 내부 단계)

표준 스킬은 단일 진입점 내부에서 동작하므로, 기존의 `generate / pattern / review / refactor` 4개 내부 에이전트는 **하나의 SKILL.md 본문이 순차 수행하는 4개 Phase**로 통합합니다. frontmatter의 `agent` 필드는 `general-purpose` 단일 값을 사용하며, 각 Phase의 상세 절차·체크리스트·결정 트리는 `references/phases/{1-generate,2-pattern,3-review,4-refactor}.md`로 분리합니다.

```
Arch 산출물 (4섹션, $ARGUMENTS[0])
    │
    ▼
Phase 1: Generate ─────────────────────────┐
    │  (기존 코드 자동 분석 → 스캐폴딩 →     │
    │   전체 모듈 구현 → 자동 완료)          │
    │  상세: references/phases/1-generate.md│
    │                                       │
    ▼                                       │
Phase 2: Pattern Application                │
    │  (generate 과정에서 식별된 패턴을       │
    │   자동 평가·적용, IDR 기록)             │
    │  상세: references/phases/2-pattern.md  │
    │                                       │
    ▼                                       │
Phase 3: Review ◄───────────────────────────┘
    │  (생성된 코드를 Arch 결정 준수 +
    │   클린 코드 원칙 기반으로 자동 리뷰)
    │  상세: references/phases/3-review.md
    │
    ├── 자동 수정 가능 ──→ Phase 4: Refactor
    │   이슈 발견 시        (Arch 경계 내에서
    │                       코드 스멜 자동 제거)
    │                       상세: references/phases/4-refactor.md
    │                           │
    │                           ▼
    │                      Phase 3: Review (재수행)
    │
    ├── Arch 결정 실현 불가 ──→ 사용자 에스컬레이션 ⚠️
    │   발견 시                    (references/escalation.md)
    │
    ▼
최종 산출물 (4섹션) → 사용자에게 결과 보고
```

### Phase 실행 규칙

- **Phase 1 (Generate)**: 항상 최초 진입. `$ARGUMENTS[0]`으로 받은 Arch 산출물 경로를 `scripts/validate_arch_input.py`로 검증 후 착수. `scripts/detect_codebase.py`로 기존 컨벤션 자동 감지
- **Phase 2 (Pattern)**: Phase 1 중 패턴 적용 기회가 식별되면 인라인으로 평가·적용. Arch 명시 패턴은 필수, 비명시 패턴은 자동 판단 후 IDR 기록
- **Phase 3 (Review)**: Phase 1·2 완료 후 자동 수행. Phase 4 완료 후 재수행
- **Phase 4 (Refactor)**: Phase 3에서 자동 수정 가능한 이슈 발견 시 자동 수행
- **전체 파이프라인은 사용자 개입 없이 자동 실행**되며, 사용자 접점은 (1) Arch 결정 실현 불가 시 에스컬레이션과 (2) 최종 결과 보고 두 곳뿐

## 구현 단계

### 1단계: `impl/SKILL.md` 작성 (진입점 + frontmatter + 본문)

Claude Code Skill 표준의 단일 진입점인 `impl/SKILL.md`를 신설합니다. 비표준 파일 `skills.yaml`은 폐기하며, 그 내용은 (1) frontmatter, (2) SKILL.md 본문, (3) `references/` 하위 문서로 분산합니다.

#### 1-1. frontmatter (YAML, `---` 블록)

다음 필드를 반드시 포함합니다:

```yaml
---
name: impl
description: Converts arch skill outputs (decisions, components, tech stack, diagrams) into source code plus a 4-section implementation artifact (map, structure, decisions, guide). Use after arch completes, before qa/security/deployment.
argument-hint: "[arch-artifact-path]"
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
model: claude-opus-4-6
effort: high
agent: general-purpose
context: fork
paths:
  - impl/**
  - src/**
disable-model-invocation: false
user-invocable: true
---
```

**`description` 작성 원칙** (표준이 가장 강조하는 필드):
- **첫 문장에 what + when을 모두 front-loading** (무엇을 하는지 + 언제 호출해야 하는지)
- **250자 이내** 엄수. CI에 길이 검증 스크립트 포함하여 초과 시 빌드 실패
- 자연어 트리거 키워드 포함: "after arch", "implement", "scaffold", "code generation"
- 절대 다른 스킬 이름이나 버전 같은 메타 정보는 포함하지 않음

**`name` 작성 원칙**: 소문자/숫자/하이픈만 사용, 64자 이내 (`impl`).

**`allowed-tools` 작성 원칙**: 코드 생성·리뷰·리팩토링에 필요한 `Read, Write, Edit, Grep, Glob, Bash`를 화이트리스트로 명시. `Bash`는 빌드·포맷터·테스트 러너 등 결정적 도구 호출만 허용하도록, SKILL.md 본문의 "Tool Usage Policy" 절에서 추가 제한을 명시.

**`effort` 작성 원칙**: Arch 모드에 연동하여 경량(low)/중량(high)으로 런타임 전환. 기본값은 `high`.

#### 1-2. SKILL.md 본문 절 구성 (500줄 이하)

본문은 다음 절만 포함하고, 상세는 모두 `references/`로 분리합니다:

1. **Overview / When to Use**: 스킬의 목적과 호출 시점 (Arch 완료 후, QA/Security/Deployment 이전)
2. **Pipeline Position**: 선행(`arch`) / 간접 참조(`re`) / 후속 소비자(`qa`, `security`, `deployment`, `operation`, `management`) 관계
3. **Input Contract**: Arch 4섹션 요약만. 상세 매핑은 `references/io-contract.md`로 링크
4. **Output Contract**: Impl 4섹션 요약만. 후속 스킬 소비 계약 요약
5. **Mode Selection**: Arch 모드에 연동한 경량/중량 전환 규칙 요약 (frontmatter `effort`와 연계)
6. **Phase 1~4 실행 절차**: 각 Phase의 핵심 단계만 요약하고, 상세 프롬프트·체크리스트는 `references/phases/*`로 링크
7. **Escalation Triggers**: 에스컬레이션 조건 요약. 상세는 `references/escalation.md`
8. **Metadata Governance**: 스크립트 매개 조작 원칙 요약. 상세는 `references/metadata-governance.md`
9. **Skill Metadata vs Artifact Metadata**: frontmatter(정적, 스킬 자체)와 산출물 메타데이터 YAML(동적, `scripts/artifact.py` 매개) 구분을 한 절로 명시
10. **Tool Usage Policy**: `allowed-tools` 내 도구 사용 범위 제한 (특히 `Bash` 화이트리스트)

#### 1-3. 문자열 치환 및 동적 컨텍스트 주입

SKILL.md 본문에서 표준이 제공하는 치환·주입 기능을 적극 활용합니다:

- **`$ARGUMENTS[0]`**: Arch 산출물 경로 수신. 사용 예: `scripts/validate_arch_input.py $ARGUMENTS[0]`
- **`${CLAUDE_SKILL_DIR}`**: 모든 스크립트/템플릿 경로를 절대화하여 cwd 독립성 확보. 예: `python "${CLAUDE_SKILL_DIR}/scripts/artifact.py" ...`
- **`${CLAUDE_SESSION_ID}`**: 감사 로그·IDR 생성 시 세션 추적에 사용
- **동적 컨텍스트 주입 (`` !`...` ``)**: Phase 1 시작 시점에 Arch 산출물 및 코드베이스 스냅샷을 본문에 자동 삽입. 사용 예:

  ```markdown
  ## Phase 1: Load Arch artifact
  Arch 산출물 내용:
  !`python "${CLAUDE_SKILL_DIR}/scripts/artifact.py" show $ARGUMENTS[0]`

  현재 코드베이스 매니페스트 스냅샷:
  !`ls -1 package.json go.mod requirements.txt Cargo.toml pom.xml 2>/dev/null`
  ```

#### 1-4. `skills.yaml` 폐기 및 내용 이관

기존 1단계에서 `skills.yaml`에 두려 했던 내용을 다음과 같이 이관합니다:

| 기존 항목 | 이관 위치 |
|----------|----------|
| 스킬 이름, 설명, 에이전트 목록 | SKILL.md `frontmatter` (`name`, `description`, `agent`) |
| 입력 스키마 (Arch 4섹션 소비 계약) | `references/io-contract.md` + `scripts/schema.py` |
| 출력 스키마 (Impl 4섹션 산출물 계약) | `references/io-contract.md` + `scripts/schema.py` |
| 적응적 깊이 설정 | SKILL.md 본문 "Mode Selection" 절 + frontmatter `effort` |
| 지원 언어 목록 | `references/supported-languages.md` + `references/languages/*.md` |
| 코딩 컨벤션 오버라이드 옵션 | `references/metadata-governance.md` |
| 에스컬레이션 조건 | SKILL.md 본문 "Escalation Triggers" 절 + `references/escalation.md` |
| 의존성/연계 정보 | SKILL.md 본문 "Pipeline Position" 절 |

### 2단계: Phase 상세 문서 작성 (`references/phases/`)

표준은 단일 SKILL.md 내에서 동작하므로, 기존의 4개 독립 에이전트 시스템 프롬프트(`agents/*.md`)는 **SKILL.md 본문의 Phase 요약 + `references/phases/*.md` 상세 문서**로 재구성합니다. SKILL.md 본문에는 Phase마다 "핵심 단계 목록 + `references/phases/N-<name>.md` 링크"만 두고, 상세한 역량·체크리스트·결정 기준은 다음 4개 파일로 분리합니다.

#### `references/phases/1-generate.md` — Phase 1: Generate (코드 생성)

- **역할**: Arch 산출물을 기반으로 설계를 **자동으로** 실제 코드로 변환
- **핵심 역량**:
  - **Arch 산출물 해석**: Arch의 4섹션을 코드 생성 지시로 변환
    - `component_structure`의 `name` + `type` → 모듈/패키지 스캐폴딩
    - `component_structure`의 `interfaces` → API 계약 코드 (인터페이스, 타입 정의)
    - `component_structure`의 `dependencies` → import 구조 및 의존성 방향
    - `architecture_decisions`의 `decision` → 코드 구조 패턴 결정
    - `technology_stack`의 `choice` → 언어/프레임워크별 관용구 적용
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
  - 프로젝트 컨벤션 자동 감지 및 준수
- **입력**: Arch 산출물 (`architecture_decisions`, `component_structure`, `technology_stack`, `diagrams`)
- **출력**:
  - 구현 맵 (Arch 컴포넌트 → 코드 모듈 매핑)
  - 코드 구조 (디렉토리 레이아웃, 의존성 그래프)
  - 생성된 코드 파일들
  - 구현 결정 기록 (코드 레벨 결정 + Arch/RE 참조)
  - 구현 가이드 (빌드, 실행, 컨벤션)
- **상호작용 모델**: Arch 산출물 수신 → 기존 코드베이스 자동 분석 → 전체 구현 생성 → **결과 보고** (Arch 편차가 있으면 해당 항목만 별도 보고)
- **에스컬레이션 조건**: Arch 결정이 코드 레벨에서 실현 불가능한 경우에만 사용자에게 질문 (예: Arch가 선택한 프레임워크가 요구하는 인터페이스를 실현할 수 없는 경우, 기존 코드베이스와 Arch 결정 간 해소 불가능한 충돌)

#### `references/phases/3-review.md` — Phase 3: Review (코드 리뷰)

- **역할**: 생성된 코드를 **Arch 결정 준수 여부**와 **클린 코드 원칙** 두 축으로 리뷰
- **핵심 역량**:
  - **Arch 결정 준수 검증**: 
    - 코드 구조가 `component_structure`의 경계를 지키는지 확인
    - `architecture_decisions`에서 정한 패턴이 코드에 반영되었는지 확인
    - `technology_stack`에서 선정된 기술만 사용되었는지 확인
    - `interfaces`에서 정의한 계약이 구현에서 충실히 구현되었는지 확인
  - **RE 제약 조건 준수 검증**: Arch `constraint_ref` 경유로 `hard` 제약이 코드에 반영되었는지 확인
  - **클린 코드 원칙 검증**:
    - SOLID 원칙 준수 여부 검증
    - 가독성, 유지보수성, 테스트 용이성 평가
    - 네이밍 컨벤션 및 코드 스타일 일관성 검사
    - 복잡도 분석 (순환 복잡도, 인지 복잡도)
    - 잠재적 버그 및 엣지 케이스 식별
  - **보안 기본 검증**: OWASP Top 10 수준의 코드 레벨 보안 이슈 탐지 (상세 보안 분석은 `security` 스킬 영역)
- **입력**: 생성된 코드 + Arch 산출물 (검증 기준) + 코드 diff (변경 리뷰 시)
- **출력**: 리뷰 리포트 (Arch 준수 여부, 클린 코드 이슈, 보안 이슈, 라인별 피드백, 심각도, 개선 제안)
- **상호작용 모델**: 자동 리뷰 수행 → 자동 수정 가능한 이슈는 `refactor` 에이전트로 직접 전달 → **Arch 결정과의 구조적 편차**가 발견된 경우에만 사용자에게 에스컬레이션 (의도적 편차인지 확인)
- **에스컬레이션 조건**: Arch `component_structure` 경계 위반, `architecture_decisions` 패턴 미반영, `technology_stack` 외 기술 사용 등 **Arch 계약 위반** 수준의 이슈만 에스컬레이션. 클린 코드 이슈는 자동 수정

#### `references/phases/4-refactor.md` — Phase 4: Refactor (리팩토링)

- **역할**: 코드 스멜 탐지 및 **Arch 결정을 유지하면서** 안전한 리팩토링 수행
- **핵심 역량**:
  - Martin Fowler의 코드 스멜 카탈로그 기반 체계적 탐지
  - 리팩토링 기법 추천 (Extract Method, Move Field, Replace Conditional 등)
  - **Arch 경계 존중**: 리팩토링이 `component_structure`의 모듈 경계를 위반하지 않는지 검증
  - **추적성 유지**: 리팩토링 후에도 `implementation_map`의 매핑이 유효한지 확인 및 갱신
  - 단계별 리팩토링 절차 제시 (안전한 변환 보장)
  - 리팩토링 전후 비교 제시
- **입력**: 리팩토링 대상 코드 + `review` 리포트 (이슈 목록) + Arch 산출물 (경계 기준)
- **출력**: 코드 스멜 목록, 리팩토링 계획, 변환된 코드, 갱신된 구현 맵
- **상호작용 모델**: `review` 리포트 수신 → Arch 경계 내에서 자동 리팩토링 수행 → 갱신된 코드와 구현 맵 출력 → `review` 재리뷰
- **에스컬레이션 조건**: 리팩토링이 Arch `component_structure` 경계를 넘어야 해결 가능한 경우 (모듈 간 책임 재분배가 필요한 수준)에만 사용자에게 에스컬레이션

#### `references/phases/2-pattern.md` — Phase 2: Pattern Application (디자인 패턴)

- **역할**: `generate` 과정에서 식별된 패턴 적용 기회를 평가하고 적용
- **핵심 역량**:
  - **Arch 결정 연계**: `architecture_decisions`에서 명시된 패턴은 필수 적용, 명시되지 않은 패턴은 추천 레벨
  - 문제 상황에 맞는 GoF/기타 패턴 추천
  - 패턴 적용 전후 코드 비교
  - 패턴의 장단점 및 적용 조건 설명 (과도한 패턴 적용 경고 포함)
  - 안티패턴 탐지 및 교정
  - **구현 결정 기록**: 패턴 적용 시 `IDR-xxx`로 결정 근거 기록
- **입력**: 문제 상황 설명 또는 코드 + Arch 산출물 (결정된 패턴 참조)
- **출력**: 추천 패턴, 적용 방법, 변환된 코드, 트레이드오프 분석, 구현 결정 기록
- **상호작용 모델**: Arch `architecture_decisions`에서 명시된 패턴은 자동 적용. 명시되지 않은 패턴은 문제 상황 분석 후 자동 적용하되, IDR에 근거 기록. 사용자 개입 없음
- **에스컬레이션 조건**: 없음 — Arch 명시 패턴은 필수 적용, 비명시 패턴은 자동 판단하여 IDR로 근거 기록

### 3단계: 메타데이터 스크립트 및 문서 템플릿 작성 (`scripts/`, `templates/`)

에이전트가 직접 YAML/JSON을 편집하지 못하도록, 산출물 상태 관리 전용 CLI와 본문 markdown 템플릿을 먼저 구축합니다.

- **메타데이터 스키마 정의** (`scripts/schema.py`)
  - 4섹션(`implementation_map`, `code_structure`, `implementation_decisions`, `implementation_guide`) 각각의 필드 스키마를 코드로 정의
  - 공통 필드(`id`, `kind`, `phase`, `progress`, `approval`, `upstream_refs`, `downstream_refs`, `document_path`) 검증 규칙 포함
  - 잘못된 상태 값 입력 시 명확한 에러 메시지 반환
- **상태 전이 규칙** (`scripts/state_machine.py`)
  - `phase`: `draft → in_progress → review → done` 단방향 전이 (역방향은 명시적 `--force` 필요)
  - `approval.state`: `pending → {approved, rejected, changes_requested}`, `changes_requested → pending` 재진입 허용
  - 전이 시 `updated_at` 자동 갱신 및 변경 로그 append
- **아티팩트 CLI** (`scripts/artifact.py`)
  - `init --kind <section> --id <id>`: `templates/`에서 메타데이터 YAML과 문서 markdown 골격을 동시 생성
  - `set-phase <id> <phase>`, `set-progress <id> <0-100>`: 진행 상태 갱신
  - `approve <id> --approver <name>`, `reject <id> --reason <text>`, `request-changes <id> --notes <text>`: 승인 상태 갱신
  - `link <id> --upstream <ref>` / `--downstream <ref>`: 추적성 레퍼런스 추가
  - `show <id>`, `list [--phase <p>] [--approval <s>]`: 조회 기능 (에이전트가 상태를 읽을 때도 스크립트 경유)
  - `validate <id>`: 스키마 및 상태 전이 규칙 검증
- **문서 markdown 템플릿** (`templates/*.md.tmpl`)
  - 4섹션별로 섹션 헤더, 필수 하위 항목, 플레이스홀더(`<!-- TODO: ... -->`), Arch/RE 참조 자리 표시자를 포함한 골격 작성
  - 에이전트는 이 템플릿을 수동 복사하지 않고, 반드시 `artifact.py init`을 통해 인스턴스화
- **에이전트 사용 계약**: 모든 에이전트(`generate`, `review`, `refactor`, `pattern`)의 프롬프트에 "메타데이터는 `scripts/artifact.py`로만 조작하고, 본문 markdown은 템플릿으로 초기화된 파일만 편집한다"는 규칙을 명시

### 4단계: 참조 문서 작성 (`references/`)

비표준 `prompts/` 디렉토리는 폐기하고, 모든 참조 콘텐츠를 표준 보조 디렉토리인 `references/` 하위에 배치합니다. SKILL.md 본문은 필요한 시점에 "see `references/...`" 형태로 명시 링크만 걸고, 상세 내용은 다음 문서로 분리합니다:

- **`references/io-contract.md`**: Arch 4섹션 → Impl 4섹션 매핑 상세. 각 Arch 필드가 코드 생성 지시로 어떻게 변환되는지 규칙 명시
- **`references/metadata-governance.md`**: 메타데이터/문서 분리 원칙 상세, 스크립트 매개 조작 규칙, 산출물 메타데이터 vs 스킬 frontmatter 구분
- **`references/escalation.md`**: Arch 결정 실현 불가 여부 판별 기준, 에스컬레이션 메시지 템플릿, 대안 제시 형식
- **`references/supported-languages.md`**: 지원 언어 목록(TypeScript, Python, Java, Go, Rust 등) 및 언어 자동 감지 규칙
- **`references/languages/{typescript,python,go,java,rust}.md`**: 언어별 관용구, 컨벤션, 프로젝트 구조, 에러 처리 전략, 로깅·관측성 표준 라이브러리
- **`references/refactor-catalog.md`**: Martin Fowler 코드 스멜 카탈로그 및 대응 리팩토링 기법
- **`references/pattern-decision-tree.md`**: GoF/기타 패턴 추천 결정 트리
- **`references/phases/*`**: 2단계에서 이미 정의한 Phase별 체크리스트·CoT 가이드·출력 형식(구현 맵, 코드 구조, IDR 형식)·few-shot 예시

SKILL.md 본문에서 각 문서를 명시적으로 참조하여 로드 시점을 제어합니다. 예: Phase 1 시작 시 `references/phases/1-generate.md`와 `references/languages/${DETECTED_LANG}.md`만 읽어오는 식으로 컨텍스트 사용량을 최소화합니다.

### 5단계: 입출력 예시 작성 (`references/examples/`)

비표준 `examples/` 디렉토리를 `references/examples/` 하위로 이전하여, 표준 보조 디렉토리 원칙을 준수합니다. 각 Phase별 대표적인 입출력 쌍을 작성합니다. 산출물 예시는 **메타데이터 YAML과 문서 markdown 파일을 쌍으로** 제공하여, 두 파일이 어떻게 연동되는지 명확히 보여줍니다. SKILL.md 본문에서 필요한 예시 경로를 `${CLAUDE_SKILL_DIR}/references/examples/...` 형태로 명시 참조합니다:
- **Arch 경량 출력 → Impl 경량 구현** 예시 (간단한 CRUD API 스캐폴딩)
- **Arch 중량 출력 → Impl 중량 구현** 예시 (멀티 모듈 프로젝트 + 인터페이스 계약)
- 기존 코드베이스 자동 분석을 통한 컨벤션 감지 예시
- Arch 결정 준수 기반 자동 리뷰 → 자동 리팩토링 예시
- Strategy 패턴 자동 적용 예시 (Arch 결정 연계 + IDR 기록)
- **구현 맵 + IDR 생성** 예시 (추적성 확인)
- **메타데이터/문서 쌍 예시**: 각 에이전트 출력별로 `*-output.metadata.yaml`(phase/progress/approval/refs 포함)과 `*-output.document.md`(템플릿 기반 본문)를 함께 수록
- **스크립트 호출 예시**: `artifact.py init`, `set-phase`, `approve` 등의 CLI 호출 시퀀스와 그 결과 메타데이터 변화 예시
- **에스컬레이션 예시**: Arch 결정과 코드 현실 간 해소 불가능한 괴리 발견 시 사용자 에스컬레이션 (질문 형식, 대안 제시 포함)
- **정상 완료 예시**: 에스컬레이션 없이 전체 자동 생성 후 결과 보고

## 핵심 설계 원칙

1. **Arch 산출물 기반 (Arch-Driven)**: 모든 코드 생성은 Arch의 4섹션 산출물에 근거하며, `arch_refs`/`re_refs`로 추적성을 유지. Arch가 확정한 컴포넌트 경계와 기술 스택은 재질문하지 않고 전제로 수용
2. **자동 실행 + 예외 에스컬레이션 (Auto-Execute with Exception Escalation)**: RE/Arch에서 의사결정이 완료된 상태이므로, 코드 레벨 맥락(컨벤션, 빌드 환경, 에러 처리 전략)은 기존 코드베이스 자동 분석과 기술 스택 관용구로 파악. **Arch 결정이 코드 레벨에서 실현 불가능한 경우에만 사용자에게 에스컬레이션**
3. **적응적 깊이 (Adaptive Depth)**: Arch 모드에 연동하여 경량(단일 스캐폴딩 + 인라인 가이드)/중량(멀티 모듈 + 인터페이스 계약 + IDR) 모드 자동 전환
4. **의사결정 추적 (Implementation Decision Records)**: 코드 레벨 주요 결정은 IDR로 기록하고, Arch/RE 산출물 ID를 참조하여 "왜 이렇게 구현했는가"를 설계/요구사항까지 추적 가능. 사용자 개입 없이 내린 자동 결정도 IDR에 근거를 기록하여 투명성 확보
5. **언어 무관성**: 핵심 원칙은 언어에 독립적이되, 언어별 관용구(idiom)와 생태계 베스트 프랙티스 존중
6. **일괄 구현 + 결과 보고 (Batch Implementation)**: 전체 코드를 Arch 산출물 기반으로 일괄 생성한 뒤, 최종 결과를 사용자에게 보고. 매 컴포넌트마다 중단하지 않음
7. **컨텍스트 자동 인식**: 기존 코드베이스가 있는 경우 코드 분석을 통해 스타일과 컨벤션을 자동 감지하고 일관성 유지. 사용자에게 컨벤션을 질문하지 않음
8. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **구현 맵 / 코드 구조 / 구현 결정 / 구현 가이드** 4섹션으로 고정하여, 후속 스킬(`qa`, `security`, `deployment`, `operation`, `management`)이 직접 소비할 수 있는 계약(contract) 역할을 수행
9. **메타데이터-문서 분리와 스크립트 매개 조작 (Metadata/Document Separation via Scripted Access)**: 문서성 산출물은 상태·승인·추적성을 담는 **YAML 메타데이터**와 사람이 읽는 **markdown 본문**으로 분리 저장하며, 메타데이터는 에이전트가 직접 편집하지 않고 `scripts/artifact.py` CLI를 통해서만 갱신. markdown 본문은 `templates/`의 사전 정의 템플릿을 스크립트로 인스턴스화한 뒤 에이전트가 편집. 이 원칙은 **실제 소스 코드 파일과는 무관**하며, 문서성 산출물의 스키마 일관성·상태 전이 무결성·감사 추적성을 보장하기 위한 것. 또한 **산출물 메타데이터(동적, YAML, `scripts/artifact.py` 매개)**는 **스킬 메타데이터(정적, SKILL.md frontmatter)**와 명확히 구분되며, 양자를 혼용하지 않음
10. **Claude Code Skill 표준 준수 (Standard-Compliant Skill Format)**: 본 스킬은 Claude Code Skill 공식 표준(https://code.claude.com/docs/ko/skills)을 따른다. 구체적으로 (a) 단일 진입점 `impl/SKILL.md`(`---` YAML frontmatter + Markdown 본문), (b) `description` 250자 이내·front-loaded(what+when)·트리거 키워드 포함, (c) SKILL.md 본문 500줄 이하·상세는 `references/` 분리, (d) 표준 보조 디렉토리(`scripts/`, `references/`, `assets/`)와 task형 스킬용 `templates/` 사용, (e) `$ARGUMENTS`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_SESSION_ID}`, `` !`...` `` 동적 컨텍스트 주입 적극 활용, (f) `allowed-tools` 화이트리스트로 도구 사용 범위 사전 승인, (g) `agent: general-purpose` 단일 값 사용하고 내부 단계는 Phase로 표현. 비표준 파일(`skills.yaml`, `agents/`, `prompts/`, 루트 `examples/`)은 사용하지 않는다
