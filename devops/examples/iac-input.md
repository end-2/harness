# Infrastructure as Code 입력 예시

> 온라인 주문 처리 시스템의 Arch 산출물 + SLO 산출물

## Arch 산출물

### 컴포넌트 구조

| ID | 이름 | 유형 | 인터페이스 | 의존성 |
|----|------|------|-----------|--------|
| COMP-001 | api-gateway | gateway | REST API (port 8080), /healthz, /ready | [COMP-002, COMP-003] |
| COMP-002 | order-service | service | REST API (port 3000), /healthz, /ready | [COMP-004, COMP-005] |
| COMP-003 | user-service | service | REST API (port 3001), /healthz, /ready | [COMP-004] |
| COMP-004 | order-db | store (SQL) | PostgreSQL (port 5432) | [] |
| COMP-005 | message-queue | queue | AMQP (port 5672) | [] |

### 기술 스택

| 카테고리 | 선택 | constraint_ref |
|---------|------|---------------|
| cloud | AWS | CON-001 |
| container | Docker + ECS Fargate | - |
| runtime | Node.js 20 | - |
| database | PostgreSQL 16 | - |
| messaging | RabbitMQ 3.12 | - |
| cache | Redis 7 | - |

### 다이어그램 (c4-container)

```
Internet → ALB → api-gateway → order-service → order-db (RDS)
                              → user-service  → order-db (RDS)
                  order-service → message-queue (RabbitMQ)
```

### RE 제약 조건 (간접 참조)

| ID | 유형 | 설명 | flexibility |
|----|------|------|-----------|
| CON-001 | technical | AWS 서울 리전(ap-northeast-2) 사용 필수 | hard |
| CON-003 | regulatory | 개인정보보호법 준수, 주문 데이터 3년 보관 | hard |

## SLO 산출물

| ID | 목표 | 대상 컴포넌트 |
|----|------|-------------|
| SLO-001 | 응답시간 p99 < 200ms | COMP-001, COMP-002 |
| SLO-002 | 가용성 ≥ 99.9% | COMP-001, COMP-002, COMP-003 |
| SLO-004 | 데이터 손실 0% | COMP-004 |
