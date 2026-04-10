# 보안 감사 출력 예시

> 휴가 관리 시스템의 Impl 산출물을 기반으로 보안 감사를 수행한 결과입니다.

## 취약점 보고서

```yaml
vulnerability_report:
  - id: VA-001
    title: "JWT 알고리즘 미고정 — 알고리즘 혼동 공격 가능"
    cwe_id: CWE-327
    owasp_category: "A02:2021-Cryptographic Failures"
    severity: high
    cvss_score: 8.1
    cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N"
    location:
      file: internal/auth/jwt.go
      line: 23
      function: ValidateToken
    description: >
      JWT 토큰 검증 시 알고리즘을 명시적으로 고정하지 않고 토큰 헤더의 alg 필드를
      신뢰하고 있음. 공격자가 alg을 'none'으로 설정하거나 HS256으로 변경하여
      공개 키로 서명하면 인증을 우회할 수 있음.
    proof_of_concept: >
      1. 유효한 JWT 토큰 획득
      2. 토큰 헤더를 base64 디코딩
      3. "alg": "none"으로 변경
      4. 서명 부분 제거
      5. 변조된 토큰으로 API 호출 → 인증 우회
    remediation: >
      jwt.Parse() 호출 시 ValidMethods 옵션으로 허용 알고리즘을 RS256으로
      고정하세요. jwt.WithValidMethods([]string{"RS256"}) 사용.
    remediation_effort: trivial
    impl_refs: [IM-002, IDR-002]
    arch_refs: [COMP-002, AD-003]
    re_refs: [NFR-003]
    threat_refs: [TM-001]

  - id: VA-002
    title: "휴가 조회 API에 소유권 검증 부재 (IDOR)"
    cwe_id: CWE-639
    owasp_category: "A01:2021-Broken Access Control"
    severity: high
    cvss_score: 7.5
    cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N"
    location:
      file: internal/leave/service.go
      line: 45
      function: GetByID
    description: >
      LeaveService.GetByID()에서 요청자의 userId와 휴가 신청자의 requesterId를
      비교하지 않음. 인증된 사용자가 leave ID를 변경하여 다른 사용자의 휴가 데이터를
      조회할 수 있음.
    proof_of_concept: >
      1. 사용자 A로 로그인하여 JWT 토큰 획득
      2. GET /api/leaves/1 (자신의 휴가) → 정상 응답
      3. GET /api/leaves/2 (사용자 B의 휴가) → 타인 데이터 접근 가능
    remediation: >
      GetByID()에서 조회된 leave.RequesterId와 요청자 userCtx.UserId를 비교하세요.
      관리자 역할은 부서 범위 내에서만 접근 허용.
      if leave.RequesterID != userCtx.UserID && !isManagerOf(userCtx, leave.RequesterID) { return ErrForbidden }
    remediation_effort: trivial
    impl_refs: [IM-003]
    arch_refs: [COMP-003, COMP-001]
    re_refs: [FR-002, NFR-003]
    threat_refs: [TM-002]

  - id: VA-003
    title: "휴가 목록 조회 시 동적 정렬 파라미터에 SQL 인젝션 가능"
    cwe_id: CWE-89
    owasp_category: "A03:2021-Injection"
    severity: high
    cvss_score: 8.6
    cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H"
    location:
      file: internal/leave/repository.go
      line: 67
      function: ListByUser
    description: >
      sqlc로 생성된 기본 쿼리는 안전하나, 정렬 파라미터(sort_by, order)를
      문자열 연결로 SQL 쿼리에 직접 삽입하고 있음. 공격자가 정렬 파라미터에
      SQL 구문을 주입할 수 있음.
    proof_of_concept: >
      GET /api/leaves?sort_by=created_at;DROP TABLE leaves--&order=asc
      → SQL: SELECT ... ORDER BY created_at;DROP TABLE leaves-- asc
    remediation: >
      정렬 필드를 화이트리스트로 검증하세요.
      allowedSortFields := map[string]bool{"created_at": true, "start_date": true, "status": true}
      if !allowedSortFields[sortBy] { sortBy = "created_at" }
    remediation_effort: trivial
    impl_refs: [IM-003, IDR-003]
    arch_refs: [COMP-003, COMP-005, AD-004]
    re_refs: [NFR-003]
    threat_refs: [TM-003]

  - id: VA-004
    title: "에러 응답에 스택 트레이스 및 DB 스키마 노출"
    cwe_id: CWE-209
    owasp_category: "A05:2021-Security Misconfiguration"
    severity: medium
    cvss_score: 5.3
    cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N"
    location:
      file: internal/handler/middleware.go
      line: 78
      function: ErrorHandler
    description: >
      커스텀 에러 핸들러에서 err.Error()를 그대로 JSON 응답에 포함하고 있음.
      데이터베이스 에러 발생 시 테이블 이름, 칼럼 이름 등 스키마 정보가
      클라이언트에 노출됨.
    proof_of_concept: >
      유효하지 않은 UUID 형식의 leave ID로 요청:
      GET /api/leaves/invalid-uuid
      → 응답: {"error": "pq: invalid input syntax for type uuid: \"invalid-uuid\""}
    remediation: >
      프로덕션 환경에서는 내부 에러 상세를 숨기고 일반 메시지를 반환하세요.
      내부 에러는 서버 로그에만 기록하세요.
      응답: {"error": "Internal server error", "request_id": "xxx"}
    remediation_effort: trivial
    impl_refs: [IM-001]
    arch_refs: [COMP-001]
    re_refs: []
    threat_refs: [TM-004]

  - id: VA-005
    title: "보안 이벤트 로깅 부재"
    cwe_id: CWE-778
    owasp_category: "A09:2021-Security Logging and Monitoring Failures"
    severity: medium
    cvss_score: 5.5
    cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:L"
    location:
      file: internal/auth/service.go
      line: 30
      function: Login
    description: >
      인증 성공/실패, 접근 제어 실패, 권한 변경 등 보안 이벤트에 대한
      감사 로깅이 구현되지 않음. 보안 사고 발생 시 원인 추적이 불가능.
    proof_of_concept: "N/A — 부재 확인"
    remediation: >
      보안 이벤트 전용 로거를 구현하세요. 최소한 다음을 기록:
      - 인증 시도 (성공/실패, IP, 사용자 ID, 타임스탬프)
      - 접근 제어 실패 (거부된 리소스, 사용자 ID)
      - 휴가 승인/반려 (승인자 ID, 대상 leave ID)
      slog.Info("auth.login", "userId", userId, "ip", ip, "success", true)
    remediation_effort: moderate
    impl_refs: [IM-002, IM-001]
    arch_refs: [COMP-002, COMP-001]
    re_refs: [NFR-003]
    threat_refs: [TM-005]

  - id: VA-006
    title: "레이트 리미팅 미적용"
    cwe_id: CWE-770
    owasp_category: "A05:2021-Security Misconfiguration"
    severity: medium
    cvss_score: 5.3
    cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L"
    location:
      file: internal/handler/router.go
      line: 15
      function: SetupRoutes
    description: >
      모든 API 엔드포인트에 레이트 리미팅이 적용되지 않음. 인증 엔드포인트
      (로그인, 회원가입)에 대한 브루트포스 공격과 일반 API에 대한 DoS 공격에 취약.
    proof_of_concept: "N/A — 부재 확인"
    remediation: >
      Echo 미들웨어로 레이트 리미팅을 추가하세요.
      middleware.RateLimiter(middleware.NewRateLimiterMemoryStore(rate.Limit(100)))
      인증 엔드포인트는 별도로 10req/min 제한.
    remediation_effort: trivial
    impl_refs: [IM-001, IDR-002]
    arch_refs: [COMP-001, AD-005]
    re_refs: [NFR-001]
    threat_refs: [TM-006]

  - id: VA-007
    title: "SMTP 자격 증명이 .env.example에 예시 값으로 포함"
    cwe_id: CWE-312
    owasp_category: "A02:2021-Cryptographic Failures"
    severity: low
    cvss_score: 3.7
    cvss_vector: "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N"
    location:
      file: .env.example
      line: 8
      function: null
    description: >
      .env.example 파일에 SMTP_PASSWORD=example_password123 형태의 예시 값이
      포함되어 있음. 실제 크리덴셜은 아니지만, 개발 환경에서 이 값을 그대로 사용할 위험.
    proof_of_concept: "N/A"
    remediation: >
      .env.example에서 시크릿 값은 플레이스홀더로 변경하세요.
      SMTP_PASSWORD=<your-smtp-password-here>
    remediation_effort: trivial
    impl_refs: [IM-004]
    arch_refs: [COMP-004]
    re_refs: [FR-004]
    threat_refs: [TM-007]

  - id: VA-008
    title: "보안 응답 헤더 미설정"
    cwe_id: CWE-16
    owasp_category: "A05:2021-Security Misconfiguration"
    severity: low
    cvss_score: 3.7
    cvss_vector: "CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N"
    location:
      file: internal/handler/router.go
      line: 15
      function: SetupRoutes
    description: >
      Content-Security-Policy, Strict-Transport-Security, X-Frame-Options,
      X-Content-Type-Options 등 보안 응답 헤더가 설정되지 않음.
    proof_of_concept: "N/A — 부재 확인"
    remediation: >
      Echo의 Secure 미들웨어를 추가하세요.
      e.Use(middleware.SecureWithConfig(middleware.SecureConfig{
        XSSProtection: "1; mode=block",
        ContentTypeNosniff: "nosniff",
        XFrameOptions: "DENY",
        HSTSMaxAge: 31536000,
        ContentSecurityPolicy: "default-src 'self'",
      }))
    remediation_effort: trivial
    impl_refs: [IM-001]
    arch_refs: [COMP-001]
    re_refs: []
    threat_refs: []
```
