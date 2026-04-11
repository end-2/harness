# 컴플라이언스 검증 프롬프트

## 입력

```
위협 모델: {{threat_model}}
신뢰 경계: {{trust_boundaries}}
취약점 보고서: {{vulnerability_report}}
보안 리뷰: {{security_review}}
대응 전략 매트릭스: {{mitigation_matrix}}
기술 스택: {{technology_stack}}
컴포넌트 구조: {{component_structure}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙을 따라 세 에이전트(threat-model, audit, review)의 결과를 보안 표준 항목에 매핑하여 준수 상태를 자동으로 검증하고, 통합 보안 권고를 생성하세요. `hard` 규제 미준수 시에만 에스컬레이션합니다.

### Step 1: 적용 표준 및 레벨 결정

RE `constraint_ref`와 적응적 깊이를 확인하여 시스템 프롬프트 **"표준 선택 규칙"** 표에 따라 OWASP ASVS 레벨과 추가 표준(PCI DSS / GDPR / HIPAA)을 결정합니다.

```
적용 표준:
- OWASP ASVS Level {{level}} (v4.0)
- {{추가 표준이 있으면 나열}}
```

### Step 2: OWASP ASVS 항목별 매핑

시스템 프롬프트 **"표준별 매핑 가이드 → OWASP ASVS 매핑"** 표에 따라 각 ASVS 영역(V1~V14)에 세 에이전트의 산출물을 매핑하고, 각 항목에 대해 `compliant | non_compliant | partial | not_applicable` 을 판정합니다:

```yaml
findings:
  - requirement_id: "V2.1.1"
    title: <항목 제목>
    status: compliant | non_compliant | partial | not_applicable
    evidence: <준수 근거 또는 미준수 사유 — 구체적 코드 위치 포함>
    gap_description: <미준수 시 갭 설명>
    remediation: <개선 방안>
```

### Step 3: 추가 표준 검증 (해당 시)

시스템 프롬프트 **"PCI DSS 코드 레벨 요구사항"**, **"GDPR 코드 레벨 요구사항"**, **"HIPAA 코드 레벨 요구사항"** 절에 따라 해당 규제가 적용되는 경우 각 요구사항에 대해 매핑·판정을 수행합니다.

### Step 4: 갭 분석

미준수/부분 준수 항목을 심각도별로 그룹화하세요:

```yaml
gap_summary:
  - severity: critical
    count: <건수>
    items: [<requirement_id 목록>]
  - severity: high
    count: <건수>
    items: [<requirement_id 목록>]
```

### Step 5: 통합 보안 권고 생성

시스템 프롬프트 **"통합 보안 권고 생성 → 권고 소스 통합"** 표에 따라 네 가지 소스를 통합하고, **"우선순위 결정 매트릭스"** 로 우선순위를 결정합니다. 동일 근본 원인은 하나의 권고로 통합합니다.

산출물 스키마는 시스템 프롬프트 **"산출물 구조 → 2. 통합 보안 권고"** 를 따릅니다.

### Step 6: 개선 로드맵 작성

갭 분석과 보안 권고를 기반으로 실행 가능한 단위로 개선 로드맵을 작성합니다 (형식: 시스템 프롬프트 **"산출물 구조 → 1. 컴플라이언스 리포트 → remediation_roadmap"** 참조).

### Step 7: 최종 보안 리포트 제시

**에스컬레이션 판단**: `hard` 규제 제약의 `non_compliant` 여부를 확인하고, 해당 시 시스템 프롬프트 **"에스컬레이션 형식"** 으로 에스컬레이션합니다.

**에스컬레이션 없는 경우** — 시스템 프롬프트 **"최종 보안 리포트 제시 형식"** 에 따라 4섹션 리포트를 제시합니다.

출력은 시스템 프롬프트 **"출력 프로토콜"** 에 따라 `meta.json`/`body.md`에 기록합니다.
