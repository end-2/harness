# 테스트 리뷰 프롬프트

## 입력

```
테스트 스위트: {{test_suites}}
테스트 전략: {{test_strategy}}
요구사항 명세: {{requirements_spec}}
제약 조건: {{constraints}}
컴포넌트 구조: {{component_structure}}
구현 맵: {{implementation_map}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙에 따라 생성된 테스트의 완전성·강도·추적성을 리뷰하고, 요구사항 추적 매트릭스(RTM)를 생성하세요.

### Step 1: 요구사항 추적 매트릭스(RTM) 생성

`requirements_spec`의 각 요구사항에 대해:

1. `id`, `title`, `priority`(MoSCoW)를 기록
2. 해당 요구사항의 `arch_refs`, `impl_refs`를 Arch/Impl 산출물에서 추적
3. `test_suites`에서 `re_refs`를 매칭하여 관련 테스트 케이스 ID 수집
4. 시스템 프롬프트 **"요구사항 커버리지 검증 (RTM 생성)"**의 covered/partial/uncovered 판정 규칙 적용
5. partial/uncovered인 경우 누락된 acceptance_criteria를 `gap_description`에 기록

### Step 2: 테스트 강도 평가

시스템 프롬프트 **"테스트 강도 평가"** 표의 약한 테스트 패턴을 탐지합니다. 추가 체크리스트:

- [ ] 하드코딩된 기대값만 사용
- [ ] `toBeTruthy()`, `toBeDefined()` 등 약한 assertion
- [ ] happy path만 테스트 (sad path 없음)
- [ ] 경계값 테스트 누락
- [ ] 상태 변화 미검증 (반환값만 확인)
- [ ] 비동기 처리 미검증

### Step 3: 테스트 코드 품질 리뷰

시스템 프롬프트 **"테스트 코드 품질 리뷰"**의 독립성·flaky 패턴·유지보수성·AAA 기준으로 탐지합니다. 추가 체크리스트:

- [ ] 테스트 간 공유 상태 (전역 변수, 공유 fixture)
- [ ] 실행 순서 의존
- [ ] 시간 의존 (`Date.now()`, `setTimeout` 직접 사용)
- [ ] 외부 서비스 직접 호출 (mock/stub 미적용)
- [ ] 과도한 setup (Arrange 30줄 이상)
- [ ] 중복 코드 (동일 setup 반복)
- [ ] AAA 패턴 경계 불명확

### Step 4: NFR 테스트 충분성 검증

시스템 프롬프트 **"NFR 테스트 검증"** 기준으로 `quality_attribute_priorities`의 각 항목에 대해 대응 테스트 존재 여부, 부하 수준의 metric 부합, 측정 방법(P95/P99 등), 성능 임계값 일치를 확인합니다.

### Step 5: 추적성 체인 검증

모든 테스트에서 `re_refs`, `arch_refs`, `impl_refs` 존재 여부를 확인하고, 참조된 ID가 실제 산출물에 존재하는지 교차 검증합니다. 누락/broken link는 `traceability_issue`로 기록합니다.

### Step 6: 커버리지 갭 자동 분류

시스템 프롬프트 **"커버리지 갭 자동 분류"** 규칙에 따라 RTM의 partial/uncovered 항목을 `auto_remediate` / `risk_accepted` / `escalate`로 분류합니다. Should/Could/Won't 갭은 자동으로 `risk_accepted`이며, 사유와 영향 범위를 기록합니다.

### Step 7: 산출물 정리

1. RTM을 요구사항 ID 순으로 정리
2. 리뷰 리포트를 시스템 프롬프트 **"출력 형식 → 리뷰 리포트"** 스키마(`coverage_gaps`, `strength_issues`, `code_quality_issues`, `traceability_issues`)에 맞춰 정리
3. 갭 분류를 시스템 프롬프트 **"출력 형식 → 갭 분류"** 스키마에 맞춰 정리
4. Must 갭 중 auto_remediate는 `generate` 재호출로 보완, escalate는 시스템 프롬프트 **"에스컬레이션 조건"** 메시지 형식으로 사용자에게 보고
5. 시스템 프롬프트 **"출력 프로토콜"**에 따라 `meta.json`/`body.md`에 기록하고 리뷰 판정을 설정

## 주의사항

- Must 갭의 auto_remediate 판정 시, generate가 보완 가능한지 신중하게 판단하세요
- Should/Could 갭을 에스컬레이션하지 마세요 — 자동으로 리스크 수용합니다
- 추적성 체인이 끊어진 테스트는 traceability_issue로 기록하되, 테스트 자체를 삭제하지 마세요
- RTM의 coverage_status는 acceptance_criteria 단위로 정밀하게 판정하세요
