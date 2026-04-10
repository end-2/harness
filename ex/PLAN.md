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

## 목표 구조

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
    ├── scan-input.md
    ├── scan-output.md
    ├── detect-input.md
    ├── detect-output.md
    ├── analyze-input.md
    ├── analyze-output.md
    ├── map-input.md
    └── map-output.md
```

## 에이전트 내부 흐름

```
프로젝트 루트 경로
    │
    ▼
ex:scan ───────────────────────────────────┐
    │  (디렉토리 구조 스캔 →                  │
    │   파일 분류 → 진입점 식별 →             │
    │   복잡도 판별 → 경량/중량 모드 결정)     │
    │                                      │
    ▼                                      │
ex:detect                                  │
    │  (매니페스트 파일 분석 →                 │
    │   언어/프레임워크/도구 탐지 →            │
    │   버전 및 설정 위치 매핑)                │
    │                                      │
    ▼                                      │
ex:analyze                                 │
    │  (import/require 분석 →               │
    │   모듈 의존성 그래프 구축 →              │
    │   컴포넌트 경계 추론 →                  │
    │   API 표면 식별 →                     │
    │   아키텍처 스타일 추론)                  │
    │                                      │
    ▼                                      │
ex:map ◄───────────────────────────────────┘
    (scan + detect + analyze 결과를
     LLM 토큰 효율 최적화하여
     4섹션 최종 산출물로 통합)
```

### 에이전트 호출 규칙

- `scan`은 항상 최초 진입점. 프로젝트 루트 경로를 수신하여 구조 스캔 시작. 적응적 깊이 모드를 결정
- `detect`는 `scan` 완료 후 자동 호출. scan이 수집한 파일 목록을 기반으로 기술 스택 탐지
- `analyze`는 `detect` 완료 후 자동 호출. scan의 구조 + detect의 기술 정보를 기반으로 의존성/아키텍처 분석. 경량 모드에서는 간략 분석만 수행
- `map`은 `analyze` 완료 후 자동 호출. 세 에이전트의 결과를 토큰 효율적 최종 산출물로 통합
- **전체 파이프라인은 사용자 개입 없이 자동 실행**되며, 사용자 접점은 (1) 분석 불가 상황 에스컬레이션과 (2) 최종 결과 보고 두 곳뿐

## 구현 단계

### 1단계: 스킬 메타데이터 정의 (`skills.yaml`)

- 스킬 이름, 버전, 설명
- 에이전트 목록 및 각 에이전트의 역할 정의
- **입력 스키마**:
  - `project_root`: 필수 — 분석 대상 프로젝트의 루트 디렉토리 경로
  - `exclude_patterns`: 선택 — 추가 제외 패턴 (기본: .gitignore + node_modules, .git, __pycache__ 등)
  - `depth_override`: 선택 — 경량/중량 모드 수동 지정 (기본: 자동 판별)
  - `token_budget`: 선택 — 최종 산출물의 목표 토큰 수 (기본: 4000 토큰)
  - `focus_areas`: 선택 — 특정 디렉토리나 컴포넌트에 집중 분석
- **출력 스키마**: 4섹션 (`project_structure_map`, `technology_stack_detection`, `component_relationship_analysis`, `architecture_inference`) 산출물 계약
- **적응적 깊이 설정**: 프로젝트 복잡도에 따른 경량/중량 모드 기준 및 전환 규칙
- **에스컬레이션 조건 정의**: 분석 불가 상황 (바이너리 프로젝트, 접근 권한 없음, 심볼릭 링크 순환 등)
- 의존성 정보 (선행: 없음 — 독립 진입점, 후속 소비자: `re`, `arch`, `impl`, `qa`, `sec`, `devops`)

### 2단계: 에이전트 시스템 프롬프트 작성 (`agents/`)

#### `scan.md` — 구조 스캔 에이전트

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

#### `detect.md` — 기술 스택 탐지 에이전트

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

#### `analyze.md` — 의존성/아키텍처 분석 에이전트

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

#### `map.md` — 컨텍스트 맵 생성 에이전트

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

### 3단계: 프롬프트 템플릿 작성 (`prompts/`)

각 에이전트에 대응하는 프롬프트 템플릿을 작성합니다:
- **디렉토리 스캔 가이드**: .gitignore 해석, 불필요 파일 제외, 토큰 효율적 트리 표현법
- **기술 탐지 패턴 카탈로그**: 언어/프레임워크/도구별 탐지 시그니처 (매니페스트 파일 패턴, import 패턴, 설정 파일 패턴)
- **아키텍처 추론 휴리스틱**: 디렉토리 구조/의존성 패턴에서 아키텍처 스타일을 추론하는 규칙
- **토큰 최적화 가이드**: 축약 규칙, 우선순위 기반 정보 선별, 반복 패턴 처리법
- 출력 형식 지정 (4섹션 각 필드의 형식)
- Chain of Thought 가이드라인
- Few-shot 예시 포함

### 4단계: 입출력 예시 작성 (`examples/`)

각 에이전트별 대표적인 입출력 쌍을 작성합니다:
- **경량 프로젝트 전체 분석** 예시 (단순 Express API — 파일 20개)
- **중량 프로젝트 전체 분석** 예시 (Next.js + Prisma + Docker — 파일 200개)
- **모노레포 분석** 예시 (turborepo/nx — 복수 패키지)
- **기존 harness 산출물로 생성된 프로젝트 분석** 예시 (impl 스킬이 생성한 코드를 ex가 재분석)
- **후속 스킬 연계** 예시: ex 산출물 → re:elicit 컨텍스트 주입
- **토큰 예산 내 축약** 예시: 대규모 프로젝트를 4000 토큰 내로 요약

## 핵심 설계 원칙

1. **코드 기반 (Code-Driven)**: 문서나 사용자 설명이 아닌, 코드베이스 자체를 유일한 진실의 원천(single source of truth)으로 사용. 모든 산출물 필드는 코드에서 자동 추출
2. **자동 실행 + 최소 에스컬레이션 (Auto-Execute with Minimal Escalation)**: 프로젝트 루트 경로만으로 전체 분석 가능. 사용자 질문 없이 코드를 기계적으로 분석하며, 물리적으로 분석 불가능한 상황에서만 에스컬레이션
3. **토큰 효율 (Token Efficiency)**: LLM 컨텍스트 윈도우는 유한한 자원. 산출물은 지정된 토큰 예산 내에서 최대 정보 밀도를 달성하도록 설계. 반복 패턴 축약, 우선순위 기반 선별, 계층적 상세화
4. **적응적 깊이 (Adaptive Depth)**: 프로젝트 복잡도를 자동 판별하여 경량(구조 + 스택 요약)/중량(컴포넌트 그래프 + 아키텍처 추론) 모드 자동 전환
5. **역방향 호환성 (Reverse Compatibility)**: 산출물의 필드와 형식을 순방향 스킬(re, arch, impl)의 입력/산출물 스키마와 정렬하여, 후속 스킬이 파싱 없이 직접 소비 가능
6. **비파괴적 분석 (Non-destructive Analysis)**: 프로젝트 파일을 절대 수정하지 않음. 읽기 전용 분석만 수행
7. **증거 기반 추론 (Evidence-based Inference)**: 모든 탐지와 추론에 근거(evidence)를 명시. "어떤 파일의 어떤 패턴에서 이 결론을 도출했는가"를 추적 가능
8. **산출물 표준화 (Standardized Output)**: 최종 산출물을 **프로젝트 구조 맵 / 기술 스택 탐지 / 컴포넌트 관계 분석 / 아키텍처 추론** 4섹션으로 고정하여, 후속 스킬(`re`, `arch`, `impl`, `qa`, `sec`, `devops`)이 직접 소비할 수 있는 계약(contract) 역할을 수행
