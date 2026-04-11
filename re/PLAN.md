# RE (Requirements Engineering) Skill 구현 계획

## 개요

사용자와의 **대화형 상호작용**을 통해 모호한 요청을 구조화된 요구사항으로 점진적으로 도출·분석·명세·검증하는 스킬입니다. Harness 파이프라인의 최상위 진입점으로서, 후속 스킬(`arch`, `impl`, `qa`, `security`, `deployment`, `operation`)이 직접 소비할 수 있는 3섹션 산출물(요구사항 명세, 제약 조건, 품질 속성 우선순위)을 생성합니다.

전통적 RE가 다수의 이해관계자, 회의록, 인터뷰 결과 등 풍부한 입력을 전제로 했다면, AI 컨텍스트의 RE는 **프롬프트를 입력하는 한 명의 사용자**가 핵심 이해관계자입니다. 사용자 입력은 대부분 불완전하고 모호하며, 사용자 자신도 원하는 바를 명확히 모르는 경우가 많습니다. 따라서 이 스킬은 **능동적으로 질문하고 multi-turn 대화로 요구사항을 구체화**하는 것을 핵심 설계 원칙으로 합니다.

### 전통적 RE vs AI 컨텍스트 RE

| 구분 | 전통적 RE | AI 컨텍스트 RE |
|------|-----------|----------------|
| 이해관계자 | 다수 (고객, 사용자, 개발팀, PM 등) | 프롬프트를 입력하는 한 명의 사용자 |
| 입력 수준 | 회의록, 인터뷰, RFP 등 풍부한 입력 | 자연어 한두 문장 수준의 모호한 입력 |
| 정보 흐름 | 분석가가 이해관계자로부터 수집 | **스킬이 사용자로부터 능동적으로 유도** |
| 프로세스 | 단계별 순차 진행 (waterfall 경향) | **대화 기반 반복적 구체화 (iterative)** |
| 산출물 수준 | 항상 무거운 SRS | **입력 복잡도에 따라 경량/중량 적응** |
| 핵심 역량 | 이해관계자 간 충돌 조정 | **모호성 탐지 + 능동적 질문 생성** |
| 주기 | 프로젝트 초기 집중 | **사용자 피드백마다 수시 갱신** |

## 사용자 입력 수집 방식

RE 스킬은 Harness 파이프라인의 **최상위 진입점**이므로 소비할 상위 스킬 산출물이 존재하지 않습니다. 대신 사용자의 초기 프롬프트(`$ARGUMENTS`)를 시작점으로 삼아, 대화 기반으로 3섹션 산출물을 점진적으로 구축합니다.

| 입력 출처 | 형태 | 처리 방법 |
|-----------|------|----------|
| 사용자 초기 요청 | 자연어 한 줄 ~ 상세 RFP | `$ARGUMENTS`로 본문에 주입하여 elicit 단계 진입 시 1차 분석 대상 |
| 대화 턴 응답 | 사용자 회신 (확인/부정/선택) | 모호성·누락·가정을 식별하여 차턴 질문 생성 |
| 명시적 선택 | 트레이드오프 선택지에 대한 사용자 결정 | 품질 속성 우선순위·제약 조건의 `flexibility` 확정 근거로 사용 |
| 기존 산출물 재검토 | 갱신 요청 | `scripts/artifact.py show`로 현재 상태를 읽어 변경 지점 파악 |

elicit 단계는 한 번의 질문으로 끝나는 것이 아니라, 사용자가 "충분하다"고 판단할 때까지 multi-turn으로 지속됩니다. 각 턴에서 이미 확인된 사항 vs 미확인 사항을 추적하여 중복 질문을 방지합니다.

## 적응적 깊이

사용자 입력의 복잡도와 elicit 결과에 따라 산출물 수준을 자동 조절합니다.

| 입력 복잡도 | 판별 기준 | RE 모드 | 산출물 수준 |
|------------|-----------|---------|------------|
| 경량 | FR ≤ 5개, NFR ≤ 2개, 품질 속성 ≤ 3개 | 경량 | User Story + Acceptance Criteria 중심의 간결한 명세 |
| 중량 | FR > 5개 또는 NFR > 2개 또는 품질 속성 > 3개 | 중량 | IEEE 830 / ISO 29148 기반 SRS, 트레이드오프 분석 보고서, 추적성 매트릭스 포함 |

모드는 elicit 종료 시점에 자동 판별되며, 사용자가 명시적으로 재지정할 수도 있습니다. 경량 모드에서는 analyze 단계의 일부(트레이드오프 매트릭스 등)를 생략할 수 있습니다.

## 최종 산출물 구조

RE 스킬의 최종 산출물은 다음 **세 가지 섹션**으로 구성됩니다. High-level 요구사항 확정까지를 범위로 하며, 아키텍처 결정이나 구현 상세는 포함하지 않습니다.

### 1. 요구사항 명세 (Requirements Specification)

기능 요구사항(FR)과 비기능 요구사항(NFR)을 구조화한 명세입니다.

| 필드 | 설명 |
|------|------|
| `id` | 고유 식별자 (예: `FR-001`, `NFR-001`) |
| `category` | 분류 (기능/비기능, 하위 카테고리) |
| `title` | 요구사항 제목 |
| `description` | 상세 설명 |
| `priority` | MoSCoW (`Must` / `Should` / `Could` / `Won't`) |
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

### 산출물 파일 구성: 메타데이터 + 문서 분리

위 3섹션의 산출물은 **메타데이터 파일과 문서 markdown 파일을 분리**하여 저장합니다. 메타데이터는 구조화된 상태·추적 정보를 담고, markdown은 사람이 읽을 서술형 본문을 담습니다.

| 파일 유형 | 형식 | 역할 |
|----------|------|------|
| 메타데이터 파일 | **YAML** (`*.meta.yaml`) | 진행 상태, 승인 상태, 추적성(refs), 3섹션의 구조화 필드 저장. 스크립트가 읽고 쓰는 단일 진실 공급원(SSoT) |
| 문서 파일 | Markdown (`*.md`) | 요구사항 서술, 제약 조건 근거, 품질 속성 트레이드오프 설명, 대화 맥락 본문 |

**YAML을 채택한 이유**:

- **주석 지원**: 결정 근거나 임시 메모를 인라인 주석으로 남길 수 있어 사람이 작성·편집 시 맥락 전달이 용이합니다.
- **사람이 읽기 쉬움**: 들여쓰기 기반 구조로 JSON 대비 시각적 가독성이 높습니다 — RE 산출물처럼 사용자가 직접 검토하는 문서에 적합합니다.
- **스크립트 파싱 용이**: PyYAML 등 표준 라이브러리로 손쉽게 로드·덤프 가능하며, 키 순서 보존도 지원합니다.

### 메타데이터 스키마 (공통 필드)

각 산출물 메타데이터 파일은 3섹션의 구조화 필드 외에 다음 공통 필드를 포함합니다.

| 필드 | 설명 |
|------|------|
| `artifact_id` | 산출물 고유 식별자 (예: `RE-requirements-001`) |
| `phase` | 현재 단계 (`draft` / `in_review` / `revising` / `approved` / `superseded`) |
| `progress` | 진행률 정보 (`section_completed`, `section_total`, `percent`) |
| `approval.state` | 승인 상태 (`pending` / `approved` / `rejected` / `changes_requested`) |
| `approval.approver` | 승인자 식별자 (사용자명/역할) |
| `approval.approved_at` | 승인 시각 (ISO 8601) |
| `approval.notes` | 승인/반려 코멘트 |
| `upstream_refs` | 상위 근거 참조 (사용자 발화, 이전 산출물 ID 등). RE는 파이프라인 최상위이므로 통상 사용자 프롬프트 ID만 기록 |
| `downstream_refs` | 이 산출물을 소비하는 후속 산출물 ID 목록 (`arch`, `impl`, `qa`, `security`, `deployment`, `operation` 등) |
| `document_path` | 짝을 이루는 markdown 문서의 상대 경로 |
| `updated_at` | 최종 수정 시각 |

RE의 **체크포인트 기반 파이프라인**(사용자 피드백 루프)은 이 `approval.state`의 상태 전이와 자연스럽게 대응됩니다. `elicit` 단계에서 `draft`로 생성되고, `analyze`/`spec`을 거치며 `in_review`로 전이되며, 사용자 피드백에 따라 `changes_requested` ↔ `in_review`를 오가다가 최종적으로 `approved`에 도달하면 후속 스킬이 소비 가능한 상태가 됩니다.

### 스크립트 기반 메타데이터 조작 (필수)

스킬은 **YAML 메타데이터 파일을 직접 편집하지 않습니다**. 모든 상태 갱신은 `scripts/` 디렉토리의 스크립트 커맨드를 통해서만 수행하며, 이는 다음을 보장합니다.

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

markdown 문서 또한 자유 양식이 아니라, `assets/templates/` 디렉토리에 3섹션별 템플릿을 사전에 정의합니다. `scripts/artifact.py init` 실행 시 해당 템플릿이 복사되어 **섹션 헤더, 플레이스홀더, 안내 주석이 채워진 골격**이 생성되며, 스킬은 이 골격 안의 플레이스홀더를 채우는 방식으로 본문을 작성합니다.

| 템플릿 파일 | 대상 섹션 |
|------------|----------|
| `assets/templates/requirements.md.tmpl` | 요구사항 명세 (FR/NFR 표, 수용 기준 섹션) |
| `assets/templates/constraints.md.tmpl` | 제약 조건 (유형별 분류, 근거, 유연성 섹션) |
| `assets/templates/quality-attributes.md.tmpl` | 품질 속성 우선순위 (우선순위 표, 트레이드오프 섹션) |
| `assets/templates/*.meta.yaml.tmpl` | 각 섹션 메타데이터의 초기 골격 |

이 방식은 (1) 워크플로우 단계 간 출력 형식을 균일하게 유지하고, (2) 필수 섹션 누락을 방지하며, (3) 후속 스킬이 기대하는 구조를 보장합니다.

### 후속 스킬 연계

```
re 산출물 구조:
┌─────────────────────────────────────────┐
│  요구사항 명세 (Requirements Spec)       │──→ arch:design (FR/NFR → 컴포넌트·드라이버)
│  - FR-001, FR-002, ...                  │──→ qa:strategy (테스트 대상 도출)
│  - NFR-001, NFR-002, ...                │──→ impl:generate (기능 구현 범위)
│                                         │──→ management:plan (범위 결정)
├─────────────────────────────────────────┤
│  제약 조건 (Constraints)                 │──→ arch:design (hard 제약 = 비협상 드라이버)
│  - CON-001: technical                   │──→ impl:generate (구현 제약)
│  - CON-002: business                    │──→ deployment:strategy (배포 제약)
│  - CON-003: regulatory                  │──→ security:threat-model (규제 요구)
├─────────────────────────────────────────┤
│  품질 속성 우선순위 (QA Priorities)       │──→ arch:design (아키텍처 드라이버)
│  - 1. performance                       │──→ security:threat-model (보안 우선순위)
│  - 2. security                          │──→ operation:slo (SLO 기준)
│  - 3. scalability                       │──→ qa:strategy (NFR 테스트 기준)
└─────────────────────────────────────────┘
```

## 목표 구조 (Claude Code Skill 표준 준수)

본 스킬은 Claude Code Skill 공식 표준(https://code.claude.com/docs/ko/skills)을 따릅니다. 단일 진입점은 `re/SKILL.md` 이며, `skills.yaml`, `agents/`, `prompts/` 디렉토리는 사용하지 않습니다. 상세 행동 규칙과 단계별 가이드는 `references/`에, 템플릿은 `assets/`에 분리합니다.

```
re/
├── SKILL.md                              # 필수 진입점 (YAML frontmatter + 4단계 워크플로우 요약, 500줄 이내)
├── scripts/
│   └── artifact.py                       # 메타데이터 init/set-phase/set-progress/approve/link/show/validate
├── assets/
│   └── templates/
│       ├── requirements.md.tmpl
│       ├── requirements.meta.yaml.tmpl
│       ├── constraints.md.tmpl
│       ├── constraints.meta.yaml.tmpl
│       ├── quality-attributes.md.tmpl
│       └── quality-attributes.meta.yaml.tmpl
└── references/
    ├── workflow/
    │   ├── elicit.md                     # 도출 단계 상세 행동 규칙 (on-demand 로드)
    │   ├── analyze.md                    # 분석 단계 상세 행동 규칙
    │   ├── spec.md                       # 명세 단계 상세 행동 규칙
    │   └── review.md                     # 리뷰 단계 상세 행동 규칙
    ├── contracts/
    │   └── downstream-contract.md        # arch/impl/qa/security/deployment/operation 소비 계약
    ├── schemas/
    │   ├── meta-schema.md                # 메타데이터 공통 필드 설명
    │   └── section-schemas.md            # 3섹션 필드 명세
    ├── adaptive-depth.md                 # 경량/중량 분기 규칙
    └── examples/
        ├── light/
        │   ├── elicit-conversation.md
        │   ├── spec-output.md
        │   └── spec-output.meta.yaml
        └── heavy/
            ├── elicit-conversation.md
            ├── analyze-tradeoffs.md
            ├── spec-output.md
            ├── spec-output.meta.yaml
            └── review-report.md
```

요점:
- `SKILL.md`가 유일한 필수 진입점이며, 4개의 워크플로우 단계(elicit/analyze/spec/review)는 **동일 SKILL.md 안에 짧게 요약**하고, 상세 규칙은 `references/workflow/*.md`로 분리하여 **on-demand 로드**합니다.
- `templates/` 대신 표준 명칭인 `assets/templates/`, `examples/` 대신 `references/examples/`를 사용합니다.
- `skills.yaml`, `agents/`, `prompts/`는 폐기합니다.

## 워크플로우 단계 (SKILL.md 내부 단일 진입점)

표준 스킬 모델을 따르기 위해, 기존에 "4개의 내부 에이전트"로 구상했던 elicit/analyze/spec/review는 **별도의 시스템 프롬프트 파일이 아니라**, SKILL.md가 순차적으로 수행하는 **4개의 워크플로우 단계**로 재정의합니다. 각 단계의 상세 행동 규칙은 `references/workflow/*.md`에 분리되어 필요 시점에 Read로 로드됩니다.

```
사용자 초기 요청 ($ARGUMENTS)
    │
    ▼
[Stage 1] elicit ───────────────────────────┐
    │  references/workflow/elicit.md 로드    │
    │  (모호성 탐지 → 능동적 질문 →           │
    │   multi-turn 구체화 → 후보 도출)        │
    │                                        │
    ▼                                        │
[Stage 2] analyze ──────────────────────────┤
    │  references/workflow/analyze.md 로드   │
    │  (충돌·누락·실현성 분석 →               │
    │   트레이드오프 제시 → 사용자 선택)      │
    │                                        │
    ▼                                        │
[Stage 3] spec ─────────────────────────────┤
    │  references/workflow/spec.md 로드      │
    │  (3섹션 구조화 → 초안 제시 →            │
    │   피드백 → 수정 → 확정)                 │
    │                                        │
    ▼                                        │
[Stage 4] review ◄──────────────────────────┘
    references/workflow/review.md 로드
    (3섹션 검증 + 후속 스킬 소비 적합성
     체크 → 사용자 최종 승인)
```

### `references/workflow/elicit.md` — 도출 단계 상세 규칙

- **역할**: 사용자와의 대화를 통해 모호한 요구를 구조화된 요구사항 후보로 점진적으로 도출
- **핵심 역량**:
  - **모호성 탐지 및 질문 생성**: 사용자 입력에서 모호한 부분, 누락된 정보, 암묵적 가정을 식별하고 targeted question 생성
  - **적응적 질문 전략**: 입력의 구체성 수준에 따라 질문 깊이와 범위를 자동 조절
    - 고수준 입력("쇼핑몰 만들어줘") → 넓은 범위의 탐색적 질문
    - 중간 수준("OAuth2 기반 로그인 구현") → 세부 사항 확인 질문
    - 상세 입력(구체적 스펙 포함) → 경계 조건/예외 확인 질문
  - **점진적 구체화**: 대화 턴마다 요구사항의 구체성 수준을 높여가는 반복적 정제
  - **대화 상태 관리**: 이미 확인된 사항 vs 미확인 사항을 추적하여 중복 질문 방지
  - **확인과 요약**: 주기적으로 "지금까지 이해한 바"를 사용자에게 제시하고 확인 요청
  - **이해관계자 역할 대행**: 사용자가 고려하지 못한 관점(최종 사용자, 운영자, 보안 담당자 등)에서 질문 제기
- **입력**: 사용자의 자연어 요청 (`$ARGUMENTS`, 한 문장부터 상세 RFP까지)
- **출력**:
  - 구조화된 요구사항 후보 목록 (ID, 분류, 우선순위, 수용 기준)
  - 식별된 제약 조건 후보 (기술적/비즈니스/규제/환경)
  - 품질 속성 후보 및 사용자가 언급한 우선순위 힌트
  - 미해결 질문 목록
- **상호작용 모델**: multi-turn 대화 (사용자가 충분하다고 판단할 때까지)

### `references/workflow/analyze.md` — 분석 단계 상세 규칙

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
  - 품질 속성 간 트레이드오프 분석
  - **사용자 의사결정이 필요한 질문 목록**
- **상호작용 모델**: 분석 결과 제시 → 사용자 확인/선택 (특히 품질 속성 트레이드오프) → 요구사항 수정 반영

### `references/workflow/spec.md` — 명세 단계 상세 규칙

- **역할**: 분석된 요구사항을 후속 스킬이 직접 소비할 수 있는 **세 가지 섹션**(요구사항 명세, 제약 조건, 품질 속성 우선순위)으로 구조화
- **핵심 역량**:
  - **적응적 명세 수준**:
    - 경량 모드: User Story + Acceptance Criteria (간단한 기능/단일 요청)
    - 중량 모드: IEEE 830 / ISO 29148 기반 SRS (복잡한 시스템/다수 요구사항)
    - 모드 자동 판별 또는 사용자 선택
  - **요구사항 명세 생성**: FR/NFR을 ID 체계 기반으로 구조화하고 수용 기준 명세
  - **제약 조건 도출**: 분석 결과에서 기술적/비즈니스/규제/환경 제약을 식별하고 유연성(`hard`/`soft`/`negotiable`) 분류
  - **품질 속성 우선순위 결정**: 대화를 통해 트레이드오프를 명확히 하고, 측정 가능한 목표치와 함께 우선순위 확정
  - **초안 제시 → 피드백 → 수정 사이클**: 세 섹션 각각에 대해 초안을 사용자에게 보여주고, 피드백을 받아 수정하는 반복 과정
- **입력**: 분석 완료된 요구사항 목록 + 사용자 의사결정 결과
- **출력**: 3섹션(요구사항 명세 / 제약 조건 / 품질 속성 우선순위)으로 구성된 명세 문서 쌍(markdown + meta.yaml)
- **상호작용 모델**: 초안 제시 → 사용자 피드백 (특히 품질 속성 트레이드오프 확인) → 수정 → 최종 확인

### `references/workflow/review.md` — 리뷰 단계 상세 규칙

- **역할**: 세 섹션으로 구성된 명세 문서를 리뷰하고, 후속 스킬 소비 적합성을 검증
- **핵심 역량**:
  - **요구사항 명세 검증**: SMART 기준 검증, 모호성·불완전성·비검증성 탐지, FR-NFR 간 추적성 확인
  - **제약 조건 검증**: 제약 간 상호 모순 탐지, 요구사항과의 정합성 확인, 누락된 제약 식별
  - **품질 속성 우선순위 검증**: 측정 목표치의 구체성 확인, 트레이드오프 설명의 충분성 확인, 요구사항·제약과의 일관성 검증
  - **후속 스킬 소비 적합성 체크**: `arch`가 아키텍처 드라이버로 사용하기에 충분한 정보인지, `qa`가 테스트 전략을 도출하기에 충분한 수용 기준이 있는지 등
  - 추적성 매트릭스 검증 (요구사항 ↔ 제약 조건 ↔ 품질 속성 간 상호 참조)
  - **사용자 의사결정 필요 사항 하이라이트**: 독단적으로 판단할 수 없는 이슈를 사용자에게 에스컬레이션
- **입력**: 3섹션으로 구성된 명세 문서 (spec 단계 산출물)
- **출력**: 섹션별 리뷰 리포트 (이슈 목록, 심각도, 개선 제안, 후속 스킬 소비 적합성 판정) + **사용자 확인 필요 사항**
- **상호작용 모델**: 리뷰 결과 제시 → 사용자 확인·반영 → 최종 승인(`approve`)

## 구현 단계

### 1단계: `SKILL.md` 작성 (필수 진입점 + frontmatter)

표준에서 메타데이터의 단일 출처는 `re/SKILL.md`의 YAML frontmatter입니다. `skills.yaml`은 표준 사양에 존재하지 않으므로 사용하지 않습니다. Claude Code Skill 표준에 따라 frontmatter는 `name`과 `description`만 필수로 두고, 나머지 옵션 필드는 기본 동작으로 스킬 목적을 달성할 수 없음이 입증된 경우에만 추가합니다.

**권장 frontmatter 초안**:

```yaml
---
name: re
description: 사용자와의 대화형 상호작용을 통해 모호한 요청을 기능/비기능 요구사항, 제약 조건, 품질 속성 우선순위 세 섹션으로 점진적으로 도출·분석·명세·검증하고, scripts/artifact.py로 메타데이터·추적성을 관리한다. 신규 프로젝트 착수, 요구사항 재정비, arch/qa/impl 후속 스킬 투입 직전에 사용.
---
```

**설계 원칙**:

- **`name`**: 스킬 디렉토리명과 일치시켜 `re`로 고정합니다. 표준에서 요구하는 두 필수 필드 중 하나입니다.
- **`description` 작성 규칙 (자동 호출 품질 결정)**: 첫 200자 안에 반드시 다음 두 요소를 포함합니다.
  - *무엇을 하는가*: "모호한 요청 → 3섹션 산출물 도출·분석·명세·검증"
  - *언제 사용하는가*: "신규 프로젝트 착수 / 요구사항 재정비 / arch·qa·impl 후속 스킬 투입 직전"
  - 250자 경계에서 잘릴 수 있음을 가정하여 핵심 키워드를 앞에 배치합니다.
- **그 외 옵션 필드(`argument-hint`, `allowed-tools`, `effort`, `model`, `disable-model-invocation`, `paths`, `hooks`, `context`, `agent` 등)는 기본값으로 두고 추가하지 않습니다.** 표준 동작으로 스킬이 동작 불가능하다는 점이 실제로 입증된 경우에만 해당 필드를 도입하고, 그 근거를 PLAN/SKILL 본문에 명시합니다.

**SKILL.md 본문 구성 (500줄 이내)**:

1. 스킬 개요 (사용자 요청 → 3섹션 산출물)
2. 입력/출력 계약 요약 (상세는 `references/contracts/*.md`로 분리)
3. 적응적 깊이 분기 로직 (입력 복잡도 판별 → 경량/중량 모드 결정)
4. 4단계 워크플로우 요약 (elicit → analyze → spec → review)
   - 각 단계는 **상세 규칙을 `references/workflow/<stage>.md`에서 로드**하도록 명시
   - 예: "analyze 진입 시 `${CLAUDE_SKILL_DIR}/references/workflow/analyze.md`를 Read로 로드한 뒤 지시를 따른다"
5. 스크립트 호출 규약: 모든 메타데이터 조작은 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 를 통해서만 수행
6. 시작 시 현재 상태 주입: SKILL.md 상단에서 `` !`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate` ``를 사용해 현재 산출물 상태를 동적 컨텍스트로 주입
7. 후속 스킬 의존성 정보(`arch`/`impl`/`qa`/`security`/`deployment`/`operation`)는 frontmatter가 아니라 본문 또는 `references/contracts/downstream-contract.md`에 기술

**치환자 활용**:

- 모든 스크립트 경로는 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 로 작성하여 사용자 호출 위치에 관계없이 동작하도록 합니다.
- 사용자 초기 요청은 `$ARGUMENTS`로 받아 elicit 단계의 시작점으로 사용합니다.

**문서 길이 관리**:

- `SKILL.md`는 500줄 이내를 유지합니다.
- 초과 위험이 있는 상세 내용은 모두 `references/` 하위로 분리하고, SKILL.md는 "언제 어떤 reference를 로드할지"만 명시합니다.

### 2단계: 워크플로우 단계별 상세 규칙 분리 (`references/workflow/`)

기존 PLAN의 "4개 내부 에이전트" 개념은 표준 스킬 모델과 직접 매핑되지 않습니다. 대신 각 단계의 상세 행동 규칙을 `references/workflow/`에 markdown 파일로 분리하고, SKILL.md가 단계 진입 시 on-demand로 Read합니다. 이는 별도의 시스템 프롬프트 파일이나 서브스킬 분할 없이, 단일 진입점을 유지하면서 단계별 로직을 캡슐화하는 표준 호환 방식입니다.

각 workflow 파일에는 해당 단계의 **역할, 핵심 역량, 입력/출력, 상호작용 모델, 질문 생성 가이드라인, 대화 상태 추적 템플릿, 스크립트 호출 시점, CoT 가이드, few-shot 예시 참조**를 담습니다. 500줄을 초과하면 few-shot을 `references/examples/`로 분리합니다.

### 3단계: 참조 문서 작성 (`references/`)

프롬프트 템플릿을 별도 `prompts/` 디렉토리로 분리하던 기존 계획은 폐기하고, 모든 가이드 문서를 표준 `references/` 디렉토리로 통합합니다. SKILL.md가 필요한 시점에 해당 파일을 Read합니다.

- `references/workflow/*.md` (4개): 단계별 상세 행동 규칙 — 2단계에서 작성
- `references/contracts/downstream-contract.md`: 후속 스킬(`arch`, `impl`, `qa`, `security`, `deployment`, `operation`) 소비 계약 — 각 스킬이 읽는 메타데이터 필드 목록과 최소 품질 기준(수용 기준 구체성, 측정 목표치 존재 여부 등)
- `references/schemas/meta-schema.md`: 메타데이터 공통 필드(`artifact_id`, `phase`, `approval`, `upstream_refs`, `downstream_refs` 등) 명세
- `references/schemas/section-schemas.md`: 3섹션(`requirements`, `constraints`, `quality-attributes`) 필드 명세
- `references/adaptive-depth.md`: 경량/중량 모드 판별 규칙과 모드별 스킵 단계 정의

**스크립트 호출 규약 배치**: "스킬이 YAML을 직접 편집하지 않고 `scripts/artifact.py` 커맨드만 호출한다"는 행동 규약은 `references/workflow/*.md`에 반복 명시하고, 각 단계(초안 → 리뷰 → 승인)에서 어떤 커맨드를 어떤 순서로 호출해야 하는지 시퀀스로 기술합니다.

### 4단계: 문서 템플릿 작성 (`assets/templates/`)

표준 디렉토리 명칭은 `assets/`입니다(기존 `templates/`는 폐기).

- 3섹션(`requirements`, `constraints`, `quality-attributes`)별 markdown 템플릿(`*.md.tmpl`)을 `assets/templates/`에 작성. 각 템플릿은 섹션 헤더, 표 골격, 플레이스홀더, HTML 주석 형태의 안내문을 포함하여 플레이스홀더만 채우도록 유도
- 각 섹션의 메타데이터 초기 골격(`*.meta.yaml.tmpl`)을 작성. `phase: draft`, `approval.state: pending`, 빈 `upstream_refs`/`downstream_refs` 등 기본값을 포함
- `requirements.md.tmpl`은 FR/NFR 분리 표 슬롯, `constraints.md.tmpl`은 유형별 분류 섹션, `quality-attributes.md.tmpl`은 우선순위 표와 트레이드오프 서술 슬롯을 포함

**적응적 깊이 → 내부 분기**:

- 하나의 스킬 안에서 경량/중량 모드를 내부 분기로 처리하며, 스킬 자체를 `re-light`/`re-full`로 분할하지 않습니다(단일 진입점 유지). SKILL.md 본문의 분기 로직이 `references/adaptive-depth.md`의 판별 기준에 따라 경량 조건이면 analyze의 일부 단계를 스킵합니다.

### 5단계: 메타데이터 조작 스크립트 구현 (`scripts/`)

- `scripts/artifact.py` 를 단일 진입점으로 구현하며, 다음 서브커맨드를 제공:
  - `init` — `assets/templates/`에서 템플릿을 복사해 메타데이터 + markdown 쌍을 생성. 템플릿 경로는 `${CLAUDE_SKILL_DIR}/assets/templates/`를 기준으로 해석
  - `set-phase`, `set-progress` — 진행 상태·진행률 갱신
  - `approve` — 승인 상태 전이 (전이 규칙 검증 포함)
  - `link` — `upstream_refs`/`downstream_refs` 추가 및 양방향 무결성 유지
  - `show`, `validate` — 조회 및 스키마·추적성 검증
- 모든 쓰기 커맨드는 `updated_at`을 자동 갱신하고, 잘못된 상태 전이·누락 필드를 차단하며, `approval.history`에 타임스탬프와 함께 자동 기록

**스크립트 호출 강제 (다층 방어)**:

행동 규약만으로는 우회될 수 있으므로 다층 방어를 구성합니다.

1. **행동 규약 (가장 약함)**: `references/workflow/*.md` 및 SKILL.md 본문에서 "메타데이터 갱신은 반드시 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 를 호출한다"를 반복 명시
2. **도구 권한 (중간)**: frontmatter `allowed-tools` 설계 시 `*.meta.yaml` 파일에 대한 직접 편집을 최소화하기 위해, Edit/Write가 필요한 대상은 markdown 본문으로 한정하도록 워크플로우 가이드에서 명시. (도구 단위 화이트리스트만 표준에 존재하므로, 파일 단위 차단은 아래 hooks로 보완)
3. **PreToolUse hooks (가장 강함)**: 가능하다면 `*.meta.yaml`에 대한 Edit/Write 시도를 차단하는 PreToolUse hook을 등록하여, 행동 규약을 우회한 직접 편집을 원천 차단
4. **시작 시 상태 주입**: SKILL.md 상단에서 `` !`python ${CLAUDE_SKILL_DIR}/scripts/artifact.py validate` ``를 사용해 현재 산출물 상태·추적성 무결성을 동적으로 주입. 이를 통해 스킬이 자연스럽게 스크립트 기반 흐름을 따르도록 유도

### 6단계: 입출력 예시 작성 (`references/examples/`)

- **다양한 입력 구체성 수준**: 모호한 한 줄 요청부터 상세한 RFP까지
- **multi-turn 대화 예시**: 질문 → 사용자 응답 → 추가 질문 → 구체화 과정 (`elicit-conversation.md`)
- 다양한 도메인 커버 (웹앱, 모바일앱, API, 데이터 파이프라인)
- 경량/중량 모드 분기 예시 (`light/`, `heavy/` 하위 디렉토리)
- 엣지 케이스 포함
- **메타데이터 + 문서 쌍 예시**: 각 산출물 예시는 markdown 본문(`*-output.md`)과 대응 메타데이터(`*-output.meta.yaml`)를 함께 포함하여, `phase`, `approval`, `upstream_refs`/`downstream_refs` 가 채워진 실제 모습을 보여줄 것
- **스크립트 커맨드 사용 흐름 예시**: `init` → `set-phase` → `approve`로 이어지는 상태 전이 시퀀스를 예시화

## 핵심 설계 원칙

1. **사용자 대화 기반 (Dialogue-Driven)**: 모든 단계는 사용자와의 양방향 대화를 기본 상호작용 모델로 채택합니다. 일방적 산출물 생성이 아닌, 질문-확인-정제 사이클을 통해 요구사항을 구체화하며, 수동적으로 입력을 기다리지 않고 모호성·누락을 탐지하여 능동적으로 질문을 생성합니다.
2. **적응적 깊이 (Adaptive Depth)**: 입력 복잡도에 따라 경량(User Story + Acceptance Criteria)/중량(IEEE 830 / ISO 29148 SRS) 모드를 자동 전환합니다. 질문의 범위와 명세의 형식을 자동 조절하여 간단한 요청에는 경량, 복잡한 프로젝트에는 중량 프로세스를 적용합니다.
3. **3섹션 산출물 표준화 (Standardized Output)**: 최종 산출물을 **요구사항 명세 / 제약 조건 / 품질 속성 우선순위** 세 섹션으로 고정하여, 후속 스킬(`arch`, `impl`, `qa`, `security`, `deployment`, `operation`)이 자연어 파싱 없이 직접 소비 가능한 계약(contract) 역할을 수행합니다.
4. **점진적 정제 (Iterative Refinement)**: elicit → analyze → spec → review 순서의 파이프라인을 지원하되, 각 단계에서 사용자 피드백 루프를 포함하여 일방향 파이프라인이 아닌 **체크포인트 기반 파이프라인**으로 동작합니다. 필요 시 이전 단계로 되돌아가 재정제할 수 있습니다.
5. **검증 가능성 (Verifiability)**: 각 요구사항은 반드시 검증 가능한 수용 기준을 포함하며, 품질 속성은 측정 가능한 목표치(예: "응답시간 < 200ms")를 갖습니다. review 단계에서 SMART 기준과 후속 스킬 소비 적합성을 검증합니다.
6. **추적성 기반 소비 계약 (Traceability Contract)**: 모든 요구사항·제약·품질 속성에 고유 ID를 부여하고, `upstream_refs`로 사용자 발화 근거를, `downstream_refs`로 후속 스킬 참조를 기록합니다. 후속 스킬은 자신의 결정 근거를 RE의 ID까지 양방향으로 추적할 수 있습니다.
7. **메타데이터-문서 분리 및 스크립트 경유 원칙 (Metadata/Document Separation via Scripts)**: 산출물은 YAML 메타데이터 파일과 markdown 문서 파일을 분리하여 관리하고, 메타데이터(진행 상태·승인 상태·추적성 ref)는 스킬이 직접 편집하지 않고 오직 `${CLAUDE_SKILL_DIR}/scripts/artifact.py` 커맨드를 통해서만 갱신합니다. markdown 본문은 `assets/templates/`의 사전 정의 템플릿으로 골격을 생성한 뒤 플레이스홀더를 채움으로써, 상태 일관성과 서식 표준을 동시에 보장합니다.
