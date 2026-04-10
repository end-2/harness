# 품질 리포트 입력 예시

> 휴가 관리 시스템 — review 완료 후 (generate 재호출로 Must 갭 보완 완료 상태)

---

## 테스트 스위트 (실행 결과 포함)

```yaml
- id: TS-001
  type: unit
  title: "인증 서비스 단위 테스트"
  target_module: src/main/java/com/company/leave/auth/
  results: { total: 4, passed: 4, failed: 0 }
  re_refs: [FR-001]

- id: TS-002
  type: unit
  title: "휴가 신청 서비스 단위 테스트"
  target_module: src/main/java/com/company/leave/service/
  results: { total: 14, passed: 14, failed: 0 }
  re_refs: [FR-002]

- id: TS-003
  type: unit
  title: "승인 서비스 단위 테스트"
  target_module: src/main/java/com/company/leave/approval/
  results: { total: 5, passed: 5, failed: 0 }
  re_refs: [FR-003]

- id: TS-004
  type: unit
  title: "팀 휴가 캘린더 단위 테스트"
  target_module: src/main/java/com/company/leave/calendar/
  results: { total: 3, passed: 3, failed: 0 }
  re_refs: [FR-004]

- id: TS-005
  type: unit
  title: "잔여 휴가 조회 단위 테스트"
  target_module: src/main/java/com/company/leave/service/
  results: { total: 3, passed: 3, failed: 0 }
  re_refs: [FR-005]

- id: TS-008
  type: unit
  title: "휴가 취소/수정 서비스 단위 테스트"
  target_module: src/main/java/com/company/leave/service/
  results: { total: 6, passed: 6, failed: 0 }
  re_refs: [FR-008]

- id: TS-010
  type: integration
  title: "휴가 신청-승인 통합 테스트"
  target_module: src/test/java/com/company/leave/integration/
  results: { total: 4, passed: 4, failed: 0 }
  re_refs: [FR-002, FR-003]

- id: TS-011
  type: integration
  title: "인증-서비스 통합 테스트"
  target_module: src/test/java/com/company/leave/integration/
  results: { total: 3, passed: 3, failed: 0 }
  re_refs: [FR-001, FR-002]

- id: TS-020
  type: e2e
  title: "휴가 신청-승인 E2E 테스트"
  results: { total: 2, passed: 2, failed: 0 }
  re_refs: [FR-001, FR-002, FR-003]
```

## 코드 커버리지 (테스트 실행 후 수집)

```yaml
code_coverage:
  overall: { line: 85.2, branch: 72.1 }
  by_module:
    - { module: "auth/", line: 92, branch: 88 }
    - { module: "service/", line: 87, branch: 75 }
    - { module: "approval/", line: 84, branch: 71 }
    - { module: "repository/", line: 90, branch: 82 }
    - { module: "notification/", line: 78, branch: 60 }
    - { module: "calendar/", line: 68, branch: 55 }
```

## RTM (review 산출물, Must 갭 보완 후)

```yaml
- { re_id: FR-001, re_priority: Must, coverage_status: covered }
- { re_id: FR-002, re_priority: Must, coverage_status: covered }
- { re_id: FR-003, re_priority: Must, coverage_status: covered }
- { re_id: FR-005, re_priority: Must, coverage_status: covered }
- { re_id: FR-008, re_priority: Must, coverage_status: covered }
- { re_id: FR-004, re_priority: Should, coverage_status: partial }
- { re_id: NFR-001, re_priority: Should, coverage_status: uncovered }
- { re_id: NFR-003, re_priority: Should, coverage_status: uncovered }
```

## 갭 분류 (review 산출물)

```yaml
gap_classification:
  auto_remediate: []  # 모두 보완 완료
  risk_accepted:
    - { re_id: FR-004, priority: Should, risk_level: low }
    - { re_id: NFR-001, priority: Should, risk_level: medium }
    - { re_id: NFR-003, priority: Should, risk_level: medium }
  escalate: []
```

## 테스트 전략 (quality_gate 기준)

```yaml
quality_gate:
  code_coverage: { line: 80, branch: 70 }
  requirements_coverage: { must: 100, should: 80 }
  test_pass_rate: 100
```

## RE 품질 속성 우선순위

```yaml
- { attribute: usability, metric: "신규 사용자가 5분 이내에 첫 휴가 신청 완료" }
- { attribute: availability, metric: "업무 시간 99.5% 가용성, 장애 시 30분 내 복구" }
- { attribute: security, metric: "민감 정보 접근 제한, 감사 로그 100% 기록" }
```
