# 요구사항 분석 입력 예시

> elicit 산출물(휴가 관리 시스템)을 그대로 입력으로 사용합니다.
> 입력 형식은 skills.yaml의 analyze.input 스키마를 따릅니다.

---

## 요구사항 후보 (requirements_candidates)

```yaml
- id: FR-001
  category: functional/authentication
  title: 사내 SSO 로그인
  description: 직원은 사내 SAML 2.0 기반 SSO를 통해 시스템에 로그인한다. 별도 회원가입 없이 사번과 SSO 인증으로 접근 가능하다.
  priority: Must
  acceptance_criteria:
    - SSO 인증 성공 시 대시보드 페이지로 이동한다
    - 미인증 사용자가 어떤 페이지에 접근해도 SSO 로그인 페이지로 리다이렉트된다
  source: "사용자 응답 (Turn 2)"

- id: FR-002
  category: functional/leave-request
  title: 휴가 신청
  description: 직원은 휴가 유형을 선택하고 기간과 사유를 입력하여 휴가를 신청한다.
  priority: Must
  acceptance_criteria:
    - 연차/반차/병가/특별휴가 유형 중 선택하여 신청 가능
    - 시작일, 종료일, 사유를 입력하여 신청
    - 신청 후 상태가 '대기중'으로 표시
  source: "사용자 응답 (Turn 1, 3)"

- id: FR-003
  category: functional/approval
  title: 휴가 승인/반려
  description: 팀장은 팀원의 휴가 신청을 검토하고 승인 또는 반려한다.
  priority: Must
  acceptance_criteria:
    - 팀장 승인/반려 가능
    - 반려 시 사유 입력 필수
    - 승인/반려 시 신청자에게 이메일 알림 발송
  source: "사용자 응답 (Turn 3)"

- id: FR-004
  category: functional/calendar
  title: 팀 휴가 캘린더
  description: 직원은 자신이 속한 팀의 휴가 일정을 캘린더 뷰로 확인할 수 있다.
  priority: Should
  acceptance_criteria:
    - 팀원 휴가 캘린더 뷰 표시
    - 월별/주별 전환 가능
  source: "사용자 응답 (Turn 4)"

- id: FR-005
  category: functional/balance
  title: 잔여 휴가 조회
  description: 직원은 자신의 유형별 휴가 잔여일수를 실시간으로 조회할 수 있다.
  priority: Must
  acceptance_criteria:
    - 유형별 총/사용/잔여일수 표시
    - 연초에 연차 자동 부여 (기본 15일, 근속 연수별 가산)
  source: "사용자 응답 (Turn 2, 5)"

- id: FR-006
  category: functional/notification
  title: 알림
  description: 주요 이벤트 발생 시 관련 사용자에게 이메일 알림을 발송한다.
  priority: Should
  acceptance_criteria:
    - 승인/반려 시 이메일 알림
    - 휴가 시작 전일 리마인더
    - 팀장에게 미처리 신청 건 알림 (일 1회)
  source: "사용자 응답 (Turn 6) + 에이전트 제안"

- id: FR-007
  category: functional/admin
  title: 관리자 기능
  description: HR 담당자가 전 직원 휴가 현황을 조회하고 정책을 관리한다.
  priority: Should
  acceptance_criteria:
    - HR 전 직원 현황 조회
    - 휴가 정책 설정
    - 연간 통계 리포트 생성
  source: "에이전트 제안 → 사용자 확인 (Turn 7)"

- id: NFR-001
  category: non-functional/performance
  title: 응답 시간
  description: 시스템의 주요 페이지 로드 시간이 사용자 경험을 저해하지 않는 수준을 유지한다.
  priority: Should
  acceptance_criteria:
    - 페이지 로드 2초 이내
    - 캘린더 렌더링 3초 이내
  source: "사용자 응답 (Turn 8)"

- id: NFR-002
  category: non-functional/availability
  title: 가용성
  description: 업무 시간 동안 시스템이 안정적으로 운영되어야 한다.
  priority: Should
  acceptance_criteria:
    - 업무시간(09:00-18:00) 99.5% 가용성
    - 야간 유지보수 허용
  source: "사용자 응답 (Turn 8)"
```

## 제약 조건 후보 (constraints_candidates)

```yaml
- id: CON-001
  type: technical
  title: 사내 SSO 연동
  description: SAML 2.0 기반 SSO 필수

- id: CON-002
  type: business
  title: 직원 수 규모
  description: 전체 사용자 약 500명, 동시 접속 최대 100명

- id: CON-003
  type: environmental
  title: 사내 클라우드
  description: OpenStack 프라이빗 클라우드 배포

- id: CON-004
  type: business
  title: 런칭 시기
  description: 3개월 내 런칭

- id: CON-005
  type: regulatory
  title: 개인정보
  description: 개인정보보호법 준수
```

## 품질 속성 힌트 (quality_attribute_hints)

```yaml
- attribute: usability
  hint: "별도 교육 없이 사용"

- attribute: availability
  hint: "업무 시간 필수 가용"

- attribute: security
  hint: "민감 정보 접근 제한"

- attribute: maintainability
  hint: "정책 변경 용이"
```

## 미해결 질문 (open_questions)

```yaml
- "모바일 접근 필요 여부"
- "기존 시스템 마이그레이션 필요 여부"
- "대리 승인 기능 필요 여부"
```
