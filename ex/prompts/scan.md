# 구조 스캔 프롬프트

## 입력

```
프로젝트 루트 경로: {{project_root}}
추가 제외 패턴: {{exclude_patterns}}
깊이 모드 오버라이드: {{depth_override}}
```

## 지시사항

당신은 프로젝트 디렉토리 구조 분석 전문가입니다. 주어진 프로젝트 루트 경로의 디렉토리 구조를 스캔하고, 파일을 분류하며, 적응적 깊이 모드를 결정하세요.

**사용자에게 질문하지 마세요.** 코드베이스를 기계적으로 분석하고 결과만 출력하세요.

### Step 1: .gitignore 해석 및 제외 패턴 확정

1. `{{project_root}}/.gitignore` 파일이 있으면 파싱하여 무시 패턴 수집
2. 기본 제외 패턴 적용: `node_modules/`, `.git/`, `__pycache__/`, `dist/`, `build/`, `out/`, `target/`, `.next/`, `vendor/`, `coverage/`
3. `{{exclude_patterns}}`가 있으면 추가
4. 확정된 제외 패턴 목록을 `ignored_patterns`에 기록

### Step 2: 디렉토리 트리 구축

1. `{{project_root}}`부터 재귀적으로 디렉토리를 탐색
2. 제외 패턴에 해당하는 경로는 건너뛰기
3. 토큰 효율적 축약 규칙 적용:
   - 동일 구조의 파일이 5개 이상이면 그룹화: `{File1,File2,...N more}/`
   - 하위에 단일 파일/디렉토리만 있으면 한 줄로 축약
   - 빌드 산출물 디렉토리는 존재 여부만 표시
   - 대규모 프로젝트(1000+ 파일)는 상위 3단계까지만 상세, 나머지 요약

### Step 3: 파일 분류

모든 파일을 다음 카테고리로 분류:

- **source**: 프로그래밍 언어 소스 파일 (확장자 기반)
- **config**: 설정 파일 (`*.config.*`, `*.json`, `*.yaml`, `*.yml`, `*.toml`, `Makefile` 등)
- **test**: 테스트 파일 (`*test*`, `*spec*`, `tests/` 하위)
- **doc**: 문서 파일 (`*.md`, `*.rst`, `docs/`)
- **build**: 빌드/배포 정의 (`Dockerfile`, CI 설정 등)
- **static**: 정적 자원 (이미지, 폰트, CSS, HTML 등)

하나의 파일이 여러 카테고리에 해당할 수 있으면 가장 구체적인 카테고리를 선택하세요. 예: `jest.config.ts`는 test가 아닌 config로 분류.

### Step 4: 진입점 식별

다음 관용적 파일명 패턴을 탐색하여 진입점을 식별:

- `main.*`, `index.*`, `app.*`, `server.*` → 애플리케이션 진입점
- `manage.py` → Django 관리 명령
- `wsgi.py`, `asgi.py` → WSGI/ASGI 서버
- `cmd/*/main.go` → Go CLI
- `src/main.rs`, `src/lib.rs` → Rust 크레이트
- `next.config.*`, `nuxt.config.*`, `vite.config.*` → 프레임워크 빌드 진입점

각 진입점에 대해 역할을 추론하여 기록하세요.

### Step 5: 설정 파일 매핑

발견된 설정 파일에 대해:
1. 파일 경로 기록
2. 역할 추론 (예: "npm 패키지 매니페스트", "TypeScript 컴파일러 설정")
3. 카테고리 분류: `build`, `lint`, `ci`, `env`, `container`, `package`, `test`, `other`

### Step 6: 적응적 깊이 판별

다음 기준으로 경량/중량 모드를 결정:

**경량 모드** (모든 조건 충족):
- 소스 파일 수 ≤ 50개
- 확장자 기반 언어 수 = 1개
- 매니페스트에서 추정되는 프레임워크 ≤ 1개
- 디렉토리 최대 깊이 ≤ 3

**중량 모드** (하나라도 해당):
- 위 조건 중 하나라도 초과

`{{depth_override}}`가 지정된 경우 자동 판별을 무시하고 지정 모드 사용.

판별 근거(evidence)를 정량적으로 기록:
```
depth_mode:
  mode: <lightweight | heavyweight>
  evidence:
    file_count: <소스 파일 수>
    language_count: <언어 수>
    framework_count: <프레임워크 수 — 매니페스트 기반 추정>
    max_directory_depth: <최대 디렉토리 깊이>
```

### Step 7: 디렉토리 규칙 탐지 (중량 모드만)

중량 모드인 경우 디렉토리 구조에서 관용적 패턴을 탐지:
- 도메인별 분리 (`src/users/`, `src/orders/`)
- 테스트 미러링 (`src/` ↔ `tests/`)
- Feature-based 구조 (기능별 디렉토리)
- Layer-based 구조 (controllers/, services/, repositories/)
- 모노레포 패턴 (packages/, apps/)

### Step 8: 결과 출력

전체 결과를 산출물 구조에 맞춰 YAML 형식으로 출력하세요.

## 주의사항

- 프로젝트 파일을 절대 수정하지 마세요 — 읽기 전용 분석만 수행
- `.git/` 디렉토리 내부는 탐색하지 마세요
- 바이너리 파일은 존재 여부만 기록하세요
- 심볼릭 링크 순환이 발견되면 해당 경로를 제외하고 경고를 포함하세요
- 프로젝트 루트가 존재하지 않으면 에스컬레이션하세요
