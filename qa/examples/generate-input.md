# 테스트 코드 생성 입력 예시

> 휴가 관리 시스템 — strategy 산출물 + RE/Impl 산출물 (발췌)

---

## 테스트 전략 (strategy 산출물)

```yaml
id: TSTR-001
mode: heavyweight
pyramid:
  unit: { ratio: "50%" }
  integration: { ratio: "30%" }
  e2e: { ratio: "15%" }
  nfr: { ratio: "5%" }
priority_matrix:
  - { re_id: FR-002, priority: Must, test_depth: "단위 + 통합 + E2E", estimated_cases: 12 }
  - { re_id: FR-008, priority: Must, test_depth: "단위 + 통합 + E2E", estimated_cases: 8 }
test_double_strategy:
  - { component: LeaveService, dependency: LeaveRepository, double_type: spy }
  - { component: LeaveRepository, dependency: Database, double_type: fake }
quality_gate:
  code_coverage: { line: 80, branch: 70 }
  requirements_coverage: { must: 100 }
```

## RE 산출물 (발췌: FR-002, FR-008)

```yaml
- id: FR-002
  title: 휴가 신청
  priority: Must
  acceptance_criteria:
    - AC-1: 연차, 반차(오전/오후), 병가, 특별휴가 유형 중 선택 가능
    - AC-2: 시작일, 종료일, 사유를 입력하여 신청
    - AC-3: 시작일은 오늘 이후여야 한다
    - AC-4: 잔여 휴가 부족 시 신청 차단 및 안내 메시지 표시
    - AC-5: 신청 완료 후 상태가 '대기중'으로 표시

- id: FR-008
  title: 휴가 신청 취소/수정
  priority: Must
  acceptance_criteria:
    - AC-1: 상태가 '대기중'인 신청 건만 취소/수정 가능
    - AC-2: 승인 완료된 신청 건의 취소는 팀장에게 취소 요청 전달
    - AC-3: 수정 시 변경 이력 기록
```

## Impl 산출물 (발췌)

```yaml
implementation_map:
  - id: IM-002
    component_ref: COMP-002
    module_path: src/main/java/com/company/leave/service/
    interfaces_implemented: [requestLeave, cancelLeave, modifyLeave, getLeaveBalance]
    re_refs: [FR-002, FR-005, FR-008]

implementation_decisions:
  - id: IDR-002
    decision: "Strategy 패턴으로 휴가 유형별 정책 분리"
    pattern_applied: Strategy
    re_refs: [FR-002]

technology_stack:
  - { category: backend, choice: "Java 17 + Spring Boot 3" }
  - { category: testing, choice: "JUnit5 + Mockito" }

implementation_guide:
  conventions:
    test_naming: "should_동작_when_조건"
```
