# 위협 모델링 입력 예시

> 휴가 관리 시스템의 Arch 산출물을 기반으로 위협 모델링을 수행하는 입력 예시입니다.

## 아키텍처 결정

```yaml
architecture_decisions:
  - id: AD-001
    title: "Modular Monolith 아키텍처 스타일 선택"
    decision: "모듈러 모놀리스 아키텍처를 채택하여 도메인 경계를 명확히 분리하면서 단일 배포 단위를 유지"
    rationale: "소규모 팀(3명)에서 마이크로서비스 운영 오버헤드 없이 도메인 분리 가능"
    alternatives_considered:
      - name: "Monolithic"
        pros: "단순, 빠른 개발"
        cons: "도메인 경계 불명확, 향후 분리 어려움"
        rejection_reason: "5개 이상 FR의 도메인 경계가 명확하여 모듈 분리 필요"
      - name: "Microservices"
        pros: "독립 배포, 기술 이질성"
        cons: "운영 복잡도, 네트워크 통신 오버헤드"
        rejection_reason: "소규모 팀에서 운영 오버헤드가 과도"
    trade_offs: "모듈 간 통신이 in-process이므로 성능 유리하나, 향후 분리 시 인터페이스 재정의 필요"
    re_refs: [FR-001, FR-002, FR-003, FR-004, FR-005, NFR-001, NFR-002]

  - id: AD-002
    title: "계층형 아키텍처 적용"
    decision: "각 모듈 내부에 Handler-Service-Repository 3계층 적용"
    rationale: "관심사 분리와 테스트 용이성 확보"
    trade_offs: "계층 간 DTO 변환 오버헤드"
    re_refs: [NFR-001]

  - id: AD-003
    title: "JWT 기반 인증"
    decision: "Stateless JWT 토큰 기반 인증 채택, 리프레시 토큰으로 세션 연장"
    rationale: "수평 확장 용이, 서버 측 세션 저장 불필요"
    trade_offs: "토큰 즉시 무효화 어려움 — 블랙리스트 또는 짧은 만료 시간으로 보완"
    re_refs: [NFR-003, CON-001]

  - id: AD-004
    title: "PostgreSQL 단일 데이터베이스"
    decision: "모든 모듈이 단일 PostgreSQL 인스턴스를 공유하되 스키마로 논리적 분리"
    rationale: "운영 단순성, 트랜잭션 일관성"
    trade_offs: "모듈 간 데이터 결합 가능성"
    re_refs: [CON-002, NFR-001]

  - id: AD-005
    title: "RESTful API 설계"
    decision: "REST API로 클라이언트-서버 통신, OpenAPI 3.0 스펙 기반"
    rationale: "팀 경험, 프론트엔드 통합 용이성"
    trade_offs: "gRPC 대비 성능 열세, 타입 안전성 부족"
    re_refs: [FR-001, FR-002, FR-003, NFR-001]
```

## 컴포넌트 구조

```yaml
component_structure:
  - id: COMP-001
    name: API Gateway
    responsibility: "클라이언트 요청 수신, 인증/인가, 라우팅"
    type: gateway
    interfaces:
      - name: REST API
        direction: inbound
        protocol: REST
    dependencies: [COMP-002, COMP-003, COMP-004, COMP-005]
    re_refs: [FR-001, FR-002, FR-003, NFR-003]

  - id: COMP-002
    name: Auth Module
    responsibility: "사용자 인증, JWT 토큰 발급/검증, 권한 관리"
    type: service
    interfaces:
      - name: AuthService
        direction: inbound
        protocol: REST
    dependencies: [COMP-005]
    re_refs: [NFR-003, CON-001]

  - id: COMP-003
    name: Leave Module
    responsibility: "휴가 신청, 승인/반려, 잔여 일수 관리"
    type: service
    interfaces:
      - name: LeaveService
        direction: inbound
        protocol: REST
    dependencies: [COMP-005]
    re_refs: [FR-001, FR-002, FR-003]

  - id: COMP-004
    name: Notification Module
    responsibility: "휴가 신청/승인/반려 시 이메일 알림 발송"
    type: service
    interfaces:
      - name: NotificationService
        direction: inbound
        protocol: REST
      - name: SMTP
        direction: outbound
        protocol: message
    dependencies: [COMP-005]
    re_refs: [FR-004]

  - id: COMP-005
    name: Database
    responsibility: "사용자, 휴가, 알림 데이터 영구 저장"
    type: store
    interfaces:
      - name: PostgreSQL
        direction: inbound
        protocol: SQL
    dependencies: []
    re_refs: [CON-002, NFR-001]
```

## 기술 스택

```yaml
technology_stack:
  - category: language
    choice: Go
    rationale: "팀 주력 언어, 동시성 처리 우수"
    decision_ref: AD-001
    constraint_ref: null
  - category: framework
    choice: Echo
    rationale: "경량 HTTP 프레임워크, 미들웨어 체인 지원"
    decision_ref: AD-005
    constraint_ref: null
  - category: database
    choice: PostgreSQL
    rationale: "안정성, ACID 트랜잭션, 팀 경험"
    decision_ref: AD-004
    constraint_ref: CON-002
  - category: tool
    choice: sqlc
    rationale: "타입 안전 SQL 쿼리, SQL 인젝션 방어"
    decision_ref: AD-004
    constraint_ref: null
```

## 다이어그램

```yaml
diagrams:
  - type: c4-context
    title: "휴가 관리 시스템 컨텍스트"
    format: mermaid
    code: |
      graph TB
        User[직원/관리자] -->|REST API| System[휴가 관리 시스템]
        System -->|SMTP| Email[이메일 서비스]
    description: "시스템의 외부 경계와 액터"

  - type: c4-container
    title: "휴가 관리 시스템 컨테이너"
    format: mermaid
    code: |
      graph TB
        Client[웹 클라이언트] -->|HTTPS| GW[API Gateway]
        GW --> Auth[Auth Module]
        GW --> Leave[Leave Module]
        GW --> Notif[Notification Module]
        Auth --> DB[(PostgreSQL)]
        Leave --> DB
        Notif --> DB
        Notif -->|SMTP| Email[이메일 서비스]
    description: "주요 컨테이너와 통신 경로"

  - type: sequence
    title: "휴가 신청 흐름"
    format: mermaid
    code: |
      sequenceDiagram
        Client->>+Gateway: POST /api/leaves (JWT)
        Gateway->>+Auth: ValidateToken(JWT)
        Auth-->>-Gateway: UserContext
        Gateway->>+Leave: CreateLeave(request, userCtx)
        Leave->>+DB: INSERT leave
        DB-->>-Leave: leaveId
        Leave->>+Notif: SendNotification(managerId, leaveId)
        Notif-->>-Leave: ok
        Leave-->>-Gateway: 201 Created
        Gateway-->>-Client: 201 Created
    description: "휴가 신청 시 인증 → 생성 → 알림 흐름"
```
