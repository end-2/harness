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

당신은 테스트 리뷰 전문가입니다. 생성된 테스트의 완전성, 강도, 추적성을 리뷰하고, 요구사항 추적 매트릭스(RTM)를 생성하세요. 커버리지 갭을 자동 분류하여 보완 또는 수용 여부를 판정합니다.

### Step 1: 요구사항 추적 매트릭스(RTM) 생성

`requirements_spec`의 각 요구사항에 대해:

1. `id`와 `title`을 기록
2. `priority`(MoSCoW)를 기록
3. 해당 요구사항의 `arch_refs`, `impl_refs`를 Arch/Impl 산출물에서 추적
4. `test_suites`에서 해당 요구사항을 참조하는 테스트 케이스 ID를 수집 (`re_refs` 매칭)
5. 커버리지 상태 판정:

| 조건 | 판정 |
|------|------|
| 모든 acceptance_criteria가 하나 이상의 테스트 케이스에 매핑 | **covered** |
| 일부 acceptance_criteria만 매핑 | **partial** |
| 테스트 케이스가 전혀 없음 | **uncovered** |

6. partial/uncovered인 경우 어떤 acceptance_criteria가 누락되었는지 `gap_description`에 기록

### Step 2: 테스트 강도 평가

각 테스트 케이스를 순회하며 약한 테스트 패턴을 탐지하세요:

**탐지 체크리스트:**

- [ ] 하드코딩된 기대값만 사용 (동적 검증 없음)
- [ ] `toBeTruthy()`, `toBeDefined()` 등 약한 assertion
- [ ] 정상 경로(happy path)만 테스트 (sad path 없음)
- [ ] 경계값 테스트 누락 (수치 조건이 있는데 경계값 미검증)
- [ ] 상태 변화 미검증 (반환값만 확인, DB/상태 미확인)
- [ ] 비동기 처리 미검증 (async 로직인데 동기적으로만 테스트)

### Step 3: 테스트 코드 품질 리뷰

**탐지 체크리스트:**

- [ ] 테스트 간 공유 상태 (전역 변수, 공유 fixture)
- [ ] 실행 순서 의존 (테스트 A가 실패하면 테스트 B도 실패)
- [ ] 시간 의존 (`Date.now()`, `setTimeout` 직접 사용)
- [ ] 외부 서비스 직접 호출 (mock/stub 미적용)
- [ ] 과도한 setup (Arrange 단계가 30줄 이상)
- [ ] 중복 코드 (동일 setup이 여러 테스트에 반복)
- [ ] AAA 패턴 미준수 (Arrange/Act/Assert 경계 불명확)

### Step 4: NFR 테스트 충분성 검증

`quality_attribute_priorities`의 각 항목에 대해:

1. 대응하는 NFR 테스트가 `test_suites`에 존재하는지 확인
2. 부하 수준이 metric 기준에 부합하는지 검증
   - 예: metric "동시 100명" → 테스트가 100명 이상을 시뮬레이션하는지
3. 측정 방법이 적정한지 확인 (P95, P99 등)
4. 성능 임계값이 metric과 일치하는지 확인

### Step 5: 추적성 체인 검증

모든 테스트에서:

1. `re_refs` 존재 여부 확인 → 없으면 traceability_issue 기록
2. `arch_refs` 존재 여부 확인 → 없으면 traceability_issue 기록
3. `impl_refs` 존재 여부 확인 → 없으면 traceability_issue 기록
4. 참조된 ID가 실제 산출물에 존재하는지 교차 검증 → 없으면 broken link로 기록

### Step 6: 커버리지 갭 자동 분류

RTM에서 partial/uncovered인 항목을 분류하세요:

**Must 갭:**

| 갭 유형 | 분류 | 예시 |
|--------|------|------|
| acceptance_criteria가 명확하고 테스트 변환 가능 | **auto_remediate** | CRUD 누락, 상태 전이 누락 |
| 인프라/외부 시스템 필요 | **escalate** | 가용성 테스트, 외부 API 통합 테스트 |
| 요구사항 자체가 모호 | **escalate** | 명확한 기준 없는 "사용하기 쉬운" |

**Should/Could/Won't 갭:**

- 모두 **risk_accepted**로 분류
- 사유와 영향 범위를 기록

### Step 7: 산출물 정리

1. RTM을 요구사항 ID 순으로 정리
2. 리뷰 리포트를 섹션별로 정리 (coverage_gaps, strength_issues, code_quality_issues, traceability_issues)
3. 갭 분류를 auto_remediate / risk_accepted / escalate로 정리

## Chain of Thought 가이드

커버리지 갭을 분류할 때 다음 사고 과정을 거치세요:

1. **갭 식별**: "어떤 요구사항의 어떤 AC가 테스트에 매핑되지 않았는가?"
2. **우선순위 확인**: "이 요구사항의 MoSCoW 우선순위는 무엇인가?"
3. **보완 가능성**: "이 갭은 generate 재호출로 자동 보완 가능한가?"
4. **분류 결정**: "auto_remediate / risk_accepted / escalate 중 어디에 해당하는가?"

예시:
```
[사고 과정]
- 갭: FR-003.AC-4 "승인/반려 즉시 이메일 알림 발송" 테스트 누락
- 우선순위: Must → 반드시 커버해야 함
- 보완 가능성: NotificationService를 Mock으로 주입하면 sendEmail 호출 검증 가능
  → 인프라 불필요, 단순 Mock 검증
- 분류: auto_remediate — generate에 TS-003-C04 추가 요청
```

## 주의사항

- Must 갭의 auto_remediate 판정 시, generate가 보완 가능한지 신중하게 판단하세요
- Should/Could 갭을 에스컬레이션하지 마세요 — 자동으로 리스크 수용합니다
- 추적성 체인이 끊어진 테스트는 traceability_issue로 기록하되, 테스트 자체를 삭제하지 마세요
- RTM의 coverage_status는 acceptance_criteria 단위로 정밀하게 판정하세요
- 에스컬레이션 시 반드시 대안을 함께 제시하세요
