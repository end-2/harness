# CI/CD 파이프라인 출력 예시

> 온라인 주문 처리 시스템의 GitHub Actions 파이프라인

## 파이프라인 설정

| ID | 플랫폼 | 트리거 | 스테이지 수 | Impl 참조 | Arch 참조 |
|----|--------|--------|-----------|----------|----------|
| PL-001 | GitHub Actions | push(main), PR, tag(v*) | 8 | IM-001~003 | COMP-001~005 |

## 스테이지 상세

| 순서 | 스테이지 | 명령어 | 조건 | 타임아웃 |
|------|---------|--------|------|---------|
| 1 | Setup | `actions/setup-node@v4` (Node.js 20) | 항상 | 2m |
| 2 | Install | `npm ci` | 항상 | 5m |
| 3 | Build | `npm run build` | 항상 | 5m |
| 4 | Test | `npm run test` | 항상 | 10m |
| 5 | Security Scan | `trivy fs .` + `npm audit` | 항상 | 5m |
| 6 | Package | Docker build + ECR push (변경된 서비스만) | main/tag only | 10m |
| 7 | Deploy (dev) | `terraform apply` + ECS deploy | main only | 15m |
| 8 | Deploy (staging) | `terraform apply` + ECS deploy + 통합 테스트 | main only, dev 성공 후 | 20m |
| 9 | Deploy (prod) | `terraform apply` + ECS deploy | tag only, 수동 승인 | 20m |

## 트리거 설정

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  push:
    tags: ['v*']
```

### 모노레포 변경 감지

| 서비스 | 경로 필터 | 영향 |
|--------|----------|------|
| api-gateway | `services/api-gateway/**` | api-gateway만 빌드/배포 |
| order-service | `services/order-service/**` | order-service만 빌드/배포 |
| user-service | `services/user-service/**` | user-service만 빌드/배포 |
| shared | `packages/shared/**` | 전체 서비스 빌드/배포 |
| infra | `infrastructure/**` | Terraform plan/apply |

## 캐싱 설정

| 캐시 유형 | 키 | 경로 | 예상 효과 |
|----------|---|------|----------|
| npm 의존성 | `npm-${{ hashFiles('package-lock.json') }}` | `~/.npm` | 설치 시간 70% 감소 |
| Docker 레이어 | `docker-${{ github.sha }}` | `/tmp/.buildx-cache` | 빌드 시간 50% 감소 |
| Terraform 플러그인 | `tf-${{ hashFiles('.terraform.lock.hcl') }}` | `~/.terraform.d/plugin-cache` | init 시간 80% 감소 |

## 시크릿 목록

| 이름 | 용도 | 주입 방법 | 환경 |
|------|------|----------|------|
| `DATABASE_URL` | PostgreSQL 연결 문자열 | GitHub Secrets → ECS Task Env | dev/staging/prod |
| `RABBITMQ_URL` | RabbitMQ 연결 문자열 | GitHub Secrets → ECS Task Env | dev/staging/prod |
| `REDIS_URL` | Redis 연결 문자열 | GitHub Secrets → ECS Task Env | dev/staging/prod |
| `JWT_SECRET` | JWT 서명 키 | GitHub Secrets → ECS Task Env | dev/staging/prod |
| `AWS_ACCESS_KEY_ID` | AWS 인증 | GitHub Secrets → OIDC Role (권장) | CI |
| `AWS_SECRET_ACCESS_KEY` | AWS 인증 | GitHub Secrets → OIDC Role (권장) | CI |
| `ECR_REGISTRY` | ECR 레지스트리 URL | GitHub Secrets | CI |

## 생성된 설정 파일

| 파일 경로 | 설명 |
|----------|------|
| `.github/workflows/ci.yml` | PR 트리거 — Build + Test + Security Scan |
| `.github/workflows/deploy-dev.yml` | main push — 전체 파이프라인 (dev 배포) |
| `.github/workflows/deploy-staging.yml` | main push, dev 성공 후 — staging 배포 |
| `.github/workflows/deploy-prod.yml` | tag push — prod 배포 (수동 승인) |
| `Dockerfile` (각 서비스) | 멀티스테이지 Docker 빌드 |
| `docker-compose.yml` | 로컬 개발 환경 |

## 후속 스킬 연동 지점

| 연동 지점 | 스킬 | 위치 | 설명 |
|----------|------|------|------|
| 품질 게이트 | qa | Test 스테이지 | 테스트 커버리지 임계값, E2E 테스트 |
| 보안 스캔 | security | Security Scan 스테이지 | SAST, DAST, 컨테이너 이미지 스캔 |
| 배포 전략 | devops:strategy | Deploy 스테이지 | 카나리/블루-그린 배포 방식 적용 |
