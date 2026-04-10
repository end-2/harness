# 인시던트 대응 입력 예시

> 온라인 주문 처리 시스템의 Strategy + Monitor + Arch + IaC 산출물

## Strategy 산출물

### 배포 전략

| 항목 | 결정 |
|------|------|
| 배포 방식 | 블루/그린 |
| 롤백 소요 | < 1분 (ALB 전환) |

### 롤백 트리거

| 트리거 | 조건 |
|--------|------|
| SLO 번-레이트 | SLO-002 14.4x (1h/5m) |
| 헬스 체크 실패 | /healthz 연속 3회 실패 |
| 에러율 급증 | 5xx > 5% (5분) |

### 롤백 절차

1. ALB 타겟 그룹을 블루 환경으로 전환
2. 그린 환경 트래픽 차단 확인
3. 블루 환경 헬스 체크 확인
4. 인시던트 채널 알림
5. 그린 환경 태스크 종료 (수동)

### 헬스 체크

| 컴포넌트 | 경로 | 간격 | 실패 임계 |
|---------|------|------|----------|
| api-gateway | /healthz | 10s | 3회 |
| order-service | /healthz | 10s | 3회 |
| user-service | /healthz | 10s | 3회 |

## Monitor 산출물

### 알림 규칙

| ID | 조건 | 심각도 |
|----|------|--------|
| MON-001 | SLO-001 응답시간 번-레이트 14.4x | critical |
| MON-003 | SLO-002 가용성 번-레이트 14.4x | critical |
| MON-006 | 데이터 손실 1건 이상 | critical |
| MON-007 | CPU > 80% (10분) | warning |
| MON-009 | RDS 연결 수 > 80% | warning |
| MON-012 | RabbitMQ 큐 > 10000 | warning |
| MON-013 | RabbitMQ 소비자 = 0 | critical |
| MON-014 | ERROR 로그 > 10건/분 | warning |

## Arch 산출물

### 컴포넌트 구조

| ID | 이름 | 유형 |
|----|------|------|
| COMP-001 | api-gateway | gateway |
| COMP-002 | order-service | service |
| COMP-003 | user-service | service |
| COMP-004 | order-db | store (SQL) |
| COMP-005 | message-queue | queue |

## IaC 산출물

| 항목 | 설정 |
|------|------|
| 클러스터 | ECS Fargate (order-system-prod) |
| 네임스페이스 | order-system |
| DB 호스트 | order-db.xxxxxx.ap-northeast-2.rds.amazonaws.com |
| MQ 호스트 | b-xxxx.mq.ap-northeast-2.amazonaws.com |
