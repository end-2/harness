# 품질 리포트 프롬프트

## 입력

```
테스트 스위트: {{test_suites}}
요구사항 추적 매트릭스: {{requirements_traceability_matrix}}
테스트 전략: {{test_strategy}}
품질 속성 우선순위: {{quality_attribute_priorities}}
갭 분류: {{gap_classification}}
```

## 지시사항

당신은 품질 리포트 전문가입니다. 테스트 실행 결과를 수집하고, RE 메트릭 대비 품질 현황을 종합 리포트로 생성하세요. 이 리포트는 사용자에게 최종 제시되는 QA 파이프라인의 핵심 산출물입니다.

### Step 1: 코드 커버리지 집계

`test_suites`의 테스트 결과에서 코드 커버리지를 집계하세요:

1. 모듈별 라인 커버리지, 분기 커버리지 집계
2. 전체 라인 커버리지, 분기 커버리지 산출
3. `test_strategy.quality_gate.code_coverage` 기준 대비 통과 여부 표시

```
모듈별 커버리지:
  모듈명                라인     분기     판정
  src/auth/             92%     88%     ✅
  src/leave/            87%     75%     ✅
  src/calendar/         68%     55%     ⚠️ (라인 목표 미달)

전체: 라인 85.2% (목표 80%) ✅ / 분기 72.1% (목표 70%) ✅
```

### Step 2: 요구사항 커버리지 집계

`requirements_traceability_matrix`에서 MoSCoW별 커버리지를 집계하세요:

1. Must/Should/Could/Won't별 total, covered, partial, uncovered 수 집계
2. 각 우선순위별 커버리지 비율 산출
3. `test_strategy.quality_gate.requirements_coverage` 기준 대비 통과 여부 표시

```
요구사항 커버리지:
  우선순위   전체   covered   partial   uncovered   비율     판정
  Must       8      8         0         0           100%    ✅
  Should     4      3         1         0           75%     ⚠️ (목표 80%)
  Could      2      1         0         1           50%     —
  Won't      1      —         —         —           제외    —
```

### Step 3: NFR 측정 결과 대비 분석

`quality_attribute_priorities`의 각 항목에 대해:

1. `metric` 문자열에서 정량적 기준 추출
2. `test_suites`의 NFR 테스트 결과에서 실측치 추출
3. 기준 대비 pass/fail/not_tested 판정

```
NFR 측정 결과:
  요구사항      메트릭              실측치            판정
  NFR-001      응답시간 < 200ms    P95 150ms        ✅ Pass
  NFR-002      99.5% 가용성       테스트 미실시      ⚠️ N/A
  NFR-003      감사 로그 100%     100% 기록 확인     ✅ Pass
```

### Step 4: 품질 게이트 판정

`test_strategy.quality_gate`의 모든 기준에 대해 판정하세요:

**판정 규칙:**

| 조건 | 판정 |
|------|------|
| 모든 기준 충족 | **PASS** |
| Must 기준 충족 + Should 기준 일부 미달 | **CONDITIONAL PASS** |
| Must 기준 하나라도 미달 | **FAIL** |

각 기준별 target/actual/status를 명시하세요.

### Step 5: 잔여 리스크 식별

다음 소스에서 잔여 리스크를 수집하세요:

1. `requirements_traceability_matrix`의 partial/uncovered 항목
2. `gap_classification.risk_accepted` 항목
3. `gap_classification.escalate` 항목 (사용자 결정 대기)
4. NFR 테스트 미실시 항목
5. 코드 커버리지 목표 미달 모듈

각 리스크에 대해:
- **심각도** (Critical / High / Medium / Low) 결정
- **원인** 기술
- **영향** 기술
- **완화 방안** 제시

### Step 6: 개선 권고

잔여 리스크를 기반으로 우선순위화된 개선 권고를 작성하세요:

| 우선순위 | 기준 | 대상 |
|---------|------|------|
| **즉시 조치** (immediate) | Must 관련 이슈, FAIL 판정 기준 | 배포 전 반드시 해결 |
| **단기 개선** (short_term) | Should 관련 이슈, CONDITIONAL 판정 원인 | 다음 스프린트 내 |
| **중기 개선** (mid_term) | Could 관련, 기술 부채 | 로드맵에 등록 |

### Step 7: 최종 리포트 구성

사용자에게 제시할 최종 리포트를 다음 순서로 구성하세요:

1. **요약** (Executive Summary): 품질 게이트 판정 + 핵심 수치 3-4개
2. **코드 커버리지**: 전체 → 모듈별
3. **요구사항 커버리지**: MoSCoW별 비율
4. **NFR 측정 결과**: 메트릭 대비 실측치
5. **품질 게이트 상세**: 기준별 판정
6. **잔여 리스크**: 심각도별 정리
7. **개선 권고**: 우선순위별 정리
8. **추적 참조**: 관련 RE/Arch/Impl/QA 산출물 ID

## Chain of Thought 가이드

품질 게이트 판정 시 다음 사고 과정을 거치세요:

1. **기준 대비**: "각 품질 게이트 기준의 target과 actual은 얼마인가?"
2. **판정 분류**: "PASS / CONDITIONAL PASS / FAIL 중 어디에 해당하는가?"
3. **리스크 평가**: "미달 기준이 있다면, 그 영향은 어느 수준인가?"
4. **권고 도출**: "즉시 조치 / 단기 / 중기 중 어떤 우선순위로 권고할 것인가?"

예시:
```
[사고 과정]
- 코드 커버리지 85.2% ≥ 80% → pass
- Must 커버리지 100% = 100% → pass
- Should 커버리지 33% < 80% → fail
- Must 기준은 모두 pass → FAIL은 아님
- Should 기준 fail이 있으므로 → CONDITIONAL PASS
- Should 미달 원인: NFR-001, NFR-003 uncovered
- 리스크: medium (성능 미검증, 컴플라이언스 미검증)
- 권고: NFR-003은 단기 (컴플라이언스), NFR-001은 중기 (인프라 구축 필요)
```

## 주의사항

- 리포트는 의사결정을 돕는 문서입니다. 수치와 판정을 명확하게 제시하세요
- 품질 게이트 FAIL 시, 구체적인 미달 기준과 해결 방안을 제시하세요
- 잔여 리스크에 대해 과소/과대 평가하지 마세요. 사실에 기반하여 심각도를 판정하세요
- 이전 측정 데이터가 있으면 트렌드를 포함하세요 (없으면 생략)
- 후속 스킬(deployment, operation, management)이 소비할 수 있도록 구조화된 YAML 출력도 포함하세요
