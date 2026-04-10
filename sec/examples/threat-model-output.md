# 위협 모델링 출력 예시

> 휴가 관리 시스템의 Arch 산출물을 기반으로 위협 모델링을 수행한 결과입니다.
> 중량 모드 (컴포넌트 5개, 외부 인터페이스 3개)

## 신뢰 경계

```yaml
trust_boundaries:
  - id: TB-001
    name: "외부-내부 경계 (API Gateway)"
    description: "인터넷에서 유입되는 모든 요청이 통과하는 경계. 인증/인가의 1차 방어선"
    components_inside: [COMP-002, COMP-003, COMP-004, COMP-005]
    components_outside: ["Client (웹 브라우저)"]

  - id: TB-002
    name: "데이터 경계 (PostgreSQL)"
    description: "영구 저장 데이터에 대한 접근 제어 경계. 모든 데이터 접근은 인가된 모듈을 통해서만 가능"
    components_inside: [COMP-005]
    components_outside: [COMP-002, COMP-003, COMP-004]

  - id: TB-003
    name: "외부 서비스 경계 (SMTP)"
    description: "알림 모듈에서 외부 이메일 서비스로의 아웃바운드 통신 경계"
    components_inside: [COMP-004]
    components_outside: ["Email Service (SMTP)"]
```

## 데이터 흐름 보안 분류

```yaml
data_flow_security:
  - id: DFS-001
    source: "Client"
    destination: COMP-001
    data_classification: confidential
    protection_required: [encryption_in_transit, input_validation, rate_limiting]

  - id: DFS-002
    source: COMP-001
    destination: COMP-002
    data_classification: restricted
    protection_required: [access_control, integrity_check]

  - id: DFS-003
    source: COMP-002
    destination: COMP-005
    data_classification: restricted
    protection_required: [encryption_at_rest, access_control, parameterized_queries]

  - id: DFS-004
    source: COMP-003
    destination: COMP-005
    data_classification: confidential
    protection_required: [access_control, parameterized_queries]

  - id: DFS-005
    source: COMP-004
    destination: "Email Service"
    data_classification: internal
    protection_required: [encryption_in_transit, credential_protection]

  - id: DFS-006
    source: COMP-001
    destination: COMP-003
    data_classification: confidential
    protection_required: [access_control, integrity_check]
```

## 위협 모델

```yaml
threat_model:
  - id: TM-001
    title: "JWT 토큰 위조를 통한 사용자 신원 위장"
    stride_category: spoofing
    description: "공격자가 JWT 토큰을 위조하여 다른 사용자로 위장할 수 있음. 약한 서명 키, 알고리즘 혼동 공격(none/HS256), 만료되지 않은 토큰 재사용 가능"
    attack_vector: "인터넷 → API Gateway → Auth Module. 전제: JWT 서명 키 유출 또는 알고리즘 검증 미비"
    affected_components: [COMP-001, COMP-002]
    trust_boundary: TB-001
    dread_score:
      damage: 9
      reproducibility: 7
      exploitability: 6
      affected_users: 9
      discoverability: 5
    risk_level: high
    mitigation: "RS256 알고리즘 고정 (alg 헤더 무시), 키 길이 2048비트 이상, 만료 시간 15분, 리프레시 토큰 별도 관리, 키 로테이션 메커니즘 구현"
    mitigation_status: partial
    arch_refs: [AD-003, COMP-001, COMP-002]
    re_refs: [NFR-003, CON-001]

  - id: TM-002
    title: "수평 권한 상승을 통한 타 사용자 휴가 데이터 접근"
    stride_category: elevation_of_privilege
    description: "인증된 사용자가 다른 사용자의 휴가 신청을 조회/수정/삭제할 수 있음. 리소스 소유권 검증 미비 시 IDOR(Insecure Direct Object Reference) 취약점"
    attack_vector: "인증된 사용자 → API Gateway → Leave Module. leave ID를 변경하여 타인 데이터 접근"
    affected_components: [COMP-001, COMP-003]
    trust_boundary: TB-001
    dread_score:
      damage: 7
      reproducibility: 9
      exploitability: 8
      affected_users: 7
      discoverability: 7
    risk_level: high
    mitigation: "모든 리소스 접근 시 소유권 검증 (userId == leave.requesterId), 관리자 역할은 부서 범위 내에서만 접근 허용"
    mitigation_status: unmitigated
    arch_refs: [COMP-001, COMP-003, AD-002]
    re_refs: [FR-002, NFR-003]

  - id: TM-003
    title: "SQL 인젝션을 통한 데이터베이스 조작"
    stride_category: tampering
    description: "입력 검증 미비 시 SQL 쿼리에 악의적 SQL 구문이 주입되어 데이터 조회/수정/삭제가 가능. sqlc 사용으로 기본 방어되나 동적 쿼리 구성 시 위험"
    attack_vector: "인터넷 → API Gateway → Leave/Auth Module → PostgreSQL. 검색 조건, 정렬 파라미터 등 동적 쿼리 부분"
    affected_components: [COMP-003, COMP-002, COMP-005]
    trust_boundary: TB-002
    dread_score:
      damage: 9
      reproducibility: 6
      exploitability: 5
      affected_users: 9
      discoverability: 6
    risk_level: high
    mitigation: "sqlc의 파라미터화된 쿼리 일관 사용, 동적 쿼리 구성 금지, 입력 화이트리스트 검증 (정렬 필드명 등)"
    mitigation_status: partial
    arch_refs: [AD-004, COMP-005, COMP-003]
    re_refs: [NFR-003]

  - id: TM-004
    title: "비밀번호/자격 증명 유출"
    stride_category: information_disclosure
    description: "사용자 비밀번호가 평문으로 저장되거나, 에러 메시지에 데이터베이스 구조가 노출되거나, 로그에 민감 정보가 기록될 수 있음"
    attack_vector: "데이터베이스 접근 → 비밀번호 평문 확인, 또는 에러 응답에서 스택 트레이스/DB 스키마 추출"
    affected_components: [COMP-002, COMP-005]
    trust_boundary: TB-002
    dread_score:
      damage: 8
      reproducibility: 5
      exploitability: 4
      affected_users: 9
      discoverability: 4
    risk_level: medium
    mitigation: "bcrypt(cost≥12)로 비밀번호 해싱, 프로덕션 에러 응답에서 상세 정보 제거, 로그에 PII 마스킹"
    mitigation_status: unmitigated
    arch_refs: [COMP-002, COMP-005, AD-003]
    re_refs: [NFR-003]

  - id: TM-005
    title: "인증/인가 이벤트 부인"
    stride_category: repudiation
    description: "사용자가 자신의 행위(휴가 승인/반려, 계정 설정 변경 등)를 부인할 수 있음. 감사 로그 부재 시 책임 추적 불가"
    attack_vector: "내부자 위협 — 관리자가 휴가 승인 후 부인, 또는 사용자가 자신의 행위를 부인"
    affected_components: [COMP-001, COMP-002, COMP-003]
    trust_boundary: TB-001
    dread_score:
      damage: 5
      reproducibility: 8
      exploitability: 3
      affected_users: 5
      discoverability: 3
    risk_level: medium
    mitigation: "모든 인증 시도(성공/실패), 휴가 승인/반려, 권한 변경에 대한 감사 로그 기록. 타임스탬프, 사용자 ID, IP 주소, 행위 내용 포함"
    mitigation_status: unmitigated
    arch_refs: [COMP-001, COMP-002, COMP-003]
    re_refs: [NFR-003]

  - id: TM-006
    title: "API 엔드포인트 대상 서비스 거부 공격"
    stride_category: denial_of_service
    description: "대량의 요청으로 API Gateway 또는 데이터베이스 리소스를 고갈시켜 서비스 가용성을 방해"
    attack_vector: "인터넷 → API Gateway. 인증 없는 엔드포인트(로그인, 회원가입)에 대한 대량 요청"
    affected_components: [COMP-001, COMP-005]
    trust_boundary: TB-001
    dread_score:
      damage: 6
      reproducibility: 9
      exploitability: 8
      affected_users: 9
      discoverability: 8
    risk_level: high
    mitigation: "IP 기반 레이트 리미팅 (인증 엔드포인트: 10req/min, 일반: 100req/min), 커넥션 풀 제한, 요청 크기 제한 (1MB), 타임아웃 설정"
    mitigation_status: unmitigated
    arch_refs: [COMP-001, AD-005]
    re_refs: [NFR-001]

  - id: TM-007
    title: "SMTP 자격 증명 탈취를 통한 이메일 서비스 악용"
    stride_category: spoofing
    description: "Notification Module의 SMTP 자격 증명이 노출되면, 공격자가 시스템 이름으로 피싱 이메일을 발송할 수 있음"
    attack_vector: "SMTP 자격 증명 노출 (환경 변수, 설정 파일) → 외부에서 SMTP 서비스 접속 → 피싱 이메일 발송"
    affected_components: [COMP-004]
    trust_boundary: TB-003
    dread_score:
      damage: 6
      reproducibility: 5
      exploitability: 4
      affected_users: 7
      discoverability: 4
    risk_level: medium
    mitigation: "SMTP 자격 증명 시크릿 매니저 저장, 환경 변수로 주입 (하드코딩 금지), 발송 IP 화이트리스트"
    mitigation_status: unmitigated
    arch_refs: [COMP-004]
    re_refs: [FR-004]
```

## 공격 트리

```yaml
attack_trees:
  - threat_ref: TM-001
    format: mermaid
    code: |
      graph TD
        A["목표: JWT 토큰 위조로 인증 우회"] --> B["서명 키 획득"]
        A --> C["알고리즘 혼동 공격"]
        A --> D["만료 토큰 재사용"]
        B --> E["소스 코드에서 하드코딩된 키 발견"]
        B --> F["환경 변수 유출 (로그, 에러 메시지)"]
        C --> G["alg: none 설정으로 서명 우회"]
        C --> H["HS256으로 변경 후 공개 키로 서명"]
        D --> I["만료 검증 로직 부재"]
        D --> J["만료 시간 과도하게 김 (>24h)"]

  - threat_ref: TM-002
    format: mermaid
    code: |
      graph TD
        A["목표: 타 사용자 휴가 데이터 접근"] --> B["IDOR 공격"]
        A --> C["수직 권한 상승"]
        B --> D["leave ID 순차 열거"]
        B --> E["응답에서 타인 ID 유추"]
        C --> F["일반 사용자로 관리자 API 호출"]
        C --> G["역할 파라미터 조작"]

  - threat_ref: TM-006
    format: mermaid
    code: |
      graph TD
        A["목표: 서비스 가용성 방해"] --> B["API 레벨 DoS"]
        A --> C["데이터베이스 레벨 DoS"]
        B --> D["로그인 엔드포인트 대량 요청"]
        B --> E["대용량 페이로드 전송"]
        C --> F["복잡한 쿼리 유도 (정렬+필터+페이징)"]
        C --> G["커넥션 풀 고갈"]
```
