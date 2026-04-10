# DevOps 리뷰 입력 예시

> 온라인 주문 처리 시스템의 전체 DevOps 산출물 + 선행 스킬 산출물

## DevOps 산출물 (4섹션)

### 1. 파이프라인 설정

| ID | 플랫폼 | 배포 방식 | 롤백 트리거 |
|----|--------|---------|-----------|
| PL-001 | GitHub Actions | 블루/그린 | SLO 번-레이트, 헬스체크, 에러율 |

### 2. 인프라 코드

| ID | 도구 | 프로바이더 | 모듈 수 |
|----|------|----------|--------|
| IAC-001 | Terraform | AWS (ap-northeast-2) | 7 |

매핑된 컴포넌트: COMP-001~005

### 3. 관찰 가능성 설정

**SLO 정의**: SLO-001~004
**알림 규칙**: MON-001~016
**대시보드**: DASH-001~006
**로깅**: JSON 구조화, 마스킹 6 규칙, 상관 ID 전파

### 4. 운영 런북

**런북**: RB-001~007
**에스컬레이션 매트릭스**: 4단계 (critical ~ low)

## Arch 산출물 (추적성 검증 기준)

### 컴포넌트 구조

| ID | 이름 | 유형 |
|----|------|------|
| COMP-001 | api-gateway | gateway |
| COMP-002 | order-service | service |
| COMP-003 | user-service | service |
| COMP-004 | order-db | store |
| COMP-005 | message-queue | queue |

### RE 품질 속성 (간접 참조)

| 속성 | 메트릭 |
|------|--------|
| QA:performance | "API 응답시간 p99 < 200ms" |
| QA:availability | "시스템 가용성 99.9%" |
| QA:scalability | "초당 500건 이상 주문 처리" |
| QA:durability | "주문 데이터 손실 0%" |

## Impl 산출물 (추적성 검증 기준)

### 구현 가이드

```yaml
build_commands:
  - npm ci
  - npm run build
  - npm run test
```

### 구현 맵

| 모듈 경로 | component_ref |
|----------|---------------|
| services/api-gateway/ | COMP-001 |
| services/order-service/ | COMP-002 |
| services/user-service/ | COMP-003 |
