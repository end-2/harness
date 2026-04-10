# 코드 리뷰 출력 예시

> internal/leave/handler.go 리뷰 결과

---

## 리뷰 리포트

```yaml
review_report:
  summary:
    total_modules: 1
    compliant_modules: 0
    issues_found: 7
    auto_fixable: 5
    escalations: 2

  arch_compliance:
    - component_ref: COMP-002
      module_path: internal/leave/handler.go
      status: deviation
      checks:
        responsibility: FAIL
        dependencies: FAIL
        interfaces: pass
        patterns: FAIL
      details:
        - issue: "COMP-002(leave)가 COMP-004(notification)의 책임인 이메일 발송을 직접 수행"
          arch_ref: COMP-002, COMP-004
          severity: critical
        - issue: "store.Store에 직접 의존 — Repository 인터페이스를 통한 추상화 없음 (AD-003 위반)"
          arch_ref: AD-003
          severity: critical
        - issue: "Layered Architecture 미반영 — handler에서 DB 직접 접근 (AD-002 위반)"
          arch_ref: AD-002
          severity: critical

  clean_code_issues:
    - location: "internal/leave/handler.go:20-45"
      principle: "SRP — Apply 핸들러가 검증, 생성, 알림을 모두 수행"
      severity: medium
      suggestion: "비즈니스 로직을 service.go로 분리, 알림을 notification 모듈로 위임"
      auto_fixable: true

    - location: "internal/leave/handler.go:25"
      principle: "에러 처리 — c.Bind(&req) 에러 무시"
      severity: high
      suggestion: "if err := c.Bind(&req); err != nil { return err } 패턴 적용"
      auto_fixable: true

    - location: "internal/leave/handler.go:29,34"
      principle: "에러 처리 — db.GetLeaveBalance, db.CreateLeave 에러 무시"
      severity: high
      suggestion: "모든 error return을 검사하고 적절히 처리"
      auto_fixable: true

    - location: "internal/leave/handler.go:47-49"
      principle: "SRP — sendEmail, formatLeaveEmail이 leave 패키지에 위치"
      severity: medium
      suggestion: "notification 모듈로 이동 (COMP-004 책임)"
      auto_fixable: true

    - location: "internal/leave/handler.go:20"
      principle: "타입 안전성 — 인라인 struct 대신 정의된 DTO 사용"
      severity: low
      suggestion: "dto.go에 ApplyRequest 타입 정의"
      auto_fixable: true

  security_issues:
    - location: "internal/leave/handler.go:25"
      category: "입력 검증"
      severity: high
      suggestion: "요청 바인딩 후 필수 필드 검증 (leave_type, start_date, end_date)"

  auto_fixable:
    - "에러 처리 추가 (c.Bind, db 호출)"
    - "비즈니스 로직을 service.go로 분리"
    - "인라인 struct → 정의된 DTO 타입"

  escalations:
    - title: "COMP-002가 COMP-004 책임을 침범"
      description: |
        leave 모듈이 이메일 발송(sendEmail, formatLeaveEmail)을 직접 수행하고 있습니다.
        Arch 산출물에서 COMP-004(notification)가 알림 발송 책임을 담당하도록 정의되어 있습니다.
      arch_ref: COMP-002, COMP-004
      question: "이것은 의도적 편차인가요?"

    - title: "Repository 패턴 미적용 (AD-003 위반)"
      description: |
        leave 핸들러가 store.Store에 직접 의존합니다.
        AD-003에서 "각 도메인 엔티티별 Repository 인터페이스를 정의하고 구현체를 분리"로 결정되었습니다.
      arch_ref: AD-003
      question: "store.Store 직접 의존을 Repository 인터페이스로 변경해야 하는지 확인합니다."

  verdict: ESCALATE
```

---

## 요약

| 분류 | 건수 | 처리 |
|------|------|------|
| Arch 계약 위반 (critical) | 2 | 사용자 에스컬레이션 |
| 에러 처리 누락 (high) | 2 | refactor 자동 수정 |
| SRP 위반 (medium) | 2 | refactor 자동 수정 |
| 타입 안전성 (low) | 1 | refactor 자동 수정 |
| 입력 검증 (high) | 1 | refactor 자동 수정 (보안) |

**판정: `ESCALATE`** — Arch 계약 위반 2건에 대한 사용자 확인 필요
