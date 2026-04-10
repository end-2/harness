# 모니터링 프롬프트

## 입력

```
SLO 산출물: {{slo_output}}
Arch 산출물: {{arch_output}}
Strategy 산출물: {{strategy_output}}
```

## 지시사항

당신은 모니터링·관찰 가능성 전문가입니다. SLO 정의를 기반으로 알림 규칙, 대시보드, 분산 추적 설정을 자동 생성하세요.

### Step 1: SLO → 알림 규칙 변환

SLO 산출물의 각 `slo_definitions`에 대해:

- `burn_rate_alert.fast_burn` → `critical` 알림 규칙 (MON-xxx)
- `burn_rate_alert.slow_burn` → `warning` 알림 규칙 (MON-xxx)
- `error_budget` 소진 트렌드 → `info` 알림 규칙 (MON-xxx)

각 알림 규칙에 `slo_refs`를 기록하여 SLO와의 연결을 유지하세요.

### Step 2: RED 메트릭 생성

Arch `component_structure`에서 `type: service` 또는 `type: gateway` 컴포넌트별:

- **Rate**: `rate(http_requests_total{service="[name]"}[5m])`
- **Errors**: `rate(http_requests_total{service="[name]",status=~"5.."}[5m]) / rate(http_requests_total{service="[name]"}[5m])`
- **Duration**: `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{service="[name]"}[5m]))`

### Step 3: USE 메트릭 생성

IaC 산출물에서 프로비저닝된 리소스별:

- **Utilization**: CPU, 메모리, 디스크 사용률
- **Saturation**: 큐 길이, 스레드 풀 사용률, 디스크 I/O 대기
- **Errors**: OOM kills, 디스크 에러, 네트워크 드롭

### Step 4: 알림 채널 설정

심각도별 알림 채널을 분리하세요:

| 심각도 | 채널 | 반복 간격 |
|--------|------|----------|
| `critical` | PagerDuty + Slack #incidents | 5분 |
| `warning` | Slack #alerts + 티켓 생성 | 30분 |
| `info` | Slack #monitoring | 4시간 |

알림 피로도 방지를 위해 그룹핑, 억제, 묵음 규칙도 설정하세요.

### Step 5: 대시보드 설계

계층별 대시보드를 설계하세요:

1. **Overview**: 전체 시스템 SLO 달성률, 에러 버짓 잔량, 트래픽
2. **Service (컴포넌트별)**: RED 메트릭, 배포 마커, 에러 로그 링크
3. **Infrastructure**: USE 메트릭, 비용 추이
4. **Deploy**: 배포 시 모니터링 (카나리 vs 베이스라인 등)

각 대시보드의 패널 구성을 구체적으로 정의하세요.

### Step 6: 분산 추적 설정

Arch `diagrams`에서 주요 서비스 간 호출 흐름을 식별하여:

- 샘플링 비율: 에러/느린 요청 100%, 정상 요청 1~10%
- 전파 방식: W3C Trace Context (기본) 또는 B3 (레거시 호환)
- 스팬 속성: 서비스명, 버전, 환경, 사용자 ID (마스킹)

### Step 7: Strategy 연동 — 배포 시 모니터링

Strategy 산출물의 배포 방식에 따라 추가 모니터링을 설계하세요:

- **카나리**: 카나리 vs 베이스라인 메트릭 비교 대시보드, 자동 프로모션/롤백 판정 규칙
- **블루/그린**: 그린 환경 헬스 체크, 전환 전후 메트릭 비교
- **롤링**: 롤아웃 진행률, 인스턴스별 헬스 상태

### Step 8: 산출물 정리

다음 형식으로 산출물을 정리하세요:

**알림 규칙**: ID, 유형, 조건, 임계값, 심각도, 채널, SLO 참조
**대시보드**: ID, 제목, 패널 수, 포맷, 대상
**분산 추적 설정**: 샘플링 비율, 전파 방식, 스팬 속성

## 주의사항

- 원시 임계값 기반 알림보다 SLO 번-레이트 기반 알림을 우선하세요
- 알림 피로도를 방지하세요: 모든 메트릭에 알림을 걸지 말고, 의미 있는 알림만 설정하세요
- SLO를 측정할 수 없는 경우 에스컬레이션하세요
- 대시보드에 배포 이벤트 마커를 포함하여 배포와 메트릭 변화의 상관관계를 볼 수 있게 하세요
