# SLO 정의 출력 예시

> 온라인 주문 처리 시스템의 SLO 정의 결과

## SLO 정의

| ID | SLI | 목표 | 윈도우 | 에러 버짓 | RE 근거 | 대상 컴포넌트 |
|----|-----|------|--------|----------|---------|-------------|
| SLO-001 | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{service=~"order-service\|api-gateway"}[5m]))` | < 0.2s | 30d | 월 43.2분 (0.1%) | QA:performance | COMP-001, COMP-002 |
| SLO-002 | `1 - (sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])))` | ≥ 0.999 | 30d | 월 43.2분 (0.1%) | QA:availability | COMP-001, COMP-002, COMP-003 |
| SLO-003 | `sum(rate(orders_processed_total[5m]))` | ≥ 500/s | 30d | - | QA:scalability | COMP-002, COMP-005 |
| SLO-004 | `1 - (sum(data_loss_events_total) / sum(orders_created_total))` | = 1.0 (100%) | 30d | 0% (무손실) | QA:durability | COMP-004 |

## 컴포넌트별 SLO 분배

시스템 가용성 SLO (99.9%)의 컴포넌트별 분배:

```
요청 경로: api-gateway → order-service → order-db
직렬 의존성 (3개): 각 컴포넌트 SLO = 99.9%^(1/3) ≈ 99.967%
```

| 컴포넌트 | 가용성 SLO | 월 허용 다운타임 | 비고 |
|---------|-----------|--------------|------|
| COMP-001 (api-gateway) | 99.967% | 14.4분 | 크리티컬 경로 진입점 |
| COMP-002 (order-service) | 99.967% | 14.4분 | 핵심 비즈니스 로직 |
| COMP-003 (user-service) | 99.97% | 13분 | 비크리티컬 (캐시 대체 가능) |
| COMP-004 (order-db) | 99.99% | 4.3분 | 데이터 지속성 최우선 |
| COMP-005 (message-queue) | 99.97% | 13분 | 재시도 메커니즘 존재 |

## 번-레이트 알림

### SLO-001 (응답시간)

| 알림 수준 | 번-레이트 | 장기 윈도우 | 단기 윈도우 | 알림 채널 |
|----------|----------|-----------|-----------|----------|
| 긴급 (page) | 14.4x | 1h | 5m | PagerDuty + Slack #incidents |
| 경고 (ticket) | 6x | 6h | 30m | Slack #alerts + Jira 티켓 |
| 알림 (notification) | 3x | 3d | 6h | Slack #monitoring |

### SLO-002 (가용성)

| 알림 수준 | 번-레이트 | 장기 윈도우 | 단기 윈도우 | 알림 채널 |
|----------|----------|-----------|-----------|----------|
| 긴급 (page) | 14.4x | 1h | 5m | PagerDuty + Slack #incidents |
| 경고 (ticket) | 6x | 6h | 30m | Slack #alerts + Jira 티켓 |
| 알림 (notification) | 3x | 3d | 6h | Slack #monitoring |

### SLO-003 (처리량)

| 알림 수준 | 번-레이트 | 장기 윈도우 | 단기 윈도우 | 알림 채널 |
|----------|----------|-----------|-----------|----------|
| 경고 (ticket) | 6x | 6h | 30m | Slack #alerts |
| 알림 (notification) | 3x | 3d | 6h | Slack #monitoring |

### SLO-004 (데이터 지속성)

| 알림 수준 | 번-레이트 | 장기 윈도우 | 단기 윈도우 | 알림 채널 |
|----------|----------|-----------|-----------|----------|
| 긴급 (page) | 1x (즉시) | - | 1m | PagerDuty + Slack #incidents + 전화 |

## 에러 버짓 정책

| 잔량 구간 | 배포 정책 | 변경 허용 범위 |
|----------|----------|-------------|
| > 50% (> 21.6분 잔여) | 정상 배포 주기 (주 2-3회), 실험적 변경 허용 | 전체 |
| 20% ~ 50% (8.6 ~ 21.6분) | 배포 주 1회로 감소, 변경 범위 축소 | 버그 수정 + 계획된 기능 |
| < 20% (< 8.6분) | 배포 동결, 안정성 개선에 집중 | 안정성 관련 변경만 |
| 0% (소진) | 긴급 안정화 모드 | SLO 개선 작업만 허용 |

## SLA-SLO 매핑

> RE `constraints`에 SLA 관련 제약이 없으므로 해당 없음.
> 향후 SLA 설정 시 SLO 대비 10% 마진 확보를 권장합니다 (예: SLO 99.9% → SLA 99.8%).
