# CI/CD 파이프라인 프롬프트

## 입력

```
Impl 산출물: {{impl_output}}
IaC 산출물: {{iac_output}}
```

## 지시사항

당신은 CI/CD 파이프라인 설계 전문가입니다. Impl 코드 구조와 IaC 인프라를 분석하여 완전한 CI/CD 파이프라인을 자동 생성하세요.

### Step 1: Impl 산출물 분석

다음 필드를 추출하세요:

- `code_structure.build_config` → 빌드 도구, 명령어
- `code_structure.external_dependencies` → 의존성 관리자, 락 파일 경로
- `implementation_guide.build_commands` → 빌드 명령어 시퀀스
- `implementation_guide.prerequisites` → 런타임, SDK 버전
- `implementation_guide.run_commands` → 실행 명령어
- `implementation_map.module_path` → 빌드 대상 경로
- `code_structure.environment_config` → 환경 변수, 시크릿

### Step 2: CI/CD 플랫폼 결정

기술 스택 맥락에 따라 플랫폼을 선택하세요:

- GitHub 호스팅 → GitHub Actions (기본값)
- Jenkins 인프라 존재 → Jenkins
- GitLab 호스팅 → GitLab CI

### Step 3: 스테이지 구성

다음 순서로 스테이지를 구성하세요:

1. **Setup**: 런타임 설치, 의존성 캐시 복원
2. **Build**: 소스 빌드, 패키징
3. **Test**: 단위 테스트, 통합 테스트 (`qa` 스킬 연동 지점)
4. **Security Scan**: SAST, 의존성 취약점 스캔 (`security` 스킬 연동 지점)
5. **Package**: Docker 이미지 빌드 & 레지스트리 푸시 (해당 시)
6. **Deploy (dev)**: dev 환경 배포 + 스모크 테스트
7. **Deploy (staging)**: staging 환경 배포 + 통합 테스트
8. **Deploy (prod)**: prod 환경 배포 (승격 규칙 적용)

### Step 4: 트리거 설정

- `push` to main/develop → 전체 파이프라인
- `pull_request` → Build + Test + Security Scan
- `tag` (v*) → 전체 파이프라인 + Release
- 모노레포: 변경 경로 필터 적용

### Step 5: 캐싱 전략

Impl `code_structure.external_dependencies`에서:

- 의존성 캐시: 락 파일 해시 기반 키
- 빌드 캐시: 소스 해시 기반 키
- Docker 레이어 캐시: buildx cache-to/cache-from

### Step 6: 시크릿 관리

Impl `code_structure.environment_config`에서 시크릿을 식별하고:

- CI 플랫폼 시크릿 스토어에 등록할 시크릿 목록 생성
- 환경별 시크릿 분리
- 시크릿 참조 방식 설정

### Step 7: IaC 배포 통합

IaC 산출물의 apply 명령을 배포 스테이지에 포함:

- `terraform plan` → 리뷰 (staging/prod)
- `terraform apply -auto-approve` → 실행
- 환경별 변수 파일 지정

### Step 8: 산출물 정리

다음 형식으로 산출물을 정리하세요:

**파이프라인 설정**: ID, 플랫폼, 트리거, 스테이지 목록, Impl 참조, Arch 참조
**스테이지 상세**: 스테이지명, 명령어, 의존성, 조건, 타임아웃
**캐싱 설정**: 캐시 유형, 키, 경로
**시크릿 목록**: 이름, 용도, 주입 방법, 환경
**생성된 설정 파일**: 파일 경로, 설명

## 주의사항

- Impl 산출물의 빌드 명령어를 정확히 반영하세요. 임의로 명령어를 변경하지 마세요
- `qa` 스킬과 `security` 스킬의 연동 지점을 명시하세요 (주석 또는 placeholder)
- 시크릿을 파이프라인 설정에 하드코딩하지 마세요
- 플랫폼 제약(타임아웃, 아티팩트 크기 등)과 충돌하면 에스컬레이션하세요
