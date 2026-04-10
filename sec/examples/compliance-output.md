# 컴플라이언스 검증 출력 예시

> 휴가 관리 시스템의 컴플라이언스 검증 결과입니다.
> 적용 표준: OWASP ASVS Level 2 (v4.0) — CON-001 개인정보보호법 hard 제약 기반

## 컴플라이언스 리포트

```yaml
compliance_report:
  - id: CR-001
    standard: OWASP-ASVS-L2
    version: "4.0"
    scope: "전체 시스템 (COMP-001 ~ COMP-005)"
    overall_status: partial
    total_requirements: 134
    compliant_count: 98
    non_compliant_count: 24
    not_applicable_count: 12
    findings:
      # V2: Authentication
      - requirement_id: "V2.1.1"
        title: "비밀번호 최소 12자 이상"
        status: non_compliant
        evidence: "internal/auth/service.go — 비밀번호 길이 검증 로직 부재"
        gap_description: "비밀번호 정책이 서버 측에서 검증되지 않음"
        remediation: "Register()에 비밀번호 정책 검증 추가 (최소 12자, 대소문자+숫자+특수문자)"

      - requirement_id: "V2.2.1"
        title: "인증 실패 시 일반 메시지 사용"
        status: non_compliant
        evidence: "SRV-003 — 사용자 존재 여부 유추 가능한 차별적 응답"
        gap_description: "로그인 실패 시 'user not found'와 'invalid password'를 구분하여 응답"
        remediation: "두 경우 모두 'Invalid credentials' 반환"

      - requirement_id: "V2.5.2"
        title: "비밀번호 bcrypt cost ≥ 12"
        status: compliant
        evidence: "internal/auth/service.go:22 — bcrypt.GenerateFromPassword(password, 12)"
        gap_description: ""
        remediation: ""

      - requirement_id: "V2.8.1"
        title: "계정 잠금 또는 점진적 지연"
        status: non_compliant
        evidence: "VA-006 — 레이트 리미팅 미적용"
        gap_description: "로그인 실패 횟수 제한 또는 계정 잠금 메커니즘이 없음"
        remediation: "5회 실패 시 계정 잠금 (15분) 또는 점진적 지연 구현"

      # V3: Session Management
      - requirement_id: "V3.2.1"
        title: "로그아웃 시 서버 측 세션 무효화"
        status: non_compliant
        evidence: "SRV-001 — 리프레시 토큰 서버 측 무효화 부재"
        gap_description: "로그아웃 후에도 리프레시 토큰으로 새 토큰 발급 가능"
        remediation: "리프레시 토큰 DB 저장 및 로그아웃 시 revoked 처리"

      - requirement_id: "V3.5.1"
        title: "토큰 기반 세션의 리프레시 토큰 로테이션"
        status: non_compliant
        evidence: "SRV-001 — 토큰 로테이션 미구현"
        gap_description: "리프레시 토큰 사용 시 기존 토큰 무효화 없음"
        remediation: "리프레시 토큰 사용 시 새 토큰 발급 + 기존 토큰 revoked"

      # V4: Access Control
      - requirement_id: "V4.1.1"
        title: "모든 보호 리소스에 서버 측 접근 제어"
        status: non_compliant
        evidence: "VA-002, SRV-002 — 소유권 검증 및 역할 검증 부재"
        gap_description: "인증된 사용자가 타인 데이터 접근 및 무단 승인 가능"
        remediation: "모든 리소스 접근에 소유권/역할 검증 추가"

      - requirement_id: "V4.2.1"
        title: "기본 거부 정책"
        status: partial
        evidence: "JWT 미들웨어로 인증은 기본 거부하나, 인가는 기본 허용 상태"
        gap_description: "인증은 적용되나 리소스 수준 인가가 미적용"
        remediation: "인가 미들웨어 추가하여 기본 거부 후 명시적 허용"

      # V5: Validation
      - requirement_id: "V5.2.1"
        title: "모든 입력에 서버 측 검증"
        status: partial
        evidence: "go-playground/validator 사용하나, 정렬 파라미터 검증 누락 (VA-003)"
        gap_description: "일부 동적 파라미터가 검증 없이 쿼리에 전달"
        remediation: "정렬/필터 파라미터 화이트리스트 검증 추가"

      # V7: Error Handling
      - requirement_id: "V7.1.1"
        title: "에러 메시지에 민감 정보 미포함"
        status: non_compliant
        evidence: "VA-004 — 에러 응답에 DB 스키마 정보 노출"
        gap_description: "프로덕션 에러 응답에 내부 에러 메시지 그대로 포함"
        remediation: "프로덕션 에러 핸들러에서 일반 메시지만 반환"

      - requirement_id: "V7.2.1"
        title: "보안 이벤트 로깅"
        status: non_compliant
        evidence: "VA-005 — 보안 이벤트 로깅 전혀 미구현"
        gap_description: "인증 시도, 접근 제어 실패 등 보안 이벤트가 기록되지 않음"
        remediation: "보안 이벤트 전용 로거 구현"

      # V8: Data Protection
      - requirement_id: "V8.3.1"
        title: "민감 데이터 전송 시 TLS"
        status: compliant
        evidence: "배포 환경에서 HTTPS 강제 설정 확인"
        gap_description: ""
        remediation: ""

      # V9: Communication
      - requirement_id: "V9.1.1"
        title: "TLS 적용"
        status: compliant
        evidence: "HTTPS 설정 확인"
        gap_description: ""
        remediation: ""

      # V14: Configuration
      - requirement_id: "V14.4.1"
        title: "보안 응답 헤더 설정"
        status: non_compliant
        evidence: "VA-008 — CSP, HSTS, X-Frame-Options 등 미설정"
        gap_description: "보안 응답 헤더가 전혀 설정되지 않음"
        remediation: "Echo Secure 미들웨어 적용"

    gap_summary:
      - severity: high
        count: 8
        items: ["V2.1.1", "V2.8.1", "V3.2.1", "V3.5.1", "V4.1.1", "V5.2.1", "V7.1.1", "V7.2.1"]
      - severity: medium
        count: 4
        items: ["V2.2.1", "V4.2.1", "V14.4.1", "V8.3.4"]

    remediation_roadmap:
      - priority: 1
        items: ["V4.1.1", "V5.2.1"]
        effort: "3일"
        description: "접근 제어 강화 — 소유권 검증, 역할 검증, 입력 화이트리스트 추가"
      - priority: 2
        items: ["V3.2.1", "V3.5.1", "V2.8.1"]
        effort: "5일"
        description: "세션/인증 강화 — 리프레시 토큰 DB 저장, 토큰 로테이션, 계정 잠금"
      - priority: 3
        items: ["V7.1.1", "V7.2.1", "V2.2.1", "V2.1.1"]
        effort: "3일"
        description: "에러 핸들링/로깅/인증 개선 — 에러 응답 정리, 감사 로그, 비밀번호 정책"
      - priority: 4
        items: ["V14.4.1", "V4.2.1"]
        effort: "1일"
        description: "설정 강화 — 보안 헤더, 기본 거부 인가 정책"

    constraint_refs: [CON-001]
    threat_refs: [TM-001, TM-002, TM-003, TM-004, TM-005, TM-006]
    vuln_refs: [VA-001, VA-002, VA-003, VA-004, VA-005, VA-006, VA-008]
```

## 통합 보안 권고

```yaml
security_recommendations:
  - id: SR-001
    title: "리소스 수준 접근 제어 전면 구현"
    category: code
    priority: 1
    description: >
      현재 인증(AuthN)은 JWT 미들웨어로 구현되어 있으나, 인가(AuthZ)가
      리소스 수준에서 구현되지 않아 IDOR과 무단 승인이 가능함.
      TM-002 위협의 대응 전략이 완전히 미구현 상태.
    current_state: "인증된 사용자는 모든 리소스에 접근 가능 (소유권/역할 무관)"
    recommended_action: >
      1. 모든 리소스 접근 API에 소유권 검증 추가 (userId == resource.ownerId)
      2. 관리자 API에 역할 + 부서 범위 검증 추가
      3. 자기 승인 방지 로직 추가
      4. 인가 미들웨어를 구현하여 기본 거부 정책 적용
    alternative_actions:
      - action: "RBAC 라이브러리(casbin) 도입"
        trade_off: "초기 설정 복잡도 증가, 그러나 향후 권한 모델 확장 용이"
    affected_components: [COMP-001, COMP-003]
    threat_refs: [TM-002]
    vuln_refs: [VA-002]
    arch_refs: [COMP-001, COMP-003, AD-002]
    re_refs: [FR-002, NFR-003]

  - id: SR-002
    title: "JWT 인증 보안 강화"
    category: code
    priority: 2
    description: >
      JWT 알고리즘 미고정(VA-001)과 리프레시 토큰 무효화 부재(SRV-001)로
      인증 체계의 근본적 보안이 취약함. TM-001 위협의 대응 전략이 부분 구현 상태.
    current_state: "알고리즘 혼동 공격 가능, 로그아웃 후 토큰 재사용 가능"
    recommended_action: >
      1. jwt.Parse()에 ValidMethods: []string{"RS256"} 고정
      2. refresh_tokens 테이블 생성 및 토큰 로테이션 구현
      3. 로그아웃 시 리프레시 토큰 revoked 처리
      4. 키 로테이션 메커니즘 구현 (kid 헤더 활용)
    alternative_actions:
      - action: "세션 기반 인증으로 전환"
        trade_off: "수평 확장 시 세션 스토어(Redis) 필요, 그러나 즉시 무효화 가능"
    affected_components: [COMP-002, COMP-001]
    threat_refs: [TM-001]
    vuln_refs: [VA-001]
    arch_refs: [COMP-002, AD-003]
    re_refs: [NFR-003, CON-001]

  - id: SR-003
    title: "SQL 인젝션 방어 완성"
    category: code
    priority: 3
    description: >
      sqlc 기반 쿼리는 안전하나 동적 정렬 파라미터에서 문자열 연결 사용으로
      SQL 인젝션이 가능함. TM-003 대응 전략 부분 구현.
    current_state: "정렬 파라미터가 검증 없이 SQL 쿼리에 직접 삽입"
    recommended_action: >
      정렬/필터 파라미터를 화이트리스트로 검증하세요.
      allowedFields := map[string]bool{"created_at": true, "start_date": true, "status": true}
    alternative_actions: []
    affected_components: [COMP-003, COMP-005]
    threat_refs: [TM-003]
    vuln_refs: [VA-003]
    arch_refs: [COMP-003, COMP-005, AD-004]
    re_refs: [NFR-003]

  - id: SR-004
    title: "보안 이벤트 감사 로깅 구현"
    category: code
    priority: 4
    description: >
      보안 이벤트 로깅이 전혀 없어 사고 발생 시 원인 추적 불가.
      TM-005 (부인 방지) 대응 전략 완전 미구현. CON-001 개인정보보호법의
      접근 기록 요구사항 미충족.
    current_state: "보안 이벤트에 대한 감사 로깅 없음"
    recommended_action: >
      slog 기반 보안 이벤트 로거 구현:
      - 인증 시도 (성공/실패, IP, userId, timestamp)
      - 접근 제어 실패 (거부된 리소스, userId)
      - 데이터 변경 (휴가 생성/수정/삭제/승인/반려)
      - 민감 데이터 접근 (개인정보 조회)
    alternative_actions:
      - action: "OpenTelemetry 기반 구조화된 로깅 + 외부 SIEM 연동"
        trade_off: "초기 설정 복잡, 그러나 장기적으로 모니터링 통합 가능"
    affected_components: [COMP-001, COMP-002, COMP-003]
    threat_refs: [TM-005]
    vuln_refs: [VA-005]
    arch_refs: [COMP-001, COMP-002, COMP-003]
    re_refs: [NFR-003, CON-001]

  - id: SR-005
    title: "에러 응답 보안 강화"
    category: code
    priority: 5
    description: >
      에러 응답에 내부 정보 노출(VA-004)과 인증 실패 시 차별적 응답(SRV-003) 수정.
    current_state: "에러 응답에 DB 스키마 노출, 로그인 실패 시 사용자 존재 여부 유추 가능"
    recommended_action: >
      1. 프로덕션 에러 핸들러에서 일반 메시지만 반환
      2. 로그인 실패 시 통일된 'Invalid credentials' 반환
      3. 내부 에러는 서버 로그에만 기록
    alternative_actions: []
    affected_components: [COMP-001, COMP-002]
    threat_refs: [TM-004, TM-001]
    vuln_refs: [VA-004]
    arch_refs: [COMP-001, COMP-002]
    re_refs: []

  - id: SR-006
    title: "레이트 리미팅 및 DoS 방어 구현"
    category: configuration
    priority: 6
    description: >
      모든 API 엔드포인트에 레이트 리미팅이 없어 브루트포스와 DoS 공격에 취약.
      TM-006 대응 전략 미구현.
    current_state: "레이트 리미팅 및 요청 크기 제한 없음"
    recommended_action: >
      1. Echo RateLimiter 미들웨어 적용 (일반: 100req/min, 인증: 10req/min)
      2. 요청 크기 제한 (1MB)
      3. 계정 잠금 또는 점진적 지연 구현
    alternative_actions:
      - action: "API Gateway (Kong, Nginx) 앞단에서 레이트 리미팅"
        trade_off: "인프라 복잡도 증가, 그러나 애플리케이션 코드 변경 최소화"
    affected_components: [COMP-001]
    threat_refs: [TM-006]
    vuln_refs: [VA-006]
    arch_refs: [COMP-001, AD-005]
    re_refs: [NFR-001]

  - id: SR-007
    title: "보안 응답 헤더 설정"
    category: configuration
    priority: 7
    description: "CSP, HSTS, X-Frame-Options 등 보안 헤더 미설정"
    current_state: "보안 응답 헤더 없음"
    recommended_action: "Echo Secure 미들웨어 적용"
    alternative_actions: []
    affected_components: [COMP-001]
    threat_refs: []
    vuln_refs: [VA-008]
    arch_refs: [COMP-001]
    re_refs: []
```

## 최종 보안 리포트 요약

```
📋 보안 분석 최종 리포트

## 1. 위협 모델 요약
- 식별된 위협: 7건 (Critical: 0, High: 4, Medium: 3, Low: 0)
- 대응 전략 구현 현황: 구현됨 0건, 부분 4건, 미구현 3건

## 2. 취약점 보고서 요약
- 발견된 취약점: 8건 (Critical: 0, High: 3, Medium: 3, Low: 2)
- 의존성 취약점: 0건
- 시크릿 노출: 1건 (VA-007, low)

## 3. 보안 권고 (우선순위순)
1. [SR-001] 리소스 수준 접근 제어 전면 구현 — code — 영향: COMP-001, COMP-003
2. [SR-002] JWT 인증 보안 강화 — code — 영향: COMP-002, COMP-001
3. [SR-003] SQL 인젝션 방어 완성 — code — 영향: COMP-003, COMP-005
4. [SR-004] 보안 이벤트 감사 로깅 구현 — code — 영향: COMP-001~003
5. [SR-005] 에러 응답 보안 강화 — code — 영향: COMP-001, COMP-002
6. [SR-006] 레이트 리미팅 및 DoS 방어 — configuration — 영향: COMP-001
7. [SR-007] 보안 응답 헤더 설정 — configuration — 영향: COMP-001

## 4. 컴플라이언스 현황
- OWASP ASVS Level 2: partial (98/134 준수, 73%)
  - High 갭: 8건
  - Medium 갭: 4건
  - 개선 로드맵: 약 12일 (4단계) 소요 예상
```
