# Infrastructure as Code 출력 예시

> 온라인 주문 처리 시스템의 IaC 산출물 (Terraform + AWS)

## 인프라 코드

| ID | IaC 도구 | 프로바이더 | 리전 | 모듈 수 | RE 제약 |
|----|---------|----------|------|--------|---------|
| IAC-001 | Terraform | AWS | ap-northeast-2 | 7 | CON-001, CON-003 |

## 모듈 상세

| 모듈명 | 경로 | 책임 | 주요 리소스 |
|-------|------|------|-----------|
| networking | `modules/networking/` | VPC, 서브넷, 보안 그룹, NAT | VPC, Public/Private Subnet (2 AZ), NAT Gateway, ALB |
| compute | `modules/compute/` | ECS 클러스터, 서비스, 태스크 | ECS Cluster, 3x Service, Task Definition, ECR |
| database | `modules/database/` | RDS PostgreSQL | RDS Instance (Multi-AZ), Subnet Group, Parameter Group |
| messaging | `modules/messaging/` | RabbitMQ | Amazon MQ Broker (RabbitMQ) |
| cache | `modules/cache/` | Redis | ElastiCache Redis Cluster |
| monitoring | `modules/monitoring/` | CloudWatch, SNS | CloudWatch Alarms, Log Groups, SNS Topics |
| security | `modules/security/` | IAM, Secrets Manager | IAM Roles, Policies, Secrets Manager Secrets |

## 모듈 입출력 변수 (예: compute)

### 입력

| 변수 | 타입 | 설명 | 기본값 |
|------|------|------|--------|
| `cluster_name` | string | ECS 클러스터 이름 | - |
| `vpc_id` | string | VPC ID (networking 모듈 출력) | - |
| `private_subnet_ids` | list(string) | 프라이빗 서브넷 ID | - |
| `services` | map(object) | 서비스별 설정 (이미지, CPU, 메모리, 포트, 레플리카 수) | - |
| `alb_target_group_arns` | map(string) | ALB 타겟 그룹 ARN | - |

### 출력

| 변수 | 설명 |
|------|------|
| `cluster_id` | ECS 클러스터 ID |
| `service_arns` | 서비스별 ARN |
| `task_definition_arns` | 태스크 정의별 ARN |

## 환경별 설정

| 환경 | api-gateway | order-service | user-service | RDS | RabbitMQ | Redis |
|------|------------|--------------|-------------|-----|---------|-------|
| dev | 0.25 vCPU / 512MB / 1개 | 0.25 vCPU / 512MB / 1개 | 0.25 vCPU / 512MB / 1개 | db.t3.micro / Single-AZ | mq.t3.micro / Single | cache.t3.micro / 1노드 |
| staging | 0.5 vCPU / 1GB / 2개 | 0.5 vCPU / 1GB / 2개 | 0.5 vCPU / 1GB / 2개 | db.t3.small / Multi-AZ | mq.m5.large / Single | cache.t3.small / 2노드 |
| prod | 1 vCPU / 2GB / 3개 | 1 vCPU / 2GB / 3개 | 0.5 vCPU / 1GB / 2개 | db.r6g.large / Multi-AZ / Read Replica | mq.m5.large / Active-Standby | cache.r6g.large / 3노드 |

## 네트워크 토폴로지

```
VPC: 10.0.0.0/16 (ap-northeast-2)
├── Public Subnet A: 10.0.1.0/24 (ap-northeast-2a)
│   └── ALB, NAT Gateway
├── Public Subnet B: 10.0.2.0/24 (ap-northeast-2c)
│   └── ALB
├── Private Subnet A: 10.0.10.0/24 (ap-northeast-2a)
│   └── ECS Tasks (api-gateway, order-service, user-service)
├── Private Subnet B: 10.0.11.0/24 (ap-northeast-2c)
│   └── ECS Tasks (replica)
├── Data Subnet A: 10.0.20.0/24 (ap-northeast-2a)
│   └── RDS Primary, ElastiCache, Amazon MQ
└── Data Subnet B: 10.0.21.0/24 (ap-northeast-2c)
    └── RDS Standby
```

### 보안 그룹

| 보안 그룹 | 인바운드 | 아웃바운드 |
|----------|---------|----------|
| sg-alb | 0.0.0.0/0:443 (HTTPS) | sg-ecs:8080 |
| sg-ecs | sg-alb:8080, sg-ecs:3000-3001 | sg-rds:5432, sg-mq:5672, sg-redis:6379 |
| sg-rds | sg-ecs:5432 | - |
| sg-mq | sg-ecs:5672 | - |
| sg-redis | sg-ecs:6379 | - |

## 상태 관리

| 항목 | 설정 |
|------|------|
| Backend | S3 (`order-system-terraform-state`) + DynamoDB locking |
| 상태 파일 분리 | 환경별 독립 (`env/{dev,staging,prod}/terraform.tfstate`) |
| 드리프트 탐지 | 일간 `terraform plan` 스케줄 → Slack 알림 |
| 상태 암호화 | S3 SSE-KMS |

## 비용 추정

| 환경 | 월 예상 비용 | 주요 비용 항목 |
|------|------------|-------------|
| dev | $150 ~ $200 | ECS Fargate ($50), RDS ($30), NAT Gateway ($35), 기타 |
| staging | $400 ~ $500 | ECS Fargate ($120), RDS Multi-AZ ($100), NAT Gateway ($70), 기타 |
| prod | $1,200 ~ $1,500 | ECS Fargate ($350), RDS Multi-AZ + Read Replica ($300), NAT Gateway ($70), ALB ($50), 기타 |

### 비용 최적화 제안

- ECS Fargate Savings Plan 적용 시 prod 컴퓨팅 비용 20% 절감 가능
- RDS Reserved Instance (1년) 적용 시 DB 비용 30% 절감 가능
- dev 환경 야간/주말 자동 중지 시 약 60% 비용 절감

## 생성된 IaC 파일

| 파일 경로 | 설명 |
|----------|------|
| `infrastructure/modules/networking/main.tf` | VPC, 서브넷, NAT, ALB |
| `infrastructure/modules/compute/main.tf` | ECS 클러스터, 서비스, 태스크 정의 |
| `infrastructure/modules/database/main.tf` | RDS PostgreSQL |
| `infrastructure/modules/messaging/main.tf` | Amazon MQ (RabbitMQ) |
| `infrastructure/modules/cache/main.tf` | ElastiCache Redis |
| `infrastructure/modules/monitoring/main.tf` | CloudWatch, SNS |
| `infrastructure/modules/security/main.tf` | IAM, Secrets Manager |
| `infrastructure/environments/dev/main.tf` | dev 환경 루트 모듈 |
| `infrastructure/environments/staging/main.tf` | staging 환경 루트 모듈 |
| `infrastructure/environments/prod/main.tf` | prod 환경 루트 모듈 |
| `infrastructure/backend.tf` | S3 + DynamoDB 상태 관리 |
| `infrastructure/versions.tf` | 프로바이더 버전 고정 |
