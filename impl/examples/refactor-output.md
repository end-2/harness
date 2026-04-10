# 리팩토링 출력 예시

> internal/leave/handler.go 리팩토링 결과

---

## 코드 스멜 분석

```yaml
code_smells:
  - name: Divergent Change
    location: internal/leave/handler.go:20-45
    severity: medium
    refactoring_technique: Extract Class
    arch_boundary_safe: true
    details: "Apply 핸들러가 HTTP 처리, 비즈니스 로직, 알림을 모두 수행 — SRP 위반"

  - name: Primitive Obsession
    location: internal/leave/handler.go:22-27
    severity: low
    refactoring_technique: Replace Primitive with Object
    arch_boundary_safe: true
    details: "인라인 struct 사용 — 정의된 DTO 타입 필요"

  - name: 에러 무시 (Code Smell: Swallowed Exception)
    location: internal/leave/handler.go:25,29,34,37
    severity: high
    refactoring_technique: Add Error Handling
    arch_boundary_safe: true
    details: "Go의 관용적 에러 처리 패턴 미준수"
```

## 리팩토링 실행

### 리팩토링 #1: DTO 타입 정의 (Primitive Obsession 해소)

```
대상: internal/leave/handler.go:22-27
코드 스멜: Primitive Obsession
기법: Replace Primitive with Object

변경: dto.go에 ApplyRequest 타입 정의

신규 파일 — internal/leave/dto.go:
  package leave

  type ApplyRequest struct {
    LeaveType string `json:"leave_type" validate:"required,oneof=annual sick special"`
    StartDate string `json:"start_date" validate:"required"`
    EndDate   string `json:"end_date" validate:"required"`
    Reason    string `json:"reason"`
  }

안전성: 동작 보존 — 동일 필드, 검증 태그 추가
Arch 경계: COMP-002 내부, 인터페이스 변경 없음
```

### 리팩토링 #2: 비즈니스 로직 분리 (Divergent Change 해소)

```
대상: internal/leave/handler.go:20-45
코드 스멜: Divergent Change (SRP 위반)
기법: Extract Class

변경 전 — handler.go:
  func (h *Handler) Apply(c echo.Context) error {
    // HTTP 바인딩 + 검증 + DB 호출 + 알림 (45줄)
  }

변경 후 — handler.go (HTTP 계층만):
  func (h *Handler) Apply(c echo.Context) error {
    userID := c.Get("userID").(string)
    
    var req ApplyRequest
    if err := c.Bind(&req); err != nil {
      return echo.NewHTTPError(http.StatusBadRequest, "잘못된 요청 형식")
    }
    
    leave, err := h.service.Apply(userID, req)
    if err != nil {
      return err  // error_handler에서 HTTP 상태 코드로 매핑
    }
    
    return c.JSON(http.StatusCreated, leave)
  }

변경 후 — service.go (비즈니스 로직):
  type Service struct {
    repo LeaveRepository
  }
  
  func (s *Service) Apply(userID string, req ApplyRequest) (*Leave, error) {
    balance, err := s.repo.GetBalance(userID)
    if err != nil {
      return nil, fmt.Errorf("잔여일수 조회 실패: %w", err)
    }
    
    days, err := calculateDays(req.StartDate, req.EndDate)
    if err != nil {
      return nil, fmt.Errorf("날짜 계산 실패: %w", err)
    }
    
    if balance < days {
      return nil, ErrInsufficientBalance
    }
    
    leave, err := s.repo.Create(userID, req)
    if err != nil {
      return nil, fmt.Errorf("휴가 생성 실패: %w", err)
    }
    
    return leave, nil
  }

안전성: 동작 보존 — 로직 분리만 수행, 입출력 동일
Arch 경계: COMP-002 내부, AD-002 (Layered Architecture) 준수
```

### 리팩토링 #3: 에러 처리 추가 (Swallowed Exception 해소)

```
대상: internal/leave/handler.go, internal/leave/service.go
코드 스멜: Swallowed Exception
기법: Add Error Handling

변경: 리팩토링 #2에서 이미 반영됨
  - c.Bind 에러 검사 추가
  - 모든 repo 호출에 에러 검사 + error wrapping 적용
  - 도메인 에러 정의 (ErrInsufficientBalance)

신규 — internal/leave/errors.go:
  package leave

  import "errors"

  var (
    ErrInsufficientBalance = errors.New("잔여 휴가 부족")
    ErrLeaveNotFound       = errors.New("휴가 신청을 찾을 수 없음")
    ErrInvalidDateRange    = errors.New("잘못된 날짜 범위")
  )

안전성: 에러 처리 추가 — 기존에 무시되던 에러를 명시적으로 처리
Arch 경계: COMP-002 내부, Go 관용적 에러 처리 (IDR-004)
```

## 구현 맵 갱신

```yaml
# 갱신 전
- id: IM-002
  internal_structure:
    - internal/leave/handler.go
    - internal/leave/service.go
    - internal/leave/balance.go
    - internal/leave/model.go
    - internal/leave/dto.go

# 갱신 후
- id: IM-002
  internal_structure:
    - internal/leave/handler.go     # HTTP 계층 (리팩토링됨)
    - internal/leave/service.go     # 비즈니스 로직 (리팩토링됨)
    - internal/leave/balance.go     # 잔여일수 계산
    - internal/leave/model.go       # 도메인 모델
    - internal/leave/dto.go         # 요청/응답 DTO (신규)
    - internal/leave/errors.go      # 도메인 에러 정의 (신규)
```

## 변경 요약

```
리팩토링 요약:
총 3건의 리팩토링 수행

1. [low] DTO 타입 정의 — dto.go 신규 생성 (ApplyRequest)
2. [medium] 비즈니스 로직 분리 — handler.go → handler.go + service.go (Layered Architecture 적용)
3. [high] 에러 처리 추가 — handler.go, service.go + errors.go 신규 생성

구현 맵 갱신: IM-002 (dto.go, errors.go 추가)
Arch 경계 위반: 없음
에스컬레이션: 없음

→ review 에이전트 재리뷰 요청
```
