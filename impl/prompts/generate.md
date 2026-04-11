# 코드 생성 프롬프트

## 입력

```
아키텍처 결정: {{architecture_decisions}}
컴포넌트 구조: {{component_structure}}
기술 스택: {{technology_stack}}
다이어그램: {{diagrams}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙을 따라 Arch 4섹션을 실제 코드로 변환하세요. 사용자에게 질문하지 말고 자동 실행하며, Arch 결정이 코드 레벨에서 실현 불가능한 경우에만 에스컬레이션합니다.

### Step 1: Arch 산출물 파싱 및 적응적 깊이 판별

`architecture_decisions`, `component_structure`, `technology_stack`, `diagrams`를 파싱하여 생성 대상 모듈·패턴·기술·흐름을 추출합니다. 시스템 프롬프트 **"적응적 깊이"** 기준으로 경량/중량 모드를 결정합니다.

### Step 2: 코드 레벨 맥락 파악

시스템 프롬프트 **"코드 레벨 맥락 자동 감지"** 절차에 따라 기존 코드베이스가 있으면 컨벤션·디렉토리·의존성·빌드 설정을 자동 분석하고, 새 프로젝트이면 `technology_stack.choice`의 관용구를 적용합니다.

### Step 3: 프로젝트 스캐폴딩

시스템 프롬프트 **"Arch 산출물 해석 규칙 → 컴포넌트 구조 → 모듈 스캐폴딩"** 표에 따라 디렉토리 구조, 빌드 설정 파일, 환경 설정 파일을 생성합니다.

### Step 4: 모듈별 코드 생성

각 `component_structure` 항목에 대해 시스템 프롬프트 **"Arch 산출물 해석 규칙"** 표를 적용하여 순서대로 생성합니다:

1. 인터페이스/타입 정의 (`COMP.interfaces` → API 계약)
2. DTO/모델
3. 구현체 (`AD.decision` 패턴 적용, 필요 시 `pattern` 에이전트 호출)
4. 의존성 주입/연결 (`COMP.dependencies` 방향 준수)

각 모듈 완료 시 `COMP.interfaces` 전체 구현, 의존성 방향, 관용적 에러 처리, 네이밍 일관성을 체크합니다.

### Step 5: 구현 맵 작성

각 컴포넌트와 코드 모듈의 매핑을 기록합니다:

```yaml
implementation_map:
  - id: IM-001
    component_ref: COMP-001
    module_path: src/auth/
    entry_point: src/auth/handler.go
    internal_structure:
      - src/auth/handler.go      # 진입점, 요청 핸들링
      - src/auth/service.go      # 비즈니스 로직
      - src/auth/repository.go   # 데이터 접근
      - src/auth/model.go        # 도메인 모델
    interfaces_implemented:
      - AuthService.Authenticate
      - AuthService.ValidateToken
    re_refs: [FR-001, NFR-003]
```

### Step 6: 구현 결정 기록 (IDR)

코드 레벨에서 내린 주요 결정을 기록합니다. `AD.trade_offs`는 IDR에 보존하고 `AD.re_refs`는 `re_refs`에 전파합니다.

```yaml
implementation_decisions:
  - id: IDR-001
    title: "Repository 패턴을 데이터 접근 계층에 적용"
    decision: "각 도메인 엔티티별 Repository 인터페이스를 정의하고 구현체를 분리"
    rationale: "AD-002 (Layered Architecture) 결정에 따라 데이터 접근을 추상화"
    alternatives_considered:
      - "직접 SQL 호출 — 단순하지만 계층 분리 위반"
      - "ORM Active Record — 도메인 모델과 DB 스키마 결합"
    pattern_applied: Repository
    arch_refs: [AD-002, COMP-003]
    re_refs: [NFR-001]
```

### Step 7: 구현 가이드 작성

```yaml
implementation_guide:
  prerequisites: ["<런타임/DB 버전 등>"]
  setup_steps: ["<클론>", "<의존성 설치>", "<환경 변수>", "<마이그레이션>"]
  build_commands: ["<빌드 명령>"]
  run_commands: ["<실행 명령>"]
  conventions: ["<네이밍>", "<에러 처리>", "<로깅>"]
  extension_points: ["<새 엔드포인트 추가 방법>", "<새 엔티티 추가 방법>"]
```

### Step 8: 산출물 출력

시스템 프롬프트 **"출력 형식"** 및 **"출력 프로토콜"**에 따라 4섹션(구현 맵, 코드 구조, 구현 결정, 구현 가이드)을 `meta.json`/`body.md`에 기록합니다. 에스컬레이션이 있으면 시스템 프롬프트 **"에스컬레이션 조건"** 형식에 따라 먼저 제시합니다.

## 주의사항

- ID 체계를 준수하세요: IM-xxx (구현 맵), IDR-xxx (구현 결정)
- 테스트 코드는 생성하지 마세요 (qa 스킬의 영역)
- 배포 설정은 생성하지 마세요 (deployment 스킬의 영역)
- 보안 설정의 상세 구현은 하지 마세요 (security 스킬의 영역). 단, OWASP 기본 수준은 준수하세요
