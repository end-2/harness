# 리팩토링 입력 예시

> review 리포트의 auto_fixable 이슈 + 대상 코드 + Arch 산출물

## 리뷰 리포트 (auto_fixable 이슈)

```yaml
clean_code_issues:
  - location: "internal/leave/handler.go:20-45"
    principle: "SRP — Apply 핸들러가 검증, 생성, 알림을 모두 수행"
    severity: medium
    auto_fixable: true

  - location: "internal/leave/handler.go:25"
    principle: "에러 처리 — c.Bind(&req) 에러 무시"
    severity: high
    auto_fixable: true

  - location: "internal/leave/handler.go:29,34"
    principle: "에러 처리 — db 호출 에러 무시"
    severity: high
    auto_fixable: true

  - location: "internal/leave/handler.go:20"
    principle: "타입 안전성 — 인라인 struct 대신 정의된 DTO 사용"
    severity: low
    auto_fixable: true
```

## 리팩토링 대상 코드

```go
// internal/leave/handler.go
package leave

import (
	"net/http"
	"github.com/labstack/echo/v4"
	"leave-management/internal/store"
)

type Handler struct {
	db *store.Store
}

func NewHandler(db *store.Store) *Handler {
	return &Handler{db: db}
}

func (h *Handler) Apply(c echo.Context) error {
	userID := c.Get("userID").(string)
	
	var req struct {
		LeaveType string `json:"leave_type"`
		StartDate string `json:"start_date"`
		EndDate   string `json:"end_date"`
		Reason    string `json:"reason"`
	}
	c.Bind(&req)
	
	balance, _ := h.db.GetLeaveBalance(userID)
	days := calculateDays(req.StartDate, req.EndDate)
	if balance < days {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "잔여 휴가 부족"})
	}
	
	leave, _ := h.db.CreateLeave(userID, req.LeaveType, req.StartDate, req.EndDate, req.Reason)
	
	approver, _ := h.db.GetApprover(userID)
	sendEmail(approver.Email, "새 휴가 신청", formatLeaveEmail(leave))
	
	return c.JSON(http.StatusCreated, leave)
}
```

## Arch 산출물 (경계 기준)

```yaml
# COMP-002 (leave) — 경계 내 리팩토링 기준
- id: COMP-002
  name: leave
  responsibility: 휴가 신청, 조회, 취소/수정, 잔여일수 계산
  interfaces:
    - "Apply(userID string, req LeaveRequest) → (Leave, error)"
  dependencies: [COMP-001, COMP-005]
```
