# SLO 정의 입력 예시

> 온라인 주문 처리 시스템의 Arch 산출물에서 RE 품질 속성을 간접 참조하는 예시

## Arch 산출물

### 아키텍처 결정

| ID | 결정 | re_refs |
|----|------|---------|
| AD-001 | 마이크로서비스 아키텍처 채택 | QA:scalability, QA:availability |
| AD-002 | 이벤트 기반 비동기 처리 | QA:performance, QA:reliability |

### 컴포넌트 구조

| ID | 이름 | 유형 | 의존성 |
|----|------|------|--------|
| COMP-001 | api-gateway | gateway | [COMP-002, COMP-003] |
| COMP-002 | order-service | service | [COMP-004, COMP-005] |
| COMP-003 | user-service | service | [COMP-004] |
| COMP-004 | order-db | store | [] |
| COMP-005 | message-queue | queue | [] |

### 기술 스택

| 카테고리 | 선택 | constraint_ref |
|---------|------|---------------|
| cloud | AWS | CON-001 |
| runtime | Node.js 20 | - |
| database | PostgreSQL 16 | - |
| messaging | RabbitMQ | - |

### RE 품질 속성 (간접 참조)

| 속성 | 우선순위 | 메트릭 |
|------|----------|--------|
| QA:performance | 1 | "API 응답시간 p99 < 200ms" |
| QA:availability | 2 | "시스템 가용성 99.9%" |
| QA:scalability | 3 | "초당 500건 이상 주문 처리" |
| QA:durability | 4 | "주문 데이터 손실 0%" |

### RE 제약 조건 (간접 참조)

| ID | 유형 | 설명 |
|----|------|------|
| CON-001 | technical | AWS 서울 리전(ap-northeast-2) 사용 필수 |
| CON-003 | regulatory | 개인정보보호법 준수, 주문 데이터 3년 보관 |
