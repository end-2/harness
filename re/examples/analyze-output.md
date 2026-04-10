# 요구사항 분석 출력 예시

> 휴가 관리 시스템 요구사항 분석 결과
> 출력 형식은 skills.yaml의 analyze.output 스키마를 따릅니다.

---

## 분석 리포트 (analysis_report)

### 충돌 사항 (conflicts)

```yaml
- requirement_a: NFR-001
  requirement_b: CON-003
  conflict_type: resource
  description: "프라이빗 클라우드(OpenStack)의 CDN 부재로 정적 자원 로딩이 느려 페이지 로드 2초 목표 달성이 어려울 수 있음"
  resolution_options:
    - "사내 CDN/캐시 서버 구축 [권고]"
    - "성능 목표를 3초로 완화"
    - "SPA로 구현하여 초기 로딩 후 빠른 네비게이션 보장"
```

### 누락 사항 (gaps)

```yaml
- area: "기능 — 휴가 신청 취소/수정"
  description: "FR-002에 취소/수정 시나리오가 누락됨. 대기중 상태에서 취소/수정이 가능해야 하고, 승인 후 취소 프로세스도 필요함"
  severity: Major
  recommendation: "별도 FR로 추가 (FR-008)"

- area: "기능 — 대리 승인"
  description: "팀장 부재 시 승인 프로세스가 중단됨. 대리 승인 기능 필요 여부 확인 필요"
  severity: Major
  recommendation: "별도 FR로 추가하거나 의도적 제외 확인 (FR-009)"

- area: "비기능 — 감사 로그"
  description: "개인정보보호법 준수(CON-005)를 위해 주요 행위에 대한 감사 로그 기록이 필요함"
  severity: Minor
  recommendation: "NFR로 추가 (NFR-003)"

- area: "비기능 — 백업/복구"
  description: "사내 클라우드 환경에서의 데이터 보호 전략이 미정의"
  severity: Minor
  recommendation: "별도 NFR로 추가하거나 devops 스킬에서 다루도록 위임"
```

### 위험 요소 (risks)

```yaml
- requirement_id: CON-004
  risk_type: "일정"
  description: "Must 요구사항 5개 + Should 4개를 3개월 내 구현해야 함. Should 항목 일부를 2차 릴리스로 분리 필요"
  mitigation: "MoSCoW 기반 2단계 릴리스 계획 수립"

- requirement_id: CON-005
  risk_type: "규제"
  description: "병가 사유의 개인정보 처리 기준이 불명확. 수집 동의, 보관 기간, 접근 권한 정의 필요"
  mitigation: "개인정보 처리 방침 수립 후 관련 FR/NFR 추가"
```

## 정제된 요구사항 목록 (refined_requirements)

```yaml
# 기존 요구사항 (FR-001 ~ FR-007, NFR-001, NFR-002)은 elicit 산출물과 동일하므로 생략.
# 아래는 분석을 통해 추가/수정 제안된 항목만 표시합니다.

- id: FR-008
  category: functional/leave-request
  title: 휴가 신청 취소/수정
  description: "직원은 대기중 상태의 휴가 신청을 취소하거나 수정할 수 있다. 승인 완료된 건의 취소는 팀장에게 취소 요청으로 전달된다."
  priority: Must
  acceptance_criteria:
    - "상태가 '대기중'인 신청 건만 취소/수정 가능"
    - "승인 완료된 신청 건의 취소는 팀장에게 취소 요청으로 전달"
    - "수정 시 변경 이력이 기록됨"
  source: "분석 단계에서 누락 식별 → 사용자 확인 (Q-002)"

- id: FR-009
  category: functional/approval
  title: 대리 승인
  description: "팀장이 부재 시 지정된 대리인이 휴가를 승인할 수 있다."
  priority: Should
  acceptance_criteria:
    - "팀장이 대리 승인자를 사전 지정 가능"
    - "팀장 부재 시 대리인에게 승인 요청이 전달됨"
  source: "분석 단계에서 누락 식별 → 사용자 확인 (Q-003)"

- id: NFR-003
  category: non-functional/security
  title: 감사 로그
  description: "모든 신청/승인/반려/수정/취소에 대한 감사 로그를 기록한다."
  priority: Should
  acceptance_criteria:
    - "주요 행위에 대한 로그가 기록됨"
    - "로그에는 행위자, 시각, 행위 유형, 대상이 포함됨"
  source: "분석 단계에서 누락 식별 (CON-005 개인정보보호법 대응)"
```

## 검증된 제약 조건 목록 (validated_constraints)

```yaml
- id: CON-001
  type: technical
  title: 사내 SAML 2.0 SSO 연동
  description: 기존 사내 SAML 2.0 기반 SSO 시스템과 연동하여 인증을 처리해야 한다

- id: CON-002
  type: business
  title: 사용자 규모
  description: 전체 사용자 약 500명, 동시 접속 최대 100명을 지원해야 한다

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
  tradeoff_description: |
    민감 정보(병가 사유) 접근 시 보안 강화(매번 재인증)와 사용 편의성 간 상충.
    옵션 A [권고]: 사용성 우선 — 기본 숨김 + 권한 확인 방식으로 절충.
    옵션 B: 보안 우선 — 민감 정보 접근 시 매번 재인증(2FA).
  user_decision: ""

- attribute_a: maintainability
  attribute_b: delivery_speed
  tradeoff_description: |
    정책 엔진을 별도 모듈로 설계하면 향후 유지보수는 용이하나 초기 개발 기간 증가.
    옵션 A: 유지보수성 투자 — 정책 엔진 별도 모듈 설계 (+2주).
    옵션 B [권고]: 빠른 구현 — 1차 릴리스 하드코딩, 2차에서 설정화.
  user_decision: ""
```

## 사용자 의사결정 필요 질문 (decision_questions)

```yaml
- id: Q-001
  description: "NFR-001 vs CON-003: 성능 목표를 유지할지, 완화할지?"
  options:
    - "A: 사내 CDN/캐시 서버 구축 [권고]"
    - "B: 성능 목표를 3초로 완화"
    - "C: SPA로 구현하여 초기 로딩 후 빠른 네비게이션"

- id: Q-002
  description: "휴가 신청 취소/수정 기능을 추가할지? (FR-008)"
  options:
    - "A: 1차 릴리스에 포함 [권고]"
    - "B: 2차 릴리스로 연기"

- id: Q-003
  description: "대리 승인 기능이 필요한지? 필요하다면 1차 릴리스에 포함할지? (FR-009)"
  options:
    - "A: 1차 릴리스에 포함"
    - "B: 2차 릴리스로 연기 (Won't)"
    - "C: 불필요 — 의도적 제외"

- id: Q-004
  description: "usability vs security 트레이드오프"
  options:
    - "A: 사용성 우선 — 기본 숨김 + 권한 확인 [권고]"
    - "B: 보안 우선 — 매번 재인증(2FA)"

- id: Q-005
  description: "maintainability vs 일정(CON-004) 트레이드오프"
  options:
    - "A: 유지보수성 투자 (+2주)"
    - "B: 1차 하드코딩, 2차 설정화 [권고]"
```
