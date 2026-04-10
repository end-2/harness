# 코드 리뷰 입력 예시

> generate 에이전트의 산출물 + Arch 산출물 (검증 기준)

## 생성된 코드 (리뷰 대상 발췌)

### internal/leave/handler.go

```go
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
	
	// 잔여일수 확인
	balance, _ := h.db.GetLeaveBalance(userID)
	days := calculateDays(req.StartDate, req.EndDate)
	if balance < days {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "잔여 휴가 부족"})
	}
	
	// 휴가 생성
	leave, _ := h.db.CreateLeave(userID, req.LeaveType, req.StartDate, req.EndDate, req.Reason)
	
	// 팀장에게 알림
	approver, _ := h.db.GetApprover(userID)
	sendEmail(approver.Email, "새 휴가 신청", formatLeaveEmail(leave))
	
	return c.JSON(http.StatusCreated, leave)
}

func calculateDays(start, end string) int {
	// ... 날짜 계산 로직 (30줄)
	return 0
}

func sendEmail(to, subject, body string) {
	// ... SMTP 직접 호출 (20줄)
}

func formatLeaveEmail(leave interface{}) string {
	// ... 이메일 포맷팅 (15줄)
}
```

## 구현 맵 (참조)

```yaml
- id: IM-002
  component_ref: COMP-002
  module_path: internal/leave/
  interfaces_implemented: [Apply, Cancel, Update, GetBalance, ListByUser]
  re_refs: [FR-002, FR-005, FR-008]
```

## Arch 산출물 (검증 기준)

generate-input.md의 Arch 산출물 참조
