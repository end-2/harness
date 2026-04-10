# CI/CD 파이프라인 입력 예시

> 온라인 주문 처리 시스템의 Impl 산출물 + IaC 산출물

## Impl 산출물

### 구현 맵

| 모듈 경로 | component_ref |
|----------|---------------|
| `services/api-gateway/` | COMP-001 |
| `services/order-service/` | COMP-002 |
| `services/user-service/` | COMP-003 |

### 코드 구조

```yaml
build_config:
  tool: npm
  node_version: "20"
  workspaces: true  # 모노레포

external_dependencies:
  manager: npm
  lock_file: package-lock.json
  paths:
    - node_modules/

environment_config:
  shared:
    - NODE_ENV
    - LOG_LEVEL
  secrets:
    - DATABASE_URL
    - RABBITMQ_URL
    - REDIS_URL
    - JWT_SECRET
    - AWS_ACCESS_KEY_ID
    - AWS_SECRET_ACCESS_KEY
```

### 구현 가이드

```yaml
prerequisites:
  - Node.js 20.x
  - Docker 24.x

build_commands:
  - npm ci
  - npm run build
  - npm run test

run_commands:
  api-gateway: "node dist/api-gateway/main.js"
  order-service: "node dist/order-service/main.js"
  user-service: "node dist/user-service/main.js"
```

## IaC 산출물

| ID | 도구 | 프로바이더 | 리전 |
|----|------|----------|------|
| IAC-001 | Terraform | AWS | ap-northeast-2 |

### 배포 대상

- ECR 리포지토리: `order-system/{api-gateway,order-service,user-service}`
- ECS 클러스터: `order-system-{dev,staging,prod}`
- 환경별 변수 파일: `infrastructure/environments/{dev,staging,prod}/terraform.tfvars`
