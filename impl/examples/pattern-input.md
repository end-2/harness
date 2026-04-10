# 디자인 패턴 입력 예시

> generate 과정에서 식별된 패턴 적용 기회

## 문제 상황

### 코드

```go
// internal/leave/balance.go
package leave

func CalculateBalance(employee Employee, leaveType string, year int) (int, error) {
	switch leaveType {
	case "annual":
		base := 15
		if employee.YearsOfService >= 3 {
			base += employee.YearsOfService - 2
		}
		used, err := getUsedDays(employee.ID, "annual", year)
		if err != nil {
			return 0, err
		}
		return base - used, nil

	case "sick":
		base := 30
		used, err := getUsedDays(employee.ID, "sick", year)
		if err != nil {
			return 0, err
		}
		return base - used, nil

	case "special":
		// 경조사, 출산 등 유형별 상이
		events, err := getSpecialLeaveEvents(employee.ID, year)
		if err != nil {
			return 0, err
		}
		total := 0
		for _, e := range events {
			total += e.Days
		}
		used, err := getUsedDays(employee.ID, "special", year)
		if err != nil {
			return 0, err
		}
		return total - used, nil

	default:
		return 0, fmt.Errorf("알 수 없는 휴가 유형: %s", leaveType)
	}
}
```

### 문제 식별

- 휴가 유형별 계산 로직이 switch문에 집중
- 새 휴가 유형 추가 시 이 함수를 수정해야 함 (OCP 위반)
- 각 유형의 계산 로직을 독립적으로 테스트할 수 없음
- FR-005에서 "유형별(연차, 병가, 특별휴가)" 언급 — 향후 유형 추가 가능성

## Arch 산출물

```yaml
architecture_decisions:
  - id: AD-003
    title: Repository 패턴으로 데이터 접근 추상화
    decision: 각 도메인 엔티티별 Repository 인터페이스를 정의하고 구현체를 분리한다
    # (Repository 패턴이 명시되어 있으나, Strategy 패턴은 명시되지 않음)

component_structure:
  - id: COMP-002
    name: leave
    responsibility: 휴가 신청, 조회, 취소/수정, 잔여일수 계산
    re_refs: [FR-002, FR-005, FR-008]
```
