# CI/CD 파이프라인 프롬프트

## 입력

```
Impl 산출물: {{impl_output}}
IaC 산출물: {{iac_output}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙을 따라 Impl 코드 구조와 IaC 인프라를 분석하여 완전한 CI/CD 파이프라인을 자동 생성하세요.

### Step 1: Impl 산출물 분석

시스템 프롬프트 **"Impl 산출물 → 파이프라인 변환"** 표의 매핑에 따라 `code_structure.build_config`, `external_dependencies`, `implementation_guide.build_commands`/`prerequisites`/`run_commands`, `implementation_map.module_path`, `environment_config`를 추출합니다.

### Step 2: CI/CD 플랫폼 결정

시스템 프롬프트 **"플랫폼별 설정 파일 생성"** 표를 참조하여 플랫폼을 선택합니다:

- GitHub 호스팅 → GitHub Actions (기본값)
- Jenkins 인프라 존재 → Jenkins
- GitLab 호스팅 → GitLab CI

### Step 3: 스테이지 구성

시스템 프롬프트 **"파이프라인 스테이지 구성"** 절(Build → Test → Security Scan → Deploy → Verify)에 따라 스테이지를 구성합니다. 환경은 dev → staging → prod 순서로 승격합니다.

### Step 4: 트리거 설정

- `push` to main/develop → 전체 파이프라인
- `pull_request` → Build + Test + Security Scan
- `tag` (v*) → 전체 + Release
- 모노레포는 시스템 프롬프트 **"모노레포 지원"** 절에 따라 변경 경로 필터 적용

### Step 5: 캐싱 전략

시스템 프롬프트 **"캐싱 전략"** 표(의존성 / 빌드 아티팩트 / Docker 레이어)에 따라 캐시 키와 경로를 설정합니다.

### Step 6: 시크릿 관리

시스템 프롬프트 **"시크릿 관리"** 절에 따라 Impl `environment_config`에서 시크릿을 식별하고, CI 플랫폼 시크릿 스토어에 등록할 목록과 환경별 분리 방식을 생성합니다.

### Step 7: IaC 배포 통합

IaC 산출물의 apply 명령을 배포 스테이지에 포함합니다:

- `terraform plan` → 리뷰 (staging/prod)
- `terraform apply -auto-approve` → 실행
- 환경별 변수 파일 지정

### Step 8: 산출물 정리

시스템 프롬프트 **"출력 형식"** 표(파이프라인 설정 / 스테이지 상세 / 캐싱 설정 / 시크릿 목록 / 생성된 설정 파일)에 맞춰 정리하고, **"출력 프로토콜"**에 따라 `meta.json`/`body.md`에 기록합니다. 플랫폼 제약 충돌 시 시스템 프롬프트 **"에스컬레이션 조건"**을 따릅니다.
