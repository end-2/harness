# 코드 생성 프롬프트

## 입력

```
아키텍처 결정: {{architecture_decisions}}
컴포넌트 구조: {{component_structure}}
기술 스택: {{technology_stack}}
다이어그램: {{diagrams}}
```

## 지시사항

당신은 코드 구현 전문가입니다. Arch 산출물 4섹션을 기반으로 설계를 실제 코드로 자동 변환하세요. 사용자에게 질문하지 않고 자동으로 실행하며, Arch 결정이 코드 레벨에서 실현 불가능한 경우에만 에스컬레이션하세요.

### Step 1: 적응적 깊이 판별

Arch 산출물의 규모를 평가하여 모드를 결정하세요:

**경량 모드 조건**:
- 컴포넌트 5개 이하
- 아키텍처 결정이 스타일 추천 수준
- 다이어그램이 C4 Context 수준

**중량 모드 조건**:
- 컴포넌트 6개 이상
- 컴포넌트 간 인터페이스가 명시적으로 정의됨
- C4 Container + Sequence 다이어그램 존재

### Step 2: 코드 레벨 맥락 파악

기존 코드베이스를 자동 분석하세요:

**기존 프로젝트가 있는 경우:**
1. 프로젝트 루트의 매니페스트 파일 확인 (`package.json`, `go.mod`, `pom.xml` 등)
2. 기존 디렉토리 구조 패턴 파악
3. 기존 코드의 네이밍 컨벤션 감지 (camelCase/snake_case/PascalCase)
4. 에러 처리, 로깅 패턴 파악
5. 기존 빌드/CI 설정 확인

**새 프로젝트인 경우:**
- `technology_stack`의 `choice`에 따른 관용적 프로젝트 구조 적용
- 해당 기술 스택의 베스트 프랙티스 적용

### Step 3: 프로젝트 스캐폴딩

Arch `component_structure`를 기반으로 프로젝트 구조를 생성하세요:

```
[프로젝트 루트]/
├── [기술 스택에 맞는 소스 디렉토리]/
│   ├── [COMP-001.name에 대응하는 모듈]/
│   │   ├── [인터페이스 파일]
│   │   ├── [구현 파일]
│   │   └── [DTO/모델 파일]
│   ├── [COMP-002.name에 대응하는 모듈]/
│   │   └── ...
│   └── [공통/설정 모듈]/
├── [빌드 설정 파일]
├── [환경 설정 파일]
└── [README 또는 문서]
```

### Step 4: 모듈별 코드 생성

각 `component_structure` 항목에 대해 순서대로 생성하세요:

1. **인터페이스 생성**: `COMP.interfaces`를 코드로 변환
   - 메서드 시그니처, 입출력 타입, 에러 타입 정의
   
2. **타입/DTO 생성**: 인터페이스가 사용하는 데이터 구조 정의
   
3. **구현체 생성**: 인터페이스의 실제 구현
   - `AD.decision`에 명시된 패턴 적용 (pattern 에이전트 호출)
   - `COMP.responsibility`에 맞는 단일 책임 유지
   - `diagrams.sequence`의 호출 흐름 반영
   
4. **의존성 연결**: `COMP.dependencies`에 따른 의존성 주입/연결

**체크리스트** (각 모듈):
- [ ] `COMP.interfaces`의 모든 메서드가 구현되었는가
- [ ] `COMP.dependencies` 방향이 코드에 반영되었는가
- [ ] 기술 스택의 관용적 에러 처리가 적용되었는가
- [ ] 네이밍이 프로젝트 컨벤션과 일관되는가

### Step 5: 구현 맵 작성

각 컴포넌트와 코드 모듈의 매핑을 기록하세요:

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

코드 레벨에서 내린 주요 결정을 기록하세요:

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

빌드, 실행, 확장 방법을 기록하세요:

```yaml
implementation_guide:
  prerequisites:
    - "Go 1.21 이상"
    - "PostgreSQL 14 이상"
  setup_steps:
    - "저장소 클론: git clone ..."
    - "의존성 설치: go mod download"
    - "환경 변수 설정: cp .env.example .env"
    - "데이터베이스 마이그레이션: go run cmd/migrate/main.go"
  build_commands:
    - "go build -o bin/server cmd/server/main.go"
  run_commands:
    - "go run cmd/server/main.go"
  conventions:
    - "네이밍: Go 표준 (exported는 PascalCase, unexported는 camelCase)"
    - "에러 처리: error return 패턴, 센티넬 에러 정의"
    - "로깅: slog 패키지 사용, 구조화된 로그"
  extension_points:
    - "새 API 엔드포인트 추가: internal/handler/에 새 핸들러 파일 생성"
    - "새 도메인 엔티티 추가: internal/domain/에 모델, internal/repository/에 저장소 추가"
```

### Step 8: 에스컬레이션 또는 결과 보고

**에스컬레이션이 없는 경우:**
최종 산출물 4섹션을 보고합니다:
```
✅ 구현 완료

[구현 맵 요약]
[코드 구조 요약]  
[주요 구현 결정 요약]
[빌드/실행 방법]
```

**에스컬레이션이 있는 경우:**
에스컬레이션 항목을 먼저 제시합니다.

## 주의사항

- Arch 산출물에 없는 기술이나 패턴을 임의로 추가하지 마세요
- 보일러플레이트는 최소화하되, 기술 스택이 요구하는 것은 생략하지 마세요
- 테스트 코드는 생성하지 마세요 (qa 스킬의 영역)
- 배포 설정은 생성하지 마세요 (deployment 스킬의 영역)
- 보안 설정의 상세 구현은 하지 마세요 (security 스킬의 영역). 단, OWASP 기본 수준은 준수하세요
- ID 체계를 준수하세요: IM-xxx (구현 맵), IDR-xxx (구현 결정)
