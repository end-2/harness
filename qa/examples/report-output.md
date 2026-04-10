# 품질 리포트 출력 예시

> 휴가 관리 시스템 — 최종 품질 리포트

---

## 요약 (Executive Summary)

**품질 게이트 판정: CONDITIONAL PASS** ⚠️

| 지표 | 실측 | 목표 | 판정 |
|------|------|------|------|
| 코드 커버리지 (라인) | 85.2% | 80% | ✅ |
| Must 요구사항 커버리지 | 100% (5/5) | 100% | ✅ |
| Should 요구사항 커버리지 | 33% (1/3) | 80% | ⚠️ |
| 테스트 통과율 | 100% (44/44) | 100% | ✅ |

Must 기준은 모두 충족하였으나, Should 요구사항 커버리지(33%)가 목표(80%)에 미달하여 **CONDITIONAL PASS** 판정합니다. 잔여 리스크 3건은 후속 조치가 권장됩니다.

---

## 1. 코드 커버리지

```yaml
code_coverage:
  overall:
    line: 85.2
    line_target: 80
    line_status: pass
    branch: 72.1
    branch_target: 70
    branch_status: pass
  by_module:
    - module: "auth/"
      line: 92
      branch: 88
      status: pass
      note: ""
    - module: "service/"
      line: 87
      branch: 75
      status: pass
      note: ""
    - module: "approval/"
      line: 84
      branch: 71
      status: pass
      note: ""
    - module: "repository/"
      line: 90
      branch: 82
      status: pass
      note: ""
    - module: "notification/"
      line: 78
      branch: 60
      status: warning
      note: "라인 목표(80%) 미달 — 알림 재시도 로직 등 일부 분기 미커버"
    - module: "calendar/"
      line: 68
      branch: 55
      status: warning
      note: "라인 목표(80%) 미달 — Should 요구사항(FR-004) 관련, 리스크 수용"
```

### 커버리지 분석

- 전체 라인 커버리지 85.2%로 목표(80%) 충족
- `notification/` 모듈(78%)과 `calendar/` 모듈(68%)이 목표 미달
  - `notification/`: 알림 재시도, 실패 처리 분기 미커버 — 단기 개선 권장
  - `calendar/`: Should 요구사항 관련 — 리스크 수용

---

## 2. 요구사항 커버리지

```yaml
requirements_coverage:
  must:
    total: 5
    covered: 5
    partial: 0
    uncovered: 0
    ratio: 100
    status: pass
    details:
      - { re_id: FR-001, title: "사내 SSO 로그인", status: covered }
      - { re_id: FR-002, title: "휴가 신청", status: covered }
      - { re_id: FR-003, title: "휴가 승인/반려", status: covered }
      - { re_id: FR-005, title: "잔여 휴가 조회", status: covered }
      - { re_id: FR-008, title: "휴가 신청 취소/수정", status: covered }
  should:
    total: 3
    covered: 1
    partial: 1
    uncovered: 1
    ratio: 33
    status: fail
    details:
      - { re_id: FR-004, title: "팀 휴가 캘린더", status: partial, gap: "AC-4 렌더링 성능 미검증" }
      - { re_id: NFR-001, title: "응답 시간", status: uncovered, gap: "성능 테스트 미실시" }
      - { re_id: NFR-003, title: "감사 로그", status: uncovered, gap: "로그 기록 완전성 미검증" }
  could:
    total: 0
    ratio: "N/A"
```

---

## 3. NFR 측정 결과

```yaml
nfr_results:
  - re_id: NFR-001
    attribute: performance
    metric: "API 응답 시간 P95 기준 1초 이내"
    measured: "N/A"
    verdict: not_tested
    note: "성능 테스트 도구 환경 미구성. 스테이징 배포 후 측정 권장"

  - re_id: NFR-001
    attribute: performance
    metric: "캘린더 뷰 렌더링 3초 이내"
    measured: "N/A"
    verdict: not_tested
    note: "프론트엔드 렌더링 성능 측정 미실시"

  - re_id: NFR-003
    attribute: security
    metric: "감사 로그 100% 기록"
    measured: "N/A"
    verdict: not_tested
    note: "감사 로그 통합 테스트 미생성. 리스크 수용"

  - re_id: "quality_attribute:usability"
    attribute: usability
    metric: "신규 사용자가 5분 이내에 첫 휴가 신청 완료"
    measured: "N/A"
    verdict: not_tested
    note: "사용성 테스트는 자동화 범위 외. 수동 사용성 테스트 권장"

  - re_id: "quality_attribute:availability"
    attribute: availability
    metric: "업무 시간 99.5% 가용성, 장애 시 30분 내 복구"
    measured: "N/A"
    verdict: not_tested
    note: "가용성은 운영 환경에서만 측정 가능. operation 스킬에서 SLO 모니터링으로 대체"
```

---

## 4. 품질 게이트 상세

```yaml
quality_gate:
  verdict: conditional_pass
  criteria:
    - name: "코드 커버리지 (라인)"
      target: 80
      actual: 85.2
      status: pass

    - name: "코드 커버리지 (분기)"
      target: 70
      actual: 72.1
      status: pass

    - name: "Must 요구사항 커버리지"
      target: 100
      actual: 100
      status: pass

    - name: "Should 요구사항 커버리지"
      target: 80
      actual: 33
      status: fail
      note: "FR-004 partial, NFR-001 uncovered, NFR-003 uncovered"

    - name: "테스트 통과율"
      target: 100
      actual: 100
      status: pass

    - name: "NFR 준수"
      target: "RE metric 기준"
      actual: "0/3 measured"
      status: not_tested
      note: "성능/가용성/감사 테스트 미실시 — 잔여 리스크로 분류"

  verdict_rationale: >
    Must 기준(코드 커버리지, Must 요구사항 커버리지, 테스트 통과율) 모두 충족.
    Should 요구사항 커버리지 33%로 목표 80% 미달.
    NFR 테스트 미실시 항목이 있으나 Must 요구사항은 아님.
    CONDITIONAL PASS 판정 — 배포 가능하나 잔여 리스크 관리 필요.
```

---

## 5. 잔여 리스크

```yaml
risk_items:
  - id: RISK-001
    severity: medium
    re_ref: NFR-001
    description: "API 응답 시간 성능 테스트 미실시"
    impact: "프로덕션에서 P95 > 1s 응답시간 발생 가능성"
    mitigation: "스테이징 배포 후 JMeter/Gatling으로 성능 테스트 실시"
    owner: "deployment 스킬에서 성능 테스트 게이트 추가 권장"

  - id: RISK-002
    severity: medium
    re_ref: NFR-003
    description: "감사 로그 기록 완전성 미검증"
    impact: "일부 행위에 대한 감사 로그 누락 가능성 — CON-005 개인정보보호법 리스크"
    mitigation: "통합 테스트에 감사 로그 검증 케이스 추가 (단기 개선)"
    owner: "security 스킬에서 컴플라이언스 테스트 보완 권장"

  - id: RISK-003
    severity: low
    re_ref: FR-004
    description: "캘린더 렌더링 성능(3초 이내) 미검증"
    impact: "대량 휴가 데이터 시 캘린더 느린 로딩 가능"
    mitigation: "Lighthouse CI 도입 또는 수동 성능 확인"
    owner: "개발팀"

  - id: RISK-004
    severity: low
    re_ref: null
    description: "notification 모듈 코드 커버리지 78% (목표 80% 미달)"
    impact: "알림 재시도/실패 처리 로직 미검증"
    mitigation: "알림 재시도 로직에 대한 단위 테스트 추가"
    owner: "개발팀"
```

---

## 6. 개선 권고

```yaml
recommendations:
  - priority: immediate
    description: "없음 — Must 기준 모두 충족"

  - priority: short_term
    items:
      - description: "NFR-003 감사 로그 통합 테스트 추가"
        rationale: "CON-005 개인정보보호법 관련 컴플라이언스 리스크"
        effort: "1-2일"
        re_ref: NFR-003

      - description: "notification 모듈 커버리지 개선 (78% → 80%+)"
        rationale: "알림 재시도/실패 처리 분기 커버"
        effort: "0.5일"
        re_ref: null

  - priority: mid_term
    items:
      - description: "성능 테스트 환경 구성 (JMeter/Gatling)"
        rationale: "NFR-001 응답시간 기준 검증"
        effort: "3-5일"
        re_ref: NFR-001

      - description: "프론트엔드 성능 측정 자동화 (Lighthouse CI)"
        rationale: "캘린더 렌더링 성능 지속 모니터링"
        effort: "1-2일"
        re_ref: FR-004

      - description: "사용성 테스트 계획 수립"
        rationale: "usability(우선순위 1) 품질 속성의 정량적 검증"
        effort: "별도 계획"
        re_ref: null
```

---

## 7. 추적 참조

```yaml
re_refs: [FR-001, FR-002, FR-003, FR-004, FR-005, FR-008, NFR-001, NFR-003]
arch_refs: [AD-001, AD-002, COMP-001, COMP-002, COMP-003, COMP-004, COMP-005]
impl_refs: [IM-001, IM-002, IM-003, IM-004, IM-005]
qa_refs: [TSTR-001, TS-001, TS-002, TS-003, TS-004, TS-005, TS-008, TS-010, TS-011, TS-020]
```

---

## 후속 스킬 전달 사항

| 후속 스킬 | 전달 항목 | 내용 |
|----------|----------|------|
| **deployment** | quality_gate | CONDITIONAL PASS — 배포 가능, 성능 게이트 추가 권장 |
| **operation** | nfr_results | 가용성/성능 미측정 → SLO 모니터링으로 대체 필요 |
| **management** | risk_items | 잔여 리스크 4건 — 스프린트 백로그에 등록 |
| **security** | RISK-002 | 감사 로그 완전성 미검증 → 컴플라이언스 테스트 보완 필요 |
