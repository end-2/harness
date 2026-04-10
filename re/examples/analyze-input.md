# 요구사항 분석 입력 예시

> elicit 산출물(휴가 관리 시스템)을 그대로 입력으로 사용합니다.

## 요구사항 후보

| ID | 분류 | 제목 | 우선순위 | 수용 기준 | 출처 |
|----|------|------|----------|-----------|------|
| FR-001 | functional/auth | 사내 SSO 로그인 | Must | SSO 인증 성공 시 대시보드 이동, 미인증 시 리다이렉트 | 사용자 (Turn 2) |
| FR-002 | functional/leave-request | 휴가 신청 | Must | 연차/반차/병가/특별휴가 선택, 시작일-종료일-사유 입력, 상태 '대기중' | 사용자 (Turn 1, 3) |
| FR-003 | functional/approval | 휴가 승인/반려 | Must | 팀장 승인/반려, 반려 시 사유 필수, 알림 발송 | 사용자 (Turn 3) |
| FR-004 | functional/calendar | 팀 휴가 캘린더 | Should | 팀원 휴가 캘린더 뷰, 월별/주별 전환 | 사용자 (Turn 4) |
| FR-005 | functional/balance | 잔여 휴가 조회 | Must | 유형별 총/사용/잔여 표시, 연초 자동 부여 | 사용자 (Turn 2, 5) |
| FR-006 | functional/notification | 알림 | Should | 승인/반려 이메일, 전일 리마인더, 미처리 알림 | 사용자 (Turn 6) + 에이전트 |
| FR-007 | functional/admin | 관리자 기능 | Should | HR 전 직원 현황 조회, 정책 설정, 통계 리포트 | 에이전트 → 사용자 확인 (Turn 7) |
| NFR-001 | non-functional/performance | 응답 시간 | Should | 페이지 로드 2초, 캘린더 3초 | 사용자 (Turn 8) |
| NFR-002 | non-functional/availability | 가용성 | Should | 업무시간 99.5%, 야간 유지보수 허용 | 사용자 (Turn 8) |

## 제약 조건 후보

| ID | 유형 | 제목 | 설명 |
|----|------|------|------|
| CON-001 | technical | 사내 SSO 연동 | SAML 2.0 기반 SSO 필수 |
| CON-002 | business | 직원 수 | 500명, 동시 접속 100명 |
| CON-003 | environmental | 사내 클라우드 | OpenStack 프라이빗 클라우드 배포 |
| CON-004 | business | 런칭 시기 | 3개월 내 런칭 |
| CON-005 | regulatory | 개인정보 | 개인정보보호법 준수 |

## 품질 속성 힌트

| 속성 | 사용자 언급 |
|------|-----------|
| usability | 별도 교육 없이 사용 |
| availability | 업무 시간 필수 가용 |
| security | 민감 정보 접근 제한 |
| maintainability | 정책 변경 용이 |

## 미해결 질문

- 모바일 접근 필요 여부
- 기존 시스템 마이그레이션 필요 여부
- 대리 승인 기능 필요 여부
