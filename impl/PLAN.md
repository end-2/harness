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

## 목표 구조

```
impl/
├── skills.yaml
├── agents/
│   ├── generate.md
│   ├── review.md
│   ├── refactor.md
│   └── pattern.md
├── prompts/
│   ├── generate.md
│   ├── review.md
│   ├── refactor.md
│   └── pattern.md
└── examples/
    ├── generate-input.md
    ├── generate-output.md
    ├── review-input.md
    ├── review-output.md
    ├── refactor-input.md
    ├── refactor-output.md
    ├── pattern-input.md
    └── pattern-output.md
```

## 에이전트 내부 흐름

```
Arch 산출물 (4섹션)
    │
    ▼
impl:generate ─────────────────────────────┐
    │  (기존 코드 자동 분석 → 스캐폴딩 →     │
    │   전체 모듈 구현 → 자동 완료)           │
    │                                      │
    ├──→ impl:pattern                      │
    │    (generate 과정에서 식별된            │
    │     패턴을 자동 평가·적용)              │
    │                                      │
    ▼                                      │
impl:review ◄──────────────────────────────┘
    │  (생성된 코드를 Arch 결정 준수 +
    │   클린 코드 원칙 기반으로 자동 리뷰)
    │
    ├── 자동 수정 가능 ──→ impl:refactor
    │   이슈 발견 시        (Arch 경계 내에서
    │                       코드 스멜 자동 제거)
    │                           │
    │                           ▼
    │                      impl:review (재리뷰)
    │
    ├── Arch 결정 실현 불가 ──→ 사용자 에스컬레이션 ⚠️
    │   발견 시
    │
    ▼
최종 산출물 (4섹션) → 사용자에게 결과 보고
```

### 에이전트 호출 규칙

- `generate`는 항상 최초 진입점. Arch 산출물을 수신하여 코드 생성을 시작. 기존 코드베이스 자동 분석 포함
- `pattern`은 `generate` 과정에서 패턴 적용이 유의미한 시점에 자동 호출. 독립적 온디맨드 호출도 가능
- `review`는 `generate` 완료 후 자동 호출. `refactor` 완료 후 재리뷰로도 자동 호출
- `refactor`는 `review`에서 자동 수정 가능한 이슈가 발견된 경우 자동 호출. 독립적 온디맨드 호출도 가능 (기존 코드 개선)
- **전체 파이프라인은 사용자 개입 없이 자동 실행**되며, 사용자 접점은 (1) Arch 결정 실현 불가 시 에스컬레이션과 (2) 최종 결과 보고 두 곳뿐

## 구현 단계

### 1단계: 스킬 메타데이터 정의 (`skills.yaml`)

- 스킬 이름, 버전, 설명
- 에이전트 목록 및 각 에이전트의 역할 정의
- **입력 스키마**: Arch 산출물 4섹션 (`architecture_decisions`, `component_structure`, `technology_stack`, `diagrams`) 소비 계약
- **출력 스키마**: 4섹션 (`implementation_map`, `code_structure`, `implementation_decisions`, `implementation_guide`) 산출물 계약
  - 각 섹션의 필드 정의 및 필수/선택 여부 명시
  - 후속 스킬 연계를 위한 출력 계약(contract) 명세
- **적응적 깊이 설정**: Arch 모드에 따른 경량/중량 모드 기준 및 전환 규칙
- 지원 언어 목록 (TypeScript, Python, Java, Go, Rust 등)
- 코딩 컨벤션 설정 옵션 (사용자 오버라이드 가능)
- **에스컬레이션 조건 정의**: Arch 결정 실현 불가 시 사용자 에스컬레이션 조건 및 판별 기준
- 의존성 정보 (선행: `arch`, RE 간접 참조, 후속 소비자: `qa`, `security`, `deployment`, `operation`, `management`)

### 2단계: 에이전트 시스템 프롬프트 작성 (`agents/`)

#### `generate.md` — 코드 생성 에이전트

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

#### `review.md` — 코드 리뷰 에이전트

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

#### `refactor.md` — 리팩토링 에이전트

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

#### `pattern.md` — 디자인 패턴 에이전트

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

### 3단계: 프롬프트 템플릿 작성 (`prompts/`)

각 에이전트에 대응하는 프롬프트 템플릿을 작성합니다:
- **Arch 산출물 파싱 가이드**: Arch 4섹션에서 코드 생성 지시를 추출하는 방법
- **기존 코드베이스 자동 분석 가이드**: 컨벤션, 디렉토리 구조, 의존성 정책을 코드에서 자동 감지하는 방법
- **에스컬레이션 판별 가이드**: Arch 결정 실현 불가 여부를 판별하는 기준 및 에스컬레이션 메시지 형식
- 언어별 코드 생성 템플릿 (관용구, 컨벤션, 프로젝트 구조)
- 리뷰 체크리스트 기반 프롬프트 (Arch 준수 + 클린 코드 두 축)
- 리팩토링 카탈로그 참조 프롬프트
- 패턴 추천 의사결정 트리 프롬프트
- 출력 형식 지정 (구현 맵, 코드 구조, IDR 형식)
- Chain of Thought 가이드라인
- Few-shot 예시 포함

### 4단계: 입출력 예시 작성 (`examples/`)

각 에이전트별 대표적인 입출력 쌍을 작성합니다:
- **Arch 경량 출력 → Impl 경량 구현** 예시 (간단한 CRUD API 스캐폴딩)
- **Arch 중량 출력 → Impl 중량 구현** 예시 (멀티 모듈 프로젝트 + 인터페이스 계약)
- 기존 코드베이스 자동 분석을 통한 컨벤션 감지 예시
- Arch 결정 준수 기반 자동 리뷰 → 자동 리팩토링 예시
- Strategy 패턴 자동 적용 예시 (Arch 결정 연계 + IDR 기록)
- **구현 맵 + IDR 생성** 예시 (추적성 확인)
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
