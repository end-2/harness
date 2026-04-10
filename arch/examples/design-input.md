# 아키텍처 설계 입력 예시

> 휴가 관리 시스템 — RE spec 산출물 (중량 모드: FR 8개, NFR 3개, 품질 속성 4개)

---

## RE 산출물 3섹션

### 섹션 1: 요구사항 명세

#### 기능 요구사항 (FR)

```yaml
- id: FR-001
  category: functional/authentication
  title: 사내 SSO 로그인
  description: |
    직원은 사내 SAML 2.0 기반 SSO를 통해 시스템에 로그인한다.
  priority: Must
  acceptance_criteria:
    - SSO 인증 성공 시 대시보드로 이동
    - 미인증 사용자는 SSO 로그인 페이지로 리다이렉트
    - 세션은 8시간 유지
  source: "사용자 요청 (Turn 2)"
  dependencies: []

- id: FR-002
  category: functional/leave-request
  title: 휴가 신청
  description: |
    직원은 휴가 유형을 선택하고 기간과 사유를 입력하여 휴가를 신청한다.
  priority: Must
  acceptance_criteria:
    - 연차, 반차, 병가, 특별휴가 유형 선택 가능
    - 잔여 휴가 부족 시 신청 차단
    - 신청 후 상태 '대기중'
  source: "사용자 요청 (Turn 1, 3)"
  dependencies: [FR-001, FR-005]

- id: FR-003
  category: functional/approval
  title: 휴가 승인/반려
  description: |
    팀장은 팀원의 휴가 신청을 승인 또는 반려한다.
  priority: Must
  acceptance_criteria:
    - 대기중 휴가 목록 확인 가능
    - 반려 시 사유 입력 필수
    - 승인/반려 즉시 이메일 알림 발송
  source: "사용자 요청 (Turn 3)"
  dependencies: [FR-001, FR-002]

- id: FR-004
  category: functional/calendar
  title: 팀 휴가 캘린더
  description: |
    직원은 팀의 휴가 일정을 캘린더 뷰로 확인한다.
  priority: Should
  acceptance_criteria:
    - 승인된 휴가가 캘린더에 표시
    - 월별/주별 보기 전환
    - 렌더링 3초 이내
  source: "사용자 요청 (Turn 4)"
  dependencies: [FR-001, FR-002]

- id: FR-005
  category: functional/balance
  title: 잔여 휴가 조회
  description: |
    직원은 유형별 휴가 잔여일수를 실시간 조회한다.
  priority: Must
  acceptance_criteria:
    - 유형별 총/사용/잔여 일수 표시
    - 연차 자동 부여 (1월 1일)
  source: "사용자 요청 (Turn 2, 5)"
  dependencies: [FR-001]

- id: FR-006
  category: functional/notification
  title: 알림
  description: |
    주요 이벤트 발생 시 이메일 알림을 발송한다.
  priority: Should
  acceptance_criteria:
    - 승인/반려 시 신청자에게 알림
    - 휴가 전일 리마인더
    - 미처리 건 매일 09:00 알림
  source: "사용자 요청 (Turn 6)"
  dependencies: [FR-003]

- id: FR-007
  category: functional/admin
  title: 관리자 기능
  description: |
    HR 담당자는 전 직원 휴가 현황 조회 및 통계 리포트를 생성한다.
  priority: Should
  acceptance_criteria:
    - 전 직원 휴가 현황 조회
    - 부서별/기간별 필터링
    - CSV 다운로드
  source: "에이전트 제안 → 사용자 확인 (Turn 7)"
  dependencies: [FR-001]

- id: FR-008
  category: functional/leave-request
  title: 휴가 신청 취소/수정
  description: |
    직원은 대기중 상태의 휴가 신청을 취소하거나 수정한다.
  priority: Must
  acceptance_criteria:
    - 대기중 건만 취소/수정 가능
    - 승인 완료 건은 취소 요청으로 전달
    - 변경 이력 기록
  source: "분석 단계 누락 식별"
  dependencies: [FR-002]
```

#### 비기능 요구사항 (NFR)

```yaml
- id: NFR-001
  category: non-functional/performance
  title: 응답 시간
  description: 주요 API 응답 시간이 사용자 경험을 저해하지 않는 수준 유지
  priority: Should
  acceptance_criteria:
    - 초기 페이지 로드 3초 이내
    - API 응답 P95 1초 이내
  source: "사용자 요청 (Turn 8)"
  dependencies: []

- id: NFR-002
  category: non-functional/availability
  title: 가용성
  description: 업무 시간 동안 시스템 안정 운영
  priority: Should
  acceptance_criteria:
    - 업무 시간 99.5% 가용성
    - 장애 시 30분 이내 복구
  source: "사용자 요청 (Turn 8)"
  dependencies: []

- id: NFR-003
  category: non-functional/security
  title: 감사 로그
  description: 모든 주요 행위에 대한 감사 로그 기록
  priority: Should
  acceptance_criteria:
    - 신청/승인/반려/수정/취소 로그 기록
    - 최소 3년 보관
    - HR만 조회 가능
  source: "분석 단계 누락 식별"
  dependencies: []
```

### 섹션 2: 제약 조건

```yaml
- id: CON-001
  type: technical
  title: 사내 SAML 2.0 SSO 연동
  description: 사내 SAML 2.0 기반 SSO 시스템과 연동
  rationale: 사내 통합 인증 정책
  impact: 자체 인증 시스템 구축 불가
  flexibility: hard

- id: CON-002
  type: business
  title: 사용자 규모
  description: 전체 500명, 동시 접속 최대 100명
  rationale: 현재 직원 수 기준, 2년 내 700명 예상
  impact: DB 및 세션 관리 용량 산정 기준
  flexibility: soft

- id: CON-003
  type: environmental
  title: 사내 프라이빗 클라우드 배포
  description: 사내 OpenStack 기반 프라이빗 클라우드에 배포
  rationale: 직원 개인정보 외부 클라우드 저장 불가
  impact: 퍼블릭 클라우드 관리형 서비스 사용 불가
  flexibility: hard

- id: CON-004
  type: business
  title: 1차 릴리스 일정
  description: 3개월 이내 1차 릴리스 완료
  rationale: 내년 1월 새 휴가 정책 적용
  impact: Must 요구사항 우선 구현
  flexibility: negotiable

- id: CON-005
  type: regulatory
  title: 개인정보보호법 준수
  description: 직원 개인정보(병가 사유 등) 처리 시 법 준수
  rationale: 법적 의무
  impact: 접근 권한 분리, 보관 기간, 파기 절차 필요
  flexibility: hard
```

### 섹션 3: 품질 속성 우선순위

```yaml
- attribute: usability
  priority: 1
  description: 별도 교육 없이 직관적 사용
  metric: "신규 사용자가 5분 이내 첫 휴가 신청 완료"
  trade_off_notes: >
    보안 강화보다 사용 편의성 우선.
    민감 정보는 기본 숨김 + 권한 확인으로 절충.

- attribute: availability
  priority: 2
  description: 업무 시간 안정 서비스
  metric: "업무 시간 99.5% 가용성, 장애 시 30분 내 복구"
  trade_off_notes: >
    24/7 고가용성 불필요, 야간 유지보수 윈도우 허용.

- attribute: security
  priority: 3
  description: 직원 개인정보 보호
  metric: "민감 정보 접근 제한, 감사 로그 100% 기록"
  trade_off_notes: >
    매 접근 시 재인증 불필요, 민감 정보 접근 시에만 권한 검증.

- attribute: maintainability
  priority: 4
  description: 휴가 정책 변경 용이
  metric: "정책 변경 시 설정 변경으로 반영 (2차 릴리스 목표)"
  trade_off_notes: >
    1차 릴리스는 하드코딩, 2차에서 설정 기반 전환.
```

---

## 기술적 맥락 (사용자 대화에서 파악)

```
팀 규모: 백엔드 2명, 프론트엔드 1명, 풀스택 1명 (총 4명)
기술 경험: Python/Django 3년+, React 2년+, PostgreSQL 운영 경험 있음
운영 경험: Docker 사용 경험 있으나 Kubernetes 미경험, 기본 모니터링(Prometheus/Grafana)
기존 코드: 없음 (신규 프로젝트)
인프라: OpenStack (VM 기반, Docker 지원, 로드밸런서 사용 가능)
비용 제약: 사내 프라이빗 클라우드이므로 인프라 비용 별도 없음, 유료 라이센스 지양
```
