# 요구사항 명세 입력 예시

> analyze 산출물 + 사용자 의사결정 결과
> 입력 형식은 skills.yaml의 spec.input 스키마를 따릅니다.

---

## 정제된 요구사항 (refined_requirements)

```yaml
- id: FR-001
  category: functional/authentication
  title: 사내 SSO 로그인
  description: 직원은 사내 SAML 2.0 기반 SSO를 통해 시스템에 로그인한다.
  priority: Must
  acceptance_criteria:
    - SSO 인증 성공 시 대시보드 페이지로 이동한다
    - 미인증 사용자는 SSO 로그인 페이지로 리다이렉트된다
  source: "사용자 응답 (Turn 2)"

- id: FR-002
  category: functional/leave-request
  title: 휴가 신청
  description: 직원은 휴가 유형을 선택하고 기간과 사유를 입력하여 휴가를 신청한다.
  priority: Must
  acceptance_criteria:
    - 연차/반차/병가/특별휴가 유형 중 선택 가능
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
    - 승인/반려 시 이메일 알림 발송
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
    - 미처리 신청 건 알림 (일 1회)
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

- id: FR-008
  category: functional/leave-request
  title: 휴가 신청 취소/수정
  description: 직원은 대기중 상태의 휴가 신청을 취소하거나 수정할 수 있다.
  priority: Must
  acceptance_criteria:
    - 대기중 상태에서만 취소/수정 가능
    - 승인 완료된 건의 취소는 팀장에게 취소 요청으로 전달
    - 수정 시 변경 이력 기록
  source: "분석 단계에서 누락 식별 → 사용자 확인 (Q-002)"

- id: FR-009
  category: functional/approval
  title: 대리 승인
  description: 팀장이 부재 시 지정된 대리인이 휴가를 승인할 수 있다.
  priority: "Won't"
  acceptance_criteria:
    - 팀장이 대리 승인자를 사전 지정 가능
    - 팀장 부재 시 대리인에게 승인 요청이 전달됨
  source: "분석 단계에서 누락 식별 → 사용자 결정: 2차 릴리스로 연기 (Q-003)"

- id: NFR-001
  category: non-functional/performance
  title: 응답 시간
  description: SPA 아키텍처를 채택하여 초기 로딩 후 빠른 네비게이션을 보장한다.
  priority: Should
  acceptance_criteria:
    - 초기 페이지 로드 3초 이내 (SPA 번들)
    - 이후 페이지 전환 500ms 이내
    - API 응답 P95 기준 1초 이내
  source: "사용자 응답 (Turn 8) + 분석 결정 (Q-001: SPA 채택)"

- id: NFR-002
  category: non-functional/availability
  title: 가용성
  description: 업무 시간 동안 시스템이 안정적으로 운영되어야 한다.
  priority: Should
  acceptance_criteria:
    - 업무시간(09:00-18:00) 99.5% 가용성
    - 야간(22:00-06:00) 유지보수 허용
  source: "사용자 응답 (Turn 8)"

- id: NFR-003
  category: non-functional/security
  title: 감사 로그
  description: 모든 주요 행위에 대한 감사 로그를 기록하여 추적 가능성을 보장한다.
  priority: Should
  acceptance_criteria:
    - 신청/승인/반려/수정/취소 행위에 대한 로그 기록
    - 로그에 행위자, 시각, 행위 유형, 대상 포함
  source: "분석 단계에서 누락 식별 (CON-005 대응)"
```

## 검증된 제약 조건 (validated_constraints)

```yaml
- id: CON-001
  type: technical
  title: 사내 SAML 2.0 SSO 연동
  description: 기존 사내 SAML 2.0 기반 SSO 시스템과 연동하여 인증을 처리해야 한다

- id: CON-002
  type: business
  title: 사용자 규모
  description: 전체 사용자 약 500명, 동시 접속 최대 100명

- id: CON-003
  type: environmental
  title: 사내 프라이빗 클라우드 배포
  description: 사내 OpenStack 기반 프라이빗 클라우드에 배포해야 한다

- id: CON-004
  type: business
  title: 1차 릴리스 일정
  description: 1차 릴리스를 3개월 이내에 완료해야 한다

- id: CON-005
  type: regulatory
  title: 개인정보보호법 준수
  description: 직원 개인정보(특히 병가 사유 등 민감 정보) 처리 시 개인정보보호법을 준수해야 한다
```

## 품질 속성 트레이드오프 (quality_tradeoffs)

```yaml
- attribute_a: usability
  attribute_b: security
  tradeoff_description: "민감 정보 접근 시 보안 강화와 사용 편의성 간 상충"
  user_decision: "옵션 A — 사용성 우선, 기본 숨김 + 권한 확인 방식으로 절충"

- attribute_a: maintainability
  attribute_b: delivery_speed
  tradeoff_description: "정책 엔진 별도 모듈 설계 vs 1차 하드코딩"
  user_decision: "옵션 B — 1차 하드코딩, 2차에서 설정화"
```

## 사용자 의사결정 결과 (user_decisions)

```yaml
- question_id: Q-001
  decision: "옵션 C — SPA로 구현, 성능 목표 유지"

- question_id: Q-002
  decision: "추가 — 1차 릴리스에 포함 (FR-008)"

- question_id: Q-003
  decision: "Won't — 2차 릴리스로 연기 (FR-009)"

- question_id: Q-004
  decision: "옵션 A — 사용성 우선, 기본 숨김 + 권한 확인"

- question_id: Q-005
  decision: "옵션 B — 1차 하드코딩, 2차 설정화"
```
