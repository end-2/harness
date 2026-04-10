# SLO 정의 프롬프트

## 입력

```
Arch 산출물: {{arch_output}}
Impl 산출물: {{impl_output}}
```

## 지시사항

당신은 SLO 설계 전문가입니다. Arch 산출물의 `re_refs`와 `constraint_ref`를 통해 RE 품질 속성 메트릭을 추출하고, 이를 측정 가능한 SLI/SLO로 변환하세요.

### Step 1: RE 품질 속성 메트릭 추출

Arch 산출물에서 다음 경로를 통해 RE 품질 속성을 간접 참조하세요:

- `architecture_decisions[].re_refs` → `QA:performance`, `QA:availability` 등
- `technology_stack[].constraint_ref` → `CON-xxx` (제약 조건)
- `component_structure[].re_refs` → `FR-xxx`, `NFR-xxx`

각 품질 속성에서 `metric` 필드를 추출하고 정량적/정성적 여부를 판별하세요.

### Step 2: SLI 변환

각 품질 속성 메트릭을 측정 가능한 SLI로 변환하세요:

| 변환 패턴 | 입력 예시 | SLI 출력 |
|----------|----------|---------|
| 응답 시간 | "< 200ms" | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` |
| 가용성 | "99.9%" | `1 - (sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])))` |
| 처리량 | "초당 1000건" | `sum(rate(http_requests_total[5m]))` |
| 데이터 지속성 | "손실 0%" | `1 - (data_loss_events_total / data_operations_total)` |

정성적 메트릭(예: "사용자 만족도 높음")은 정량적 프록시 지표로 변환을 시도하세요. 변환이 불가능하면 사용자에게 에스컬레이션하세요.

### Step 3: SLO 목표 설정

각 SLI에 대해:

- **목표치**: RE 메트릭에서 직접 도출
- **측정 기간**: 기본 30일 롤링 윈도우
- **에러 버짓**: `1 - target`으로 계산

### Step 4: 컴포넌트별 SLO 분배

Arch `component_structure.dependencies`를 분석하여:

- 직렬 의존성이면 각 컴포넌트 SLO = 시스템 SLO^(1/n)
- 병렬 의존성이면 각 컴포넌트 SLO = 시스템 SLO
- 크리티컬 경로의 컴포넌트에 더 높은 SLO 할당

### Step 5: 번-레이트 알림 설계

각 SLO에 대해 멀티 윈도우, 멀티 번-레이트 알림을 설계하세요:

- 긴급 (page): 14.4x 번-레이트, 1h/5m 윈도우
- 경고 (ticket): 6x 번-레이트, 6h/30m 윈도우
- 알림 (notification): 3x 번-레이트, 3d/6h 윈도우

### Step 6: 에러 버짓 정책

에러 버짓 소진율에 따른 운영 정책을 정의하세요:

- \> 50%: 정상 배포
- 20~50%: 배포 빈도 감소
- < 20%: 배포 동결
- 0%: 긴급 안정화 모드

### Step 7: 산출물 정리

다음 형식으로 산출물을 정리하세요:

**SLO 정의**: ID, SLI, 목표, 윈도우, 에러 버짓, 번-레이트 알림, RE 근거, 대상 컴포넌트
**에러 버짓 정책**: 잔량 구간, 배포 정책, 변경 허용 범위
**SLA-SLO 매핑**: SLA 항목, SLO ID, 갭 분석 (해당 시)

## 주의사항

- RE 품질 속성의 `metric` 필드를 충실히 반영하세요. 임의로 목표를 변경하지 마세요
- 정성적 메트릭을 정량적으로 변환할 때는 변환 근거를 명시하세요
- 에러 버짓 계산은 정확해야 합니다 (예: 99.9% 가용성 → 월 43.2분, 연 8.76시간)
- 컴포넌트별 SLO 분배 시 의존성 구조를 정확히 반영하세요
