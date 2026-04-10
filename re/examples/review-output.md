# 요구사항 리뷰 출력 예시

> 휴가 관리 시스템 명세 문서 리뷰 결과
> 출력 형식은 skills.yaml의 review.output 스키마를 따릅니다.

---

## 리뷰 리포트 (review_report)

### 요구사항 명세 리뷰 (requirements_review)

```yaml
- id: FR-002
  issue: "acceptance_criteria에 '시작일은 오늘 이후여야 한다'고 되어 있으나, 당일 신청 허용 여부가 모호"
  severity: Minor
  suggestion: "'시작일은 신청일 기준 다음 영업일 이후' 또는 '당일 신청 허용' 중 명확화"

- id: FR-005
  issue: "연차 자동 부여의 기준일(입사일 기준 vs 1월 1일 기준)이 acceptance_criteria와 description 간 불일치 가능성. 입사 첫해 비례 부여(proration) 규칙 누락"
  severity: Major
  suggestion: "입사 첫해 비례 부여 규칙을 acceptance_criteria에 추가 (월할 계산 또는 전액 부여)"

- id: FR-007
  issue: "'휴가 정책 설정'의 범위가 불명확 — 어떤 정책 항목을 설정할 수 있는지 구체화 필요"
  severity: Major
  suggestion: "acceptance_criteria에 설정 가능 항목 목록 추가 (유형별 기본 일수, 근속 가산 규칙, 반차 차감 비율 등)"

- id: FR-008
  issue: "'승인 완료 후 취소 요청' 시나리오에서 이미 지난 날짜의 승인건 취소 가능 여부가 불명확"
  severity: Minor
  suggestion: "경계 조건 추가: '이미 시작된 휴가는 취소 불가, 미래 날짜의 승인건만 취소 요청 가능'"

- id: NFR-001
  issue: "'초기 페이지 로드 3초'와 'API 응답 P95 1초'의 측정 조건이 불명확 (네트워크 환경, 측정 도구)"
  severity: Minor
  suggestion: "측정 조건 명시: '사내 네트워크 환경에서, Lighthouse 기준 LCP 3초 이내'"

- id: NFR-003
  issue: "'3년 보관'은 개인정보보호법의 어떤 조항에 근거하는지 불명확"
  severity: Info
  suggestion: "법적 근거 추가 또는 '사내 정보보호 정책에 따름'으로 출처 명시"
```

### 제약 조건 리뷰 (constraints_review)

```yaml
- id: CON-002
  issue: "'2년 내 700명 증가 예상'이 rationale에 있으나 이에 대한 확장 전략이 요구사항에 미반영"
  severity: Minor
  suggestion: "NFR로 확장성 요구사항 추가하거나, 의도적으로 2차 릴리스 범위로 명시"

- id: CON-003
  issue: "OpenStack 버전 및 사용 가능한 서비스(블록 스토리지, 로드밸런서 등)가 미명시"
  severity: Major
  suggestion: "arch:design이 인프라를 설계하려면 OpenStack 환경의 구체적 사양이 필요"

- id: null
  issue: "(누락) 데이터베이스 관련 제약이 없음 — 기존 DB 인프라 사용 필수인지, 새로 프로비저닝 가능한지 불명확"
  severity: Info
  suggestion: "기존 DB 인프라 사용 가능 여부를 확인하여 제약 조건으로 기록 권고"
```

### 품질 속성 리뷰 (quality_attributes_review)

```yaml
- attribute: usability
  issue: "metric '5분 이내 첫 신청'은 측정하기 어려움 (사용자 테스트 필요)"
  severity: Minor
  suggestion: "'주요 태스크(신청, 조회, 승인)가 3클릭 이내'와 같은 휴리스틱 기준 병행"

- attribute: maintainability
  issue: "'코드 수정 없이 설정 변경'이 2차 릴리스 목표이므로 1차에서는 metric 미달"
  severity: Info
  suggestion: "현 상태가 의도적임을 명시. 1차 릴리스 기준 metric 별도 추가 권고"
```

### 후속 스킬 소비 적합성 (downstream_readiness)

```yaml
- skill: "arch:design"
  verdict: CONDITIONAL
  missing_info: "CON-003의 OpenStack 환경 사양 보완 필요. 나머지는 설계 착수에 충분"

- skill: "qa:strategy"
  verdict: PASS
  missing_info: ""

- skill: "impl:generate"
  verdict: PASS
  missing_info: ""

- skill: "sec:threat-model"
  verdict: PASS
  missing_info: ""

- skill: "devops:slo"
  verdict: CONDITIONAL
  missing_info: "가용성/성능 metric 존재하나, 모니터링 방법 및 알림 기준은 미정의 (devops 영역에서 결정 가능)"
```

### 사용자 확인 필요 사항 (escalations)

```yaml
- id: ESC-001
  description: "FR-005: 입사 첫해 연차 비례 부여(proration) 규칙을 어떻게 정의할지?"
  options:
    - "A: 입사월 기준 월할 계산 (예: 7월 입사 → 15 x 6/12 = 7.5일)"
    - "B: 입사일과 무관하게 15일 전액 부여"
    - "C: 사내 HR 정책에 따름 (확인 필요)"

- id: ESC-002
  description: "CON-003: OpenStack 환경의 구체적 사양을 확인할 수 있는가? arch:design에서 인프라를 설계하려면 사용 가능한 서비스 목록이 필요합니다"
  options:
    - "A: 인프라팀에 확인 후 CON-003 보완"
    - "B: 일반적인 OpenStack 환경 가정하에 진행"

- id: ESC-003
  description: "FR-007: HR이 설정할 수 있는 휴가 정책 항목의 범위를 결정해주세요"
  options:
    - "A: 최소 범위 — 유형별 기본 일수, 근속 가산 규칙"
    - "B: 확장 범위 — 반차 차감 비율, 특별휴가 종류, 자동 승인 규칙 추가"
```

---

## 최종 판정 (verdict)

```yaml
verdict: CONDITIONAL
```

Major 이슈 2건(FR-005 proration 규칙, CON-003 OpenStack 사양)의 보완이 필요하지만, 나머지 요구사항은 후속 스킬이 소비하기에 충분한 품질입니다.

**권고 조치**:
1. ESC-001, ESC-002, ESC-003에 대한 사용자 의사결정
2. Major 이슈 반영 후 해당 항목만 재리뷰
3. Minor/Info 이슈는 후속 단계에서 점진적으로 보완 가능

> CONDITIONAL 판정이므로 파이프라인의 on_conditional 규칙에 따라 Minor 이슈 목록을 후속 스킬에 전달하며 진행합니다.
