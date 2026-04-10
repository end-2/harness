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

## 목표 구조

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
    ├── design-input.md
    ├── design-output.md
    ├── review-input.md
    ├── review-output.md
    ├── adr-input.md
    ├── adr-output.md
    ├── diagram-input.md
    └── diagram-output.md
```

## 에이전트 내부 흐름

```
RE:spec 산출물
    │
    ▼
arch:design ──────────────────────────────┐
    │  (기술적 맥락 대화 → 설계 초안 →     │
    │   사용자 피드백 → 확정)              │
    │                                     │
    ├──→ arch:adr                         │
    │    (design 과정에서 내려진            │
    │     주요 결정을 ADR로 기록)           │
    │                                     │
    ├──→ arch:diagram                     │
    │    (확정된 설계를 시각화)              │
    │                                     │
    ▼                                     │
arch:review ◄─────────────────────────────┘
    (design 출력을 RE 메트릭 기반
     시나리오로 검증)
```

## 구현 단계

### 1단계: 스킬 메타데이터 정의 (`skills.yaml`)

- 스킬 이름, 버전, 설명
- 에이전트 목록 및 역할 정의
- **입력 스키마**: RE `spec` 산출물 3섹션 (`requirements_spec`, `constraints`, `quality_attribute_priorities`) 소비 계약
- **출력 스키마**: 4섹션 (`architecture_decisions`, `component_structure`, `technology_stack`, `diagrams`) 산출물 계약
- **적응적 깊이 설정**: RE 출력 밀도에 따른 경량/중량 모드 기준 및 전환 규칙
- 참조 아키텍처 패턴 카탈로그
- 의존성 정보 (선행: `re`, 후속 소비자: `impl`, `qa`, `security`, `deployment`, `operation`)

### 2단계: 에이전트 시스템 프롬프트 작성 (`agents/`)

#### `design.md` — 아키텍처 설계 에이전트
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

#### `review.md` — 아키텍처 리뷰 에이전트
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

#### `adr.md` — ADR 생성 에이전트
- **역할**: `design` 에이전트가 내린 주요 결정을 Architecture Decision Record로 기록
- **핵심 역량**:
  - Michael Nygard 형식의 ADR 생성
  - **RE 참조 포함**: 각 ADR의 컨텍스트에 근거가 된 RE 산출물 ID를 명시 (예: "NFR-003의 성능 요구사항과 CON-002의 기술 제약에 의해...")
  - `design` 에이전트의 `alternatives_considered`와 `trade_offs`를 ADR의 대안 비교 분석표로 구조화
  - 기존 ADR과의 관계 (supersedes, amends) 관리
- **입력**: `design` 에이전트의 아키텍처 결정 요약 (`architecture_decisions`)
- **출력**: ADR 문서 목록 (상태, 컨텍스트, 결정, 결과, 대안 비교, RE 참조)
- **상호작용 모델**: ADR 초안 제시 → 사용자 확인 → 필요시 보완

#### `diagram.md` — 다이어그램 생성 에이전트
- **역할**: `design` 에이전트의 확정된 설계를 시각화
- **핵심 역량**:
  - C4 모델 (Context, Container) 다이어그램 — 경량 모드에서는 Context만, 중량 모드에서는 Container까지
  - 시퀀스 다이어그램 (주요 흐름)
  - Mermaid 코드 생성
  - 데이터 흐름 다이어그램 (DFD)
- **입력**: `design` 에이전트의 컴포넌트 구조 (`component_structure`) + 기술 스택 (`technology_stack`)
- **출력**: 다이어그램 코드 (Mermaid) 및 설명
- **상호작용 모델**: 다이어그램 초안 제시 → 사용자 피드백 → 수정

### 3단계: 프롬프트 템플릿 작성 (`prompts/`)

- 각 에이전트별 프롬프트 템플릿
- **RE 산출물 파싱 가이드**: RE 3섹션에서 아키텍처 드라이버를 추출하는 방법
- **기술적 맥락 질문 가이드**: 어떤 기술적 맥락이 부족할 때 어떤 질문을 생성할지
- RE 메트릭 → 시나리오 변환 템플릿
- ADR 템플릿 (RE 참조 포함)
- 다이어그램 스타일 가이드

### 4단계: 입출력 예시 작성 (`examples/`)

- RE 경량 출력 → Arch 경량 설계 예시 (간단한 CRUD API)
- RE 중량 출력 → Arch 중량 설계 예시 (분산 시스템)
- 기술적 맥락 대화를 통한 기술 스택 결정 예시
- RE 메트릭 기반 아키텍처 시나리오 검증 예시
- ADR (RE 참조 포함) 예시
- C4 Context/Container 다이어그램 예시

## 핵심 설계 원칙

1. **RE 산출물 기반 (RE-Driven)**: 모든 아키텍처 결정은 RE의 3섹션 산출물에 근거하며, `re_refs`로 추적성을 유지. RE가 확정한 품질 속성 트레이드오프는 재질문하지 않고 전제로 수용
2. **기술적 맥락 대화 (Technical Context Dialogue)**: RE에서 다루지 않는 기술적 맥락(팀 역량, 인프라, 비용)을 사용자와의 대화로 파악하여 설계 결정에 반영
3. **적응적 깊이 (Adaptive Depth)**: RE 출력 밀도에 연동하여 경량(스타일 + 가이드)/중량(컴포넌트 + 다이어그램 + ADR) 모드 자동 전환
4. **의사결정 추적**: 모든 주요 결정은 ADR로 기록하고, RE 산출물 ID를 참조하여 "왜 이 결정을 했는가"를 RE까지 추적 가능
5. **시나리오 기반 검증**: RE의 `quality_attributes.metric`을 시나리오로 변환하여 설계 적합성을 검증. 전통적 ATAM의 축소 적용
6. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **아키텍처 결정 / 컴포넌트 구조 / 기술 스택 / 다이어그램** 4섹션으로 고정하여, 후속 스킬(`impl`, `qa`, `security`, `deployment`, `operation`)이 직접 소비할 수 있는 계약(contract) 역할을 수행
