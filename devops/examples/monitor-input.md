# 모니터링 입력 예시

> 온라인 주문 처리 시스템의 SLO + Arch + Strategy 산출물

## SLO 산출물

| ID | SLI | 목표 | 에러 버짓 | 대상 컴포넌트 |
|----|-----|------|----------|-------------|
| SLO-001 | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` | < 0.2s | 0.1% | COMP-001, COMP-002 |
| SLO-002 | `1 - (error_requests / total_requests)` | ≥ 0.999 | 월 43.2분 | COMP-001~003 |
| SLO-003 | `sum(rate(orders_processed_total[5m]))` | ≥ 500/s | - | COMP-002, COMP-005 |
| SLO-004 | `1 - (data_loss_events / orders_total)` | = 1.0 | 0% | COMP-004 |

### 번-레이트 알림 설정

각 SLO에 대해:
- 긴급: 14.4x, 1h/5m
- 경고: 6x, 6h/30m
- 알림: 3x, 3d/6h

## Arch 산출물

### 컴포넌트 구조

| ID | 이름 | 유형 | 의존성 |
|----|------|------|--------|
| COMP-001 | api-gateway | gateway | [COMP-002, COMP-003] |
| COMP-002 | order-service | service | [COMP-004, COMP-005] |
| COMP-003 | user-service | service | [COMP-004] |
| COMP-004 | order-db | store | [] |
| COMP-005 | message-queue | queue | [] |

## Strategy 산출물

| 항목 | 결정 |
|------|------|
| 배포 방식 | 블루/그린 |
| 롤백 트리거 | SLO-002 14.4x 번-레이트 (1h), 헬스 체크 3회 실패, 5xx > 5% |
