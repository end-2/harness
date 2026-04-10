# 모니터링 출력 예시

> 온라인 주문 처리 시스템의 모니터링 설정 결과

## 알림 규칙

### SLO 번-레이트 알림

| ID | 유형 | 조건 | 심각도 | 채널 | SLO 참조 |
|----|------|------|--------|------|---------|
| MON-001 | metric | SLO-001 응답시간 번-레이트 14.4x (1h/5m) | critical | PagerDuty + Slack #incidents | SLO-001 |
| MON-002 | metric | SLO-001 응답시간 번-레이트 6x (6h/30m) | warning | Slack #alerts + Jira | SLO-001 |
| MON-003 | metric | SLO-002 가용성 번-레이트 14.4x (1h/5m) | critical | PagerDuty + Slack #incidents | SLO-002 |
| MON-004 | metric | SLO-002 가용성 번-레이트 6x (6h/30m) | warning | Slack #alerts + Jira | SLO-002 |
| MON-005 | metric | SLO-003 처리량 번-레이트 6x (6h/30m) | warning | Slack #alerts | SLO-003 |
| MON-006 | metric | SLO-004 데이터 손실 1건 이상 | critical | PagerDuty + 전화 호출 | SLO-004 |

### 인프라 알림

| ID | 유형 | 조건 | 심각도 | 채널 | 대상 |
|----|------|------|--------|------|------|
| MON-007 | metric | CPU 사용률 > 80% (10분) | warning | Slack #alerts | ECS Tasks |
| MON-008 | metric | 메모리 사용률 > 85% (10분) | warning | Slack #alerts | ECS Tasks |
| MON-009 | metric | RDS 연결 수 > 80% max_connections (5분) | warning | Slack #alerts | COMP-004 |
| MON-010 | metric | RDS 디스크 사용률 > 80% | warning | Slack #alerts | COMP-004 |
| MON-011 | metric | RDS 레플리케이션 지연 > 5초 | warning | Slack #alerts | COMP-004 |
| MON-012 | metric | RabbitMQ 큐 길이 > 10000 (5분) | warning | Slack #alerts | COMP-005 |
| MON-013 | metric | RabbitMQ 소비자 수 = 0 | critical | PagerDuty | COMP-005 |
| MON-014 | log | ERROR 로그 > 10건/분 | warning | Slack #alerts | 전체 서비스 |

### 배포 시 알림 (Strategy 연동)

| ID | 유형 | 조건 | 심각도 | 채널 |
|----|------|------|--------|------|
| MON-015 | metric | 블루/그린 배포 중 그린 환경 5xx > 1% (2분) | critical | Slack #deployments | 
| MON-016 | metric | 블루/그린 배포 중 그린 환경 응답시간 p99 > 300ms (2분) | warning | Slack #deployments |

### 알림 피로도 방지 설정

```yaml
alertmanager_config:
  group_by: ['alertname', 'service', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval:
    critical: 5m
    warning: 30m
    info: 4h
  inhibit_rules:
    - source_match: { severity: 'critical' }
      target_match: { severity: 'warning' }
      equal: ['service']
```

## 대시보드

| ID | 제목 | 패널 수 | 포맷 | 대상 |
|----|------|--------|------|------|
| DASH-001 | System Overview | 8 | grafana-json | 전체 시스템 |
| DASH-002 | api-gateway Service | 6 | grafana-json | COMP-001 |
| DASH-003 | order-service Service | 6 | grafana-json | COMP-002 |
| DASH-004 | user-service Service | 6 | grafana-json | COMP-003 |
| DASH-005 | Infrastructure | 10 | grafana-json | ECS/RDS/MQ/Redis |
| DASH-006 | Deploy Monitor | 4 | grafana-json | 배포 시 |

### DASH-001 패널 구성 (System Overview)

| 패널 | 쿼리 | 시각화 |
|------|------|--------|
| SLO 달성률 | 각 SLO 달성 비율 | Stat (gauge) |
| 에러 버짓 잔량 | `1 - (burned / total)` | Gauge (green/yellow/red) |
| 전체 트래픽 (RPS) | `sum(rate(http_requests_total[5m]))` | Time series |
| 에러율 | `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` | Time series |
| 응답시간 분포 | p50, p90, p99 히트맵 | Heatmap |
| 활성 알림 | 현재 firing 알림 목록 | Table |
| 최근 배포 | 배포 이벤트 어노테이션 | Annotation overlay |
| 서비스 상태 | 컴포넌트별 UP/DOWN | Status map |

### DASH-006 패널 구성 (Deploy Monitor)

| 패널 | 쿼리 | 용도 |
|------|------|------|
| 블루 vs 그린 응답시간 | 환경별 p99 비교 | 성능 비교 |
| 블루 vs 그린 에러율 | 환경별 5xx 비율 비교 | 안정성 비교 |
| 롤아웃 진행률 | 태스크 교체 상태 | 배포 진행 추적 |
| 헬스 체크 상태 | 각 태스크 헬스 | 배포 성공 판단 |

## 분산 추적 설정

| 항목 | 설정 |
|------|------|
| 백엔드 | AWS X-Ray |
| 샘플링 비율 | 에러 요청: 100%, 느린 요청 (> 200ms): 100%, 정상 요청: 5% |
| 전파 방식 | W3C Trace Context (`traceparent` 헤더) |
| 스팬 속성 | `service.name`, `service.version`, `deployment.environment`, `http.method`, `http.status_code`, `http.url` (경로만), `user.id` (해시) |
| 계측 | OpenTelemetry SDK (Node.js) |

## 생성된 설정 파일

| 파일 경로 | 설명 |
|----------|------|
| `monitoring/prometheus/rules/slo-alerts.yml` | SLO 번-레이트 알림 규칙 |
| `monitoring/prometheus/rules/infra-alerts.yml` | 인프라 알림 규칙 |
| `monitoring/prometheus/rules/deploy-alerts.yml` | 배포 시 알림 규칙 |
| `monitoring/alertmanager/config.yml` | Alertmanager 설정 |
| `monitoring/grafana/dashboards/overview.json` | DASH-001 대시보드 |
| `monitoring/grafana/dashboards/service-*.json` | DASH-002~004 서비스 대시보드 |
| `monitoring/grafana/dashboards/infrastructure.json` | DASH-005 인프라 대시보드 |
| `monitoring/grafana/dashboards/deploy.json` | DASH-006 배포 대시보드 |
| `monitoring/otel/collector-config.yaml` | OpenTelemetry Collector 설정 |
