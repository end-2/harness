# 테스트 전략 수립 출력 예시

> 휴가 관리 시스템 — 중량 모드 (요구사항 8개, 모듈 5개)

---

## 테스트 전략

```yaml
id: TSTR-001

mode: heavyweight
mode_rationale: "요구사항 8개, 구현 모듈 5개, NFR 2건, regulatory 제약 1건 — 중량 모드 적용"

scope:
  included:
    - { target: "FR-001 ~ FR-005, FR-008", rationale: "Must/Should 요구사항 전체" }
    - { target: "NFR-001, NFR-003", rationale: "Should 비기능 요구사항" }
    - { target: "CON-005 컴플라이언스", rationale: "regulatory 제약, flexibility: hard" }
  excluded:
    - { target: "Won't 요구사항", rationale: "MoSCoW Won't — 리스크 수용" }

pyramid:
  unit:
    ratio: "50%"
    rationale: "레이어드 아키텍처(AD-001) — 각 레이어의 비즈니스 로직을 독립적으로 검증"
  integration:
    ratio: "30%"
    rationale: "3-tier 레이어 간 데이터 흐름 검증 (Service → Repository, Controller → Service)"
  e2e:
    ratio: "15%"
    rationale: "Must 요구사항의 핵심 사용자 시나리오 (로그인 → 휴가 신청 → 승인)"
  nfr:
    ratio: "5%"
    rationale: "NFR-001 응답시간, NFR-003 감사 로그 검증"

priority_matrix:
  - re_id: FR-001
    priority: Must
    test_depth: "단위 + 통합 + E2E"
    estimated_cases: 8
    rationale: "인증은 모든 기능의 전제 조건"
  - re_id: FR-002
    priority: Must
    test_depth: "단위 + 통합 + E2E"
    estimated_cases: 12
    rationale: "핵심 비즈니스 기능, acceptance_criteria 5개 + 경계값"
  - re_id: FR-003
    priority: Must
    test_depth: "단위 + 통합 + E2E"
    estimated_cases: 10
    rationale: "승인 워크플로우 상태 전이 검증"
  - re_id: FR-005
    priority: Must
    test_depth: "단위 + 통합 + E2E"
    estimated_cases: 8
    rationale: "잔여 휴가 계산 정확성 (경계값 분석 필수)"
  - re_id: FR-008
    priority: Must
    test_depth: "단위 + 통합 + E2E"
    estimated_cases: 8
    rationale: "취소/수정 상태 전이 + 이력 기록"
  - re_id: FR-004
    priority: Should
    test_depth: "단위 + 통합"
    estimated_cases: 6
    rationale: "캘린더 뷰 데이터 정합성"
  - re_id: NFR-001
    priority: Should
    test_depth: "NFR (성능)"
    estimated_cases: 3
    rationale: "API 응답시간 P95 < 1s, 캘린더 렌더링 < 3s"
  - re_id: NFR-003
    priority: Should
    test_depth: "단위 + 통합"
    estimated_cases: 4
    rationale: "감사 로그 기록 완전성"

nfr_test_plan:
  - re_id: NFR-001
    metric: "API 응답 시간 P95 기준 1초 이내"
    test_type: performance
    scenario: "동시 100명 접속 상태에서 주요 API 엔드포인트 호출, P95 응답시간 측정"
    threshold: "P95 < 1000ms"
    tool: "JMeter 또는 Gatling"
  - re_id: NFR-001
    metric: "캘린더 뷰 렌더링 3초 이내"
    test_type: performance
    scenario: "100건의 승인된 휴가가 있는 팀의 캘린더 뷰 렌더링 시간 측정"
    threshold: "렌더링 완료 < 3000ms"
    tool: "Lighthouse 또는 Web Vitals"
  - re_id: NFR-003
    metric: "감사 로그 100% 기록"
    test_type: audit
    scenario: "신청/승인/반려/수정/취소 각 행위 수행 후 감사 로그 존재 여부 확인"
    threshold: "누락 0건"
    tool: "통합 테스트"

environment_matrix:
  - dimension: "SSO Provider"
    values: ["SAML 2.0 Mock (테스트)", "사내 IdP (스테이징)"]
    constraint_ref: CON-001
  - dimension: "배포 환경"
    values: ["로컬 (Docker Compose)", "프라이빗 클라우드 (스테이징)"]
    constraint_ref: CON-003
  - dimension: "데이터베이스"
    values: ["H2 (단위 테스트)", "PostgreSQL (통합/E2E)"]
    constraint_ref: null

test_double_strategy:
  - component: AuthService
    dependency: "SSO Provider"
    double_type: mock
    rationale: "외부 SAML 2.0 IdP 의존성 제거, 인증 결과 제어"
  - component: LeaveRepository
    dependency: Database
    double_type: fake
    rationale: "H2 인메모리 DB로 빠른 단위 테스트, PostgreSQL은 통합 테스트"
  - component: NotificationService
    dependency: "Email Server"
    double_type: mock
    rationale: "이메일 발송 의존성 제거, 호출 검증에 집중"
  - component: LeaveService
    dependency: LeaveRepository
    double_type: spy
    rationale: "실제 저장 동작 유지하면서 호출 검증"

quality_gate:
  code_coverage:
    line: 80
    branch: 70
  requirements_coverage:
    must: 100
    should: 80
  nfr_compliance: "NFR-001: P95 < 1000ms, NFR-003: 로그 누락 0건"
  test_pass_rate: 100

re_refs: [FR-001, FR-002, FR-003, FR-004, FR-005, FR-008, NFR-001, NFR-003]
arch_refs: [AD-001, AD-002, COMP-001, COMP-002, COMP-003, COMP-004, COMP-005]
```
