# 의존성/아키텍처 분석 출력 예시

> Task Manager API — 중량 모드 전체 분석

---

```yaml
components:
  - id: CM-001
    name: Routes
    path: src/routes/
    type: handler
    responsibility: "HTTP 라우트 정의 및 요청을 컨트롤러에 위임"
    dependencies_internal: [CM-002, CM-005]
    dependencies_external: [express]
    dependents: [CM-008]
    api_surface:
      - "GET /api/tasks — 태스크 목록 조회"
      - "POST /api/tasks — 태스크 생성"
      - "GET /api/tasks/:id — 태스크 상세 조회"
      - "PUT /api/tasks/:id — 태스크 수정"
      - "DELETE /api/tasks/:id — 태스크 삭제"
      - "POST /api/auth/login — 로그인"
      - "POST /api/auth/register — 회원가입"
      - "GET /api/users/me — 현재 사용자 정보"
    patterns_detected: []

  - id: CM-002
    name: Controllers
    path: src/controllers/
    type: handler
    responsibility: "요청 파싱, 입력 검증, 서비스 호출, 응답 반환"
    dependencies_internal: [CM-003, CM-007]
    dependencies_external: [express]
    dependents: [CM-001]
    api_surface: []
    patterns_detected:
      - "Controller 패턴 — 요청/응답 처리를 비즈니스 로직과 분리"

  - id: CM-003
    name: Services
    path: src/services/
    type: service
    responsibility: "비즈니스 로직 처리 (태스크 CRUD, 사용자 관리, 인증)"
    dependencies_internal: [CM-004, CM-006]
    dependencies_external: [bcrypt, jsonwebtoken]
    dependents: [CM-002]
    api_surface: []
    patterns_detected:
      - "Service 패턴 — 비즈니스 로직 캡슐화"

  - id: CM-004
    name: Repositories
    path: src/repositories/
    type: library
    responsibility: "데이터베이스 접근 추상화 (Prisma Client 래핑)"
    dependencies_internal: []
    dependencies_external: ["@prisma/client"]
    dependents: [CM-003]
    api_surface: []
    patterns_detected:
      - "Repository 패턴 — 데이터 접근 로직 분리"

  - id: CM-005
    name: Middlewares
    path: src/middlewares/
    type: library
    responsibility: "HTTP 미들웨어 (인증 검증, 에러 처리, 입력 유효성 검증)"
    dependencies_internal: [CM-007]
    dependencies_external: [jsonwebtoken, zod]
    dependents: [CM-001, CM-008]
    api_surface: []
    patterns_detected:
      - "Middleware 패턴 — 횡단 관심사를 파이프라인에 삽입"

  - id: CM-006
    name: Models
    path: src/models/
    type: model
    responsibility: "도메인 모델 타입 정의 (Task, User)"
    dependencies_internal: []
    dependencies_external: []
    dependents: [CM-003, CM-004]
    api_surface: []
    patterns_detected: []

  - id: CM-007
    name: Utils
    path: src/utils/
    type: util
    responsibility: "공통 유틸리티 (로거, 설정 로딩)"
    dependencies_internal: []
    dependencies_external: [winston, dotenv]
    dependents: [CM-002, CM-003, CM-005]
    api_surface: []
    patterns_detected: []

  - id: CM-008
    name: App Entry
    path: src/
    type: config
    responsibility: "Express 앱 초기화, 미들웨어 등록, 라우트 마운트, 서버 시작"
    dependencies_internal: [CM-001, CM-005]
    dependencies_external: [express, cors, helmet]
    dependents: []
    api_surface: []
    patterns_detected: []

  - id: CM-009
    name: Tests
    path: tests/
    type: test
    responsibility: "단위 테스트 (controllers, services) + 통합 테스트 (API 엔드포인트)"
    dependencies_internal: [CM-002, CM-003]
    dependencies_external: [jest, supertest]
    dependents: []
    api_surface: []
    patterns_detected:
      - "테스트 미러링 — src/ 구조를 tests/에서 미러링"

architecture_inference:
  architecture_style: layered
  style_evidence:
    - "controllers → services → repositories 단방향 의존 체인이 명확한 3-tier 레이어 구조"
    - "각 계층이 독립 디렉토리(controllers/, services/, repositories/)로 분리"
    - "단일 진입점(server.ts) + 단일 배포 단위(Dockerfile 1개)"
    - "공유 데이터베이스(PostgreSQL) 단일 접근 경로(repositories → Prisma)"
  layer_structure:
    - "presentation: src/routes/, src/controllers/ — HTTP 요청 처리"
    - "business: src/services/ — 비즈니스 로직"
    - "data: src/repositories/, src/models/ — 데이터 접근"
    - "infrastructure: src/middlewares/, src/utils/ — 횡단 관심사"
  communication_patterns:
    - "REST API — Express 라우트를 통한 HTTP 통신 (클라이언트 → 서버)"
    - "직접 함수 호출 — 계층 간 동기 호출 (controller → service → repository)"
  data_stores:
    - "PostgreSQL — Prisma ORM을 통한 접근, prisma/schema.prisma에서 스키마 정의, migrations/에서 마이그레이션 관리"
  cross_cutting_concerns:
    - "인증: src/middlewares/auth.ts — JWT 토큰 검증 미들웨어"
    - "에러 처리: src/middlewares/errorHandler.ts — 전역 에러 핸들러"
    - "입력 검증: src/middlewares/validator.ts — Zod 기반 요청 바디 검증"
    - "로깅: src/utils/logger.ts — Winston 로거"
    - "설정 관리: src/utils/config.ts — dotenv 기반 환경 변수 로딩"
  circular_dependencies: []
```
