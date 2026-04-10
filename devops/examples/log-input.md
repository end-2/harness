# 로깅 입력 예시

> 온라인 주문 처리 시스템의 Arch + IaC 산출물

## Arch 산출물

### 컴포넌트 구조

| ID | 이름 | 유형 | 인터페이스 | 의존성 |
|----|------|------|-----------|--------|
| COMP-001 | api-gateway | gateway | REST API (port 8080) | [COMP-002, COMP-003] |
| COMP-002 | order-service | service | REST API (port 3000) | [COMP-004, COMP-005] |
| COMP-003 | user-service | service | REST API (port 3001) | [COMP-004] |
| COMP-004 | order-db | store (SQL) | PostgreSQL (port 5432) | [] |
| COMP-005 | message-queue | queue | AMQP (port 5672) | [] |

### RE 제약 조건 (간접 참조)

| ID | 유형 | 설명 | flexibility |
|----|------|------|-----------|
| CON-003 | regulatory | 개인정보보호법 준수, 주문 데이터 3년 보관 | hard |
| CON-005 | regulatory | 결제 관련 로그 5년 보관 (PCI DSS) | hard |

## IaC 산출물

| ID | 프로바이더 | 리전 |
|----|----------|------|
| IAC-001 | AWS | ap-northeast-2 |

### 로깅 인프라

- CloudWatch Logs: 각 ECS 서비스별 로그 그룹
- 로그 전달: ECS → CloudWatch Logs → (선택) Elasticsearch/OpenSearch
