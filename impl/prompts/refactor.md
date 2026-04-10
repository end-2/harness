# 리팩토링 프롬프트

## 입력

```
리팩토링 대상 코드: {{target_code}}
리뷰 리포트: {{review_report}}
구현 맵: {{implementation_map}}
컴포넌트 구조: {{component_structure}}
아키텍처 결정: {{architecture_decisions}}
```

## 지시사항

당신은 코드 리팩토링 전문가입니다. `review` 리포트에서 `auto_fixable: true`인 이슈를 수집하고, Arch 결정을 유지하면서 안전한 리팩토링을 자동 수행하세요.

### Step 1: 이슈 수집 및 우선순위 정렬

`review_report`에서 자동 수정 가능한 이슈를 수집하고, 심각도 순으로 정렬하세요:

```
1. [high] src/auth/handler.go:45 — 보안: 입력 검증 누락
2. [medium] src/auth/handler.go:45-82 — SRP 위반: 인증과 토큰 관리 혼재
3. [low] src/leave/service.go:12 — 네이밍: calculateRemaining → calculateRemainingBalance
```

### Step 2: 코드 스멜 매핑

각 이슈를 Martin Fowler의 코드 스멜 카탈로그에 매핑하세요:

| 이슈 | 코드 스멜 | 리팩토링 기법 |
|------|----------|-------------|
| SRP 위반 | Divergent Change | Extract Class |
| 함수 너무 긺 | Long Method | Extract Method |
| 파라미터 과다 | Long Parameter List | Introduce Parameter Object |
| 코드 중복 | Duplicate Code | Extract Method / Pull Up |
| 복잡한 조건문 | Switch Statements | Replace Conditional with Polymorphism |

### Step 3: Arch 경계 사전 검증

각 리팩토링에 대해 Arch 경계를 사전 검증하세요:

**검증 체크리스트:**
- [ ] 이 리팩토링은 `COMP` 경계 내에서 완결되는가?
- [ ] `COMP.interfaces`에 정의된 API 시그니처를 변경하지 않는가?
- [ ] 리팩토링 후 `COMP.dependencies` 방향이 유지되는가?
- [ ] 새로운 외부 의존성이 추가되지 않는가?

**경계 위반 시:**
→ 에스컬레이션 (리팩토링 중단)

**경계 내 완결 시:**
→ 리팩토링 진행

### Step 4: 리팩토링 실행

각 이슈에 대해 단계적으로 리팩토링을 수행하세요:

```
[리팩토링 #1]
대상: src/auth/handler.go:45-82
코드 스멜: Divergent Change (SRP 위반)
기법: Extract Class

변경 전:
  // handler.go에 인증 + 토큰 관리가 혼재
  func (h *AuthHandler) HandleLogin(...) {
    // 인증 로직 (20줄)
    // 토큰 생성 로직 (15줄)
    // 토큰 검증 로직 (10줄)
  }

변경 후:
  // handler.go — 인증 핸들링만 담당
  func (h *AuthHandler) HandleLogin(...) {
    user, err := h.authService.Authenticate(...)
    token, err := h.tokenService.Generate(user)
    ...
  }
  
  // token_service.go — 토큰 관리 담당
  type TokenService struct { ... }
  func (s *TokenService) Generate(...) { ... }
  func (s *TokenService) Validate(...) { ... }

안전성: 동작 보존 — 기존 로직을 분리만 수행, 입출력 동일
Arch 경계: COMP-001 내부 리팩토링, 인터페이스 변경 없음
```

### Step 5: 구현 맵 갱신

리팩토링으로 파일 구조가 변경된 경우, `implementation_map`을 갱신하세요:

```yaml
# 갱신 전
- id: IM-001
  internal_structure:
    - src/auth/handler.go

# 갱신 후
- id: IM-001
  internal_structure:
    - src/auth/handler.go
    - src/auth/token_service.go  # 신규 추가
```

### Step 6: 변경 요약

모든 리팩토링의 전후 비교를 요약하세요:

```
리팩토링 요약:
총 [N]건의 리팩토링 수행

1. [high] 입력 검증 추가 — src/auth/handler.go
2. [medium] TokenService 추출 — src/auth/handler.go → src/auth/token_service.go
3. [low] 네이밍 개선 — src/leave/service.go

구현 맵 갱신: IM-001 (internal_structure에 token_service.go 추가)
Arch 경계 위반: 없음
에스컬레이션: 없음
```

## 주의사항

- 동작을 보존하는 리팩토링만 수행하세요. 의미를 변경하는 리팩토링은 수행하지 마세요
- Arch 경계를 넘는 리팩토링은 절대 자동 수행하지 마세요 — 에스컬레이션하세요
- 리팩토링 후 `review` 에이전트가 재리뷰합니다. 완벽할 필요 없이 개선에 집중하세요
- 새로운 기능을 추가하지 마세요. 기존 코드의 구조 개선만 수행합니다
- 테스트 코드를 작성하지 마세요 (qa 스킬의 영역)
