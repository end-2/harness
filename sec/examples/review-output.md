# 보안 코드 리뷰 출력 예시

> 휴가 관리 시스템의 보안 코드 리뷰 결과입니다.

## 보안 리뷰 리포트

```yaml
security_review:
  - id: SRV-001
    category: authn
    title: "JWT 리프레시 토큰에 대한 서버 측 무효화 메커니즘 부재"
    severity: high
    description: >
      AD-003에서 "리프레시 토큰으로 세션 연장"을 결정했으나, 리프레시 토큰의
      서버 측 저장/무효화 메커니즘이 구현되지 않음. 로그아웃 후에도 리프레시 토큰으로
      새 액세스 토큰을 발급받을 수 있으며, 토큰 탈취 시 공격자가 무제한으로
      세션을 연장할 수 있음.
    location:
      file: internal/auth/service.go
      line: 85
      function: RefreshToken
    current_state: >
      RefreshToken()은 토큰의 서명과 만료만 검증하고 새 액세스 토큰을 발급.
      서버 측에 리프레시 토큰 저장소가 없으므로 무효화 불가.
    expected_state: >
      리프레시 토큰을 DB에 저장하고, 사용 시 유효성 검증 후 새 토큰 발급과
      동시에 기존 토큰 무효화 (토큰 로테이션). 로그아웃 시 즉시 무효화.
    remediation: >
      1. refresh_tokens 테이블 생성 (token_hash, user_id, expires_at, revoked)
      2. RefreshToken() 호출 시 DB에서 토큰 유효성 검증
      3. 새 리프레시 토큰 발급 시 기존 토큰 revoked 처리
      4. Logout() 구현 시 해당 사용자의 모든 리프레시 토큰 revoked 처리
    threat_refs: [TM-001]
    vuln_refs: []
    arch_refs: [COMP-002, AD-003]

  - id: SRV-002
    category: authz
    title: "휴가 승인/반려 API에 관리자 역할 검증 불완전"
    severity: high
    description: >
      PUT /api/leaves/:id/approve, PUT /api/leaves/:id/reject 엔드포인트에서
      JWT 인증은 수행하지만, 요청자가 해당 휴가 신청자의 관리자인지 검증하지 않음.
      인증된 모든 사용자가 아무 휴가나 승인/반려할 수 있음.
    location:
      file: internal/leave/service.go
      line: 112
      function: Approve
    current_state: >
      Approve()는 leaveId로 휴가를 조회하고 상태를 approved로 변경.
      요청자의 역할이나 부서 관계를 검증하지 않음.
    expected_state: >
      승인/반려 시 다음을 검증해야 함:
      1. 요청자가 manager 역할인지
      2. 요청자가 해당 휴가 신청자의 상위 관리자인지 (부서 관계)
      3. 자기 자신의 휴가를 승인할 수 없는지
    remediation: >
      func (s *LeaveService) Approve(ctx context.Context, leaveID string, approverCtx UserContext) error {
        leave, _ := s.repo.GetByID(ctx, leaveID)
        if approverCtx.Role != "manager" { return ErrForbidden }
        if !s.isManagerOf(approverCtx.UserID, leave.RequesterID) { return ErrForbidden }
        if approverCtx.UserID == leave.RequesterID { return ErrSelfApproval }
        return s.repo.UpdateStatus(ctx, leaveID, "approved", approverCtx.UserID)
      }
    threat_refs: [TM-002]
    vuln_refs: [VA-002]
    arch_refs: [COMP-003, COMP-001]

  - id: SRV-003
    category: authn
    title: "로그인 실패 시 사용자 존재 여부 유추 가능한 차별적 응답"
    severity: medium
    description: >
      Login() 함수에서 "사용자를 찾을 수 없습니다"와 "비밀번호가 일치하지 않습니다"를
      구분하여 응답하고 있어, 공격자가 유효한 이메일 주소를 열거할 수 있음.
    location:
      file: internal/auth/service.go
      line: 35
      function: Login
    current_state: >
      사용자 미존재 시 "user not found", 비밀번호 불일치 시 "invalid password" 반환.
    expected_state: >
      사용자 미존재와 비밀번호 불일치 모두 동일한 "invalid credentials" 메시지 반환.
      응답 시간도 일정하게 유지 (타이밍 공격 방어).
    remediation: >
      두 경우 모두 동일한 에러 메시지를 반환하세요.
      if user == nil || !bcrypt.CompareHashAndPassword(user.PasswordHash, password) {
        return nil, ErrInvalidCredentials // "Invalid email or password"
      }
      참고: 사용자 미존재 시에도 bcrypt.CompareHashAndPassword를 호출하여 응답 시간 일정하게 유지.
    threat_refs: [TM-001, TM-004]
    vuln_refs: []
    arch_refs: [COMP-002]

  - id: SRV-004
    category: input_validation
    title: "휴가 신청 시 날짜 범위 검증 불완전"
    severity: medium
    description: >
      LeaveService.Create()에서 시작일이 종료일보다 이후인지만 검증하고,
      과거 날짜 신청, 최대 연속 휴가 일수 초과, 공휴일 중복 등의
      비즈니스 로직 검증이 없음. 비즈니스 로직 악용으로 잔여 일수 조작 가능.
    location:
      file: internal/leave/validator.go
      line: 15
      function: ValidateLeaveRequest
    current_state: >
      startDate < endDate만 검증. 과거 날짜, 음수 일수, 100일 연속 휴가 등 허용.
    expected_state: >
      서버 측에서 다음을 검증:
      - 시작일 ≥ 오늘
      - 연속 휴가 일수 ≤ 정책 상한
      - 잔여 휴가 일수 ≥ 신청 일수
      - 기존 승인된 휴가와 날짜 중복 없음
    remediation: >
      ValidateLeaveRequest()에 추가 검증 로직을 구현하세요.
      비즈니스 규칙은 서비스 계층에서, 형식 검증은 validator에서 수행.
    threat_refs: []
    vuln_refs: []
    arch_refs: [COMP-003]

  - id: SRV-005
    category: data_protection
    title: "알림 이메일 템플릿에 민감 정보 포함 가능"
    severity: low
    description: >
      NotificationService의 이메일 템플릿에서 휴가 사유(reason)를 그대로 포함하고 있음.
      이메일은 암호화되지 않은 채널이므로 민감한 사유(건강 문제 등)가 노출될 수 있음.
    location:
      file: internal/notification/template.go
      line: 22
      function: RenderLeaveRequest
    current_state: "이메일 본문에 휴가 사유 전문 포함"
    expected_state: "이메일에는 최소 정보만 포함하고, 상세 내용은 시스템 링크로 안내"
    remediation: >
      이메일 템플릿에서 휴가 사유를 제거하고 시스템 링크만 포함하세요.
      "{{name}}님이 {{startDate}}~{{endDate}} 휴가를 신청했습니다. 상세 내용은 시스템에서 확인하세요: {{link}}"
    threat_refs: [TM-004]
    vuln_refs: []
    arch_refs: [COMP-004]
```

## 대응 전략 구현 매트릭스

```yaml
mitigation_matrix:
  - threat_ref: TM-001
    mitigation: "RS256 알고리즘 고정, 키 길이 2048비트 이상, 만료 시간 15분, 리프레시 토큰 별도 관리, 키 로테이션"
    implementation_status: partial
    code_location: internal/auth/jwt.go:10-55
    verification_notes: >
      - 알고리즘 고정: 미구현 — VA-001에서 보고됨
      - 키 길이: 구현됨 — RSA 2048비트 키 사용 확인
      - 만료 시간: 구현됨 — 15분 설정 확인
      - 리프레시 토큰: 부분 구현 — 발급은 되나 서버 측 무효화 부재 (SRV-001)
      - 키 로테이션: 미구현 — 단일 고정 키 사용

  - threat_ref: TM-002
    mitigation: "모든 리소스 접근 시 소유권 검증, 관리자 역할은 부서 범위 내 접근"
    implementation_status: missing
    code_location: internal/leave/service.go:45-120
    verification_notes: >
      - 소유권 검증: 미구현 — VA-002에서 보고됨
      - 관리자 부서 범위: 미구현 — SRV-002에서 보고됨
      - 자기 승인 방지: 미구현

  - threat_ref: TM-003
    mitigation: "sqlc 파라미터화 쿼리 일관 사용, 동적 쿼리 금지, 입력 화이트리스트"
    implementation_status: partial
    code_location: internal/leave/repository.go:1-80
    verification_notes: >
      - sqlc 파라미터화: 구현됨 — 대부분 쿼리에서 sqlc 사용 확인
      - 동적 쿼리: 위반 — 정렬 파라미터에서 문자열 연결 사용 (VA-003)
      - 입력 화이트리스트: 미구현

  - threat_ref: TM-004
    mitigation: "bcrypt(cost≥12) 해싱, 프로덕션 에러 상세 제거, 로그 PII 마스킹"
    implementation_status: partial
    code_location: internal/auth/service.go, internal/handler/middleware.go
    verification_notes: >
      - bcrypt 해싱: 구현됨 — cost 12 확인
      - 에러 상세 제거: 미구현 — VA-004에서 보고됨
      - PII 마스킹: 미구현 — 로그에 이메일 주소 평문 기록

  - threat_ref: TM-005
    mitigation: "보안 이벤트 감사 로그 기록"
    implementation_status: missing
    code_location: N/A
    verification_notes: >
      보안 이벤트 로깅이 전혀 구현되지 않음 — VA-005에서 보고됨

  - threat_ref: TM-006
    mitigation: "IP 기반 레이트 리미팅, 커넥션 풀 제한, 요청 크기 제한, 타임아웃"
    implementation_status: partial
    code_location: internal/handler/router.go, cmd/server/main.go
    verification_notes: >
      - 레이트 리미팅: 미구현 — VA-006에서 보고됨
      - 커넥션 풀: 구현됨 — DB 커넥션 풀 25개 설정 확인
      - 요청 크기 제한: 미구현
      - 타임아웃: 구현됨 — 서버 타임아웃 30초 설정 확인

  - threat_ref: TM-007
    mitigation: "SMTP 자격 증명 시크릿 매니저 저장, 발송 IP 화이트리스트"
    implementation_status: partial
    code_location: internal/notification/smtp.go, .env.example
    verification_notes: >
      - 환경 변수 사용: 구현됨 — 코드에 하드코딩 없음
      - .env.example: 주의 필요 — 예시 값 포함 (VA-007)
      - 시크릿 매니저: 미구현 — 환경 변수 직접 사용
      - 발송 IP 화이트리스트: 미구현 (인프라 레벨)
```
