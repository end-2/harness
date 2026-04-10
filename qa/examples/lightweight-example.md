# 경량 모드 예시 — 간단한 TODO API

> RE 경량 출력 → QA 경량: CRUD API의 acceptance_criteria 기반 단위 테스트 자동 생성

---

## 입력 (RE/Arch/Impl 산출물 발췌)

### RE spec 산출물

```yaml
requirements_spec:
  - id: FR-001
    title: TODO 항목 생성
    priority: Must
    acceptance_criteria:
      - 제목을 입력하여 TODO를 생성할 수 있다
      - 제목은 1자 이상 100자 이하여야 한다
      - 생성된 TODO의 상태는 'pending'이다
    dependencies: []

  - id: FR-002
    title: TODO 항목 완료 처리
    priority: Must
    acceptance_criteria:
      - pending 상태의 TODO를 완료 처리할 수 있다
      - 완료 처리 시 상태가 'done'으로 변경된다
    dependencies: [FR-001]

  - id: FR-003
    title: TODO 목록 조회
    priority: Should
    acceptance_criteria:
      - 전체 TODO 목록을 조회할 수 있다
      - 상태별(pending/done) 필터링이 가능하다
    dependencies: [FR-001]

constraints:
  - id: CON-001
    type: technical
    title: SQLite 사용
    flexibility: hard

quality_attribute_priorities:
  - attribute: simplicity
    priority: 1
    metric: "코드 500줄 이내"
```

### Arch 산출물

```yaml
architecture_decisions:
  - id: AD-001
    decision: "단일 모듈 모놀리식 구조"
    re_refs: [FR-001, FR-002, FR-003]

component_structure:
  - id: COMP-001
    name: TodoService
    type: service
    interfaces: [create, complete, list]
    dependencies: [COMP-002]
  - id: COMP-002
    name: TodoRepository
    type: store
    interfaces: [save, findById, findAll]
    dependencies: [Database]

technology_stack:
  - { category: language, choice: "Python 3.12" }
  - { category: framework, choice: "FastAPI" }
  - { category: database, choice: "SQLite" }
  - { category: testing, choice: "pytest" }
```

### Impl 산출물

```yaml
implementation_map:
  - id: IM-001
    component_ref: COMP-001
    module_path: src/service.py
    re_refs: [FR-001, FR-002, FR-003]
  - id: IM-002
    component_ref: COMP-002
    module_path: src/repository.py
    re_refs: [FR-001, FR-002, FR-003]

implementation_decisions:
  - id: IDR-001
    pattern_applied: Repository
    re_refs: [FR-001, FR-002, FR-003]
```

---

## 출력

### 테스트 전략 (경량 모드)

```yaml
id: TSTR-001
mode: lightweight
mode_rationale: "요구사항 3개, 구현 모듈 2개 — 경량 모드 적용"

scope:
  included:
    - { target: "FR-001, FR-002", rationale: "Must 요구사항" }
    - { target: "FR-003", rationale: "Should 요구사항" }

pyramid:
  unit: { ratio: "70%", rationale: "모놀리식(AD-001) — 단위 테스트 위주" }
  integration: { ratio: "30%", rationale: "Service → Repository 통합" }

test_double_strategy:
  - { component: TodoService, dependency: TodoRepository, double_type: fake, rationale: "인메모리 리포지토리" }

quality_gate:
  code_coverage: { line: 80, branch: 70 }
  requirements_coverage: { must: 100, should: 80 }

re_refs: [FR-001, FR-002, FR-003]
arch_refs: [AD-001, COMP-001, COMP-002]
```

### 테스트 스위트 (경량 모드)

```yaml
- id: TS-001
  type: unit
  title: "TODO 서비스 단위 테스트"
  target_module: src/service.py
  framework: pytest
  test_cases:
    - case_id: TS-001-C01
      description: "유효한 제목으로 TODO 생성"
      given: "제목 '장보기'"
      when: "create 호출"
      then: "status가 pending인 TODO가 반환된다"
      technique: equivalence_partition
      acceptance_criteria_ref: "FR-001.AC-1"

    - case_id: TS-001-C02
      description: "빈 제목으로 생성 시 에러"
      given: "빈 문자열 제목"
      when: "create 호출"
      then: "ValidationError 발생"
      technique: boundary_value
      acceptance_criteria_ref: "FR-001.AC-2"

    - case_id: TS-001-C03
      description: "100자 초과 제목으로 생성 시 에러"
      given: "101자 제목"
      when: "create 호출"
      then: "ValidationError 발생"
      technique: boundary_value
      acceptance_criteria_ref: "FR-001.AC-2"

    - case_id: TS-001-C04
      description: "100자 제목으로 생성 성공 (경계값)"
      given: "정확히 100자 제목"
      when: "create 호출"
      then: "TODO 생성 성공"
      technique: boundary_value
      acceptance_criteria_ref: "FR-001.AC-2"

    - case_id: TS-001-C05
      description: "pending 상태의 TODO를 완료 처리"
      given: "pending 상태의 TODO"
      when: "complete 호출"
      then: "status가 done으로 변경"
      technique: state_transition
      acceptance_criteria_ref: "FR-002.AC-2"

    - case_id: TS-001-C06
      description: "상태별 필터링 조회"
      given: "pending 2건, done 1건의 TODO"
      when: "list(status='pending') 호출"
      then: "pending 상태 2건만 반환"
      technique: equivalence_partition
      acceptance_criteria_ref: "FR-003.AC-2"

  re_refs: [FR-001, FR-002, FR-003]
  arch_refs: [COMP-001]
  impl_refs: [IM-001]
```

### 테스트 코드 (경량 모드)

```python
# @re_ref: FR-001, FR-002, FR-003
# @arch_ref: COMP-001
# @impl_ref: IM-001
import pytest
from src.service import TodoService
from src.repository import InMemoryTodoRepository


@pytest.fixture
def service():
    repo = InMemoryTodoRepository()
    return TodoService(repository=repo)


# @acceptance_criteria_ref: FR-001.AC-1, FR-001.AC-3
def test_should_create_todo_with_pending_status(service):
    # Arrange & Act
    todo = service.create(title="장보기")

    # Assert
    assert todo.title == "장보기"
    assert todo.status == "pending"


# @acceptance_criteria_ref: FR-001.AC-2
@pytest.mark.parametrize("title,should_raise", [
    ("", True),           # 빈 제목 → 에러
    ("a", False),         # 1자 경계값 → 성공
    ("a" * 100, False),   # 100자 경계값 → 성공
    ("a" * 101, True),    # 101자 → 에러
])
def test_should_validate_title_length(service, title, should_raise):
    if should_raise:
        with pytest.raises(ValidationError):
            service.create(title=title)
    else:
        todo = service.create(title=title)
        assert todo.title == title


# @acceptance_criteria_ref: FR-002.AC-1, FR-002.AC-2
def test_should_complete_pending_todo(service):
    # Arrange
    todo = service.create(title="장보기")

    # Act
    completed = service.complete(todo.id)

    # Assert
    assert completed.status == "done"
```

### RTM (경량 모드 — 간소화)

| re_id | priority | test_refs | coverage |
|-------|----------|-----------|----------|
| FR-001 | Must | TS-001-C01~C04 | covered |
| FR-002 | Must | TS-001-C05 | covered |
| FR-003 | Should | TS-001-C06 | covered |

### 품질 게이트: PASS

```
코드 커버리지: 라인 91% ≥ 80% ✅
Must 커버리지: 100% ✅
Should 커버리지: 100% ✅
```
