# 보안 감사 프롬프트

## 입력

```
구현 맵: {{implementation_map}}
코드 구조: {{code_structure}}
구현 결정: {{implementation_decisions}}
위협 모델: {{threat_model}}
신뢰 경계: {{trust_boundaries}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙을 따라 Impl 산출물과 threat-model 결과를 기반으로 코드 레벨 보안 취약점을 자동으로 정적 분석하고 의존성 취약점을 스캔하세요. 사용자에게 질문하지 말고 결과만 출력합니다.

### Step 1: 감사 범위 및 우선순위 결정

시스템 프롬프트 **"Impl 산출물 → 감사 범위 결정"** 표에 따라 `implementation_map`과 `code_structure`에서 감사 대상을 결정하세요. 이어서 시스템 프롬프트 **"threat-model 연동"** 기준으로 우선순위를 부여합니다:

1. `risk_level: critical` 위협의 `affected_components` → P1
2. `risk_level: high` 위협의 `affected_components` → P2
3. `trust_boundaries`를 넘는 데이터 흐름 / `mitigation_status: unmitigated` → P2
4. 나머지 → P3

### Step 2: OWASP Top 10 정적 분석

각 감사 대상에 대해 시스템 프롬프트 **"OWASP Top 10 (2021) 감사 체크리스트"** 를 A01부터 A10까지 순서대로 적용합니다. 고위험 컴포넌트(P1/P2)부터 분석합니다.

### Step 3: 의존성 취약점 스캔

`code_structure.external_dependencies`의 각 패키지에 대해:

1. 알려진 CVE 매핑
2. CVSS 점수 기반 심각도 분류
3. 패치 가용 여부 및 `fixed_version` 확인
4. 패치 불가 시 대안(대체 라이브러리, 워크어라운드) 제시

### Step 4: 시크릿/크리덴셜 탐지

`code_structure.environment_config`와 코드 파일에서 시스템 프롬프트 **"하드코딩 시크릿 탐지"** 절의 패턴을 적용하여 하드코딩된 시크릿을 탐지하세요.

### Step 5: 패턴별 보안 약점 점검

시스템 프롬프트 **"Impl 산출물 → 감사 범위 결정 → 구현 결정 → 패턴별 감사"** 표에 따라 `implementation_decisions.pattern_applied`별 보안 점검을 수행합니다.

### Step 6: CWE 분류 및 CVSS 점수 산정

각 발견 사항에 대해 시스템 프롬프트 **"CWE 분류 가이드"** 표로 CWE ID를 할당하고, **"CVSS v3.1 점수 산정"** 표의 메트릭과 심각도 범위에 따라 점수·벡터·심각도를 산정합니다.

### Step 7: 결과 구성 및 에스컬레이션 판단

시스템 프롬프트 **"산출물 구조"** 스키마에 따라 `vulnerability_report`를 구성하고, **"에스컬레이션 조건"** 에 해당하면 **"에스컬레이션 형식"** 으로 즉시 에스컬레이션합니다.

**에스컬레이션 없는 경우** 요약 출력:

```
✅ 보안 감사 완료

취약점 요약:
- Critical: {{count}}건
- High: {{count}}건
- Medium: {{count}}건
- Low: {{count}}건
- Informational: {{count}}건

의존성 취약점: {{count}}건 (패치 가용: {{patched}}, 패치 불가: {{unpatched}})
시크릿 노출: {{count}}건

[상세 취약점 보고서]
...
```

출력은 시스템 프롬프트 **"출력 프로토콜"** 에 따라 `meta.json`/`body.md`에 기록합니다.
