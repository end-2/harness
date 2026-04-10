# 테스트 리뷰 입력 예시

> 휴가 관리 시스템 — generate 산출물 + 전략 + RE/Arch/Impl 산출물 (발췌)

---

## generate 산출물 (test_suites, 발췌)

```yaml
- id: TS-001
  type: unit
  title: "인증 서비스 단위 테스트"
  target_module: src/main/java/com/company/leave/auth/
  test_cases:
    - { case_id: TS-001-C01, acceptance_criteria_ref: "FR-001.AC-1" }
    - { case_id: TS-001-C02, acceptance_criteria_ref: "FR-001.AC-2" }
    - { case_id: TS-001-C03, acceptance_criteria_ref: "FR-001.AC-3" }
    - { case_id: TS-001-C04, acceptance_criteria_ref: "FR-001.AC-4" }
  re_refs: [FR-001]
  arch_refs: [COMP-001]
  impl_refs: [IM-001]

- id: TS-002
  type: unit
  title: "휴가 신청 서비스 단위 테스트"
  target_module: src/main/java/com/company/leave/service/
  test_cases:
    - { case_id: TS-002-C01, acceptance_criteria_ref: "FR-002.AC-5" }
    - { case_id: TS-002-C02, acceptance_criteria_ref: "FR-002.AC-1" }
    - { case_id: TS-002-C03, acceptance_criteria_ref: "FR-002.AC-1" }
    - { case_id: TS-002-C04, acceptance_criteria_ref: "FR-002.AC-3" }
    - { case_id: TS-002-C05, acceptance_criteria_ref: "FR-002.AC-3" }
    - { case_id: TS-002-C06, acceptance_criteria_ref: "FR-002.AC-3" }
    - { case_id: TS-002-C07, acceptance_criteria_ref: "FR-002.AC-4" }
    - { case_id: TS-002-C08, acceptance_criteria_ref: "FR-002.AC-4" }
    - { case_id: TS-002-C09, acceptance_criteria_ref: "FR-002.AC-4" }
    - { case_id: TS-002-C10, acceptance_criteria_ref: "FR-002.AC-1" }
    - { case_id: TS-002-C11, acceptance_criteria_ref: "FR-002.AC-1" }
  re_refs: [FR-002]
  arch_refs: [COMP-002]
  impl_refs: [IM-002, IDR-002]

- id: TS-003
  type: unit
  title: "승인 서비스 단위 테스트"
  target_module: src/main/java/com/company/leave/approval/
  test_cases:
    - { case_id: TS-003-C01, acceptance_criteria_ref: "FR-003.AC-1" }
    - { case_id: TS-003-C02, acceptance_criteria_ref: "FR-003.AC-2" }
    - { case_id: TS-003-C03, acceptance_criteria_ref: "FR-003.AC-3" }
    # 주의: FR-003.AC-4 (승인/반려 시 이메일 알림) 누락
  re_refs: [FR-003]
  arch_refs: [COMP-003]
  impl_refs: [IM-003]

- id: TS-005
  type: unit
  title: "잔여 휴가 조회 단위 테스트"
  target_module: src/main/java/com/company/leave/service/
  test_cases:
    - { case_id: TS-005-C01, acceptance_criteria_ref: "FR-005.AC-1" }
    - { case_id: TS-005-C02, acceptance_criteria_ref: "FR-005.AC-2" }
    - { case_id: TS-005-C03, acceptance_criteria_ref: "FR-005.AC-3" }
  re_refs: [FR-005]
  arch_refs: [COMP-002]
  impl_refs: [IM-002]

# 주의: TS-008 (FR-008 휴가 취소/수정) 테스트 스위트 전체 누락

- id: TS-004
  type: unit
  title: "팀 휴가 캘린더 단위 테스트"
  target_module: src/main/java/com/company/leave/calendar/
  test_cases:
    - { case_id: TS-004-C01, acceptance_criteria_ref: "FR-004.AC-1" }
    - { case_id: TS-004-C02, acceptance_criteria_ref: "FR-004.AC-2" }
    - { case_id: TS-004-C03, acceptance_criteria_ref: "FR-004.AC-3" }
    # 주의: FR-004.AC-4 (렌더링 3초 이내) — Should이므로 NFR 테스트에서 커버
  re_refs: [FR-004]
  arch_refs: []  # 주의: arch_refs 누락
  impl_refs: [IM-006]

- id: TS-010
  type: integration
  title: "휴가 신청-승인 통합 테스트"
  target_module: src/test/java/com/company/leave/integration/
  test_cases:
    - { case_id: TS-010-C01, description: "휴가 신청 → 대기중 → 승인 플로우" }
    - { case_id: TS-010-C02, description: "휴가 신청 → 대기중 → 반려 플로우" }
  re_refs: [FR-002, FR-003]
  arch_refs: [COMP-002, COMP-003, COMP-004]
  impl_refs: [IM-002, IM-003, IM-004]
```

## RE 산출물 (requirements_spec, 전체)

> strategy-input.md의 requirements_spec 참조

## 테스트 전략 (test_strategy)

> strategy-output.md 참조
