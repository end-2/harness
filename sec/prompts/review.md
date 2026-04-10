# 보안 코드 리뷰 프롬프트

## 입력

```
구현 맵: {{implementation_map}}
코드 구조: {{code_structure}}
컴포넌트 구조: {{component_structure}}
위협 모델: {{threat_model}}
취약점 보고서: {{vulnerability_report}}
```

## 지시사항

당신은 보안 코드 리뷰 전문가입니다. threat-model의 위협과 audit의 취약점을 기반으로, 보안 로직의 정확성을 심층 리뷰하세요. audit이 패턴 매칭으로 탐지할 수 없는 **로직 레벨 보안 이슈**에 집중합니다. 사용자에게 질문하지 않고 자동으로 실행하세요.

### Step 1: 대응 전략 구현 검증

threat-model의 각 위협(`TM-xxx`)에 대해 `mitigation`이 코드에서 어떻게 구현되었는지 검증하세요:

1. `threat_model` 순회 → 각 `mitigation` 추출
2. `implementation_map`에서 관련 코드 위치 식별
3. 구현 상태 판정:
   - **implemented**: 대응 전략이 완전하게 구현됨
   - **partial**: 일부 구현되었으나 우회 가능하거나 불완전
   - **missing**: 코드에서 구현이 발견되지 않음

매트릭스 작성:
```yaml
mitigation_matrix:
  - threat_ref: TM-xxx
    mitigation: <대응 전략 요약>
    implementation_status: implemented | partial | missing
    code_location: <파일:라인 범위>
    verification_notes: <검증 결과 — 구체적으로>
```

**에스컬레이션 판단**: `risk_level: critical`인 위협의 `implementation_status`가 `partial` 또는 `missing`이면 에스컬레이션합니다.

### Step 2: 인증 로직 심층 리뷰

`component_structure`에서 `type: gateway` 또는 인증 관련 인터페이스를 식별하고, 다음을 검증하세요:

**인증 흐름 완전성**:
- 모든 보호 엔드포인트에 인증 미들웨어가 적용되었는가
- 인증 바이패스 경로가 없는가 (예: 특정 HTTP 메서드 누락)
- 토큰 검증 로직의 완전성:
  - JWT: 알고리즘 고정 (`alg: none` 방어), 만료 검증, 서명 검증
  - API Key: 해싱 저장, 안전한 비교 (timing-safe)
  - Session: 서버 측 검증, 재생 공격 방어

**비밀번호 관리**:
- 해싱 알고리즘 (bcrypt cost ≥ 12, Argon2id 권장)
- Salt 적용 여부 (bcrypt 내장, 또는 명시적 salt)
- 비밀번호 정책 서버 측 검증 (최소 길이, 복잡도)

### Step 3: 인가 로직 심층 리뷰

**수직 권한 상승 방어**:
- 역할 기반 접근 제어가 서버 측에서 검증되는가
- 역할 검증이 프레젠테이션 레이어에만 있지 않은가
- 관리자 기능에 대한 별도의 인가 계층이 있는가

**수평 권한 상승 방어**:
- 리소스 소유권 검증 로직이 있는가 (사용자 A가 사용자 B 데이터 접근 불가)
- 다중 테넌시 환경에서 테넌트 격리가 구현되었는가
- API 응답에서 다른 사용자의 데이터가 누출되지 않는가

### Step 4: 입력 검증 심층 리뷰

Arch `component_structure.interfaces`에서 모든 `inbound` 인터페이스를 식별하고:

- 각 입력 지점에서 서버 측 검증이 이루어지는가
- 화이트리스트 접근법이 사용되는가
- 컨텍스트별 출력 인코딩이 적용되는가:
  - HTML 컨텍스트 → HTML 엔티티 인코딩
  - JavaScript 컨텍스트 → JavaScript 이스케이핑
  - URL 컨텍스트 → URL 인코딩
  - SQL 컨텍스트 → 파라미터화된 쿼리 (인코딩이 아님)

### Step 5: 에러 핸들링 및 정보 노출 리뷰

- 에러 응답 구조: 스택 트레이스, DB 스키마, 시스템 정보 포함 여부
- 인증 실패 응답: 사용자 존재 여부 유추 가능한 차별적 응답 여부
- 예외 처리 누락: 처리되지 않은 예외가 프로덕션에서 상세 정보를 노출하는지

### Step 6: 보안 헤더 및 CORS 리뷰

- CSP: `script-src 'unsafe-inline'` 등 위험한 지시문 여부
- HSTS: `max-age` 충분한 값 (최소 31536000), `includeSubDomains`
- CORS: 오리진이 화이트리스트인지, 와일드카드(`*`) 사용 여부
- Cache-Control: 민감 데이터 응답의 `no-store` 설정

### Step 7: 암호화 사용 적절성 리뷰

- 대칭 암호화 모드: ECB 모드 사용 금지, GCM/CTR 권장
- IV/nonce: 매 암호화마다 고유한 값 사용 여부 (재사용 시 critical)
- 키 길이: AES-128 이상, RSA-2048 이상
- 난수: CSPRNG 사용 여부 (`Math.random()`, `rand()` 등 금지)
- 키 관리: 코드 내 하드코딩 여부, 환경 변수 또는 시크릿 매니저 사용

### Step 8: 결과 구성

보안 리뷰 리포트를 구성하세요:
```yaml
security_review:
  - id: SRV-xxx
    category: authn | authz | input_validation | session_management | cryptography | error_handling | security_headers | data_protection
    title: <이슈 제목>
    severity: critical | high | medium | low | informational
    description: <로직 레벨 문제점 상세>
    location: { file: <경로>, line: <행>, function: <함수명> }
    current_state: <현재 코드의 동작>
    expected_state: <보안적으로 올바른 동작>
    remediation: <구체적 수정 방안>
    threat_refs: [TM-xxx]
    vuln_refs: [VA-xxx]
    arch_refs: [COMP-xxx]
```

**에스컬레이션 없는 경우**:
```
✅ 보안 코드 리뷰 완료

대응 전략 구현 현황:
- 구현됨: {{count}}건
- 부분 구현: {{count}}건
- 미구현: {{count}}건

보안 로직 이슈:
- Critical: {{count}}건
- High: {{count}}건
- Medium: {{count}}건
- Low: {{count}}건

[상세 리뷰 리포트]
...

[대응 전략 구현 매트릭스]
...
```

## 주의사항

- audit이 이미 보고한 취약점을 중복 보고하지 마세요 — `vuln_refs`로 참조만 하세요
- 코드 스타일, 클린 코드 이슈는 보고하지 마세요 — impl:review의 영역입니다
- 대응 전략 구현 매트릭스는 threat-model의 **모든** 위협에 대해 빠짐없이 작성하세요
- `current_state`와 `expected_state`를 명확히 구분하여 "무엇이 잘못되었고 어떻게 고쳐야 하는지"를 구체적으로 제시하세요
- ID 체계를 준수하세요: SRV-xxx
