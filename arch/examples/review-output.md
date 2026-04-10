# 아키텍처 리뷰 출력 예시

> 휴가 관리 시스템 아키텍처 리뷰 결과

---

## 전체 요약

휴가 관리 시스템의 아키텍처 설계는 전반적으로 RE 산출물의 요구사항과 제약 조건을 잘 반영하고 있습니다. 모듈러 모놀리스 선택은 팀 규모와 일정 제약에 적합하며, 기술 스택은 팀 역량과 잘 부합합니다. 일부 Minor 이슈와 확인 필요 사항이 있습니다.

---

## 시나리오 검증 결과

| ID | 시나리오 | RE 근거 | 평가 | 분석 |
|----|---------|---------|------|------|
| SV-001 | 100명 동시 접속 시 API 응답 P95 1초 이내 | NFR-001 (performance) | **PASS** | Django + PostgreSQL 구성에서 100명 동시 접속은 충분히 처리 가능. 인덱스 최적화와 커넥션 풀링으로 달성 가능한 수준 |
| SV-002 | 업무 시간 99.5% 가용성 유지 | QA:availability | **RISK** | 단일 서버 배포 시 서버 장애 = 전체 중단. Docker Compose 구성에서 자동 복구 메커니즘 부재 |
| SV-003 | 신규 사용자 5분 이내 첫 휴가 신청 | QA:usability | **PASS** | React SPA + REST API 구성으로 빠른 인터랙션 가능. UI/UX는 구현 단계에서 검증 필요 |
| SV-004 | 민감 정보 접근 제한, 감사 로그 100% | QA:security | **PASS** | RBAC 3역할로 접근 제어, Django 미들웨어로 감사 로그 기록 가능 |
| SV-005 | API Server 장애 시 30분 내 복구 | QA:availability | **RISK** | 복구 절차가 아키텍처 수준에서 정의되지 않음. Docker restart 정책 설정 필요 |

---

## 제약 조건 준수 결과

| 제약 ID | 제약 제목 | 유연성 | 준수 여부 | 근거 |
|---------|----------|--------|----------|------|
| CON-001 | SAML 2.0 SSO 연동 | hard | **COMPLIANT** | AD-004에서 SAML 2.0 인증 채택, django-saml2-auth 라이브러리 사용 |
| CON-002 | 사용자 규모 500명 | soft | **COMPLIANT** | AD-003 단일 PostgreSQL로 500명 충분, 수직 확장으로 700명 대응 가능 |
| CON-003 | 프라이빗 클라우드 배포 | hard | **COMPLIANT** | Docker Compose + OpenStack VM 배포, 퍼블릭 클라우드 서비스 미사용 |
| CON-004 | 3개월 릴리스 일정 | negotiable | **COMPLIANT** | 모듈러 모놀리스(AD-001) + 팀 숙련 기술(Django/React)로 일정 달성 가능 |
| CON-005 | 개인정보보호법 준수 | hard | **COMPLIANT** | RBAC(AD-004)으로 접근 제어, 감사 로그(NFR-003), DB 스키마 분리 |

---

## 추적성 매트릭스

| 요구사항 ID | 매핑된 컴포넌트 | 상태 |
|------------|---------------|------|
| FR-001 | COMP-001, COMP-002, COMP-005 | COVERED |
| FR-002 | COMP-001, COMP-002 | COVERED |
| FR-003 | COMP-001, COMP-002 | COVERED |
| FR-004 | COMP-001, COMP-002 | COVERED |
| FR-005 | COMP-001, COMP-002 | COVERED |
| FR-006 | COMP-002, COMP-004 | COVERED |
| FR-007 | COMP-001, COMP-002 | COVERED |
| FR-008 | COMP-001, COMP-002 | COVERED |
| NFR-001 | COMP-002 | COVERED |
| NFR-002 | COMP-002, COMP-003 | COVERED |
| NFR-003 | COMP-002, COMP-003 | COVERED |

모든 요구사항이 최소 하나의 컴포넌트에 매핑되어 있습니다.

**참고**: COMP-002(API Server)가 10개 요구사항을 담당하고 있으나, 모듈러 모놀리스 구조에서 내부 모듈로 분리되므로 God Component 리스크는 낮습니다.

---

## 리스크 및 기술 부채

| ID | 유형 | 설명 | 심각도 | 개선 제안 |
|----|------|------|--------|----------|
| RISK-001 | SPOF | API Server(COMP-002)가 단일 인스턴스로 SPOF | Minor | Docker restart 정책(`restart: always`) 설정. 2차 릴리스에서 이중화 검토 |
| RISK-002 | SPOF | Database(COMP-003)가 단일 인스턴스로 SPOF | Minor | 정기 백업(pg_dump) + 복구 절차 문서화. 2차 릴리스에서 스트리밍 복제 검토 |
| RISK-003 | 메시지 유실 | Redis 브로커의 메시지 유실 가능성 | Info | 알림 재발송 로직(3회 재시도)으로 대응. 미션 크리티컬하지 않으므로 허용 |

---

## 후속 스킬 소비 적합성

| 소비자 스킬 | 판정 | 부족한 정보 |
|------------|------|-----------|
| impl:generate | **PASS** | 컴포넌트 구조와 기술 스택이 구현 착수에 충분 |
| qa:strategy | **PASS** | REST API 인터페이스가 정의되어 테스트 범위 도출 가능 |
| security:threat-model | **PASS** | SAML + RBAC 인증/인가 결정 존재, 감사 로그 요구사항 존재 |
| deployment:strategy | **PASS** | Docker Compose + OpenStack VM 배포 방식 명확 |
| operation:runbook | **CONDITIONAL** | 모니터링 도구(Prometheus/Grafana) 결정은 있으나, 알림 기준/대시보드 구성은 미정의 (operation 영역) |

---

## 사용자 확인 필요 사항

- [ ] [ESC-001] SV-002/SV-005: 단일 서버 구성에서 99.5% 가용성 목표를 달성하기 위한 복구 전략을 어떻게 할까요?
  - 옵션 A: Docker restart 정책 + 헬스체크로 자동 복구 (1차 릴리스 범위)
  - 옵션 B: Nginx + 2대 API 서버로 이중화 (복잡도 증가)
  - 리뷰어 의견: 옵션 A가 일정(CON-004)을 고려하면 적합. 2차 릴리스에서 이중화 검토 권고

---

## 최종 판정

### **CONDITIONAL**

Critical 이슈 없음. Minor 이슈 2건(SPOF)은 1차 릴리스 규모에서 허용 가능하며, ESC-001의 사용자 확인 후 후속 스킬 진행이 가능합니다.

**권고 조치**:
1. ESC-001에 대한 사용자 의사결정
2. Docker restart 정책 및 DB 백업 전략을 deployment/operation 스킬에서 구체화
3. 2차 릴리스에서 이중화 및 스트리밍 복제 검토
