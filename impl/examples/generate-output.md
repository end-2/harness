# 코드 생성 출력 예시

> 휴가 관리 시스템 — 중량 모드 (Go + Echo + PostgreSQL)

---

✅ 구현 완료 — 에스컬레이션 없음

---

## 섹션 1: 구현 맵

```yaml
implementation_map:
  - id: IM-001
    component_ref: COMP-001
    module_path: internal/auth/
    entry_point: internal/auth/handler.go
    internal_structure:
      - internal/auth/handler.go       # HTTP 핸들러 (SSO 콜백, 로그아웃)
      - internal/auth/service.go       # 인증 비즈니스 로직
      - internal/auth/middleware.go    # 세션 검증 미들웨어
      - internal/auth/model.go         # User, Session 모델
    interfaces_implemented:
      - Authenticate
      - ValidateSession
      - Logout
    re_refs: [FR-001, CON-001]

  - id: IM-002
    component_ref: COMP-002
    module_path: internal/leave/
    entry_point: internal/leave/handler.go
    internal_structure:
      - internal/leave/handler.go      # HTTP 핸들러
      - internal/leave/service.go      # 휴가 신청/조회/취소 로직
      - internal/leave/balance.go      # 잔여일수 계산
      - internal/leave/model.go        # Leave, LeaveRequest, LeaveBalance 모델
      - internal/leave/dto.go          # 요청/응답 DTO
    interfaces_implemented:
      - Apply
      - Cancel
      - Update
      - GetBalance
      - ListByUser
    re_refs: [FR-002, FR-005, FR-008]

  - id: IM-003
    component_ref: COMP-003
    module_path: internal/approval/
    entry_point: internal/approval/handler.go
    internal_structure:
      - internal/approval/handler.go   # HTTP 핸들러
      - internal/approval/service.go   # 승인/반려 로직
      - internal/approval/model.go     # Approval 모델
    interfaces_implemented:
      - Approve
      - Reject
      - ListPending
    re_refs: [FR-003]

  - id: IM-004
    component_ref: COMP-004
    module_path: internal/notification/
    entry_point: internal/notification/service.go
    internal_structure:
      - internal/notification/service.go    # 알림 발송 로직
      - internal/notification/template.go   # 이메일 템플릿
      - internal/notification/smtp.go       # SMTP 클라이언트
    interfaces_implemented:
      - SendApprovalNotification
      - SendReminder
      - SendPendingAlert
    re_refs: [FR-006]

  - id: IM-005
    component_ref: COMP-005
    module_path: internal/store/
    entry_point: internal/store/store.go
    internal_structure:
      - internal/store/store.go             # DB 연결 및 초기화
      - internal/store/user_repository.go   # UserRepository 구현
      - internal/store/leave_repository.go  # LeaveRepository 구현
      - internal/store/approval_repository.go  # ApprovalRepository 구현
      - internal/store/query/               # sqlc 생성 코드
    interfaces_implemented:
      - UserRepository
      - LeaveRepository
      - ApprovalRepository
    re_refs: [CON-001, AD-003]

  - id: IM-006
    component_ref: COMP-006
    module_path: internal/api/
    entry_point: internal/api/router.go
    internal_structure:
      - internal/api/router.go         # 라우트 등록 및 미들웨어 설정
      - internal/api/error_handler.go  # 공통 에러 핸들링
      - internal/api/response.go       # 공통 응답 포맷
    interfaces_implemented:
      - "POST /api/leaves"
      - "GET /api/leaves"
      - "PUT /api/leaves/:id"
      - "DELETE /api/leaves/:id"
      - "POST /api/leaves/:id/approve"
      - "POST /api/leaves/:id/reject"
      - "GET /api/leaves/balance"
      - "GET /api/leaves/calendar"
    re_refs: [FR-001, FR-002, FR-003, FR-004]
```

## 섹션 2: 코드 구조

```yaml
code_structure:
  project_root: leave-management/

  directory_layout: |
    leave-management/
    ├── cmd/
    │   └── server/
    │       └── main.go              # 애플리케이션 진입점
    ├── internal/
    │   ├── api/
    │   │   ├── router.go            # 라우트 등록
    │   │   ├── error_handler.go     # 공통 에러 핸들링
    │   │   └── response.go          # 공통 응답 포맷
    │   ├── auth/
    │   │   ├── handler.go           # 인증 핸들러
    │   │   ├── service.go           # 인증 서비스
    │   │   ├── middleware.go        # 세션 미들웨어
    │   │   └── model.go            # User, Session 모델
    │   ├── leave/
    │   │   ├── handler.go           # 휴가 핸들러
    │   │   ├── service.go           # 휴가 서비스
    │   │   ├── balance.go           # 잔여일수 계산
    │   │   ├── model.go            # Leave 모델
    │   │   └── dto.go              # 요청/응답 DTO
    │   ├── approval/
    │   │   ├── handler.go           # 승인 핸들러
    │   │   ├── service.go           # 승인 서비스
    │   │   └── model.go            # Approval 모델
    │   ├── notification/
    │   │   ├── service.go           # 알림 서비스
    │   │   ├── template.go          # 이메일 템플릿
    │   │   └── smtp.go             # SMTP 클라이언트
    │   └── store/
    │       ├── store.go             # DB 연결
    │       ├── user_repository.go   # UserRepository
    │       ├── leave_repository.go  # LeaveRepository
    │       ├── approval_repository.go # ApprovalRepository
    │       └── query/               # sqlc 생성 코드
    ├── migrations/
    │   ├── 001_create_users.sql
    │   ├── 002_create_leaves.sql
    │   └── 003_create_approvals.sql
    ├── go.mod
    ├── go.sum
    ├── .env.example
    └── Makefile

  module_dependencies:
    - from: internal/api
      to: [internal/auth, internal/leave, internal/approval]
      type: direct
    - from: internal/leave
      to: [internal/store]
      type: interface (LeaveRepository)
    - from: internal/approval
      to: [internal/leave, internal/notification, internal/store]
      type: interface (ApprovalRepository)
    - from: internal/notification
      to: []
      type: standalone

  external_dependencies:
    - name: github.com/labstack/echo/v4
      version: v4.11.4
      purpose: HTTP 프레임워크
    - name: github.com/lib/pq
      version: v1.10.9
      purpose: PostgreSQL 드라이버
    - name: github.com/crewjam/saml
      version: v0.4.14
      purpose: SAML 2.0 SSO 연동
    - name: github.com/sqlc-dev/sqlc
      version: v1.25.0
      purpose: 타입 안전 SQL 코드 생성 (dev dependency)

  build_config:
    - file: go.mod
      description: Go 모듈 정의 및 의존성
    - file: Makefile
      description: 빌드, 마이그레이션, 코드 생성 명령어

  environment_config:
    - file: .env.example
      variables:
        - "DB_HOST=localhost"
        - "DB_PORT=5432"
        - "DB_NAME=leave_management"
        - "DB_USER=app"
        - "DB_PASSWORD="
        - "SSO_METADATA_URL=https://sso.company.com/metadata"
        - "SMTP_HOST=smtp.company.com"
        - "SMTP_PORT=587"
        - "SESSION_SECRET="
        - "PORT=8080"
```

## 섹션 3: 구현 결정

```yaml
implementation_decisions:
  - id: IDR-001
    title: "Repository 인터페이스를 각 도메인 모듈에 정의"
    decision: |
      Repository 인터페이스를 store 모듈이 아닌 각 도메인 모듈(leave, approval)에 정의하고,
      store 모듈이 이를 구현하는 구조를 채택
    rationale: |
      Go의 관용적 인터페이스 패턴 (consumer-side interface).
      도메인 모듈이 자신이 필요한 인터페이스만 정의하여 ISP 준수.
      AD-003 (Repository 패턴)의 의존성 역전 원칙 적용.
    alternatives_considered:
      - "store 모듈에 인터페이스 정의 — Go 관용구 위반, 불필요한 import 순환 가능"
      - "공통 interfaces 패키지 — 과도한 추상화, YAGNI"
    pattern_applied: Repository + Dependency Inversion
    arch_refs: [AD-003, AD-002]
    re_refs: [QA:maintainability]

  - id: IDR-002
    title: "Echo 미들웨어로 인증 세션 검증 구현"
    decision: |
      모든 보호된 API 엔드포인트에 Echo 미들웨어를 적용하여
      세션 검증을 핸들러 외부에서 처리
    rationale: |
      횡단 관심사(Cross-cutting concern)를 미들웨어로 분리하여 SRP 준수.
      각 핸들러가 인증 로직을 반복하지 않음.
    alternatives_considered:
      - "각 핸들러에서 직접 세션 검증 — 코드 중복, DRY 위반"
    pattern_applied: Middleware (Chain of Responsibility)
    arch_refs: [COMP-001, COMP-006]
    re_refs: [FR-001, CON-001]

  - id: IDR-003
    title: "도메인 모델과 DTO 분리"
    decision: |
      API 요청/응답 DTO를 도메인 모델과 분리하여 각 계층의 데이터 구조를 독립적으로 관리
    rationale: |
      AD-002 (Layered Architecture)에 따라 Presentation 계층과 Business 계층의 데이터 구조를 분리.
      API 변경이 도메인 모델에 영향을 주지 않으며, 그 반대도 마찬가지.
    alternatives_considered:
      - "도메인 모델을 API에 직접 노출 — 계층 결합, 민감 정보 노출 위험"
    pattern_applied: DTO (Data Transfer Object)
    arch_refs: [AD-002]
    re_refs: [NFR-003, CON-005]

  - id: IDR-004
    title: "에러 처리를 Go 관용적 error return 패턴으로 통일"
    decision: |
      모든 함수에서 error를 반환하고, 도메인 에러는 센티넬 에러(sentinel error)로 정의.
      API 계층에서 도메인 에러를 HTTP 상태 코드로 매핑.
    rationale: |
      Go의 관용적 에러 처리 패턴. panic/recover를 사용하지 않고
      명시적 에러 전파로 에러 흐름을 추적 가능하게 함.
    alternatives_considered:
      - "커스텀 에러 타입 계층 — Go에서는 과도한 추상화"
    pattern_applied: Sentinel Error + Error Wrapping
    arch_refs: [AD-002]
    re_refs: []
```

## 섹션 4: 구현 가이드

```yaml
implementation_guide:
  prerequisites:
    - "Go 1.21 이상"
    - "PostgreSQL 14 이상"
    - "sqlc CLI (go install github.com/sqlc-dev/sqlc/cmd/sqlc@latest)"
    - "사내 SSO 메타데이터 URL 접근 권한"
    - "사내 SMTP 서버 접근 권한"

  setup_steps:
    - "저장소 클론"
    - "의존성 설치: go mod download"
    - "환경 변수 설정: cp .env.example .env 후 값 입력"
    - "PostgreSQL 데이터베이스 생성: createdb leave_management"
    - "마이그레이션 실행: make migrate"
    - "sqlc 코드 생성: make sqlc"

  build_commands:
    - "make build     # 바이너리 빌드 → bin/server"
    - "make sqlc      # SQL → Go 코드 생성"
    - "make migrate   # DB 마이그레이션 실행"

  run_commands:
    - "make run       # 개발 모드 실행 (go run)"
    - "make build && ./bin/server  # 프로덕션 모드 실행"

  conventions:
    - "네이밍: Go 표준 — exported는 PascalCase, unexported는 camelCase"
    - "패키지 구조: internal/ 아래 도메인별 패키지 분리 (Modular Monolith)"
    - "에러 처리: error return 패턴, var ErrXxx = errors.New(...) 센티넬 에러"
    - "로깅: log/slog 패키지, 구조화된 JSON 로그"
    - "인터페이스: consumer-side 정의 (Go 관용구)"
    - "DTO 변환: 각 handler에서 DTO ↔ 도메인 모델 변환"

  extension_points:
    - "새 API 엔드포인트 추가: internal/api/router.go에 라우트 등록 + 해당 모듈의 handler.go에 핸들러 추가"
    - "새 도메인 엔티티 추가: internal/<domain>/에 model.go, service.go, handler.go 생성 + internal/store/에 repository 추가"
    - "새 알림 채널 추가: internal/notification/에 새 클라이언트(예: slack.go) 추가, service.go에서 호출"
    - "새 휴가 유형 추가: internal/leave/model.go에 LeaveType 상수 추가, balance.go에 계산 로직 추가"
```
