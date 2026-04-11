# 테스트 코드 생성 프롬프트

## 입력

```
테스트 전략: {{test_strategy}}
요구사항 명세: {{requirements_spec}}
구현 맵: {{implementation_map}}
컴포넌트 구조: {{component_structure}}
기술 스택: {{technology_stack}}
구현 결정: {{implementation_decisions}}
구현 가이드: {{implementation_guide}}
추가 생성 요청: {{additional_generation_request}}  (review에서 재호출 시)
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙에 따라 테스트 전략 기반으로 테스트 코드를 일괄 생성하세요. 모든 테스트가 RE 요구사항까지 추적 가능해야 합니다.

### Step 1: 테스트 프레임워크 확인

`technology_stack`에서 언어/프레임워크를 확인하고, 시스템 프롬프트 **"Arch 산출물 해석 → 테스트 구조 결정"**의 프레임워크 매핑에 따라 테스트 프레임워크와 모킹 라이브러리를 선택합니다.

### Step 2: acceptance_criteria → 테스트 케이스 변환

시스템 프롬프트 **"acceptance_criteria → 테스트 케이스 변환"** 규칙에 따라 `requirements_spec`의 각 요구사항을 `priority_matrix` 순서대로 처리합니다. 각 AC 문장을 Given-When-Then으로 분해하고 정상/비정상 경로를 모두 생성하며, 다음 문장 유형별 추가 규칙을 적용합니다:

- "~하면 ~한다" → Given: 사전 조건 / When: 트리거 / Then: 기대 결과
- "~할 수 있다" → Given: 권한/상태 / When: 기능 실행 / Then: 성공 확인
- "~이어야 한다" → Given: 초기 상태 / When: 조건 충족 확인 / Then: 제약 충족 검증
- 수치 조건 → 경계값 분석 적용

적용할 설계 기법은 시스템 프롬프트 **"테스트 설계 기법 적용"** 표에 따라 `priority_matrix.test_depth`와 함께 결정하고, `acceptance_criteria_ref`로 원천 추적을 유지합니다.

### Step 3: 테스트 유형별 생성

시스템 프롬프트 **"테스트 유형별 생성"** 절의 단위/통합/E2E/계약/NFR 가이드에 따라 각 유형별 테스트를 생성합니다. 산출물 바인딩:

- **단위**: `implementation_map`의 각 모듈 — `module_path` 미러링, `interfaces_implemented`의 메서드별 케이스, `test_double_strategy`에 따른 의존성 대체
- **통합**: `component_structure.interfaces`, `dependencies` 기반 컴포넌트 간 호출·데이터 흐름·에러 전파 검증
- **E2E**: `diagrams.sequence` 기반 Must 핵심 흐름
- **계약**: `component_structure.interfaces` 기반 Provider/Consumer 검증 (마이크로서비스 시)
- **NFR**: `nfr_test_plan` 기반 성능/부하/스트레스 측정

### Step 4: 테스트 코드 작성

시스템 프롬프트 **"테스트 코드 컨벤션"**에 따라 각 테스트에 `@re_ref`, `@arch_ref`, `@impl_ref`, `@acceptance_criteria_ref` 주석과 AAA 패턴을 포함하고, 프레임워크 관용구를 준수합니다. 주요 프레임워크 예시:

#### Jest / Vitest (TypeScript)

```typescript
// @re_ref: FR-001
// @arch_ref: COMP-001
// @impl_ref: IM-001
describe('인증 모듈', () => {
  let authService: AuthService;
  let ssoProvider: jest.Mocked<SSOProvider>;

  beforeEach(() => {
    ssoProvider = createMock<SSOProvider>();
    authService = new AuthService(ssoProvider);
  });

  // @acceptance_criteria_ref: FR-001.AC-1
  it('SSO 인증 성공 시 대시보드로 이동', async () => {
    // Arrange
    ssoProvider.validate.mockResolvedValue({ userId: 'user-1', valid: true });
    // Act
    const result = await authService.login(validToken);
    // Assert
    expect(result.redirectUrl).toBe('/dashboard');
  });
});
```

#### pytest (Python)

```python
# @re_ref: FR-002
# @acceptance_criteria_ref: FR-002.AC-4
@pytest.mark.parametrize("balance,requested,should_raise", [
    (0, 1, True),   # 잔여 0일 → 차단
    (1, 1, False),  # 경계값: 성공
    (1, 2, True),   # 초과 → 차단
])
def test_leave_request_balance_boundary(leave_service, balance, requested, should_raise):
    leave_service.set_balance(balance)
    if should_raise:
        with pytest.raises(InsufficientBalanceError):
            leave_service.request_leave(days=requested)
    else:
        assert leave_service.request_leave(days=requested).status == LeaveStatus.PENDING
```

JUnit5/Mockito, Go testing, Rust `#[test]` 등도 동일한 추적 주석 체계와 AAA 패턴을 유지하며 관용구를 따릅니다.

### Step 5: 산출물 정리

시스템 프롬프트 **"출력 형식 → 테스트 스위트"** 스키마에 맞춰 `TS-001` 형식으로 구조화합니다:

- 스위트: `id`, `type`, `title`, `target_module`, `framework`, `re_refs`, `arch_refs`, `impl_refs`
- 케이스: `case_id`, `description`, `given`, `when`, `then`, `technique`, `acceptance_criteria_ref`

### Step 6: 추가 생성 (review 재호출 시)

`additional_generation_request`가 존재하면 요청된 갭에 해당하는 테스트 케이스만 생성하여 기존 스위트에 추가하거나 새 스위트를 만들고, 동일한 추적 참조 체계를 유지합니다.

마지막으로 시스템 프롬프트 **"출력 프로토콜"**에 따라 `meta.json`/`body.md`에 기록합니다.

## 주의사항

- 테스트 설명은 한국어로, 코드는 영어로 작성하세요
- `implementation_guide.conventions`의 코딩 컨벤션을 테스트 코드에도 적용하세요
- 하드코딩된 기대값보다 동적 계산값과 비교하는 assertion을 선호하세요
- 테스트 간 공유 상태를 피하고, 각 테스트가 독립적으로 실행 가능하도록 작성하세요
