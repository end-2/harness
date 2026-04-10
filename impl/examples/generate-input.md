# 코드 생성 입력 예시

> Arch design 산출물 4섹션 (휴가 관리 시스템 — 중량 모드)

## 아키텍처 결정

```yaml
- id: AD-001
  title: Modular Monolith 아키텍처 채택
  decision: 모듈 경계가 명확한 모놀리식 아키텍처를 채택한다
  rationale: |
    500명 규모의 사내 시스템으로, 독립 배포가 불필요하며
    팀 규모가 소규모이므로 마이크로서비스의 운영 복잡도 불필요
  alternatives_considered:
    - "Microservices — 운영 복잡도 과다, 팀 규모 대비 비효율"
    - "Simple Monolith — 모듈 경계 불명확으로 유지보수 어려움"
  trade_offs: "향후 서비스 분리 시 모듈 경계를 따라 분리 가능하나, 초기 모듈 설계에 추가 노력 필요"
  re_refs: [NFR-002, CON-002]

- id: AD-002
  title: Layered Architecture 적용
  decision: Presentation-Business-Data 계층형 아키텍처를 각 모듈 내에 적용한다
  rationale: 관심사 분리를 통한 유지보수성 확보. 각 계층을 독립적으로 변경 가능
  alternatives_considered:
    - "Hexagonal — 도메인 복잡도 대비 과도한 추상화"
  trade_offs: "계층 간 데이터 변환(DTO 매핑) 보일러플레이트 발생"
  re_refs: [QA:maintainability]

- id: AD-003
  title: Repository 패턴으로 데이터 접근 추상화
  decision: 각 도메인 엔티티별 Repository 인터페이스를 정의하고 구현체를 분리한다
  rationale: 데이터 접근 계층의 교체 가능성 확보 및 테스트 용이성
  alternatives_considered:
    - "직접 SQL 호출 — 계층 분리 위반"
    - "ORM Active Record — 도메인-DB 결합"
  trade_offs: "Repository 인터페이스 관리 부담 증가"
  re_refs: [NFR-001, QA:maintainability]
```

## 컴포넌트 구조

```yaml
- id: COMP-001
  name: auth
  responsibility: 사내 SSO 연동 인증 및 세션 관리
  type: service
  interfaces:
    - "Authenticate(samlToken string) → (User, error)"
    - "ValidateSession(sessionID string) → (User, error)"
    - "Logout(sessionID string) → error"
  dependencies: []
  re_refs: [FR-001, CON-001]

- id: COMP-002
  name: leave
  responsibility: 휴가 신청, 조회, 취소/수정, 잔여일수 계산
  type: service
  interfaces:
    - "Apply(userID string, req LeaveRequest) → (Leave, error)"
    - "Cancel(userID string, leaveID string) → error"
    - "Update(userID string, leaveID string, req LeaveUpdateRequest) → (Leave, error)"
    - "GetBalance(userID string) → (LeaveBalance, error)"
    - "ListByUser(userID string, filter LeaveFilter) → ([]Leave, error)"
  dependencies: [COMP-001, COMP-005]
  re_refs: [FR-002, FR-005, FR-008]

- id: COMP-003
  name: approval
  responsibility: 휴가 승인/반려 처리 및 승인 워크플로우
  type: service
  interfaces:
    - "Approve(approverID string, leaveID string) → error"
    - "Reject(approverID string, leaveID string, reason string) → error"
    - "ListPending(approverID string) → ([]Leave, error)"
  dependencies: [COMP-001, COMP-002, COMP-004]
  re_refs: [FR-003]

- id: COMP-004
  name: notification
  responsibility: 이메일 알림 발송 (승인/반려, 리마인더)
  type: service
  interfaces:
    - "SendApprovalNotification(leave Leave, result string) → error"
    - "SendReminder(leave Leave) → error"
    - "SendPendingAlert(approverID string, count int) → error"
  dependencies: []
  re_refs: [FR-006]

- id: COMP-005
  name: store
  responsibility: PostgreSQL 데이터 접근 (Repository 구현체)
  type: store
  interfaces:
    - "UserRepository"
    - "LeaveRepository"
    - "ApprovalRepository"
  dependencies: []
  re_refs: [CON-001, AD-003]

- id: COMP-006
  name: api
  responsibility: REST API 엔드포인트 및 요청 라우팅
  type: gateway
  interfaces:
    - "POST /api/leaves"
    - "GET /api/leaves"
    - "PUT /api/leaves/:id"
    - "DELETE /api/leaves/:id"
    - "POST /api/leaves/:id/approve"
    - "POST /api/leaves/:id/reject"
    - "GET /api/leaves/balance"
    - "GET /api/leaves/calendar"
  dependencies: [COMP-001, COMP-002, COMP-003]
  re_refs: [FR-001, FR-002, FR-003, FR-004]
```

## 기술 스택

```yaml
- category: language
  choice: Go 1.21
  rationale: 간결한 문법, 빠른 컴파일, 강타입, 동시성 지원
  decision_ref: AD-001
  constraint_ref: null

- category: framework
  choice: Echo v4
  rationale: 경량 HTTP 프레임워크, 미들웨어 지원, Go 생태계 표준
  decision_ref: AD-002
  constraint_ref: null

- category: database
  choice: PostgreSQL 14
  rationale: 기존 인프라 호환, 운영팀 경험
  decision_ref: AD-003
  constraint_ref: CON-001

- category: tool
  choice: sqlc
  rationale: 타입 안전한 SQL → Go 코드 생성, Repository 패턴과 조합
  decision_ref: AD-003
  constraint_ref: null
```

## 다이어그램

```yaml
- type: c4-container
  title: 휴가 관리 시스템 Container 다이어그램
  format: mermaid
  code: |
    graph TB
      User[직원/팀장/HR]
      API[API Gateway<br/>Echo v4]
      Auth[Auth Module]
      Leave[Leave Module]
      Approval[Approval Module]
      Notification[Notification Module]
      DB[(PostgreSQL)]
      SSO[사내 SSO]
      SMTP[SMTP 서버]

      User --> API
      API --> Auth
      API --> Leave
      API --> Approval
      Auth --> SSO
      Leave --> DB
      Approval --> Leave
      Approval --> Notification
      Notification --> SMTP
  description: 시스템의 주요 모듈과 외부 시스템 간의 관계

- type: sequence
  title: 휴가 신청 흐름
  format: mermaid
  code: |
    sequenceDiagram
      actor User
      participant API
      participant Auth
      participant Leave
      participant Store
      participant Notification

      User->>API: POST /api/leaves
      API->>Auth: ValidateSession
      Auth-->>API: User
      API->>Leave: Apply(userID, request)
      Leave->>Store: GetBalance(userID)
      Store-->>Leave: balance
      Leave->>Leave: validateBalance
      Leave->>Store: CreateLeave(leave)
      Store-->>Leave: leave
      Leave->>Notification: SendPendingAlert
      Leave-->>API: leave
      API-->>User: 201 Created
  description: 직원의 휴가 신청 처리 흐름
```
