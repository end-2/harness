# 테스트 리뷰 출력 예시

> 휴가 관리 시스템 — RTM + 리뷰 리포트 + 갭 분류

---

## 요구사항 추적 매트릭스 (RTM)

```yaml
- re_id: FR-001
  re_title: "사내 SSO 로그인"
  re_priority: Must
  arch_refs: [COMP-001, AD-001]
  impl_refs: [IM-001]
  test_refs: [TS-001-C01, TS-001-C02, TS-001-C03, TS-001-C04]
  coverage_status: covered
  gap_description: ""

- re_id: FR-002
  re_title: "휴가 신청"
  re_priority: Must
  arch_refs: [COMP-002, AD-001]
  impl_refs: [IM-002, IDR-002]
  test_refs: [TS-002-C01, TS-002-C02, TS-002-C03, TS-002-C04, TS-002-C05, TS-002-C06, TS-002-C07, TS-002-C08, TS-002-C09, TS-002-C10, TS-002-C11]
  coverage_status: partial
  gap_description: "AC-2(시작일, 종료일, 사유 입력) — 필수 필드 누락 시 유효성 검증 테스트 없음"

- re_id: FR-003
  re_title: "휴가 승인/반려"
  re_priority: Must
  arch_refs: [COMP-003, AD-001]
  impl_refs: [IM-003, IDR-003]
  test_refs: [TS-003-C01, TS-003-C02, TS-003-C03]
  coverage_status: partial
  gap_description: "AC-4(승인/반려 즉시 이메일 알림 발송) — 알림 발송 테스트 누락"

- re_id: FR-004
  re_title: "팀 휴가 캘린더"
  re_priority: Should
  arch_refs: []
  impl_refs: [IM-006]
  test_refs: [TS-004-C01, TS-004-C02, TS-004-C03]
  coverage_status: partial
  gap_description: "AC-4(캘린더 렌더링 3초 이내) — NFR 성능 테스트에서 커버 예정이나 미생성"

- re_id: FR-005
  re_title: "잔여 휴가 조회"
  re_priority: Must
  arch_refs: [COMP-002]
  impl_refs: [IM-002]
  test_refs: [TS-005-C01, TS-005-C02, TS-005-C03]
  coverage_status: covered
  gap_description: ""

- re_id: FR-008
  re_title: "휴가 신청 취소/수정"
  re_priority: Must
  arch_refs: [COMP-002]
  impl_refs: [IM-002]
  test_refs: []
  coverage_status: uncovered
  gap_description: "테스트 스위트 전체 누락 — AC-1(대기중만 취소/수정), AC-2(승인 건 취소 요청), AC-3(변경 이력) 모두 미검증"

- re_id: NFR-001
  re_title: "응답 시간"
  re_priority: Should
  arch_refs: [AD-002]
  impl_refs: []
  test_refs: []
  coverage_status: uncovered
  gap_description: "NFR 성능 테스트 미생성 (API P95 < 1s, 캘린더 렌더링 < 3s)"

- re_id: NFR-003
  re_title: "감사 로그"
  re_priority: Should
  arch_refs: []
  impl_refs: []
  test_refs: []
  coverage_status: uncovered
  gap_description: "감사 로그 기록 완전성 테스트 미생성"
```

---

## 리뷰 리포트

```yaml
review_report:
  coverage_gaps:
    - re_id: FR-008
      gap_type: uncovered
      priority: Must
      reason: "테스트 스위트 TS-008 전체 누락. cancelLeave, modifyLeave, 상태 전이 검증 없음"
      classification: auto_remediate

    - re_id: FR-002
      gap_type: partial
      priority: Must
      reason: "AC-2 필수 필드 유효성 검증 누락 — 시작일/종료일/사유 미입력 시 동작 미검증"
      classification: auto_remediate

    - re_id: FR-003
      gap_type: partial
      priority: Must
      reason: "AC-4 이메일 알림 발송 테스트 누락 — NotificationService.sendEmail 호출 검증 없음"
      classification: auto_remediate

    - re_id: FR-004
      gap_type: partial
      priority: Should
      reason: "AC-4 캘린더 렌더링 성능 테스트 미포함"
      classification: risk_accepted

    - re_id: NFR-001
      gap_type: uncovered
      priority: Should
      reason: "NFR 성능 테스트 미생성"
      classification: risk_accepted

    - re_id: NFR-003
      gap_type: uncovered
      priority: Should
      reason: "감사 로그 기록 완전성 테스트 미생성"
      classification: risk_accepted

  strength_issues:
    - test_ref: TS-002-C01
      issue: "반환값의 상태만 확인하고 저장된 데이터의 필드 정합성 미검증"
      recommendation: "저장된 LeaveApplication의 type, startDate, endDate, reason, employeeId도 검증"

    - test_ref: TS-005-C02
      issue: "연차 자동 부여 경계값 미검증 — '3년 이상 근속 시 1일 가산' 경계인 정확히 3년 근속 케이스 없음"
      recommendation: "근속 2년 11개월, 3년 0일, 3년 1일 경계값 테스트 추가"

  code_quality_issues:
    - test_ref: TS-004
      issue: "arch_refs가 빈 배열 — 추적성 체인 단절"
      recommendation: "arch_refs에 관련 COMP-xxx 추가"

  traceability_issues:
    - test_ref: TS-004
      issue: "arch_refs 누락 — Arch 컴포넌트 역추적 불가"
      recommendation: "TS-004에 arch_refs: [COMP-002] 또는 해당 캘린더 컴포넌트 참조 추가"

    - test_ref: TS-010
      issue: "통합 테스트에 acceptance_criteria_ref 미매핑"
      recommendation: "각 테스트 케이스에 검증 대상 acceptance_criteria_ref 추가"
```

---

## 갭 분류

```yaml
gap_classification:
  auto_remediate:
    - re_id: FR-008
      reason: "취소/수정 서비스의 단위 테스트 전체 누락. acceptance_criteria 3개 모두 명확하며 상태 전이 테스트로 변환 가능"
      action: "generate 재호출 — TS-008 스위트 생성 요청"
      estimated_cases: 8

    - re_id: FR-002
      reason: "AC-2 필수 필드 유효성 검증 누락. 시작일/종료일/사유 null 또는 빈 값 입력 시 예외 검증"
      action: "generate 재호출 — TS-002에 C12, C13, C14 추가 요청"
      estimated_cases: 3

    - re_id: FR-003
      reason: "AC-4 이메일 알림 발송 검증 누락. NotificationService mock으로 sendEmail 호출 검증 가능"
      action: "generate 재호출 — TS-003에 C04 추가 요청"
      estimated_cases: 2

  risk_accepted:
    - re_id: FR-004
      priority: Should
      reason: "캘린더 렌더링 성능 테스트(AC-4) — 프론트엔드 렌더링 성능은 E2E 환경에서만 정확히 측정 가능. 현재 단계에서는 리스크 수용"
      risk_level: low
      mitigation: "수동 테스트 또는 Lighthouse CI 도입 시 자동화"

    - re_id: NFR-001
      priority: Should
      reason: "API 응답시간 P95 < 1s — 성능 테스트 도구(JMeter/Gatling) 환경 설정 필요. 현재 단계에서는 리스크 수용"
      risk_level: medium
      mitigation: "스테이징 환경 배포 후 성능 테스트 실시 권장"

    - re_id: NFR-003
      priority: Should
      reason: "감사 로그 100% 기록 — 통합 테스트에서 검증 가능하나 현재 미생성. 리스크 수용"
      risk_level: medium
      mitigation: "통합 테스트 단계에서 감사 로그 검증 포함 권장"

  escalate: []
  # 에스컬레이션 대상 없음 — 모든 Must 갭이 자동 보완 가능
```
