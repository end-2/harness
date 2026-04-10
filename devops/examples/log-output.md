# 로깅 출력 예시

> 온라인 주문 처리 시스템의 로깅 설정 결과

## 로깅 설정 요약

| 항목 | 설정 |
|------|------|
| 로그 포맷 | JSON (구조화) |
| 상관 ID 전파 | `X-Correlation-ID` HTTP 헤더 + AMQP 메시지 속성 |
| 마스킹 규칙 | 6개 필드 유형 |
| 보존 정책 | dev 7일 / staging 30일 / prod 90일 (결제 로그 5년) |

## 구조화 로깅 표준

### 필수 필드

```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "info",
  "service": "order-service",
  "version": "1.2.3",
  "environment": "production",
  "trace_id": "abc123def456",
  "span_id": "789ghi",
  "correlation_id": "req-uuid-001",
  "message": "Order created successfully",
  "context": {
    "order_id": "ORD-12345",
    "user_id": "USR-***"
  },
  "duration_ms": 45
}
```

## 컴포넌트별 로깅 전략

| 컴포넌트 | 유형 | 추가 로그 항목 | 로그 레벨 (prod) |
|---------|------|-------------|----------------|
| api-gateway | gateway | 라우팅 결정, 인증 결과, 레이트 리밋 상태, 클라이언트 IP | INFO |
| order-service | service | 주문 생성/수정/취소 이벤트, 결제 결과 (금액 마스킹), 재고 확인 | INFO |
| user-service | service | 로그인/로그아웃 이벤트, 프로필 변경, 세션 관리 | INFO |
| order-db | store | 슬로우 쿼리 (> 100ms), 커넥션 풀 상태, 마이그레이션 실행 | WARN |
| message-queue | queue | 메시지 발행/소비, 재시도 (횟수 포함), 데드 레터 큐 이동 | INFO |

### 로그 레벨 가이드라인

| 레벨 | 용도 | 예시 |
|------|------|------|
| ERROR | 즉각 조치 필요, 자동 복구 불가 | DB 연결 실패, 외부 결제 API 오류, 데이터 정합성 위반 |
| WARN | 잠재적 문제, 자동 복구됨 | 재시도 성공, 캐시 미스 급증, 커넥션 풀 80% 도달 |
| INFO | 비즈니스 이벤트, 상태 변경 | 주문 생성, 결제 완료, 사용자 로그인 |
| DEBUG | 디버깅용 (prod 비활성) | 쿼리 파라미터, HTTP 헤더, 중간 계산값 |

## 상관 ID 전파

```
[클라이언트]
    │
    ▼ (X-Correlation-ID: uuid-001)
[api-gateway] ──→ 생성: X-Correlation-ID (없으면 UUID 생성)
    │                    로그: { correlation_id: "uuid-001", message: "Request received" }
    ▼ (X-Correlation-ID: uuid-001)
[order-service] ──→ 전파: HTTP 헤더에서 추출
    │                     로그: { correlation_id: "uuid-001", message: "Processing order" }
    ├──▶ [order-db] ──→ 로그: { correlation_id: "uuid-001", message: "Query executed", duration_ms: 12 }
    │
    └──▶ [message-queue] ──→ 전파: AMQP message properties { headers: { correlation_id: "uuid-001" } }
```

## 민감 정보 마스킹 규칙

| 필드 유형 | 마스킹 방법 | 예시 | 적용 위치 |
|----------|-----------|------|----------|
| 이메일 | 부분 마스킹 | `u***@example.com` | 전체 서비스 |
| 전화번호 | 뒤 4자리 유지 | `***-****-1234` | 전체 서비스 |
| 카드 번호 | 앞 6/뒤 4자리 유지 | `4111-11**-****-1111` | order-service |
| 비밀번호 | 완전 마스킹 | `[REDACTED]` | 전체 서비스 |
| 주민등록번호 | 완전 마스킹 | `[REDACTED]` | user-service |
| API 키 | 앞 4자리 유지 | `sk-l***` | api-gateway |

## 보존 및 로테이션 정책

| 환경 | 보존 기간 | 로테이션 | 아카이브 | 비고 |
|------|----------|---------|---------|------|
| dev | 7일 | 일별 | 없음 | |
| staging | 30일 | 일별 | 없음 | |
| prod (일반) | 90일 | 일별 | 1년 → S3 Glacier | CON-003 준수 |
| prod (결제) | 5년 | 일별 | 5년 → S3 Glacier Deep Archive | CON-005 (PCI DSS) 준수 |

### CloudWatch Logs 그룹

| 로그 그룹 | 보존 | 대상 |
|----------|------|------|
| `/ecs/order-system-prod/api-gateway` | 90일 | COMP-001 |
| `/ecs/order-system-prod/order-service` | 90일 | COMP-002 |
| `/ecs/order-system-prod/order-service/payment` | 5년 | COMP-002 (결제) |
| `/ecs/order-system-prod/user-service` | 90일 | COMP-003 |

## 로그 기반 메트릭 (Monitor 연동)

| 로그 패턴 | 생성 메트릭 | 용도 |
|----------|-----------|------|
| `level: "ERROR"` 발생 빈도 | `log_errors_total{service="...", error_type="..."}` | 서비스별 에러율 모니터링 |
| `level: "ERROR"` + `message: "DB connection"` | `db_connection_errors_total` | DB 연결 장애 감지 |
| `duration_ms > 100` (order-db) | `slow_query_count{threshold="100ms"}` | 슬로우 쿼리 추적 |
| `message: "Dead letter"` | `dead_letter_total{queue="..."}` | 메시지 처리 실패 추적 |
| `message: "Rate limit"` | `rate_limit_hits_total` | 레이트 리밋 도달 모니터링 |

## 생성된 설정 파일

| 파일 경로 | 설명 |
|----------|------|
| `config/logging/logger-config.json` | 구조화 로깅 설정 (포맷, 레벨, 필수 필드) |
| `config/logging/masking-rules.json` | 민감 정보 마스킹 규칙 |
| `config/logging/retention-policy.json` | 보존 정책 설정 |
| `infrastructure/modules/monitoring/cloudwatch-logs.tf` | CloudWatch Logs 그룹 및 보존 설정 |
| `infrastructure/modules/monitoring/log-metrics.tf` | 로그 기반 메트릭 필터 |
