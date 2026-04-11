# RE (Requirements Engineering) Skill 구현 계획

## 개요

사용자와의 **대화형 상호작용**을 통해 요구사항을 점진적으로 도출, 분석, 명세, 검증하는 스킬입니다.

전통적 RE가 다수의 이해관계자, 회의록, 인터뷰 결과 등 풍부한 입력을 전제로 했다면, AI 컨텍스트에서의 RE는 **프롬프트를 입력하는 한 명의 사용자**가 핵심 이해관계자입니다. 사용자의 입력은 대부분 불완전하고 모호하며, 사용자 자신도 원하는 바를 명확히 모르는 경우가 많습니다.

따라서 이 스킬의 에이전트들은 **능동적으로 사용자에게 질문하고, multi-turn 대화를 통해 요구사항을 점진적으로 구체화**하는 것을 핵심 설계 원칙으로 합니다.

### 전통적 RE vs AI 컨텍스트 RE

| 구분 | 전통적 RE | AI 컨텍스트 RE |
|------|-----------|----------------|
| 이해관계자 | 다수 (고객, 사용자, 개발팀, PM 등) | 프롬프트를 입력하는 한 명의 사용자 |
| 입력 수준 | 회의록, 인터뷰, RFP 등 풍부한 입력 | 자연어 한두 문장 수준의 모호한 입력 |
| 정보 흐름 | 분석가가 이해관계자로부터 수집 | **에이전트가 사용자로부터 능동적으로 유도** |
| 프로세스 | 단계별 순차 진행 (waterfall 경향) | **대화 기반 반복적 구체화 (iterative)** |
| 산출물 수준 | 항상 무거운 SRS | **입력 복잡도에 따라 경량/중량 적응** |
| 핵심 역량 | 이해관계자 간 충돌 조정 | **모호성 탐지 + 능동적 질문 생성** |

## 최종 산출물 구조

RE 스킬의 최종 산출물은 다음 **세 가지 섹션**으로 구성됩니다. 이 구조는 후속 스킬(특히 `arch`)이 직접 소비할 수 있도록 설계되었습니다.

### 1. 요구사항 명세 (Requirements Specification)

기능 요구사항(FR)과 비기능 요구사항(NFR)을 구조화한 명세입니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `FR-001`, `NFR-001`) |
| `category` | 분류 (기능/비기능, 하위 카테고리) |
| `title` | 요구사항 제목 |
| `description` | 상세 설명 |
| `priority` | MoSCoW (Must/Should/Could/Won't) |
| `acceptance_criteria` | 검증 가능한 수용 기준 목록 |
| `source` | 도출 근거 (사용자 발화, 분석 추론 등) |
| `dependencies` | 의존하는 다른 요구사항 ID 목록 |

### 2. 제약 조건 (Constraints)

시스템 설계 및 구현 시 반드시 준수해야 하는 제약 사항입니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `CON-001`) |
| `type` | 제약 유형 (`technical` / `business` / `regulatory` / `environmental`) |
| `title` | 제약 조건 제목 |
| `description` | 상세 설명 |
| `rationale` | 제약이 존재하는 이유 |
| `impact` | 위반 시 영향 범위 |
| `flexibility` | 협상 가능 여부 (`hard` / `soft` / `negotiable`) |

### 3. 품질 속성 우선순위 (Quality Attribute Priorities)

아키텍처 결정에 직접 영향을 미치는 품질 속성의 우선순위입니다.

| 필드 | 설명 |
|------|------|
| `attribute` | 품질 속성 (예: `performance`, `security`, `scalability`, `availability`, `maintainability`, `usability`) |
| `priority` | 우선순위 (1이 가장 높음) |
| `description` | 이 프로젝트에서의 구체적 의미 |
| `metric` | 측정 가능한 목표치 (예: "응답시간 < 200ms", "99.9% 가용성") |
| `trade_off_notes` | 다른 속성과의 트레이드오프 설명 |

### 산출물 파일 구성: 메타데이터와 문서의 분리

각 섹션의 산출물은 **메타데이터 파일**과 **문서 파일**로 분리하여 관리합니다. 이 분리는 RE 스킬이 후속 스킬들에게 **소비 계약(contract)**을 제공하는 시작점이기 때문에 특히 중요합니다. 구조화된 메타데이터가 독립 파일로 존재하면, 후속 스킬(`arch`, `qa`, `impl` 등)은 자연어 파싱 없이 메타데이터만 직접 읽어 안정적으로 소비할 수 있습니다.

| 파일 유형 | 포맷 | 역할 |
|-----------|------|------|
| 메타데이터 파일 | **YAML** (권장) | 구조화된 필드(ID, priority, status, approval, refs 등)를 기계 판독 가능한 형태로 저장. 후속 스킬의 자동 소비 대상 |
| 문서 파일 | Markdown | 사람이 읽는 상세 설명, 근거, 다이어그램, 대화 맥락 등을 서술. 리뷰 및 사용자 피드백의 주요 대상 |

**YAML을 권장하는 이유**:
- 주석을 지원하여 필드의 의도나 결정 맥락을 함께 기록할 수 있음
- 들여쓰기 기반 문법으로 사람이 읽기 쉬움
- Python/쉘 스크립트에서 손쉽게 파싱·갱신 가능 (`PyYAML`, `yq` 등)
- JSON 대비 중첩 구조와 다줄 문자열 표현이 자연스러움

**메타데이터 스키마 (공통 필드)**:

| 필드 | 설명 |
|------|------|
| `artifact_id` | 산출물 식별자 (예: `re-spec-requirements`) |
| `section` | 세 섹션 중 하나 (`requirements_spec` / `constraints` / `quality_attribute_priorities`) |
| `phase` | 현재 진행 단계 (`elicit` / `analyze` / `spec` / `review` / `finalized`) |
| `progress` | 진행률 (0.0 ~ 1.0) 또는 단계별 체크리스트 상태 |
| `approval.state` | 승인 상태 (`draft` / `pending_review` / `changes_requested` / `approved`) |
| `approval.approver` | 승인자 식별자 (사용자) |
| `approval.approved_at` | 승인 시각 |
| `approval.history` | 승인 상태 전이 이력 |
| `upstream_refs` | 상위 근거 참조 (사용자 발화, 이전 산출물 ID 등) |
| `downstream_refs` | 이 산출물을 소비할 후속 스킬/산출물 ID 목록 |
| `document_path` | 대응되는 markdown 문서 파일의 상대 경로 |

RE의 **체크포인트 기반 파이프라인**(사용자 피드백 루프)은 이 `approval.state`의 상태 전이와 자연스럽게 대응됩니다. `elicit` 단계에서 `draft`로 생성되고, `analyze`/`spec`을 거치며 `pending_review`로 전이되며, 사용자 피드백에 따라 `changes_requested` ↔ `pending_review`를 오가다가 최종적으로 `approved`에 도달하면 후속 스킬이 소비할 수 있는 상태가 됩니다.

### 메타데이터 조작 스크립트 (필수)

에이전트는 **YAML/JSON 메타데이터 파일을 직접 편집하지 않습니다**. 모든 상태 갱신은 `scripts/` 디렉토리에 위치한 전용 스크립트 커맨드를 통해서만 이루어집니다. 이는 다음을 보장합니다:

- 스키마 일관성 (잘못된 필드명/타입 유입 방지)
- 상태 전이 규칙 강제 (예: `draft` → `approved` 직접 전이 차단)
- 변경 이력 자동 기록 (`approval.history`에 타임스탬프 포함 추가)
- 메타데이터 ↔ 문서 파일 간 정합성 유지

**주요 스크립트 커맨드 (예시)**:

| 커맨드 | 설명 |
|--------|------|
| `scripts/artifact.py init <section>` | 섹션별 메타데이터와 markdown 문서(템플릿 기반)를 한 쌍으로 생성 |
| `scripts/artifact.py set-phase <id> <phase>` | 현재 진행 단계 전이 |
| `scripts/artifact.py set-progress <id> <value>` | 진행률 갱신 |
| `scripts/artifact.py request-review <id>` | `draft` → `pending_review` 상태 전이 |
| `scripts/artifact.py approve <id> --approver <user>` | 최종 승인 처리 |
| `scripts/artifact.py request-changes <id> --note <msg>` | 변경 요청 상태로 전이 |
| `scripts/artifact.py add-ref <id> --upstream/--downstream <ref>` | 추적성 참조 추가 |
| `scripts/artifact.py show <id>` | 메타데이터 조회 (에이전트가 현재 상태 확인 시 사용) |

### 문서 템플릿 (`templates/`)

각 섹션의 markdown 문서는 `templates/` 디렉토리에 **미리 정의된 템플릿**을 기반으로 생성됩니다. `scripts/artifact.py init` 커맨드는 해당 섹션의 템플릿을 복사하여 섹션 헤더, 플레이스홀더, 안내 주석이 포함된 기본 골격을 만들고, 이후 에이전트가 이 골격을 채워 넣는 방식으로 작업을 진행합니다.

| 템플릿 파일 | 대상 섹션 |
|-------------|-----------|
| `templates/requirements-spec.md` | 요구사항 명세 (FR/NFR 표, 수용 기준 섹션) |
| `templates/constraints.md` | 제약 조건 (유형별 분류, 근거, 유연성 섹션) |
| `templates/quality-attributes.md` | 품질 속성 우선순위 (우선순위 표, 트레이드오프 섹션) |
| `templates/metadata.yaml` | 메타데이터 파일의 기본 스키마 및 기본값 |

이 방식은 (1) 에이전트 간 출력 형식을 균일하게 유지하고, (2) 필수 섹션 누락을 방지하며, (3) 후속 스킬이 기대하는 구조를 보장합니다.

### 후속 스킬 연계

```
re:spec 산출물 구조:
┌─────────────────────────────────────────┐
│  요구사항 명세 (Requirements Spec)       │──→ arch:design (기능/비기능 요구사항)
│  - FR-001, FR-002, ...                  │──→ qa:strategy (테스트 대상 도출)
│  - NFR-001, NFR-002, ...               │──→ management:plan (범위 결정)
├─────────────────────────────────────────┤
│  제약 조건 (Constraints)                 │──→ arch:design (설계 제약)
│  - CON-001: technical                   │──→ impl:generate (구현 제약)
│  - CON-002: business                    │──→ deployment:strategy (배포 제약)
├─────────────────────────────────────────┤
│  품질 속성 우선순위 (QA Priorities)       │──→ arch:design (아키텍처 드라이버)
│  - 1. performance                       │──→ security:threat-model (보안 우선순위)
│  - 2. security                          │──→ operation:slo (SLO 기준)
│  - 3. scalability                       │──→ qa:strategy (NFR 테스트 기준)
└─────────────────────────────────────────┘
```

## 목표 구조 (Claude Code Skill 표준 준수)

이 스킬은 Claude Code Skill 표준 포맷을 따릅니다. 필수 진입점은 `re/SKILL.md`이며, 상세 지침과 참고 자료는 `references/` 하위에 지연 로드되는 형태로 분리합니다. 비표준 디렉토리(`agents/`, `prompts/`, 루트의 `examples/`, `templates/`)는 사용하지 않습니다.

```
re/
├── SKILL.md                         # 필수 진입점 (YAML frontmatter + 본문)
├── scripts/
│   ├── artifact.py                  # 메타데이터 상태 전이 단일 진입점
│   └── lib/
│       ├── schema.py
│       └── transitions.py
├── references/
│   ├── phases/
│   │   ├── elicit.md                # 단계별 상세 지침 (역할, 질문 전략, few-shot)
│   │   ├── analyze.md
│   │   ├── spec.md
│   │   └── review.md
│   ├── templates/
│   │   ├── metadata.yaml
│   │   ├── requirements-spec.md
│   │   ├── constraints.md
│   │   └── quality-attributes.md
│   ├── contracts/
│   │   └── downstream-consumers.md  # arch/qa/impl/... 소비 계약 설명
│   └── examples/
│       ├── elicit-conversation.md
│       ├── analyze-tradeoffs.md
│       ├── spec-light-mode.md
│       ├── spec-heavy-mode.md
│       ├── review-report.md
│       └── artifact-pair/
│           ├── spec.metadata.yaml
│           ├── spec.requirements-spec.md
│           ├── spec.constraints.md
│           └── spec.quality-attributes.md
└── assets/                          # (선택) 다이어그램, 체크리스트 등 정적 리소스
```

핵심 변경 사항:

- **`SKILL.md` 필수 진입점**: 기존 계획의 `skills.yaml`은 제거한다. 스킬 메타데이터는 `SKILL.md` 상단의 YAML frontmatter로 이관한다.
- **`agents/`와 `prompts/` 통합**: 동일한 파일명이 두 디렉토리에 중복되던 구조를 폐기하고, 단계별 역할·프롬프트·few-shot을 `references/phases/<phase>.md` 한 파일로 통합한다. `SKILL.md`는 본문에서 현재 단계에 해당하는 phase 파일만 Read로 지연 로드한다.
- **`templates/`와 `examples/` 재배치**: 표준이 명명하는 `references/` 계층 하위로 이동한다 (`references/templates/`, `references/examples/`).
- **`contracts/` 추가**: 후속 스킬(`arch`, `qa`, `impl`, `security`, `deployment`, `operation`)의 소비 계약을 `references/contracts/downstream-consumers.md`로 문서화하여, 필요 시에만 로드되도록 한다.
- **산출물 쌍 예시**: `references/examples/artifact-pair/`에 세 섹션 각각의 메타데이터(YAML)와 문서(markdown) 쌍을 수록하여, 에이전트 구현자와 후속 스킬 구현자가 실제 소비 가능한 형태를 바로 확인할 수 있도록 한다.

### `SKILL.md` 본문 구성 방침

`SKILL.md`는 표준의 500줄 가이드라인을 준수하기 위해 **200~300줄 이내의 요약·분기 로직**만 담고, 상세 내용은 모두 `references/`로 지연 로드한다. 구체적으로는 다음 흐름을 따른다.

1. **YAML frontmatter** (아래 "스킬 메타데이터" 절 참고)
2. **진입 시 상태 스냅샷 주입**: 프리프로세싱(`` !`...` ``)으로 현재 산출물 상태를 본문에 삽입
   ```
   ## 현재 산출물 상태
   !`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py show --all`
   ```
   이렇게 하면 에이전트가 매 턴마다 상태 조회를 위해 별도 도구 호출을 할 필요가 없다.
3. **사용자 입력 수신**: `$ARGUMENTS` 치환으로 초기 요청을 본문에 삽입
   ```
   ## 사용자 요청
   $ARGUMENTS
   ```
4. **4단계 워크플로 요약** (각 단계 50줄 내외): `elicit → analyze → spec → review` 체크포인트 파이프라인과 각 단계별 진입 조건·종료 조건·상태 전이 커맨드를 명시
5. **단계별 지연 로드 지시**: "현재 phase == `elicit`인 경우 `Read ${CLAUDE_SKILL_DIR}/references/phases/elicit.md`" 같은 조건부 로드 지침
6. **스크립트 호출 규약**: 모든 메타데이터 변경은 `Bash: python ${CLAUDE_SKILL_DIR}/scripts/artifact.py ...` 절대 경로로만 지시. 상대 경로 호출은 금지하여 cwd 의존성을 제거
7. **후속 스킬 소비 계약 링크**: 필요 시 `Read ${CLAUDE_SKILL_DIR}/references/contracts/downstream-consumers.md`

## 구현 단계

### 1단계: 스킬 메타데이터 정의 (`SKILL.md` YAML frontmatter)

`SKILL.md` 최상단에 표준 YAML frontmatter를 둔다. Claude Code Skill 표준에 따라 frontmatter는 최소한으로 유지하며, `name`과 `description`만 기본으로 포함한다. 그 외 선택 필드는 기본 동작으로 스킬의 목적을 달성할 수 없음이 명백히 입증될 때에 한해 도입한다. `description`은 250자 이내로 "무엇을 / 언제" 정보를 front-load하여, 모델의 자동 선택 정확도를 높인다.

```yaml
---
name: re
description: 사용자와의 대화형 상호작용을 통해 모호한 요청을 기능/비기능 요구사항, 제약 조건, 품질 속성 우선순위 세 섹션으로 점진적으로 도출·분석·명세·검증한다. 신규 프로젝트 착수, 요구사항 재정비, arch/qa/impl 후속 스킬 투입 직전에 사용.
---
```

필드별 결정 근거:

- **`name: re`**: 소문자/하이픈, 64자 이하 표준 준수.
- **`description`**: "무엇을"(세 섹션 산출물 도출·분석·명세·검증)과 "언제"(신규 착수, 재정비, arch/qa/impl 투입 직전)를 함께 명시. 한국어 기준 약 170자.
- **그 외 선택 필드**(`argument-hint`, `allowed-tools`, `context`, `agent`, `effort`, `model`, `hooks`, `paths`, `disable-model-invocation` 등): 기본값으로 스킬의 목적을 달성할 수 없음이 명확히 입증되는 경우에만 추가한다. 기본 정책상 추가하지 않는다.

본문에서는 `$ARGUMENTS`로 사용자 초기 요청을 수신하고, `${CLAUDE_SKILL_DIR}`로 스킬 경로를 치환한다. 예:

```
## 사용자 요청
$ARGUMENTS

## 현재 산출물 상태
!`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py show --all`
```

입력/출력 스키마, 단계별 역할, 대화 모드/적응적 깊이 설정, 후속 스킬 소비 계약 등은 `SKILL.md` 본문과 `references/phases/`, `references/contracts/downstream-consumers.md`에 분산 기술하여 frontmatter를 가볍게 유지한다.

### 2단계: 문서 템플릿 및 메타데이터 스키마 정의 (`references/templates/`)

- `references/templates/metadata.yaml`: 공통 메타데이터 스키마의 기본값과 필수 필드 정의 (`phase`, `progress`, `approval`, `upstream_refs`, `downstream_refs` 등)
- `references/templates/requirements-spec.md`: FR/NFR 표, 수용 기준, 추적성 섹션 플레이스홀더
- `references/templates/constraints.md`: 유형별(기술/비즈니스/규제/환경) 분류 플레이스홀더, 근거·유연성 섹션
- `references/templates/quality-attributes.md`: 우선순위 표, 측정 목표치, 트레이드오프 서술 섹션
- 각 템플릿은 HTML 주석(`<!-- 여기에 ... 를 작성 -->`) 형태의 안내문을 포함하여, `init` 커맨드로 생성한 뒤 에이전트가 채워 넣을 영역을 명확히 표시
- `scripts/artifact.py init` 커맨드는 `${CLAUDE_SKILL_DIR}/references/templates/` 하위를 소스로 삼아 산출물 쌍(메타데이터 + 문서)을 생성

### 3단계: 메타데이터 조작 스크립트 구현 (`scripts/`)

- `scripts/artifact.py`: 단일 CLI 진입점. 하위 커맨드로 `init`, `set-phase`, `set-progress`, `request-review`, `approve`, `request-changes`, `add-ref`, `show`, `validate` 제공
- `scripts/lib/schema.py`: 메타데이터 필드 검증 (YAML 로드 후 스키마 체크). `hooks.pre-request-review`에서 호출되는 `validate` 커맨드의 내부 구현
- `scripts/lib/transitions.py`: `approval.state`의 유효한 상태 전이 규칙 정의 및 강제 (예: `draft` → `approved` 직접 전이 차단, `changes_requested` ↔ `pending_review` 왕복 허용)
- 모든 상태 변경은 `approval.history`에 타임스탬프와 함께 자동 기록
- 에이전트는 YAML을 직접 편집하지 않고 오직 이 스크립트 커맨드를 통해서만 상태를 갱신하도록 `SKILL.md` 본문과 `references/phases/` 지침에 명시
- 에이전트 프롬프트 및 `SKILL.md` 본문에서 스크립트 호출은 항상 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 절대 경로를 사용하여 cwd 의존성을 제거

### 4단계: 단계별 지침 작성 (`references/phases/`)

표준 스킬은 단일 `SKILL.md`를 진입점으로 하므로, 기존 계획의 `agents/` + `prompts/` 이원 구조를 폐기하고 단계별 상세 지침을 `references/phases/<phase>.md` 한 파일로 통합한다. 각 파일에는 해당 단계의 **역할, 핵심 역량, 입력/출력, 상호작용 모델, 질문 전략, few-shot 예시, CoT 가이드, 스크립트 호출 시점**을 모두 담는다. `SKILL.md`는 현재 phase에 해당하는 파일만 Read로 지연 로드하여 컨텍스트를 절약한다.

각 phase 파일은 500줄 이하 가이드라인을 준수하기 위해, 분량이 초과될 경우 few-shot 예시를 `references/examples/` 하위로 분리한다.

#### `references/phases/elicit.md` — 요구사항 도출 단계

- **역할**: 사용자와의 대화를 통해 모호한 요구를 구조화된 요구사항으로 점진적으로 도출
- **핵심 역량**:
  - **모호성 탐지 및 질문 생성**: 사용자 입력에서 모호한 부분, 누락된 정보, 암묵적 가정을 식별하고 targeted question 생성
  - **적응적 질문 전략**: 입력의 구체성 수준에 따라 질문 깊이와 범위를 자동 조절
    - 고수준 입력 ("쇼핑몰 만들어줘") → 넓은 범위의 탐색적 질문
    - 중간 수준 ("OAuth2 기반 로그인 구현") → 세부 사항 확인 질문
    - 상세 입력 (구체적 스펙 포함) → 경계 조건/예외 확인 질문
  - **점진적 구체화**: 대화 턴마다 요구사항의 구체성 수준을 높여가는 반복적 정제
  - **대화 상태 관리**: 이미 확인된 사항 vs 아직 미확인인 사항을 추적하여 중복 질문 방지
  - **확인과 요약**: 주기적으로 "지금까지 이해한 바"를 사용자에게 제시하고 확인 요청
  - **이해관계자 역할 대행**: 사용자가 고려하지 못한 관점 (최종 사용자, 운영자, 보안 담당자 등)에서 질문 제기
  - 사용자 스토리 및 유스케이스 형태로 구조화
- **입력**: 사용자의 자연어 요청 (한 문장부터 상세 RFP까지)
- **출력**: 
  - 구조화된 요구사항 후보 목록 (ID, 분류, 우선순위, 수용 기준)
  - 식별된 제약 조건 후보 (기술적/비즈니스/규제/환경)
  - 품질 속성 후보 및 사용자가 언급한 우선순위 힌트
  - 미해결 질문 목록
- **상호작용 모델**: multi-turn 대화 (사용자가 충분하다고 판단할 때까지)

#### `references/phases/analyze.md` — 요구사항 분석 단계

- **역할**: 요구사항의 완전성, 일관성, 실현 가능성을 분석하고, 발견된 문제에 대해 사용자에게 추가 질문
- **핵심 역량**:
  - 요구사항 간 충돌 및 모순 탐지
  - 누락된 요구사항 식별 (경계 조건, 예외 케이스, 비기능 요구사항)
  - 실현 가능성 평가 (기술적, 시간적, 비용적)
  - 의존 관계 분석 및 우선순위 매트릭스 생성
  - **발견된 이슈에 대한 해결 질문 생성**: 충돌/누락/위험을 발견하면 사용자에게 선택지와 함께 질문 제시
  - **트레이드오프 제시**: "A를 선택하면 X가 희생됩니다. B를 선택하면 Y가 희생됩니다. 어떤 것이 더 중요합니까?"
- **입력**: elicit 산출물 (요구사항 후보, 제약 조건 후보, 품질 속성 후보)
- **출력**: 
  - 분석 리포트 (충돌, 누락, 위험 요소, 개선 권고)
  - 정제된 요구사항 목록 (충돌 해소, 누락 보완)
  - 검증된 제약 조건 목록 (실현 가능성 평가 완료)
  - 품질 속성 간 트레이드오프 분석 (사용자 의사결정 근거 제시)
  - **사용자 의사결정이 필요한 질문 목록**
- **상호작용 모델**: 분석 결과 제시 → 사용자 확인/선택 (특히 품질 속성 트레이드오프) → 요구사항 수정 반영

#### `references/phases/spec.md` — 요구사항 명세 단계

- **역할**: 분석된 요구사항을 후속 스킬이 직접 소비할 수 있는 **세 가지 섹션**(요구사항 명세, 제약 조건, 품질 속성 우선순위)으로 구조화
- **핵심 역량**:
  - **적응적 명세 수준**:
    - 경량 모드: User Story + Acceptance Criteria (간단한 기능/단일 요청)
    - 중량 모드: IEEE 830 / ISO 29148 기반 SRS (복잡한 시스템/다수 요구사항)
    - 모드 자동 판별 또는 사용자 선택
  - **요구사항 명세 생성**: FR/NFR을 ID 체계 기반으로 구조화하고 수용 기준 명세
  - **제약 조건 도출**: 분석 결과에서 기술적/비즈니스/규제/환경 제약을 식별하고 유연성(hard/soft/negotiable) 분류
  - **품질 속성 우선순위 결정**: 사용자와의 대화를 통해 품질 속성 간 트레이드오프를 명확히 하고, 측정 가능한 목표치와 함께 우선순위 확정
  - **초안 제시 → 피드백 → 수정 사이클**: 세 섹션 각각에 대해 초안을 사용자에게 보여주고, 피드백을 받아 수정하는 반복 과정
- **입력**: 분석 완료된 요구사항 목록 + 사용자 의사결정 결과
- **출력**: 아래 세 섹션으로 구성된 명세 문서
  1. **요구사항 명세** — FR/NFR 목록 (ID, 분류, 우선순위, 수용 기준, 의존 관계)
  2. **제약 조건** — 기술적/비즈니스/규제/환경 제약 목록 (유형, 근거, 유연성)
  3. **품질 속성 우선순위** — 우선순위가 부여된 품질 속성 목록 (측정 목표치, 트레이드오프)
- **상호작용 모델**: 초안 제시 → 사용자 피드백 (특히 품질 속성 간 트레이드오프 확인) → 수정 → 최종 확인

#### `references/phases/review.md` — 요구사항 리뷰 단계

- **역할**: 세 섹션(요구사항 명세, 제약 조건, 품질 속성 우선순위)으로 구성된 명세 문서를 리뷰하고, 후속 스킬 소비 적합성을 검증
- **핵심 역량**:
  - **요구사항 명세 검증**: SMART 기준 검증, 모호성/불완전성/비검증성 탐지, FR-NFR 간 추적성 확인
  - **제약 조건 검증**: 제약 간 상호 모순 탐지, 요구사항과의 정합성 확인, 누락된 제약 식별
  - **품질 속성 우선순위 검증**: 측정 목표치의 구체성 확인, 트레이드오프 설명의 충분성 확인, 요구사항/제약과의 일관성 검증
  - **후속 스킬 소비 적합성 체크**: `arch`가 아키텍처 드라이버로 사용하기에 충분한 정보인지, `qa`가 테스트 전략을 도출하기에 충분한 수용 기준이 있는지 등
  - 추적성 매트릭스 검증 (요구사항 ↔ 제약 조건 ↔ 품질 속성 간 상호 참조)
  - 개선 제안 및 대안 제시
  - **사용자 의사결정 필요 사항 하이라이트**: 리뷰어가 독단적으로 판단할 수 없는 이슈를 사용자에게 에스컬레이션
- **입력**: 세 섹션으로 구성된 명세 문서 (spec 에이전트 산출물)
- **출력**: 섹션별 리뷰 리포트 (이슈 목록, 심각도, 개선 제안, 후속 스킬 소비 적합성 판정) + **사용자 확인 필요 사항**
- **상호작용 모델**: 리뷰 결과 제시 → 사용자 확인/반영 → 최종 승인

### 5단계: 단계별 지침 본문 세부화 (`references/phases/<phase>.md`)

`references/phases/`의 각 파일에 기존 계획의 `prompts/` 내용도 통합한다. 즉, 단계별 지침 파일 하나에 다음 요소를 모두 담는다:
- 입력 변수 (placeholder) 정의 — `$ARGUMENTS`, `${CLAUDE_SKILL_DIR}`, 이전 단계 산출물 경로 등
- 출력 형식 지정
- **질문 생성 가이드라인**: 어떤 유형의 모호성에 어떤 형태의 질문을 생성할지
- **대화 상태 추적 템플릿**: 확인된 사항 / 미확인 사항 / 가정 사항을 구조화
- **스크립트 호출 가이드**: 단계별로 어떤 시점에 어떤 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 커맨드를 호출해야 하는지 명시 (예: `elicit` 시작 시 `init`, 단계 종료 시 `set-phase`, 리뷰 요청 시 `request-review`, 승인 수령 시 `approve`)
- **메타데이터 직접 편집 금지 규칙**: 에이전트가 YAML/JSON을 직접 수정하지 않도록 강제하는 지침
- Chain of Thought 가이드라인
- Few-shot 예시 참조 (본문 내 인라인 또는 `references/examples/` 링크)

각 phase 파일은 `SKILL.md`가 현재 단계에 진입할 때 지연 로드되며, 500줄을 초과하면 few-shot을 `references/examples/`로 분리하여 핵심 지침만 유지한다.

### 6단계: 입출력 예시 작성 (`references/examples/`)

`references/examples/` 하위에 단계별 대표 입출력 쌍을 작성합니다:
- **다양한 입력 구체성 수준**: 모호한 한 줄 요청부터 상세한 RFP까지
- **multi-turn 대화 예시**: 에이전트 질문 → 사용자 응답 → 추가 질문 → 구체화 과정 (`elicit-conversation.md`)
- 다양한 도메인 커버 (웹앱, 모바일앱, API, 데이터 파이프라인)
- 경량/중량 명세 모드 분기 예시 (`spec-light-mode.md`, `spec-heavy-mode.md`)
- 엣지 케이스 포함
- **메타데이터-문서 파일 쌍 예시**: `references/examples/artifact-pair/`에 세 섹션 각각에 대해 `*.metadata.yaml`(진행 상태, 승인 상태, 추적성 참조 포함)과 대응 markdown 문서를 함께 수록하여, 후속 스킬이 기대하는 소비 형식을 실물로 제공
- **스크립트 커맨드 사용 흐름 예시**: `init` → `set-phase` → `request-review` → `approve`로 이어지는 상태 전이 시퀀스를 예시화

### 7단계: 후속 스킬 소비 계약 문서화 (`references/contracts/`)

`references/contracts/downstream-consumers.md`에 후속 스킬(`arch`, `qa`, `impl`, `security`, `deployment`, `operation`)이 RE 산출물을 어떻게 소비하는지 명시한다:
- 각 후속 스킬이 읽는 메타데이터 필드 목록
- 각 후속 스킬이 요구하는 최소 품질(수용 기준 구체성, 측정 목표치 존재 여부 등)
- `review` 단계의 "후속 스킬 소비 적합성 체크"가 참조하는 체크리스트 원본
- 이 파일은 `SKILL.md` 본문에서 `review` 단계 진입 시 선택적으로 Read하도록 지시

## 핵심 설계 원칙

1. **대화 우선 (Conversation-first)**: 모든 에이전트는 사용자와의 양방향 대화를 기본 상호작용 모델로 채택. 일방적 산출물 생성이 아닌, 질문-확인-정제 사이클을 통해 요구사항을 구체화
2. **능동적 도출 (Active Elicitation)**: 에이전트가 수동적으로 입력을 기다리지 않고, 모호성과 누락을 탐지하여 능동적으로 질문을 생성. 사용자가 고려하지 못한 관점에서도 질문을 제기
3. **적응적 깊이 (Adaptive Depth)**: 간단한 요청에는 경량 프로세스를, 복잡한 프로젝트에는 중량 프로세스를 적용. 입력 복잡도에 따라 질문의 범위와 명세의 형식을 자동 조절
4. **추적성 (Traceability)**: 모든 요구사항에 고유 ID를 부여하고, 이후 단계(설계, 구현, 테스트)와 양방향 추적 가능
5. **검증 가능성**: 각 요구사항은 반드시 검증 가능한 수용 기준을 포함
6. **에이전트 간 연계**: elicit → analyze → spec → review 순서의 파이프라인 지원. 단, 각 단계에서 사용자 피드백 루프를 포함하여 일방향 파이프라인이 아닌 **체크포인트 기반 파이프라인**으로 동작
7. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **요구사항 명세 / 제약 조건 / 품질 속성 우선순위** 세 섹션으로 고정하여, 후속 스킬(`arch`, `impl`, `qa`, `security`, `deployment`, `operation`)이 파싱 없이 직접 소비할 수 있는 계약(contract) 역할을 수행
8. **메타데이터-문서 분리 및 스크립트 매개 상태 관리 (Metadata/Document Separation via Scripted State)**: 산출물은 기계 판독용 메타데이터 파일(YAML)과 사람 판독용 문서 파일(markdown)로 분리 저장. 에이전트는 메타데이터 파일을 직접 편집하지 않고 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 커맨드를 통해서만 `phase`, `progress`, `approval.state` 등을 갱신. 이를 통해 (1) 스키마 일관성과 상태 전이 규칙이 강제되고, (2) 체크포인트 기반 파이프라인의 승인 흐름이 감사 가능한 이력으로 자동 기록되며, (3) 후속 스킬이 구조화된 메타데이터만으로 안정적으로 소비 계약을 이행할 수 있음
9. **Claude Code Skill 표준 준수 (Standard Compliance)**: 필수 진입점은 `SKILL.md`이며, 메타데이터는 YAML frontmatter로 선언한다. 디렉토리 구조는 표준이 명명하는 `scripts/`, `references/`, `assets/`만 사용한다. `$ARGUMENTS`, `${CLAUDE_SKILL_DIR}`, `` !`...` `` 치환과 `context: fork`, `agent: Explore`, `allowed-tools`, `paths`, `hooks` 등 표준 메커니즘을 적극 활용한다. `SKILL.md` 본문은 500줄 이하로 유지하고 상세는 `references/`로 지연 로드한다.
