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

시스템 프롬프트에 정의된 역할과 규칙을 따라 `review_report`에서 `auto_fixable: true`인 이슈를 수집하고, Arch 결정을 유지하면서 안전한 리팩토링을 자동 수행하세요.

### Step 1: 이슈 수집 및 우선순위 정렬

`review_report`에서 자동 수정 가능한 이슈를 수집하고 심각도(high → medium → low) 순으로 정렬합니다.

```
1. [high] src/auth/handler.go:45 — 보안: 입력 검증 누락
2. [medium] src/auth/handler.go:45-82 — SRP 위반: 인증과 토큰 관리 혼재
3. [low] src/leave/service.go:12 — 네이밍: calculateRemaining → calculateRemainingBalance
```

### Step 2: 코드 스멜 매핑

시스템 프롬프트 **"코드 스멜 카탈로그"**(블로터/OO 남용/변경 방해자/불필요한 것/결합 문제) 표에 따라 각 이슈를 Martin Fowler 코드 스멜과 리팩토링 기법에 매핑합니다.

### Step 3: Arch 경계 사전 검증

시스템 프롬프트 **"Arch 경계 검증"** 절차(모듈 이동, 인터페이스 변경, 의존성 방향)를 각 리팩토링에 대해 적용합니다. 경계 내 완결이면 진행, 경계 위반이면 에스컬레이션하고 해당 리팩토링은 중단합니다.

### Step 4: 리팩토링 실행

각 이슈에 대해 단계적으로 리팩토링을 수행합니다:

```
[리팩토링 #N]
대상: <파일:라인>
코드 스멜: <스멜 이름>
기법: <리팩토링 기법>

변경 전:
  <코드>

변경 후:
  <코드>

안전성: <동작 보존 설명>
Arch 경계: <영향받는 COMP 및 경계 내 완결 여부>
```

### Step 5: 구현 맵 갱신

리팩토링으로 파일/모듈 구조가 변경된 경우 `implementation_map`의 해당 항목을 갱신합니다.

```yaml
- id: IM-001
  internal_structure:
    - src/auth/handler.go
    - src/auth/token_service.go  # 신규 추가
```

### Step 6: 변경 요약 및 산출물 출력

모든 리팩토링의 전후 비교를 요약하고, 시스템 프롬프트 **"출력 형식"** 및 **"출력 프로토콜"**에 따라 `code_smells`, `refactored_code`, `updated_implementation_map`, `changes_summary`를 `meta.json`/`body.md`에 기록합니다. 에스컬레이션이 있으면 시스템 프롬프트 **"에스컬레이션 조건"** 형식에 따라 먼저 제시합니다.

## 주의사항

- 리팩토링 후 `review` 에이전트가 재리뷰합니다. 완벽할 필요 없이 개선에 집중하세요
- 새로운 기능을 추가하지 마세요. 기존 코드의 구조 개선만 수행합니다
- 테스트 코드를 작성하지 마세요 (qa 스킬의 영역)
