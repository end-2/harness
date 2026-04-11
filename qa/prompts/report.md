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

시스템 프롬프트에 정의된 역할과 규칙에 따라 테스트 실행 결과를 수집하고, RE 메트릭 대비 품질 현황을 종합 리포트로 생성하세요. 이 리포트는 QA 파이프라인의 최종 사용자 접점입니다.

### Step 1: 코드 커버리지 집계

시스템 프롬프트 **"코드 커버리지 집계"** 절차에 따라 `test_suites`의 결과에서 모듈별 라인/분기 커버리지와 전체 값을 산출하고, `test_strategy.quality_gate.code_coverage` 기준 대비 통과 여부를 표시합니다.

### Step 2: 요구사항 커버리지 집계

시스템 프롬프트 **"요구사항 커버리지 집계"** 절차에 따라 `requirements_traceability_matrix`에서 MoSCoW별 total/covered/partial/uncovered 수와 비율을 산출하고, `test_strategy.quality_gate.requirements_coverage` 기준 대비 판정을 표시합니다.

### Step 3: NFR 측정 결과 대비 분석

시스템 프롬프트 **"NFR 측정 결과 대비 분석"** 표 형식으로 `quality_attribute_priorities`의 각 항목에 대해:

1. `metric` 문자열에서 정량 기준 추출
2. `test_suites`의 NFR 테스트 결과에서 실측치 추출
3. 기준 대비 pass/fail/not_tested 판정

### Step 4: 품질 게이트 판정

시스템 프롬프트 **"품질 게이트 판정"**의 PASS / CONDITIONAL PASS / FAIL 규칙을 `test_strategy.quality_gate`의 모든 기준에 적용하고, 각 기준별 target/actual/status를 명시합니다.

### Step 5: 잔여 리스크 식별

다음 소스에서 잔여 리스크를 수집합니다:

1. `requirements_traceability_matrix`의 partial/uncovered 항목
2. `gap_classification.risk_accepted` 항목
3. `gap_classification.escalate` 항목 (사용자 결정 대기)
4. NFR 테스트 미실시 항목
5. 코드 커버리지 목표 미달 모듈

각 리스크에 대해 시스템 프롬프트 **"잔여 리스크 식별"** 표 형식으로 **심각도**(Critical/High/Medium/Low), **원인**, **영향**, **완화 방안**을 기록합니다.

### Step 6: 개선 권고

잔여 리스크를 기반으로 우선순위화된 개선 권고를 작성합니다:

| 우선순위 | 기준 | 대상 |
|---------|------|------|
| **즉시 조치** (immediate) | Must 관련 이슈, FAIL 판정 기준 | 배포 전 반드시 해결 |
| **단기 개선** (short_term) | Should 관련 이슈, CONDITIONAL 판정 원인 | 다음 스프린트 내 |
| **중기 개선** (mid_term) | Could 관련, 기술 부채 | 로드맵에 등록 |

### Step 7: 최종 리포트 구성

사용자에게 제시할 리포트를 다음 순서로 구성합니다:

1. **요약** (Executive Summary): 품질 게이트 판정 + 핵심 수치 3-4개
2. **코드 커버리지**: 전체 → 모듈별
3. **요구사항 커버리지**: MoSCoW별 비율
4. **NFR 측정 결과**: 메트릭 대비 실측치
5. **품질 게이트 상세**: 기준별 판정
6. **잔여 리스크**: 심각도별 정리
7. **개선 권고**: 우선순위별 정리
8. **추적 참조**: 관련 RE/Arch/Impl/QA 산출물 ID

시스템 프롬프트 **"출력 형식 → 품질 리포트"** YAML 스키마로 구조화 데이터를 함께 출력하고, **"출력 프로토콜"**에 따라 `meta.json`/`body.md`에 기록합니다. 이전 측정 데이터가 있으면 시스템 프롬프트 **"트렌드 분석"** 형식으로 포함합니다.

## 주의사항

- 리포트는 의사결정을 돕는 문서입니다. 수치와 판정을 명확하게 제시하세요
- 품질 게이트 FAIL 시, 구체적인 미달 기준과 해결 방안을 제시하세요
- 잔여 리스크에 대해 과소/과대 평가하지 마세요. 사실에 기반하여 심각도를 판정하세요
- 후속 스킬(deployment, operation, management)이 소비할 수 있도록 구조화된 YAML 출력도 포함하세요
