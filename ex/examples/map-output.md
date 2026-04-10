# 컨텍스트 맵 생성 출력 예시

> Task Manager API — 최종 4섹션 산출물 (중량 모드, 토큰 예산 4000)

---

```yaml
metadata:
  analyzed_at: "2026-04-10T14:30:00Z"
  depth_mode: heavyweight
  project_root: /workspace/task-manager-api
  analysis_scope:
    files_analyzed: 38
    files_excluded: 0
    exclude_patterns: [node_modules/, dist/, .git/, coverage/]
  token_budget: 4000
  estimated_tokens: 3200
```

---

## 섹션 1: 프로젝트 구조 맵

```yaml
project_structure_map:
  project_root: /workspace/task-manager-api
  directory_tree: |
    src/
    ├── controllers/    (3) taskController, userController, authController
    ├── services/       (3) taskService, userService, authService
    ├── repositories/   (2) taskRepository, userRepository
    ├── middlewares/     (3) auth, errorHandler, validator
    ├── models/         (2) task, user
    ├── routes/         (3) taskRoutes, userRoutes, index
    ├── utils/          (2) logger, config
    ├── types/          (1) index
    ├── app.ts
    └── server.ts
    tests/
    ├── controllers/    (2) task, user
    ├── services/       (2) task, user
    ├── integration/    (1) api
    └── setup.ts
    prisma/
    ├── schema.prisma
    └── migrations/     (3 migrations)
  file_count:
    total: 38
    source: 21
    test: 6
    config: 7
    doc: 1
    other: 3
  directory_conventions:
    - "Layer-based 구조: controllers/ → services/ → repositories/ 계층 분리"
    - "테스트 미러링: tests/ 하위에 controllers/, services/ 구조가 src/를 미러링"
    - "미들웨어 분리: middlewares/에 횡단 관심사 집중"
  entry_points:
    - path: src/server.ts
      role: "HTTP 서버 시작점 (Express 리스닝)"
    - path: src/app.ts
      role: "Express 앱 설정, 미들웨어/라우트 등록"
  config_files:
    - path: package.json
      role: "npm 패키지 매니페스트"
    - path: tsconfig.json
      role: "TypeScript 컴파일러 설정"
    - path: prisma/schema.prisma
      role: "Prisma ORM 스키마 (PostgreSQL)"
    - path: jest.config.ts
      role: "Jest 테스트 설정"
    - path: Dockerfile
      role: "컨테이너 이미지 빌드"
    - path: docker-compose.yml
      role: "로컬 개발 환경 (app + postgres)"
    - path: .github/workflows/ci.yml
      role: "CI 파이프라인 (lint → test → build)"
  ignored_patterns: [node_modules/, dist/, .git/, coverage/, "*.log", .env]
```

---

## 섹션 2: 기술 스택 탐지

```yaml
technology_stack_detection:
  - id: TS-001
    category: language
    name: TypeScript
    version: "5.3.3"
    evidence: "package.json devDependencies"
    role: "주 개발 언어"
    config_location: tsconfig.json

  - id: TS-002
    category: framework
    name: Express
    version: "4.18.2"
    evidence: "package.json dependencies + src/app.ts import"
    role: "REST API 웹 프레임워크"
    config_location: src/app.ts

  - id: TS-003
    category: database
    name: Prisma + PostgreSQL
    version: "5.7.1 / 15"
    evidence: "package.json + prisma/schema.prisma provider=postgresql + docker-compose postgres:15"
    role: "ORM + 주 데이터베이스"
    config_location: prisma/schema.prisma

  - id: TS-004
    category: test
    name: Jest + Supertest
    version: "29.7.0 / 6.3.3"
    evidence: "package.json devDependencies + jest.config.ts"
    role: "단위/통합 테스트"
    config_location: jest.config.ts

  - id: TS-005
    category: lint
    name: ESLint + Prettier
    version: "8.56.0 / 3.2.4"
    evidence: ".eslintrc.json + .prettierrc"
    role: "코드 품질/포매팅"
    config_location: .eslintrc.json, .prettierrc

  - id: TS-006
    category: ci
    name: GitHub Actions
    version: "미확인"
    evidence: ".github/workflows/ci.yml"
    role: "CI/CD (lint → test → build)"
    config_location: .github/workflows/ci.yml

  - id: TS-007
    category: container
    name: Docker + Docker Compose
    version: "미확인"
    evidence: "Dockerfile (node:20-alpine) + docker-compose.yml"
    role: "컨테이너화 + 로컬 개발 환경"
    config_location: Dockerfile, docker-compose.yml

  tech_relationships:
    - "TypeScript + Express REST API + Prisma ORM + PostgreSQL 백엔드 스택"
    - "Jest 단위 테스트 + Supertest HTTP 통합 테스트 이중 전략"
    - "Docker 컨테이너화 + GitHub Actions CI 자동화"
```

---

## 섹션 3: 컴포넌트 관계 분석

```yaml
component_relationship_analysis:
  - id: CM-001
    name: Routes
    path: src/routes/
    type: handler
    responsibility: "HTTP 라우트 정의, 컨트롤러 위임"
    dependencies_internal: [CM-002, CM-005]
    dependencies_external: [express]
    dependents: [CM-008]
    api_surface:
      - "GET/POST /api/tasks — 태스크 CRUD"
      - "GET/PUT/DELETE /api/tasks/:id"
      - "POST /api/auth/login, /api/auth/register"
      - "GET /api/users/me"
    patterns_detected: []

  - id: CM-002
    name: Controllers
    path: src/controllers/
    type: handler
    responsibility: "요청 파싱, 서비스 호출, 응답 반환"
    dependencies_internal: [CM-003, CM-007]
    dependents: [CM-001]
    patterns_detected: [Controller]

  - id: CM-003
    name: Services
    path: src/services/
    type: service
    responsibility: "비즈니스 로직 (태스크 CRUD, 인증)"
    dependencies_internal: [CM-004, CM-006]
    dependencies_external: [bcrypt, jsonwebtoken]
    dependents: [CM-002]
    patterns_detected: [Service]

  - id: CM-004
    name: Repositories
    path: src/repositories/
    type: library
    responsibility: "DB 접근 추상화 (Prisma Client)"
    dependencies_internal: []
    dependencies_external: ["@prisma/client"]
    dependents: [CM-003]
    patterns_detected: [Repository]

  - id: CM-005
    name: Middlewares
    path: src/middlewares/
    type: library
    responsibility: "인증, 에러 처리, 입력 검증"
    dependencies_internal: [CM-007]
    dependencies_external: [jsonwebtoken, zod]
    dependents: [CM-001, CM-008]
    patterns_detected: [Middleware]

  - id: CM-006
    name: Models
    path: src/models/
    type: model
    responsibility: "도메인 타입 정의 (Task, User)"
    dependents: [CM-003, CM-004]

  - id: CM-007
    name: Utils (logger, config)
    path: src/utils/
    type: util
    responsibility: "Winston 로거, dotenv 설정"
    dependencies_external: [winston, dotenv]
    dependents: [CM-002, CM-003, CM-005]

  - id: CM-008
    name: App Entry
    path: src/app.ts, src/server.ts
    type: config
    responsibility: "Express 초기화, 미들웨어/라우트 등록, 서버 시작"
    dependencies_internal: [CM-001, CM-005]
    dependencies_external: [express, cors, helmet]
```

---

## 섹션 4: 아키텍처 추론

```yaml
architecture_inference:
  architecture_style: layered
  style_evidence:
    - "controllers → services → repositories 단방향 3-tier 의존 체인"
    - "계층별 독립 디렉토리 분리 (controllers/, services/, repositories/)"
    - "단일 진입점 + 단일 배포 단위 + 공유 PostgreSQL"
  layer_structure:
    - "presentation: routes/, controllers/ — HTTP 요청/응답"
    - "business: services/ — 비즈니스 로직"
    - "data: repositories/, models/ — 데이터 접근"
    - "cross-cutting: middlewares/, utils/ — 인증, 로깅, 에러"
  communication_patterns:
    - "REST API — Express 라우트를 통한 HTTP 통신"
    - "동기 함수 호출 — 계층 간 직접 호출"
  data_stores:
    - "PostgreSQL — Prisma ORM 경유, schema.prisma + migrations/ 관리"
  cross_cutting_concerns:
    - "인증: middlewares/auth.ts — JWT 검증"
    - "에러: middlewares/errorHandler.ts — 전역 핸들러"
    - "검증: middlewares/validator.ts — Zod 스키마"
    - "로깅: utils/logger.ts — Winston"
  test_patterns:
    - framework: Jest + Supertest
      pattern: "단위(controllers, services) + 통합(API 엔드포인트) — 테스트 미러링 구조"
      coverage_config: false
  build_deploy_patterns:
    - build: tsc
      container: Docker (node:20-alpine)
      ci: GitHub Actions (lint → test → build)
      iac: false
  token_budget_summary:
    budget: 4000
    estimated_tokens: 3200
    truncation_applied: true
    truncated_sections:
      - "tech_stack: ESLint/Prettier를 단일 항목으로 병합"
      - "components: Models, Utils는 상세 의존성 생략"
```
