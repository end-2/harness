# 테스트 전략 수립 입력 예시

> 휴가 관리 시스템 — RE/Arch/Impl 산출물 기반

---

## RE spec 산출물

### 요구사항 명세 (requirements_spec)

```yaml
- id: FR-001
  category: functional/authentication
  title: 사내 SSO 로그인
  priority: Must
  acceptance_criteria:
    - SSO 인증 성공 시 대시보드 페이지로 이동한다
    - 미인증 사용자가 어떤 페이지에 접근해도 SSO 로그인 페이지로 리다이렉트된다
    - SSO 인증 실패 시 에러 메시지가 표시된다
    - 로그인 후 세션은 8시간 유지되며 만료 시 재인증 필요
  dependencies: []

- id: FR-002
  category: functional/leave-request
  title: 휴가 신청
  priority: Must
  acceptance_criteria:
    - 연차, 반차(오전/오후), 병가, 특별휴가 유형 중 선택 가능
    - 시작일, 종료일, 사유를 입력하여 신청
    - 시작일은 오늘 이후여야 한다
    - 잔여 휴가 부족 시 신청 차단 및 안내 메시지 표시
    - 신청 완료 후 상태가 '대기중'으로 표시
  dependencies: [FR-001, FR-005]

- id: FR-003
  category: functional/approval
  title: 휴가 승인/반려
  priority: Must
  acceptance_criteria:
    - 팀장은 대기중인 팀원의 휴가 신청 목록 확인 가능
    - 승인 시 상태가 '승인됨'으로 변경
    - 반려 시 사유 입력 필수, 상태가 '반려됨'으로 변경
    - 승인/반려 즉시 신청자에게 이메일 알림 발송
  dependencies: [FR-001, FR-002]

- id: FR-004
  category: functional/calendar
  title: 팀 휴가 캘린더
  priority: Should
  acceptance_criteria:
    - 승인된 팀원 휴가가 캘린더에 표시
    - 월별/주별 보기 전환 가능
    - 휴가 유형별 색상 구분
    - 캘린더 렌더링 3초 이내 완료
  dependencies: [FR-001, FR-002]

- id: FR-005
  category: functional/balance
  title: 잔여 휴가 조회
  priority: Must
  acceptance_criteria:
    - 유형별 총 일수, 사용 일수, 잔여 일수 표시
    - 매년 1월 1일 연차 자동 부여 (기본 15일, 3년 이상 근속 시 연 1일 가산)
    - 대기중인 신청 건도 반영한 '예상 잔여일수' 표시
  dependencies: [FR-001]

- id: FR-008
  category: functional/leave-request
  title: 휴가 신청 취소/수정
  priority: Must
  acceptance_criteria:
    - 상태가 '대기중'인 신청 건만 취소/수정 가능
    - 승인 완료된 신청 건의 취소는 팀장에게 취소 요청 전달
    - 수정 시 변경 이력 기록
  dependencies: [FR-002]

- id: NFR-001
  category: non-functional/performance
  title: 응답 시간
  priority: Should
  acceptance_criteria:
    - API 응답 시간 P95 기준 1초 이내
    - 캘린더 뷰 렌더링 3초 이내
  dependencies: []

- id: NFR-003
  category: non-functional/security
  title: 감사 로그
  priority: Should
  acceptance_criteria:
    - 신청, 승인, 반려, 수정, 취소 행위 로그 기록
    - 로그에 행위자, 시각, 행위 유형, 대상 포함
    - 로그 최소 3년간 보관
  dependencies: []
```

### 제약 조건 (constraints)

```yaml
- id: CON-001
  type: technical
  title: 사내 SAML 2.0 SSO 연동
  flexibility: hard

- id: CON-003
  type: environmental
  title: 사내 프라이빗 클라우드 배포
  flexibility: hard

- id: CON-005
  type: regulatory
  title: 개인정보보호법 준수
  flexibility: hard
```

### 품질 속성 우선순위 (quality_attribute_priorities)

```yaml
- attribute: usability
  priority: 1
  metric: "신규 사용자가 5분 이내에 첫 휴가 신청 완료"
  trade_off_notes: "보안 강화보다 사용 편의성 우선"

- attribute: availability
  priority: 2
  metric: "업무 시간(09:00-18:00) 99.5% 가용성, 장애 시 30분 내 복구"
  trade_off_notes: "24/7 고가용성 불필요, 야간 유지보수 윈도우 허용"

- attribute: security
  priority: 3
  metric: "민감 정보 접근은 권한 있는 사용자로 제한, 감사 로그 100% 기록"
  trade_off_notes: "매 접근 시 재인증 불필요, 민감 정보 접근 시에만 권한 검증"
```

---

## Arch 산출물

### 아키텍처 결정 (architecture_decisions)

```yaml
- id: AD-001
  decision: "3-tier 레이어드 아키텍처 (Presentation → Business → Data)"
  trade_offs: "단순성과 유지보수성 우선, 수평 확장은 제한적"
  re_refs: [FR-001, FR-002, FR-003, NFR-001]

- id: AD-002
  decision: "SPA(React) + REST API(Spring Boot) 구조"
  trade_offs: "초기 로딩 후 빠른 네비게이션, SEO 불필요"
  re_refs: [NFR-001]
```

### 컴포넌트 구조 (component_structure)

```yaml
- id: COMP-001
  name: AuthService
  type: service
  interfaces: [login, logout, validateSession]
  dependencies: [SSO Provider]

- id: COMP-002
  name: LeaveService
  type: service
  interfaces: [requestLeave, cancelLeave, modifyLeave, getLeaveBalance]
  dependencies: [COMP-001, COMP-004]

- id: COMP-003
  name: ApprovalService
  type: service
  interfaces: [approve, reject, getPendingList]
  dependencies: [COMP-001, COMP-002, COMP-005]

- id: COMP-004
  name: LeaveRepository
  type: store
  interfaces: [save, findById, findByEmployee, findByTeam, update]
  dependencies: [Database]

- id: COMP-005
  name: NotificationService
  type: service
  interfaces: [sendEmail, sendReminder]
  dependencies: [Email Server]
```

### 기술 스택 (technology_stack)

```yaml
- category: backend
  choice: "Java 17 + Spring Boot 3"
  decision_ref: AD-002

- category: frontend
  choice: "TypeScript + React 18"
  decision_ref: AD-002

- category: database
  choice: "PostgreSQL 15"
  decision_ref: AD-001

- category: testing
  choice: "JUnit5 + Mockito (backend), Vitest + Testing Library (frontend)"
  decision_ref: AD-002
```

---

## Impl 산출물

### 구현 맵 (implementation_map)

```yaml
- id: IM-001
  component_ref: COMP-001
  module_path: src/main/java/com/company/leave/auth/
  entry_point: AuthController.java
  interfaces_implemented: [login, logout, validateSession]
  re_refs: [FR-001]

- id: IM-002
  component_ref: COMP-002
  module_path: src/main/java/com/company/leave/service/
  entry_point: LeaveService.java
  interfaces_implemented: [requestLeave, cancelLeave, modifyLeave, getLeaveBalance]
  re_refs: [FR-002, FR-005, FR-008]

- id: IM-003
  component_ref: COMP-003
  module_path: src/main/java/com/company/leave/approval/
  entry_point: ApprovalController.java
  interfaces_implemented: [approve, reject, getPendingList]
  re_refs: [FR-003]

- id: IM-004
  component_ref: COMP-004
  module_path: src/main/java/com/company/leave/repository/
  entry_point: LeaveRepository.java
  interfaces_implemented: [save, findById, findByEmployee, findByTeam, update]
  re_refs: [FR-002, FR-003, FR-005]

- id: IM-005
  component_ref: COMP-005
  module_path: src/main/java/com/company/leave/notification/
  entry_point: NotificationService.java
  interfaces_implemented: [sendEmail, sendReminder]
  re_refs: [FR-003]
```

### 코드 구조 (code_structure)

```yaml
directory_layout:
  - src/main/java/com/company/leave/
  - src/main/java/com/company/leave/auth/
  - src/main/java/com/company/leave/service/
  - src/main/java/com/company/leave/approval/
  - src/main/java/com/company/leave/repository/
  - src/main/java/com/company/leave/notification/
  - src/main/java/com/company/leave/config/

module_dependencies:
  auth: []
  service: [auth, repository]
  approval: [auth, service, notification]
  repository: []
  notification: []

external_dependencies:
  - { name: "SSO Provider", type: "SAML 2.0 IdP" }
  - { name: "PostgreSQL", type: "RDBMS" }
  - { name: "Email Server", type: "SMTP" }
```

### 구현 결정 (implementation_decisions)

```yaml
- id: IDR-001
  decision: "Repository 패턴으로 데이터 접근 추상화"
  pattern_applied: Repository
  arch_refs: [AD-001]
  re_refs: [FR-002, FR-003, FR-005]

- id: IDR-002
  decision: "Strategy 패턴으로 휴가 유형별 정책 분리"
  pattern_applied: Strategy
  arch_refs: [AD-001]
  re_refs: [FR-002]

- id: IDR-003
  decision: "Observer 패턴으로 알림 이벤트 처리"
  pattern_applied: Observer
  arch_refs: [AD-001]
  re_refs: [FR-003]
```

### 구현 가이드 (implementation_guide)

```yaml
conventions:
  naming: "camelCase (Java), PascalCase (React components)"
  test_naming: "should_동작_when_조건"
  package_structure: "기능별 패키지 분리"
```
