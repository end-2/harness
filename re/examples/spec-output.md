# 요구사항 명세 출력 예시

> 휴가 관리 시스템 — 중량 모드 (요구사항 12개, 제약 조건 5개)
> 출력 형식은 skills.yaml의 spec.output 스키마를 따릅니다.

---

## 요구사항 명세 (requirements_spec)

### 기능 요구사항 (FR)

```yaml
- id: FR-001
  category: functional/authentication
  title: 사내 SSO 로그인
  description: |
    직원은 사내 SAML 2.0 기반 SSO를 통해 시스템에 로그인한다.
    별도 회원가입 없이 사번과 SSO 인증으로 접근 가능하다.
  priority: Must
  acceptance_criteria:
    - SSO 인증 성공 시 대시보드 페이지로 이동한다
    - 미인증 사용자가 어떤 페이지에 접근해도 SSO 로그인 페이지로 리다이렉트된다
    - SSO 인증 실패 시 "인증에 실패했습니다. 관리자에게 문의하세요" 메시지가 표시된다
    - 로그인 후 세션은 8시간 유지되며, 만료 시 재인증이 필요하다
  source: "사용자 요청 (Turn 2)"
  dependencies: []

- id: FR-002
  category: functional/leave-request
  title: 휴가 신청
  description: |
    직원은 휴가 유형을 선택하고 기간과 사유를 입력하여 휴가를 신청한다.
    신청된 휴가는 '대기중' 상태로 직속 팀장에게 전달된다.
  priority: Must
  acceptance_criteria:
    - 연차, 반차(오전/오후), 병가, 특별휴가 유형 중 선택 가능하다
    - 시작일, 종료일, 사유를 입력하여 신청한다
    - 시작일은 오늘 이후여야 한다
    - 잔여 휴가가 부족하면 신청이 차단되고 안내 메시지가 표시된다
    - 신청 완료 후 상태가 '대기중'으로 표시된다
  source: "사용자 요청 (Turn 1, 3)"
  dependencies: [FR-001, FR-005]

- id: FR-003
  category: functional/approval
  title: 휴가 승인/반려
  description: |
    팀장은 팀원의 휴가 신청을 검토하고 승인 또는 반려한다.
    반려 시 사유를 입력해야 하며, 결과는 신청자에게 알림으로 전달된다.
  priority: Must
  acceptance_criteria:
    - 팀장은 대기중인 팀원의 휴가 신청 목록을 확인할 수 있다
    - 승인 버튼 클릭 시 상태가 '승인됨'으로 변경된다
    - 반려 시 사유 입력이 필수이며, 상태가 '반려됨'으로 변경된다
    - 승인/반려 즉시 신청자에게 이메일 알림이 발송된다
  source: "사용자 요청 (Turn 3)"
  dependencies: [FR-001, FR-002]

- id: FR-004
  category: functional/calendar
  title: 팀 휴가 캘린더
  description: |
    직원은 자신이 속한 팀의 휴가 일정을 캘린더 뷰로 확인할 수 있다.
  priority: Should
  acceptance_criteria:
    - 승인된 팀원 휴가가 캘린더에 표시된다
    - 월별 보기와 주별 보기 전환이 가능하다
    - 휴가 유형별로 색상이 구분된다
    - 캘린더 렌더링이 3초 이내에 완료된다
  source: "사용자 요청 (Turn 4)"
  dependencies: [FR-001, FR-002]

- id: FR-005
  category: functional/balance
  title: 잔여 휴가 조회
  description: |
    직원은 자신의 유형별 휴가 잔여일수를 실시간으로 조회할 수 있다.
    연차는 매년 1월 1일에 근속 연수 기준으로 자동 부여된다.
  priority: Must
  acceptance_criteria:
    - 유형별(연차, 병가, 특별휴가) 총 일수, 사용 일수, 잔여 일수가 표시된다
    - 매년 1월 1일에 연차가 자동 부여된다 (기본 15일, 3년 이상 근속 시 연 1일 가산)
    - 대기중인 신청 건도 반영하여 '예상 잔여일수'를 표시한다
  source: "사용자 요청 (Turn 2, 5)"
  dependencies: [FR-001]

- id: FR-006
  category: functional/notification
  title: 알림
  description: |
    주요 이벤트 발생 시 관련 사용자에게 이메일 알림을 발송한다.
  priority: Should
  acceptance_criteria:
    - 휴가 승인/반려 시 신청자에게 이메일 알림이 발송된다
    - 휴가 시작 전일 17:00에 리마인더 이메일이 발송된다
    - 미처리 신청 건이 있는 팀장에게 매일 09:00에 알림이 발송된다
    - 알림 발송 실패 시 최대 3회 재시도한다
  source: "사용자 요청 (Turn 6) + 에이전트 제안"
  dependencies: [FR-003]

- id: FR-007
  category: functional/admin
  title: 관리자 기능
  description: |
    HR 담당자는 전 직원의 휴가 현황을 조회하고, 휴가 정책을 관리하며,
    통계 리포트를 생성할 수 있다.
  priority: Should
  acceptance_criteria:
    - HR 역할의 사용자는 전 직원 휴가 현황을 조회할 수 있다
    - 부서별, 기간별 필터링이 가능하다
    - 연간 휴가 사용 통계 리포트를 CSV로 다운로드할 수 있다
  source: "에이전트 제안 → 사용자 확인 (Turn 7)"
  dependencies: [FR-001]

- id: FR-008
  category: functional/leave-request
  title: 휴가 신청 취소/수정
  description: |
    직원은 대기중 상태의 휴가 신청을 취소하거나 수정할 수 있다.
  priority: Must
  acceptance_criteria:
    - 상태가 '대기중'인 신청 건만 취소/수정 가능하다
    - 승인 완료된 신청 건의 취소는 팀장에게 취소 요청으로 전달된다
    - 수정 시 변경 이력이 기록된다
  source: "분석 단계에서 누락 식별 → 사용자 확인 (Q-002)"
  dependencies: [FR-002]
```

### 비기능 요구사항 (NFR)

```yaml
- id: NFR-001
  category: non-functional/performance
  title: 응답 시간
  description: |
    시스템의 주요 페이지 로드 시간과 API 응답 시간이 사용자 경험을
    저해하지 않는 수준을 유지한다. SPA 아키텍처를 채택하여 초기 로딩 후
    빠른 네비게이션을 보장한다.
  priority: Should
  acceptance_criteria:
    - 초기 페이지 로드 시간이 3초 이내이다 (SPA 번들)
    - 이후 페이지 전환 시간이 500ms 이내이다
    - API 응답 시간이 P95 기준 1초 이내이다
    - 캘린더 뷰 렌더링이 3초 이내이다
  source: "사용자 요청 (Turn 8) + 분석 결정 (Q-001: SPA 채택)"
  dependencies: []

- id: NFR-002
  category: non-functional/availability
  title: 가용성
  description: |
    업무 시간 동안 시스템이 안정적으로 운영되어야 한다.
  priority: Should
  acceptance_criteria:
    - 업무 시간(09:00-18:00, 평일) 내 99.5% 가용성을 유지한다
    - 야간(22:00-06:00) 유지보수 윈도우를 허용한다
    - 장애 발생 시 30분 이내에 복구한다
  source: "사용자 요청 (Turn 8)"
  dependencies: []

- id: NFR-003
  category: non-functional/security
  title: 감사 로그
  description: |
    모든 주요 행위에 대한 감사 로그를 기록하여 추적 가능성을 보장한다.
  priority: Should
  acceptance_criteria:
    - 신청, 승인, 반려, 수정, 취소 행위에 대한 로그가 기록된다
    - 로그에는 행위자, 시각, 행위 유형, 대상이 포함된다
    - 로그는 최소 3년간 보관된다
    - HR 담당자만 감사 로그를 조회할 수 있다
  source: "분석 단계에서 누락 식별 (CON-005 개인정보보호법 대응)"
  dependencies: []
```

---

## 제외 항목 (excluded_items)

```yaml
- id: FR-009
  title: 대리 승인
  reason: "1차 릴리스 일정(CON-004) 내 구현 범위를 초과. 사용자가 2차 릴리스로 연기 결정 (Q-003)"
  reconsider_trigger: "1차 릴리스 이후 팀장 부재로 인한 승인 지연이 빈번하게 발생하는 경우"
```

---

## 제약 조건 (constraints)

```yaml
- id: CON-001
  type: technical
  title: 사내 SAML 2.0 SSO 연동
  description: 기존 사내 SAML 2.0 기반 SSO 시스템과 연동하여 인증을 처리해야 한다
  rationale: 사내 통합 인증 정책에 따라 모든 내부 시스템은 SSO를 사용해야 함
  impact: 자체 인증 시스템 구축 불가, SSO 장애 시 시스템 전체 접근 불가
  flexibility: hard

- id: CON-002
  type: business
  title: 사용자 규모
  description: 전체 사용자 약 500명, 동시 접속 최대 100명을 지원해야 한다
  rationale: 현재 직원 수 기준이며, 2년 내 700명까지 증가 예상
  impact: 데이터베이스 및 세션 관리 용량 산정의 기준
  flexibility: soft

- id: CON-003
  type: environmental
  title: 사내 프라이빗 클라우드 배포
  description: 사내 OpenStack 기반 프라이빗 클라우드에 배포해야 한다
  rationale: 사내 보안 정책에 따라 직원 개인정보를 외부 클라우드에 저장할 수 없음
  impact: 퍼블릭 클라우드 관리형 서비스(RDS, ElastiCache 등) 사용 불가
  flexibility: hard

- id: CON-004
  type: business
  title: 1차 릴리스 일정
  description: 1차 릴리스를 3개월 이내에 완료해야 한다
  rationale: 내년 1월부터 새 휴가 정책 적용 예정
  impact: Must 요구사항 우선 구현, Should/Could는 2차 릴리스로 분리 가능
  flexibility: negotiable

- id: CON-005
  type: regulatory
  title: 개인정보보호법 준수
  description: 직원 개인정보(특히 병가 사유 등 민감 정보) 처리 시 개인정보보호법을 준수해야 한다
  rationale: 법적 의무 사항
  impact: 개인정보 수집 동의, 접근 권한 분리, 보관 기간 설정, 파기 절차 필요
  flexibility: hard
```

---

## 품질 속성 우선순위 (quality_attribute_priorities)

```yaml
- attribute: usability
  priority: 1
  description: 직원들이 별도 교육 없이 직관적으로 사용할 수 있어야 한다
  metric: "신규 사용자가 5분 이내에 첫 휴가 신청을 완료할 수 있다"
  trade_off_notes: >
    보안 강화(매번 재인증 등)보다 사용 편의성을 우선한다.
    민감 정보는 기본 숨김 + 권한 확인 방식으로 보안과 사용성을 절충한다.

- attribute: availability
  priority: 2
  description: 업무 시간 동안 안정적으로 서비스를 제공해야 한다
  metric: "업무 시간(09:00-18:00) 99.5% 가용성, 장애 시 30분 내 복구"
  trade_off_notes: >
    24/7 고가용성은 요구하지 않으며, 야간 유지보수 윈도우를 허용한다.
    프라이빗 클라우드 환경의 제약 내에서 달성 가능한 수준이다.

- attribute: security
  priority: 3
  description: 직원 개인정보(병가 사유 등)가 적절히 보호되어야 한다
  metric: "민감 정보 접근은 권한 있는 사용자(팀장, HR)로 제한, 감사 로그 100% 기록"
  trade_off_notes: >
    usability를 위해 매 접근 시 재인증은 하지 않되,
    민감 정보 접근 시에는 권한 검증을 수행한다.

- attribute: maintainability
  priority: 4
  description: 매년 변경되는 휴가 정책을 쉽게 반영할 수 있어야 한다
  metric: "휴가 정책 변경 시 코드 수정 없이 설정 변경으로 반영 가능 (2차 릴리스 목표)"
  trade_off_notes: >
    1차 릴리스에서는 일정(CON-004)을 위해 하드코딩하고,
    2차 릴리스에서 설정 기반 정책 엔진으로 전환한다.
```
