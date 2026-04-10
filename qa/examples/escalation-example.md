# 에스컬레이션 & FAIL 시나리오 예시

> Must 요구사항의 해소 불가능한 커버리지 갭 발견 시 에스컬레이션 + 품질 게이트 FAIL 시나리오

---

## 시나리오 1: Must NFR 에스컬레이션

> 분산 시스템에서 "P99 응답시간 < 50ms" 성능 테스트 인프라 부재

### review 에이전트의 갭 분류

```yaml
gap_classification:
  auto_remediate: []
  risk_accepted:
    - { re_id: FR-010, priority: Should, reason: "실시간 대시보드 UI 테스트 미생성" }
  escalate:
    - re_id: NFR-001
      priority: Must
      reason: "P99 응답시간 < 50ms 검증에 분산 부하 테스트 인프라 필요 (k6 cluster 또는 Gatling distributed)"
      impact: "핵심 성능 SLA 미검증 — 프로덕션 배포 후 SLA 위반 리스크"
      alternatives:
        - "A) k6 단일 인스턴스로 간이 성능 테스트 (P99 정확도 낮음, 즉시 실행 가능)"
        - "B) 분산 부하 테스트 인프라(k6-operator on K8s) 구축 후 테스트 (1-2주 소요)"
        - "C) 잔여 리스크로 수용하고 운영 APM 모니터링으로 대체"
```

### 사용자에게 제시되는 에스컬레이션 메시지

```
## Must 요구사항 커버리지 갭 보고

### 갭 사유
NFR-001 (P99 응답시간 < 50ms) 검증을 위한 분산 부하 테스트 인프라가 프로젝트에 구성되어 있지 않습니다.
단일 인스턴스 부하 테스트로는 P99 레이턴시를 정확히 측정할 수 없으며, 분산 환경에서의 네트워크 지연과
서비스 간 통신 오버헤드를 반영하지 못합니다.

### 영향 범위
- 검증 불가: NFR-001 "P99 응답시간 < 50ms" (Must)
- 관련 요구사항: FR-001(실시간 데이터 조회), FR-005(대시보드 렌더링)
- 리스크: 프로덕션 배포 후 SLA 위반 가능성

### 대안
1. **간이 성능 테스트** — k6 단일 인스턴스로 로컬 환경 벤치마크
   - 장점: 즉시 실행 가능, 대략적 성능 기준선 확인
   - 단점: P99 정확도 낮음, 분산 환경 미반영
   - 품질 게이트: Must 기준을 "간이 측정 < 50ms"로 완화

2. **인프라 구축 후 테스트** — k6-operator on K8s 분산 부하 테스트
   - 장점: 정확한 P99 측정, 프로덕션 유사 환경
   - 단점: 1-2주 구축 소요, 인프라 비용 발생
   - 품질 게이트: 구축 완료 후 Must 기준 그대로 적용

3. **리스크 수용** — 성능 테스트 생략, 운영 모니터링으로 대체
   - 장점: 추가 비용/일정 없음
   - 단점: SLA 위반 시 사후 대응, 잔여 리스크 높음
   - 품질 게이트: NFR-001을 Must에서 Should로 재분류 필요 (RE 변경)

→ 어떤 방향으로 진행할지 결정해 주세요.
```

### 사용자 응답 후 파이프라인 재개

```
사용자: "대안 1로 진행합니다. 간이 성능 테스트로 기준선을 확인하고, 2차 릴리스에서 인프라 구축하겠습니다."

→ 파이프라인 재개:
  - generate: k6 단일 인스턴스 성능 테스트 스크립트 생성
  - review: 간이 측정 기준으로 RTM 업데이트
  - report: "간이 측정 결과" + "잔여 리스크: 분산 환경 미검증" 포함
```

---

## 시나리오 2: 품질 게이트 FAIL

> Must 요구사항 커버리지 미달로 인한 FAIL 판정

### report 에이전트 출력

```yaml
quality_report:
  quality_gate:
    verdict: fail
    criteria:
      - name: "코드 커버리지 (라인)"
        target: 80
        actual: 75.3
        status: fail
        note: "payment/ 모듈 52%, order/ 모듈 61%가 전체 평균을 하락시킴"

      - name: "코드 커버리지 (분기)"
        target: 70
        actual: 58.2
        status: fail
        note: "복잡한 결제 상태 분기가 대부분 미커버"

      - name: "Must 요구사항 커버리지"
        target: 100
        actual: 80
        status: fail
        note: "FR-005(결제 취소) uncovered — 외부 PG사 연동 테스트 인프라 미구성"

      - name: "Should 요구사항 커버리지"
        target: 80
        actual: 60
        status: fail

      - name: "테스트 통과율"
        target: 100
        actual: 95.6
        status: fail
        note: "2건 실패 — TS-003-C07(타임아웃), TS-005-C02(PG 응답 파싱 에러)"

    verdict_rationale: >
      Must 기준 3개 항목(코드 커버리지 라인, Must 요구사항 커버리지, 테스트 통과율) 미달.
      배포 불가 판정. 아래 즉시 조치 사항 해결 후 재테스트 필요.

  risk_items:
    - id: RISK-001
      severity: critical
      description: "FR-005(결제 취소) 완전 미검증 — 프로덕션에서 결제 취소 실패 시 금전적 손실"
      mitigation: "PG 샌드박스 환경 연동 후 테스트 추가 (즉시 조치)"

    - id: RISK-002
      severity: critical
      description: "TS-003-C07 타임아웃 실패 — 결제 처리 타임아웃 로직 버그 의심"
      mitigation: "타임아웃 로직 디버깅 및 수정 (즉시 조치)"

    - id: RISK-003
      severity: high
      description: "payment/ 모듈 커버리지 52% — 결제 로직 대부분 미검증"
      mitigation: "결제 상태 분기별 단위 테스트 추가 (단기 개선)"

  recommendations:
    - priority: immediate
      items:
        - description: "TS-003-C07, TS-005-C02 실패 원인 분석 및 수정"
          effort: "0.5일"

        - description: "FR-005(결제 취소) 테스트 추가 — PG 샌드박스 Mock 적용"
          effort: "1일"

        - description: "payment/ 모듈 핵심 분기 테스트 추가 (커버리지 52% → 80%+)"
          effort: "1-2일"

    - priority: short_term
      items:
        - description: "order/ 모듈 커버리지 개선 (61% → 80%+)"
          effort: "1일"

        - description: "Should 요구사항 테스트 보강"
          effort: "2일"
```

### 사용자에게 제시되는 FAIL 리포트

```
## 품질 게이트: FAIL ❌

배포 불가 판정입니다. 다음 기준이 미달입니다:

| 기준 | 목표 | 실측 | 판정 |
|------|------|------|------|
| 코드 커버리지 (라인) | ≥ 80% | 75.3% | FAIL |
| 코드 커버리지 (분기) | ≥ 70% | 58.2% | FAIL |
| Must 요구사항 커버리지 | 100% | 80% | FAIL |
| Should 요구사항 커버리지 | ≥ 80% | 60% | FAIL |
| 테스트 통과율 | 100% | 95.6% | FAIL |

### 즉시 조치 사항 (배포 전 필수)

1. **테스트 실패 수정** — TS-003-C07(타임아웃), TS-005-C02(PG 파싱) [0.5일]
2. **FR-005 결제 취소 테스트 추가** — PG 샌드박스 Mock 적용 [1일]
3. **payment/ 모듈 커버리지 보강** — 결제 상태 분기 테스트 [1-2일]

### Critical 리스크 (2건)

1. FR-005(결제 취소) 완전 미검증 — 금전적 손실 위험
2. 결제 타임아웃 로직 버그 의심 — 테스트 실패 원인 분석 필요

즉시 조치 완료 후 QA 파이프라인을 재실행하여 재판정하세요.
```
