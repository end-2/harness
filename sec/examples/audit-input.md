# 보안 감사 입력 예시

> 휴가 관리 시스템의 Impl 산출물 + threat-model 결과를 기반으로 보안 감사를 수행하는 입력 예시입니다.

## 구현 맵

```yaml
implementation_map:
  - id: IM-001
    component_ref: COMP-001
    module_path: internal/handler/
    entry_point: internal/handler/router.go
    internal_structure:
      - internal/handler/router.go
      - internal/handler/middleware.go
      - internal/handler/auth_handler.go
      - internal/handler/leave_handler.go
      - internal/handler/notification_handler.go
    interfaces_implemented:
      - "POST /api/auth/login"
      - "POST /api/auth/register"
      - "POST /api/auth/refresh"
      - "GET /api/leaves"
      - "POST /api/leaves"
      - "PUT /api/leaves/:id"
      - "DELETE /api/leaves/:id"
      - "PUT /api/leaves/:id/approve"
      - "PUT /api/leaves/:id/reject"
    re_refs: [FR-001, FR-002, FR-003, NFR-003]

  - id: IM-002
    component_ref: COMP-002
    module_path: internal/auth/
    entry_point: internal/auth/service.go
    internal_structure:
      - internal/auth/service.go
      - internal/auth/jwt.go
      - internal/auth/repository.go
      - internal/auth/model.go
    interfaces_implemented:
      - AuthService.Login
      - AuthService.Register
      - AuthService.ValidateToken
      - AuthService.RefreshToken
    re_refs: [NFR-003, CON-001]

  - id: IM-003
    component_ref: COMP-003
    module_path: internal/leave/
    entry_point: internal/leave/service.go
    internal_structure:
      - internal/leave/service.go
      - internal/leave/repository.go
      - internal/leave/model.go
      - internal/leave/validator.go
    interfaces_implemented:
      - LeaveService.Create
      - LeaveService.GetByID
      - LeaveService.ListByUser
      - LeaveService.Update
      - LeaveService.Delete
      - LeaveService.Approve
      - LeaveService.Reject
    re_refs: [FR-001, FR-002, FR-003]

  - id: IM-004
    component_ref: COMP-004
    module_path: internal/notification/
    entry_point: internal/notification/service.go
    internal_structure:
      - internal/notification/service.go
      - internal/notification/smtp.go
      - internal/notification/template.go
    interfaces_implemented:
      - NotificationService.SendLeaveRequest
      - NotificationService.SendApproval
      - NotificationService.SendRejection
    re_refs: [FR-004]
```

## 코드 구조

```yaml
code_structure:
  project_root: leave-management/
  directory_layout: |
    leave-management/
    ├── cmd/
    │   └── server/
    │       └── main.go
    ├── internal/
    │   ├── handler/
    │   ├── auth/
    │   ├── leave/
    │   ├── notification/
    │   └── config/
    ├── db/
    │   ├── migrations/
    │   └── queries/
    ├── go.mod
    ├── go.sum
    ├── .env.example
    └── Makefile
  module_dependencies:
    - source: internal/handler
      target: internal/auth
      type: direct
    - source: internal/handler
      target: internal/leave
      type: direct
    - source: internal/handler
      target: internal/notification
      type: direct
    - source: internal/auth
      target: db
      type: direct
    - source: internal/leave
      target: db
      type: direct
  external_dependencies:
    - name: github.com/labstack/echo/v4
      version: v4.11.4
      purpose: HTTP 프레임워크
    - name: github.com/golang-jwt/jwt/v5
      version: v5.2.0
      purpose: JWT 토큰 처리
    - name: github.com/lib/pq
      version: v1.10.9
      purpose: PostgreSQL 드라이버
    - name: golang.org/x/crypto
      version: v0.18.0
      purpose: bcrypt 해싱
    - name: github.com/joho/godotenv
      version: v1.5.1
      purpose: 환경 변수 로딩
    - name: github.com/go-playground/validator/v10
      version: v10.17.0
      purpose: 입력 검증
  build_config:
    - file: go.mod
      type: go_module
    - file: Makefile
      type: makefile
  environment_config:
    - name: DB_HOST
      type: string
      required: true
    - name: DB_PASSWORD
      type: secret
      required: true
    - name: JWT_SECRET_KEY
      type: secret
      required: true
    - name: SMTP_PASSWORD
      type: secret
      required: true
    - name: SMTP_HOST
      type: string
      required: true
```

## 구현 결정

```yaml
implementation_decisions:
  - id: IDR-001
    title: "Repository 패턴으로 데이터 접근 추상화"
    decision: "각 도메인별 Repository 인터페이스 정의 후 sqlc 기반 구현체 분리"
    rationale: "AD-002 계층형 아키텍처 결정에 따라 데이터 접근 계층 분리"
    pattern_applied: Repository
    arch_refs: [AD-002, COMP-005]
    re_refs: [NFR-001]

  - id: IDR-002
    title: "Echo 미들웨어 체인으로 인증/인가 구현"
    decision: "JWT 검증 미들웨어를 라우터에 적용하여 보호 엔드포인트 일괄 인증"
    rationale: "AD-003 JWT 기반 인증 결정에 따라 미들웨어 패턴 적용"
    pattern_applied: Middleware
    arch_refs: [AD-003, COMP-001]
    re_refs: [NFR-003]

  - id: IDR-003
    title: "sqlc로 타입 안전 SQL 쿼리 생성"
    decision: "SQL 파일에서 Go 코드를 자동 생성하여 타입 안전성과 SQL 인젝션 방어 확보"
    rationale: "AD-004 PostgreSQL 결정에 따라 안전한 쿼리 방식 선택"
    pattern_applied: CodeGeneration
    arch_refs: [AD-004, COMP-005]
    re_refs: [NFR-003]
```

## 위협 모델 (threat-model 산출물)

> threat-model-output.md의 `threat_model` 섹션 참조

## 신뢰 경계 (threat-model 산출물)

> threat-model-output.md의 `trust_boundaries` 섹션 참조
