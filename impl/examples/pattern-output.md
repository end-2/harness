# 디자인 패턴 출력 예시

> Strategy 패턴 적용 (비명시 패턴 — 자동 판단)

---

## 패턴 분석

### Arch 명시 패턴 확인

- AD-003: Repository 패턴 → 이미 적용됨 (IDR-001)
- **Strategy 패턴은 Arch에 명시되지 않음** → 문제 상황 기반 자동 판단

### 문제 상황 분석

의사결정 트리 적용:

```
행위적 문제가 있는가?
├── 알고리즘을 런타임에 교체? → ✅ 휴가 유형별 계산 로직이 다름
└── Strategy 검토

과도한 패턴 경계 확인:
├── 조건 분기가 2개 이하인가? → ❌ (3개: annual, sick, special)
├── 확장 가능성이 낮은가? → ❌ (FR-005에서 유형별 잔여일수 조회 요구, 향후 추가 가능)
└── 적용 타당

Go 관용구 확인:
├── Go에서 Strategy = 인터페이스 기반 다형성
└── Go 관용적 구현으로 적용
```

## 추천 패턴

```yaml
recommended_patterns:
  - pattern_name: Strategy
    category: behavioral
    arch_mandated: false
    problem_context: |
      휴가 유형(annual, sick, special)별로 잔여일수 계산 로직이 다르며,
      각 유형의 계산 규칙(기본 일수, 가산 조건)이 독립적이다.
      FR-005에서 유형별 조회를 요구하고, 향후 새 유형 추가 가능성이 있다.
    rationale: |
      유형별 계산 로직을 BalanceCalculator 인터페이스로 추상화하여:
      1. 새 유형 추가 시 기존 코드 수정 불필요 (OCP)
      2. 유형별 독립 테스트 가능
      3. 계산 규칙 변경이 다른 유형에 영향 없음
    trade_offs: |
      + OCP 준수 — 새 유형 추가 시 BalanceCalculator 구현체만 추가
      + 유형별 독립 테스트 가능
      + 각 유형의 계산 복잡도가 증가해도 관리 용이
      - 인터페이스 + 구현체 파일 증가 (유형당 1개)
      - 간접 호출 1단계 증가
      - 유형이 3개뿐이고 변경이 드물다면 과도한 추상화일 수 있음
```

## 패턴 적용

### 적용 전

```go
func CalculateBalance(employee Employee, leaveType string, year int) (int, error) {
	switch leaveType {
	case "annual":
		// 연차 계산 (10줄)
	case "sick":
		// 병가 계산 (7줄)
	case "special":
		// 특별휴가 계산 (15줄)
	default:
		return 0, fmt.Errorf("알 수 없는 휴가 유형: %s", leaveType)
	}
}
```

### 적용 후

```go
// internal/leave/balance.go — 인터페이스 정의 + 팩토리

// BalanceCalculator는 휴가 유형별 잔여일수 계산 전략
type BalanceCalculator interface {
	Calculate(employee Employee, year int) (int, error)
}

// calculators는 유형별 계산기 레지스트리
var calculators = map[string]BalanceCalculator{
	"annual":  &AnnualCalculator{},
	"sick":    &SickCalculator{},
	"special": &SpecialCalculator{},
}

// CalculateBalance는 유형에 맞는 계산기를 선택하여 잔여일수를 계산한다
func CalculateBalance(employee Employee, leaveType string, year int) (int, error) {
	calc, ok := calculators[leaveType]
	if !ok {
		return 0, fmt.Errorf("알 수 없는 휴가 유형: %s", leaveType)
	}
	return calc.Calculate(employee, year)
}

// RegisterCalculator는 새 휴가 유형의 계산기를 등록한다
func RegisterCalculator(leaveType string, calc BalanceCalculator) {
	calculators[leaveType] = calc
}
```

```go
// internal/leave/balance_annual.go — 연차 계산기

type AnnualCalculator struct {
	repo LeaveRepository
}

func (c *AnnualCalculator) Calculate(employee Employee, year int) (int, error) {
	base := 15
	if employee.YearsOfService >= 3 {
		base += employee.YearsOfService - 2
	}
	used, err := c.repo.GetUsedDays(employee.ID, "annual", year)
	if err != nil {
		return 0, fmt.Errorf("연차 사용일수 조회 실패: %w", err)
	}
	return base - used, nil
}
```

```go
// internal/leave/balance_sick.go — 병가 계산기

type SickCalculator struct {
	repo LeaveRepository
}

func (c *SickCalculator) Calculate(employee Employee, year int) (int, error) {
	base := 30
	used, err := c.repo.GetUsedDays(employee.ID, "sick", year)
	if err != nil {
		return 0, fmt.Errorf("병가 사용일수 조회 실패: %w", err)
	}
	return base - used, nil
}
```

```go
// internal/leave/balance_special.go — 특별휴가 계산기

type SpecialCalculator struct {
	repo LeaveRepository
}

func (c *SpecialCalculator) Calculate(employee Employee, year int) (int, error) {
	events, err := c.repo.GetSpecialLeaveEvents(employee.ID, year)
	if err != nil {
		return 0, fmt.Errorf("특별휴가 이벤트 조회 실패: %w", err)
	}
	total := 0
	for _, e := range events {
		total += e.Days
	}
	used, err := c.repo.GetUsedDays(employee.ID, "special", year)
	if err != nil {
		return 0, fmt.Errorf("특별휴가 사용일수 조회 실패: %w", err)
	}
	return total - used, nil
}
```

## 안티패턴 탐지

탐지된 안티패턴 없음.

## 구현 결정 기록

```yaml
implementation_decisions:
  - id: IDR-005
    title: "Strategy 패턴을 휴가 잔여일수 계산에 적용"
    decision: |
      각 휴가 유형별 잔여일수 계산 로직을 BalanceCalculator 인터페이스로 추상화.
      유형별 구현체(AnnualCalculator, SickCalculator, SpecialCalculator)를 별도 파일로 분리.
      Map 기반 레지스트리로 유형 → 계산기 매핑.
    rationale: |
      Arch에 명시되지 않은 비명시 패턴이나, 다음 근거로 적용을 결정:
      1. 3개 유형의 독립적 계산 로직이 switch문에 집중 (OCP 위반)
      2. FR-005에서 유형별 잔여일수 조회 요구 — 유형 확장 가능성
      3. 각 유형의 계산 규칙이 독립적으로 변경될 수 있음
      4. Go의 인터페이스 기반 다형성은 Strategy 패턴의 관용적 구현
    alternatives_considered:
      - "switch문 유지 — 유형이 3개뿐이므로 충분. 그러나 OCP 위반 및 독립 테스트 불가"
      - "함수 맵 (map[string]func) — Go에서 가능하나 타입 안전성 부족, 구조체 상태 관리 불가"
    pattern_applied: Strategy
    arch_refs: []
    re_refs: [FR-002, FR-005]
```
