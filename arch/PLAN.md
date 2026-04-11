# Arch (Architecture) Skill 구현 계획

## 개요

RE 스킬의 산출물(요구사항 명세, 제약 조건, 품질 속성 우선순위)을 입력으로 받아, **시스템 구조 설계와 기술 의사결정**을 수행하는 스킬입니다.

RE가 "무엇을 만들 것인가"를 확정했다면, Arch는 "어떻게 구조를 잡을 것인가"를 결정합니다. 이 과정에서 RE가 다루지 않는 **기술적 맥락**(팀 역량, 기존 인프라, 운영 경험 등)을 사용자와의 대화로 파악하고, 이를 근거로 아키텍처 결정을 내립니다.

### 전통적 아키텍처 vs AI 컨텍스트 아키텍처

| 구분 | 전통적 아키텍처 | AI 컨텍스트 아키텍처 |
|------|----------------|---------------------|
| 수행자 | 전담 아키텍트 (시니어) | 개발자가 AI에게 조언을 구함 |
| 입력 | 요구사항 문서, 이해관계자 워크숍 | **RE 스킬의 구조화된 3섹션 산출물** + 기술적 맥락 대화 |
| 평가 | ATAM 워크숍 (다수 이해관계자 며칠간) | **RE 메트릭 기반 시나리오 검증** (AI + 사용자 대화) |
| 산출물 | 정형화된 아키텍처 문서 세트 | **RE 밀도에 연동되는 적응적 산출물** |
| 의사결정 | 아키텍처 위원회 승인 | **사용자와의 대화로 기술 결정 확인** |
| 트레이드오프 | 품질 속성 간 트레이드오프를 아키텍트가 분석 | RE가 확정한 품질 속성 트레이드오프를 **전제로**, 기술적 트레이드오프(패턴/기술 선택)에 집중 |
| 주기 | 프로젝트 초기 집중 | **RE 산출물이 갱신될 때마다 수시로** |

## RE 산출물 소비 계약

Arch 스킬은 RE `spec` 에이전트의 최종 산출물 3섹션을 직접 소비합니다.

### RE 출력 → Arch 소비 매핑

| RE 산출물 섹션 | 주요 필드 | Arch에서의 소비 방법 |
|---------------|-----------|---------------------|
| **요구사항 명세** | `id`, `category`, `priority`(MoSCoW), `acceptance_criteria`, `dependencies` | FR로 주요 컴포넌트 식별, NFR로 아키텍처 드라이버 도출. `dependencies`로 컴포넌트 경계 힌트 파악 |
| **제약 조건** | `type`, `flexibility`(hard/soft/negotiable), `rationale`, `impact` | `hard` 제약은 비협상 설계 드라이버로 고정, `negotiable` 제약은 대안 탐색 시 완화 가능 여부 사용자에게 확인. `type`에 따라 기술적/비즈니스/규제 제약을 구분하여 설계에 반영 |
| **품질 속성 우선순위** | `priority`, `metric`, `trade_off_notes` | `priority` 순서로 아키텍처 드라이버 우선순위 결정. `metric`("응답시간 < 200ms")을 시나리오로 변환하여 설계 검증. `trade_off_notes`는 RE에서 이미 사용자가 확인한 것이므로 재질문하지 않고 전제로 수용 |

### 적응적 깊이 연동

RE의 출력 밀도에 따라 Arch의 산출물 수준을 자동 조절합니다.

| RE 출력 밀도 | 판별 기준 | Arch 모드 | 산출물 수준 |
|-------------|-----------|-----------|------------|
| 경량 | FR ≤ 5개, NFR ≤ 2개, 품질 속성 ≤ 3개 | 경량 | 아키텍처 스타일 추천 + 레이어/디렉토리 가이드 + 기술 스택 추천 |
| 중량 | FR > 5개 또는 NFR > 2개 또는 품질 속성 > 3개 | 중량 | 컴포넌트 정의 + 커넥터/통신 패턴 + C4 Context/Container 다이어그램 + ADR |

## 최종 산출물 구조

Arch 스킬의 최종 산출물은 다음 **네 가지 섹션**으로 구성됩니다. High-level 아키텍처 결정까지를 범위로 하며, 상세 컴포넌트 내부 설계나 코드 레벨 설계는 포함하지 않습니다.

### 1. 아키텍처 결정 요약 (Architecture Decisions)

주요 아키텍처 결정과 그 근거를 구조화합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `AD-001`) |
| `title` | 결정 제목 |
| `decision` | 선택한 결정 내용 |
| `rationale` | 결정 근거 (RE 품질 속성/제약 조건 참조 포함) |
| `alternatives_considered` | 고려한 대안 목록 및 기각 사유 |
| `trade_offs` | 이 결정으로 인한 기술적 트레이드오프 |
| `re_refs` | 근거가 된 RE 산출물 ID (`NFR-001`, `CON-003`, `QA:performance` 등) |

### 2. 컴포넌트 구조 (Component Structure)

시스템을 구성하는 주요 컴포넌트와 그 관계를 정의합니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `COMP-001`) |
| `name` | 컴포넌트 이름 |
| `responsibility` | 핵심 책임 (한 문장) |
| `type` | 유형 (`service` / `library` / `gateway` / `store` / `queue` 등) |
| `interfaces` | 외부에 노출하는 인터페이스 목록 (이름, 방향, 프로토콜) |
| `dependencies` | 의존하는 다른 컴포넌트 ID 목록 |
| `re_refs` | 담당하는 FR/NFR ID 목록 |

### 3. 기술 스택 (Technology Stack)

선정된 기술과 그 근거를 명시합니다.

| 필드 | 설명 |
|------|------|
| `category` | 기술 카테고리 (`language` / `framework` / `database` / `messaging` / `infra` 등) |
| `choice` | 선택한 기술 |
| `rationale` | 선정 근거 |
| `decision_ref` | 관련 아키텍처 결정 ID (`AD-001` 등) |
| `constraint_ref` | 관련 RE 제약 조건 ID (`CON-001` 등) |

### 4. 다이어그램 (Diagrams)

아키텍처 구조를 시각화한 다이어그램입니다.

| 필드 | 설명 |
|------|------|
| `type` | 다이어그램 유형 (`c4-context` / `c4-container` / `sequence` / `data-flow`) |
| `title` | 다이어그램 제목 |
| `format` | 코드 형식 (`mermaid`) |
| `code` | 다이어그램 코드 |
| `description` | 다이어그램 설명 |

### 산출물 파일 구성: 메타데이터 + 문서 분리

위 4섹션의 산출물은 **메타데이터 파일과 문서 markdown 파일을 분리**하여 저장합니다. 메타데이터는 구조화된 상태/추적 정보를 담고, markdown은 사람이 읽을 서술형 본문을 담습니다.

| 파일 유형 | 형식 | 역할 |
|----------|------|------|
| 메타데이터 파일 | **YAML** (`*.meta.yaml`) | 진행 상태, 승인 상태, 추적성(refs), 4섹션의 구조화 필드 저장. 스크립트가 읽고 쓰는 단일 진실 공급원(SSoT) |
| 문서 파일 | Markdown (`*.md`) | 아키텍처 결정 서술, 컴포넌트 설명, 기술 스택 근거, 다이어그램(Mermaid) 본문 |

**YAML을 채택한 이유**:

- **주석 지원**: 결정 근거나 임시 메모를 인라인 주석으로 남길 수 있어 사람이 작성/편집 시 맥락 전달이 용이
- **사람이 읽기 쉬움**: 들여쓰기 기반 구조로 JSON 대비 시각적 가독성이 높음 — RE/Arch 산출물처럼 사용자가 직접 검토하는 문서에 적합
- **스크립트 파싱 용이**: PyYAML 등 표준 라이브러리로 손쉽게 로드/덤프 가능하며, 키 순서 보존도 지원

### 메타데이터 스키마 (공통 필드)

각 산출물 메타데이터 파일은 4섹션의 구조화 필드 외에 다음 공통 필드를 포함합니다.

| 필드 | 설명 |
|------|------|
| `artifact_id` | 산출물 고유 식별자 (예: `ARCH-design-001`) |
| `phase` | 현재 단계 (`draft` / `in_review` / `revising` / `approved` / `superseded`) |
| `progress` | 진행률 정보 (`section_completed`, `section_total`, `percent`) |
| `approval.state` | 승인 상태 (`pending` / `approved` / `rejected` / `changes_requested`) |
| `approval.approver` | 승인자 식별자 (사용자명/역할) |
| `approval.approved_at` | 승인 시각 (ISO 8601) |
| `approval.notes` | 승인/반려 코멘트 |
| `upstream_refs` | 상위 산출물 ID 목록 (예: RE의 `NFR-001`, `CON-002`, `QA:performance`) |
| `downstream_refs` | 이 산출물을 소비하는 후속 산출물 ID 목록 (`impl`, `qa`, `security` 등) |
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
| `scripts/artifact.py init --section <name>` | 메타데이터 + markdown 템플릿 쌍을 새로 생성 |
| `scripts/artifact.py set-phase <id> <phase>` | 진행 단계 전이 |
| `scripts/artifact.py set-progress <id> --completed N --total M` | 진행률 갱신 |
| `scripts/artifact.py approve <id> --approver <name> [--notes ...]` | 승인 상태 전이 |
| `scripts/artifact.py link <id> --upstream <ref>` / `--downstream <ref>` | 추적성 ref 추가 |
| `scripts/artifact.py show <id>` | 메타데이터 조회 (사람이 읽기 좋은 형태) |
| `scripts/artifact.py validate [<id>]` | 스키마/추적성 검증 |

### 문서 템플릿 (`templates/`)

markdown 문서 또한 자유 양식이 아니라, `templates/` 디렉토리에 4섹션별 템플릿을 사전에 정의합니다. `scripts/artifact.py init` 실행 시 해당 템플릿이 복사되어 **섹션 헤더, 플레이스홀더, RE 참조 위치가 채워진 골격**이 생성되며, 에이전트는 이 골격 안의 플레이스홀더를 채우는 방식으로 본문을 작성합니다.

| 템플릿 파일 | 대상 섹션 |
|------------|----------|
| `templates/decisions.md.tmpl` | 아키텍처 결정 요약 |
| `templates/components.md.tmpl` | 컴포넌트 구조 |
| `templates/tech-stack.md.tmpl` | 기술 스택 |
| `templates/diagrams.md.tmpl` | 다이어그램 (Mermaid 코드 블록 슬롯 포함) |
| `templates/*.meta.yaml.tmpl` | 각 섹션 메타데이터의 초기 골격 |

### 후속 스킬 연계

```
arch 산출물 구조:
┌─────────────────────────────────────────┐
│  아키텍처 결정 요약 (Decisions)          │──→ impl:generate (설계 의도 전달)
│  - AD-001, AD-002, ...                  │──→ security:threat-model (결정의 보안 함의)
│                                         │──→ management:plan (기술 리스크)
├─────────────────────────────────────────┤
│  컴포넌트 구조 (Components)              │──→ impl:generate (구현 단위 결정)
│  - COMP-001: API Gateway                │──→ qa:strategy (테스트 범위/경계)
│  - COMP-002: Auth Service               │──→ deployment:strategy (배포 단위)
├─────────────────────────────────────────┤
│  기술 스택 (Tech Stack)                  │──→ impl:generate (언어/프레임워크)
│  - language: TypeScript                 │──→ deployment:strategy (인프라 요구사항)
│  - database: PostgreSQL                 │──→ operation:runbook (운영 대상)
├─────────────────────────────────────────┤
│  다이어그램 (Diagrams)                   │──→ 전 스킬 공통 참조 자료
│  - C4 Context / Container              │
└─────────────────────────────────────────┘
```

## 목표 구조 (Claude Code Skill 표준 준수)

본 스킬은 Claude Code Skill 공식 표준(https://code.claude.com/docs/ko/skills)을 따릅니다. 단일 진입점은 `arch/SKILL.md` 이며, `skills.yaml`, `agents/`, `prompts/` 디렉토리는 사용하지 않습니다. 상세 행동 규칙과 단계별 가이드는 `references/`에, 템플릿은 `assets/`에 분리합니다.

```
arch/
├── SKILL.md                              # 필수 진입점 (YAML frontmatter + 4단계 워크플로우 요약, 500줄 이내)
├── scripts/
│   └── artifact.py                       # 메타데이터 init/set-phase/set-progress/approve/link/show/validate
├── assets/
│   └── templates/
│       ├── decisions.md.tmpl
│       ├── decisions.meta.yaml.tmpl
│       ├── components.md.tmpl
│       ├── components.meta.yaml.tmpl
│       ├── tech-stack.md.tmpl
│       ├── tech-stack.meta.yaml.tmpl
│       ├── diagrams.md.tmpl
│       └── diagrams.meta.yaml.tmpl
└── references/
    ├── workflow/
    │   ├── design.md                     # 설계 단계 상세 행동 규칙 (on-demand 로드)
    │   ├── review.md                     # 리뷰 단계 상세 행동 규칙
    │   ├── adr.md                        # ADR 작성 단계 상세 행동 규칙
    │   └── diagram.md                    # 다이어그램 작성 단계 상세 행동 규칙
    ├── contracts/
    │   ├── re-input-contract.md          # RE 3섹션 소비 계약
    │   └── downstream-contract.md        # impl/qa/security/deployment/operation 소비 계약
    ├── schemas/
    │   ├── meta-schema.md                # 메타데이터 공통 필드 설명
    │   └── section-schemas.md            # 4섹션 필드 명세
    ├── adaptive-depth.md                 # 경량/중량 분기 규칙
    ├── scenario-validation.md            # RE metric → 시나리오 변환 가이드
    └── examples/
        ├── light/
        │   ├── design-input.md
        │   ├── design-output.md
        │   └── design-output.meta.yaml
        └── heavy/
            ├── design-input.md
            ├── design-output.md
            ├── design-output.meta.yaml
            ├── review-output.md
            ├── adr-output.md
            └── diagram-output.md
```

요점:
- `SKILL.md`가 유일한 필수 진입점이며, 4개의 워크플로우 단계(design/review/adr/diagram)는 **동일 SKILL.md 안에 짧게 요약**하고, 상세 규칙은 `references/workflow/*.md`로 분리하여 **on-demand 로드**합니다.
- `templates/` 대신 표준 명칭인 `assets/templates/`, `examples/` 대신 `references/examples/`를 사용합니다.
- `skills.yaml`, `agents/`, `prompts/`는 폐기합니다.

## 워크플로우 단계 (SKILL.md 내부 단일 진입점)

표준 스킬 모델을 따르기 위해, 기존에 "4개의 내부 에이전트"로 구상했던 design/review/adr/diagram은 **별도의 시스템 프롬프트 파일이 아니라**, SKILL.md가 순차적으로 수행하는 **4개의 워크플로우 단계**로 재정의합니다. 각 단계의 상세 행동 규칙은 `references/workflow/*.md`에 분리되어 필요 시점에 Read로 로드됩니다.

```
RE:spec 산출물
    │
    ▼
[Stage 1] design ──────────────────────────┐
    │  references/workflow/design.md 로드  │
    │  (기술적 맥락 대화 → 설계 초안 →       │
    │   사용자 피드백 → 확정)               │
    │                                      │
    ├──→ [Stage 2] adr                     │
    │    references/workflow/adr.md 로드   │
    │    (design 과정에서 내려진            │
    │     주요 결정을 ADR로 기록)           │
    │                                      │
    ├──→ [Stage 3] diagram                 │
    │    references/workflow/diagram.md    │
    │    (확정된 설계를 시각화)              │
    │                                      │
    ▼                                      │
[Stage 4] review ◄─────────────────────────┘
    references/workflow/review.md 로드
    (design 출력을 RE 메트릭 기반
     시나리오로 검증)
```

## 구현 단계

### 1단계: `SKILL.md` 작성 (필수 진입점 + frontmatter)

표준에서 메타데이터의 단일 출처는 `arch/SKILL.md`의 YAML frontmatter입니다. `skills.yaml`은 표준 사양에 존재하지 않으므로 사용하지 않습니다. Claude Code Skill 표준(https://code.claude.com/docs/ko/skills)에 따라 frontmatter는 `name`과 `description`만 필수로 두고, 나머지 옵션 필드는 기본 동작으로 스킬 목적을 달성할 수 없음이 입증된 경우에만 추가합니다.

**권장 frontmatter 초안**:

```yaml
---
name: arch
description: RE 산출물(요구사항·제약·품질속성)을 입력으로 받아 아키텍처 결정·컴포넌트 구조·기술 스택·다이어그램(C4/Mermaid) 4섹션 산출물을 생성하고, scripts/artifact.py로 메타데이터·추적성을 관리한다. 새로운 시스템 설계, RE 산출물 갱신 후 아키텍처 재검토, ADR 기록, C4 다이어그램 생성이 필요할 때 사용.
---
```

**설계 원칙**:

- **`name`**: 스킬 디렉토리명과 일치시켜 `arch`로 고정합니다. 표준에서 요구하는 두 필수 필드 중 하나입니다.
- **`description` 작성 규칙 (자동 호출 품질 결정)**: 첫 200자 안에 반드시 다음 두 요소를 포함합니다.
  - *무엇을 하는가*: "RE 3섹션 → Arch 4섹션 산출물 생성"
  - *언제 사용하는가*: "신규 시스템 설계 / RE 산출물 갱신 후 아키텍처 재검토 / ADR·C4 다이어그램 작성 시"
  - 250자 경계에서 잘릴 수 있음을 가정하여 핵심 키워드를 앞에 배치합니다.
- **그 외 옵션 필드(`argument-hint`, `allowed-tools`, `effort`, `model`, `disable-model-invocation`, `paths`, `hooks`, `context`, `agent` 등)는 기본값으로 두고 추가하지 않습니다.** 표준 동작으로 스킬이 동작 불가능하다는 점이 실제로 입증된 경우에만 해당 필드를 도입하고, 그 근거를 PLAN/SKILL 본문에 명시합니다.

**SKILL.md 본문 구성 (500줄 이내)**:

1. 스킬 개요 (RE 3섹션 → Arch 4섹션)
2. 입력/출력 계약 요약 (상세는 `references/contracts/*.md`로 분리)
3. 적응적 깊이 분기 로직 (RE 메트릭 판별 → 경량/중량 모드 결정)
4. 4단계 워크플로우 요약 (design → adr → diagram → review)
   - 각 단계는 **상세 규칙을 `references/workflow/<stage>.md`에서 로드**하도록 명시
   - 예: "ADR 작성 시 `${SKILL_DIR}/references/workflow/adr.md`를 Read로 로드한 뒤 지시를 따른다"
5. 스크립트 호출 규약: 모든 메타데이터 조작은 `${SKILL_DIR}/scripts/artifact.py` 를 통해서만 수행
6. 시작 시 현재 상태 주입: SKILL.md 상단에서 `` !`python ${SKILL_DIR}/scripts/artifact.py validate` ``를 사용해 현재 산출물 상태를 동적 컨텍스트로 주입
7. 의존성 정보(선행: `re`, 후속: `impl`/`qa`/`security`/`deployment`/`operation`)는 frontmatter가 아니라 본문 또는 `references/contracts/downstream-contract.md`에 기술

**치환자 활용**:

- 모든 스크립트 경로는 `${SKILL_DIR}/scripts/artifact.py` 로 작성하여 사용자 호출 위치에 관계없이 동작하도록 합니다.
- 사용자 인자는 `$ARGUMENTS`로 받아 `init/show/approve` 등의 서브커맨드 인자로 전달합니다.

**문서 길이 관리**:

- `SKILL.md`는 500줄 이내를 유지합니다.
- 초과 위험이 있는 상세 내용은 모두 `references/` 하위로 분리하고, SKILL.md는 "언제 어떤 reference를 로드할지"만 명시합니다.

### 2단계: 워크플로우 단계별 상세 규칙 분리 (`references/workflow/`)

기존 PLAN의 "4개 내부 에이전트" 개념은 표준 스킬 모델과 직접 매핑되지 않습니다. 대신 각 단계의 상세 행동 규칙을 `references/workflow/`에 markdown 파일로 분리하고, SKILL.md가 단계 진입 시 on-demand로 Read합니다. 이는 별도의 시스템 프롬프트 파일이나 서브스킬 분할 없이, 단일 진입점을 유지하면서 단계별 로직을 캡슐화하는 표준 호환 방식입니다.

#### `references/workflow/design.md` — 설계 단계 상세 규칙
- **역할**: RE 산출물을 기반으로 사용자와의 대화를 통해 아키텍처를 결정
- **핵심 역량**:
  - **RE 산출물 해석**: RE의 3섹션을 아키텍처 드라이버로 변환
    - NFR + `quality_attributes.metric` → 아키텍처 스타일 결정의 근거
    - `constraints`의 `flexibility`가 `hard`인 항목 → 비협상 설계 제약으로 고정
    - `requirements.dependencies` → 컴포넌트 경계 도출 힌트
  - **기술적 맥락 도출**: RE에서 다루지 않는 기술적 맥락을 사용자에게 능동적으로 질문
    - 팀 규모, 기술 스택 경험, 운영 역량
    - 기존 인프라 현황 (클라우드, 온프레미스, 하이브리드)
    - 비용 제약의 구체적 규모
    - 기존 코드베이스가 있는 경우 그 구조와 제약
  - 요구사항 기반 아키텍처 스타일 추천 (마이크로서비스, 모놀리식, 이벤트 드리븐, 레이어드 등)
  - **기술적 트레이드오프 분석**: RE가 확정한 품질 속성 트레이드오프를 전제로, 패턴/기술 선택 수준의 트레이드오프에 집중
  - 컴포넌트 분해 및 인터페이스 정의
  - 기술 스택 추천 및 근거 제시 (RE 제약 조건 참조)
- **입력**: RE `spec` 산출물 (`requirements_spec`, `constraints`, `quality_attribute_priorities`)
- **출력**:
  - 아키텍처 결정 요약 (스타일, 패턴, 주요 결정 + RE 참조)
  - 컴포넌트 구조 (이름, 책임, 인터페이스, 의존 관계)
  - 기술 스택 (선택, 근거, RE 제약 참조)
- **상호작용 모델**: RE 산출물 수신 → 기술적 맥락 질문 → 사용자 응답 → 설계 초안 제시 → 사용자 피드백 → 수정 → 확정

#### `references/workflow/review.md` — 리뷰 단계 상세 규칙
- **역할**: `design` 에이전트의 출력을 RE 품질 속성 메트릭 기반으로 검증
- **핵심 역량**:
  - **RE 메트릭 기반 시나리오 검증**: RE의 `quality_attributes.metric`을 구체적 시나리오로 변환하여 설계가 이를 충족하는지 평가
    - 예: `metric: "응답시간 < 200ms"` → "동시 사용자 N명이 API 호출 시, 선택된 아키텍처 스타일과 기술 스택이 200ms 이내 응답을 보장할 수 있는가?"
  - **RE 제약 조건 준수 검증**: `hard` 제약이 설계에 모두 반영되었는지, `negotiable` 제약의 완화가 정당한지 확인
  - **컴포넌트-요구사항 추적성 검증**: 모든 FR/NFR이 최소 하나의 컴포넌트에 매핑되어 있는지 확인
  - 아키텍처 기술 부채 식별
  - 확장성/가용성 병목 지점 분석
  - 개선 제안 및 리스크 식별
- **입력**: `design` 에이전트 출력 + RE `spec` 산출물 (검증 기준으로 사용)
- **출력**: 리뷰 리포트 (시나리오별 검증 결과, RE 추적성 검증, 강점, 약점, 리스크, 개선 제안) + **사용자 확인 필요 사항**
- **상호작용 모델**: 리뷰 결과 제시 → 사용자 확인 (특히 리스크 수용 여부) → 필요시 design 에이전트로 피드백

#### `references/workflow/adr.md` — ADR 작성 단계 상세 규칙
- **역할**: `design` 에이전트가 내린 주요 결정을 Architecture Decision Record로 기록
- **핵심 역량**:
  - Michael Nygard 형식의 ADR 생성
  - **RE 참조 포함**: 각 ADR의 컨텍스트에 근거가 된 RE 산출물 ID를 명시 (예: "NFR-003의 성능 요구사항과 CON-002의 기술 제약에 의해...")
  - `design` 에이전트의 `alternatives_considered`와 `trade_offs`를 ADR의 대안 비교 분석표로 구조화
  - 기존 ADR과의 관계 (supersedes, amends) 관리
- **입력**: `design` 에이전트의 아키텍처 결정 요약 (`architecture_decisions`)
- **출력**: ADR 문서 목록 (상태, 컨텍스트, 결정, 결과, 대안 비교, RE 참조)
- **상호작용 모델**: ADR 초안 제시 → 사용자 확인 → 필요시 보완

#### `references/workflow/diagram.md` — 다이어그램 작성 단계 상세 규칙
- **역할**: `design` 에이전트의 확정된 설계를 시각화
- **핵심 역량**:
  - C4 모델 (Context, Container) 다이어그램 — 경량 모드에서는 Context만, 중량 모드에서는 Container까지
  - 시퀀스 다이어그램 (주요 흐름)
  - Mermaid 코드 생성
  - 데이터 흐름 다이어그램 (DFD)
- **입력**: `design` 에이전트의 컴포넌트 구조 (`component_structure`) + 기술 스택 (`technology_stack`)
- **출력**: 다이어그램 코드 (Mermaid) 및 설명
- **상호작용 모델**: 다이어그램 초안 제시 → 사용자 피드백 → 수정

### 3단계: 참조 문서 작성 (`references/`)

프롬프트 템플릿을 별도 `prompts/` 디렉토리로 분리하던 기존 계획은 폐기하고, 모든 가이드 문서를 표준 `references/` 디렉토리로 통합합니다. SKILL.md가 필요한 시점에 해당 파일을 Read합니다.

- `references/workflow/*.md` (4개): 단계별 상세 행동 규칙 — 2단계에서 작성
- `references/contracts/re-input-contract.md`: RE 3섹션 → Arch 드라이버 파싱 가이드 (FR → 컴포넌트, NFR·metric → 아키텍처 드라이버, hard constraint → 비협상 설계 제약 등)
- `references/contracts/downstream-contract.md`: 후속 스킬(`impl`, `qa`, `security`, `deployment`, `operation`) 소비 계약
- `references/schemas/meta-schema.md`: 메타데이터 공통 필드 (`artifact_id`, `phase`, `approval`, `upstream_refs`, `downstream_refs` 등) 명세
- `references/schemas/section-schemas.md`: 4섹션(`decisions`, `components`, `tech-stack`, `diagrams`) 필드 명세
- `references/adaptive-depth.md`: 경량/중량 모드 판별 규칙과 모드별 스킵 단계 정의
- `references/scenario-validation.md`: RE `quality_attributes.metric` → 아키텍처 시나리오 변환 템플릿 (ATAM 축소형)
- `references/examples/` 하위: 기술적 맥락 대화 예시, 아키텍처 시나리오 검증 예시, ADR 예시(RE 참조 포함), C4 다이어그램 예시

**스크립트 호출 규약 배치**: "에이전트가 YAML을 직접 편집하지 않고 `scripts/artifact.py` 커맨드만 호출한다"는 행동 규약은 `references/workflow/*.md`에 반복 명시하고, 각 단계(설계 초안 → 리뷰 → 승인)에서 어떤 커맨드를 어떤 순서로 호출해야 하는지 시퀀스로 기술합니다.

### 4단계: 문서 템플릿 작성 (`assets/templates/`)

표준 디렉토리 명칭은 `assets/`입니다(기존 `templates/`는 폐기).

- 4섹션(`decisions`, `components`, `tech-stack`, `diagrams`)별 markdown 템플릿(`*.md.tmpl`)을 `assets/templates/`에 작성. 각 템플릿은 섹션 헤더, 표 골격, RE 참조 슬롯, 플레이스홀더를 포함하여 에이전트가 본문만 채우도록 유도
- 각 섹션의 메타데이터 초기 골격(`*.meta.yaml.tmpl`)을 작성. `phase: draft`, `approval.state: pending`, 빈 `upstream_refs`/`downstream_refs` 등 기본값을 포함
- `diagrams.md.tmpl`은 Mermaid 코드 펜스(```` ```mermaid ````) 슬롯을 다이어그램 유형별로 미리 배치

**적응적 깊이 → `effort` 매핑**:

- frontmatter의 기본값을 `effort: high`로 설정하되, SKILL.md 본문의 분기 로직에서 `references/adaptive-depth.md`의 판별 기준에 따라 경량 조건이면 adr/diagram 단계의 일부를 스킵합니다.
- 즉 하나의 스킬 안에서 경량/중량 모드를 내부 분기로 처리하며, 스킬 자체를 `arch-light`/`arch-full`로 분할하지 않습니다(단일 진입점 유지).

**문서 길이 관리**:

- `SKILL.md` 500줄 이내를 유지하기 위해, 4단계 워크플로우의 상세 규칙/가이드/예시는 모두 이 단계에서 `references/`로 분리합니다.

### 5단계: 메타데이터 조작 스크립트 구현 (`scripts/`)

- `scripts/artifact.py` 를 단일 진입점으로 구현하며, 다음 서브커맨드를 제공:
  - `init` — `assets/templates/`에서 템플릿을 복사해 메타데이터 + markdown 쌍을 생성. 템플릿 경로는 `${SKILL_DIR}/assets/templates/`를 기준으로 해석
  - `set-phase`, `set-progress` — 진행 상태/진행률 갱신
  - `approve` — 승인 상태 전이 (전이 규칙 검증 포함)
  - `link` — `upstream_refs`/`downstream_refs` 추가 및 양방향 무결성 유지
  - `show`, `validate` — 조회 및 스키마/추적성 검증
- 모든 쓰기 커맨드는 `updated_at`을 자동 갱신하고, 잘못된 상태 전이/누락 필드를 차단

**스크립트 호출 강제 (다층 방어)**:

행동 규약만으로는 우회될 수 있으므로 다층 방어를 구성합니다.

1. **행동 규약 (가장 약함)**: `references/workflow/*.md` 및 SKILL.md 본문에서 "메타데이터 갱신은 반드시 `${SKILL_DIR}/scripts/artifact.py` 를 호출한다"를 반복 명시
2. **도구 권한 (중간)**: frontmatter `allowed-tools` 설계 시 `*.meta.yaml` 파일에 대한 직접 편집을 최소화하기 위해, Edit/Write가 필요한 대상은 markdown 본문으로 한정하도록 워크플로우 가이드에서 명시. (도구 단위 화이트리스트만 표준에 존재하므로, 파일 단위 차단은 아래 hooks로 보완)
3. **PreToolUse hooks (가장 강함)**: 가능하다면 `*.meta.yaml`에 대한 Edit/Write 시도를 차단하는 PreToolUse hook을 등록하여, 행동 규약을 우회한 직접 편집을 원천 차단
4. **시작 시 상태 주입**: SKILL.md 상단에서 `` !`python ${SKILL_DIR}/scripts/artifact.py validate` ``를 사용해 현재 산출물 상태·추적성 무결성을 동적으로 주입. 이를 통해 에이전트가 자연스럽게 스크립트 기반 흐름을 따르도록 유도

### 6단계: 입출력 예시 작성 (`references/examples/`)

- RE 경량 출력 → Arch 경량 설계 예시 (간단한 CRUD API)
- RE 중량 출력 → Arch 중량 설계 예시 (분산 시스템)
- 기술적 맥락 대화를 통한 기술 스택 결정 예시
- RE 메트릭 기반 아키텍처 시나리오 검증 예시
- ADR (RE 참조 포함) 예시
- C4 Context/Container 다이어그램 예시
- **메타데이터 + 문서 쌍 예시**: 각 산출물 예시는 markdown 본문(`*-output.md`)과 그에 대응하는 메타데이터(`*-output.meta.yaml`)를 함께 포함하여, `phase`, `approval`, `upstream_refs`/`downstream_refs` 가 채워진 실제 모습을 보여줄 것

## 핵심 설계 원칙

1. **RE 산출물 기반 (RE-Driven)**: 모든 아키텍처 결정은 RE의 3섹션 산출물에 근거하며, `re_refs`로 추적성을 유지. RE가 확정한 품질 속성 트레이드오프는 재질문하지 않고 전제로 수용
2. **기술적 맥락 대화 (Technical Context Dialogue)**: RE에서 다루지 않는 기술적 맥락(팀 역량, 인프라, 비용)을 사용자와의 대화로 파악하여 설계 결정에 반영
3. **적응적 깊이 (Adaptive Depth)**: RE 출력 밀도에 연동하여 경량(스타일 + 가이드)/중량(컴포넌트 + 다이어그램 + ADR) 모드 자동 전환
4. **의사결정 추적**: 모든 주요 결정은 ADR로 기록하고, RE 산출물 ID를 참조하여 "왜 이 결정을 했는가"를 RE까지 추적 가능
5. **시나리오 기반 검증**: RE의 `quality_attributes.metric`을 시나리오로 변환하여 설계 적합성을 검증. 전통적 ATAM의 축소 적용
6. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **아키텍처 결정 / 컴포넌트 구조 / 기술 스택 / 다이어그램** 4섹션으로 고정하여, 후속 스킬(`impl`, `qa`, `security`, `deployment`, `operation`)이 직접 소비할 수 있는 계약(contract) 역할을 수행
7. **메타데이터-문서 분리 및 스크립트 경유 원칙 (Metadata/Document Separation via Scripts)**: 산출물은 YAML 메타데이터 파일과 markdown 문서 파일을 분리하여 관리하고, 메타데이터(진행 상태·승인 상태·추적성 ref)는 에이전트가 직접 편집하지 않고 오직 `${SKILL_DIR}/scripts/artifact.py` 커맨드를 통해서만 갱신. markdown 본문은 `assets/templates/` 의 사전 정의 템플릿으로 골격을 생성한 뒤 에이전트가 플레이스홀더를 채움으로써, 상태 일관성과 서식 표준을 동시에 보장
8. **Claude Code Skill 표준 준수 (Standard Compliance)**: 단일 진입점 `SKILL.md` + YAML frontmatter, `scripts/`·`assets/`·`references/`의 표준 디렉토리 명칭, `${SKILL_DIR}`/`$ARGUMENTS` 치환자 활용, `description`/`paths`/`allowed-tools`/`disable-model-invocation`/`effort` 필드 명시를 통해 공식 표준(https://code.claude.com/docs/ko/skills)과 완전히 호환
