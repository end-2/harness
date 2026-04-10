# 아키텍처 설계 출력 예시

> 휴가 관리 시스템 — 중량 모드

---

## RE 산출물 분석 결과

- 요구사항: FR 8개, NFR 3개
- 제약 조건: 5개 (hard: 3, soft: 1, negotiable: 1)
- 품질 속성: 4개
- → **중량 모드**로 진행합니다

### 핵심 아키텍처 드라이버

1. **usability** (priority 1): "신규 사용자가 5분 이내 첫 휴가 신청 완료"
2. **availability** (priority 2): "업무 시간 99.5% 가용성, 장애 시 30분 내 복구"
3. **CON-001** (hard): 사내 SAML 2.0 SSO 연동 필수
4. **CON-003** (hard): 사내 OpenStack 프라이빗 클라우드 배포 필수
5. **CON-005** (hard): 개인정보보호법 준수

---

## 섹션 1: 아키텍처 결정 요약

```yaml
- id: AD-001
  title: 모듈러 모놀리스 아키텍처 채택
  decision: |
    시스템을 단일 배포 단위의 모듈러 모놀리스로 구성한다.
    내부적으로 도메인 모듈(인증, 휴가관리, 알림, 관리)로 분리하되,
    하나의 프로세스로 배포한다.
  rationale: |
    4명의 소규모 팀으로 3개월 내 1차 릴리스(CON-004)를 달성하려면
    마이크로서비스의 운영 복잡도를 감당하기 어렵다.
    팀에 Kubernetes 경험이 없고(기술적 맥락), 사용자 규모가 500명(CON-002)으로
    분산 시스템이 불필요하다.
    모듈 경계를 명확히 하여 향후 필요 시 서비스 분리가 가능하도록 한다.
  alternatives_considered:
    - name: 마이크로서비스
      pros: 독립 배포, 기술 이질성, 확장성
      cons: 운영 복잡도 높음, K8s 경험 부재, 3개월 일정 리스크
      rejection_reason: 팀 규모와 일정 제약에 비해 과도한 복잡성
    - name: 전통적 모놀리스
      pros: 단순함, 빠른 개발
      cons: 모듈 경계 불명확, 향후 분리 어려움
      rejection_reason: 2차 릴리스에서 정책 엔진 도입 시 모듈 경계 필요
  trade_offs: |
    단일 배포 단위로 인해 개별 모듈의 독립 확장은 불가하나,
    500명 규모에서는 수직 확장으로 충분하다.
    향후 사용자가 크게 증가하면 모듈 단위 서비스 분리를 검토한다.
  re_refs: [CON-002, CON-004, QA:availability, QA:maintainability]

- id: AD-002
  title: SPA + REST API 아키텍처
  decision: |
    프론트엔드는 React SPA, 백엔드는 Django REST API로 구성한다.
    프론트엔드와 백엔드를 별도 프로젝트로 분리하되 동일 서버에 배포한다.
  rationale: |
    usability(priority 1)를 위해 SPA의 빠른 페이지 전환이 필요하다(NFR-001).
    팀의 React 2년+, Django 3년+ 경험을 활용한다.
  alternatives_considered:
    - name: SSR (Django Template)
      pros: 단순한 구조, SEO 유리
      cons: 페이지 전환 느림, 사용성 저하
      rejection_reason: usability(priority 1) 요구에 미달
    - name: Next.js + Django
      pros: SSR + CSR 혼합, SEO 유리
      cons: 팀의 Next.js 경험 부족, 복잡도 증가
      rejection_reason: 사내 시스템으로 SEO 불필요, 팀 역량 미스매치
  trade_offs: |
    SPA 초기 로딩이 SSR 대비 느리나(3초 이내 목표),
    이후 페이지 전환은 500ms 이내로 훨씬 빠르다.
  re_refs: [NFR-001, QA:usability, FR-004]

- id: AD-003
  title: PostgreSQL 단일 데이터베이스
  decision: |
    PostgreSQL 14를 단일 데이터베이스로 사용한다.
    도메인 모듈별로 스키마(schema)를 분리하여 논리적 경계를 유지한다.
  rationale: |
    팀의 PostgreSQL 운영 경험 활용.
    프라이빗 클라우드(CON-003)에서 관리형 서비스 불가하므로
    직접 운영이 가능한 기술을 선택한다.
    500명 규모(CON-002)에서 단일 DB로 충분하다.
  alternatives_considered:
    - name: PostgreSQL + Redis 캐시
      pros: 읽기 성능 향상
      cons: 운영 포인트 증가, 캐시 무효화 복잡
      rejection_reason: P95 1초 목표는 DB 인덱스 최적화로 달성 가능
    - name: MySQL
      pros: 널리 사용, 다양한 도구
      cons: 팀 경험 부족, JSON 지원 열위
      rejection_reason: 팀의 기존 PostgreSQL 역량 활용
  trade_offs: |
    캐시 레이어 없이 운영하므로 읽기 부하가 모두 DB에 집중되나,
    100명 동시 접속 수준에서는 인덱스 최적화로 충분하다.
  re_refs: [CON-002, CON-003, NFR-001]

- id: AD-004
  title: SAML 2.0 기반 인증 + RBAC 인가
  decision: |
    인증은 사내 SAML 2.0 SSO를 통해 처리하고,
    인가는 역할 기반 접근 제어(RBAC)로 구현한다.
    역할: 직원(employee), 팀장(manager), HR(admin).
  rationale: |
    CON-001(hard)에 의해 SAML 2.0 SSO 필수.
    CON-005(hard) 개인정보보호를 위해 민감 정보(병가 사유)에 대한
    역할별 접근 제어 필요.
  alternatives_considered:
    - name: RBAC + ABAC 혼합
      pros: 더 세밀한 접근 제어
      cons: 구현 복잡도 증가, 정책 관리 부담
      rejection_reason: 3개 역할로 충분한 수준, 과도한 복잡성
  trade_offs: |
    RBAC은 역할이 추가될 때 코드 변경이 필요하나,
    현재 3개 역할로 단순하므로 적절하다.
  re_refs: [CON-001, CON-005, QA:security, FR-001]

- id: AD-005
  title: 비동기 이메일 발송 (Celery + Redis)
  decision: |
    이메일 알림은 Celery 태스크 큐를 통해 비동기로 처리한다.
    브로커로 Redis를 사용한다.
  rationale: |
    알림 발송(FR-006)이 사용자 요청의 응답 시간에 영향을 주지 않도록
    비동기 처리가 필요하다(NFR-001).
    팀의 Django + Celery 경험 활용.
  alternatives_considered:
    - name: 동기 이메일 발송
      pros: 단순한 구현
      cons: API 응답 시간 증가, 메일 서버 장애 시 요청 실패
      rejection_reason: NFR-001 응답 시간 목표 위반 리스크
    - name: RabbitMQ 브로커
      pros: 더 강력한 메시지 보장
      cons: 운영 복잡도, 추가 인프라
      rejection_reason: 알림 발송 수준에서 Redis로 충분
  trade_offs: |
    Redis 브로커는 메시지 유실 가능성이 있으나,
    알림 재발송 로직(3회 재시도)으로 대응한다.
    미션 크리티컬한 메시지가 아니므로 허용 가능.
  re_refs: [FR-006, NFR-001, QA:usability]
```

---

## 섹션 2: 컴포넌트 구조

```yaml
- id: COMP-001
  name: Web Frontend
  responsibility: 사용자 인터페이스 제공 (SPA)
  type: ui
  interfaces:
    - name: User Interface
      direction: inbound
      protocol: HTTPS
  dependencies: [COMP-002]
  re_refs: [FR-001, FR-002, FR-003, FR-004, FR-005, FR-007, FR-008, QA:usability]

- id: COMP-002
  name: API Server
  responsibility: 비즈니스 로직 처리 및 REST API 제공
  type: service
  interfaces:
    - name: REST API
      direction: inbound
      protocol: REST
    - name: Database Access
      direction: outbound
      protocol: SQL
    - name: Task Queue
      direction: outbound
      protocol: message
    - name: SSO Integration
      direction: outbound
      protocol: SAML
  dependencies: [COMP-003, COMP-004, COMP-005]
  re_refs: [FR-001, FR-002, FR-003, FR-005, FR-007, FR-008, NFR-001, NFR-003]

- id: COMP-003
  name: Database
  responsibility: 데이터 영구 저장 (요구사항, 사용자, 감사 로그)
  type: store
  interfaces:
    - name: SQL Interface
      direction: inbound
      protocol: SQL
  dependencies: []
  re_refs: [NFR-002, NFR-003, CON-005]

- id: COMP-004
  name: Task Queue
  responsibility: 비동기 작업 처리 (이메일 발송, 스케줄 작업)
  type: queue
  interfaces:
    - name: Task Submission
      direction: inbound
      protocol: message
    - name: SMTP Outbound
      direction: outbound
      protocol: SMTP
  dependencies: []
  re_refs: [FR-006]

- id: COMP-005
  name: SSO Provider
  responsibility: 사내 SAML 2.0 기반 인증 서비스 (외부 시스템)
  type: service
  interfaces:
    - name: SAML Interface
      direction: inbound
      protocol: SAML
  dependencies: []
  re_refs: [FR-001, CON-001]
```

---

## 섹션 3: 기술 스택

```yaml
- category: language
  choice: Python 3.11
  rationale: 팀 전원 3년+ 경험, Django 생태계 활용
  decision_ref: AD-002
  constraint_ref: null

- category: framework
  choice: Django 4.2 + Django REST Framework
  rationale: 팀 숙련도 높음, SAML 라이브러리(django-saml2-auth) 활용, ORM으로 빠른 개발
  decision_ref: AD-002
  constraint_ref: CON-004

- category: framework
  choice: React 18 + TypeScript
  rationale: 팀 2년+ 경험, SPA로 usability(priority 1) 충족
  decision_ref: AD-002
  constraint_ref: null

- category: database
  choice: PostgreSQL 14
  rationale: 팀 운영 경험, 프라이빗 클라우드에서 직접 운영 가능
  decision_ref: AD-003
  constraint_ref: CON-003

- category: messaging
  choice: Redis 7 (Celery 브로커)
  rationale: 비동기 알림 발송용 경량 브로커, Django + Celery 생태계 통합
  decision_ref: AD-005
  constraint_ref: null

- category: infra
  choice: Docker + Docker Compose
  rationale: 팀 Docker 경험 있음, OpenStack VM 위에서 컨테이너 실행
  decision_ref: AD-001
  constraint_ref: CON-003

- category: tool
  choice: Nginx (리버스 프록시)
  rationale: SPA 정적 파일 서빙 + API 프록시, 무료 오픈소스
  decision_ref: AD-002
  constraint_ref: null

- category: tool
  choice: Prometheus + Grafana (모니터링)
  rationale: 팀 기존 경험 활용, 가용성(QA:availability) 모니터링
  decision_ref: null
  constraint_ref: null
```
