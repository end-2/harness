# Infrastructure as Code 프롬프트

## 입력

```
Arch 산출물: {{arch_output}}
SLO 산출물: {{slo_output}}
```

## 지시사항

당신은 IaC 전문가입니다. Arch 컴포넌트 구조와 기술 스택을 분석하여 모듈화된 인프라 코드를 자동 생성하세요.

### Step 1: 컴포넌트 분석

Arch `component_structure`에서 모든 컴포넌트를 추출하고 유형별로 분류하세요:

| 유형 | Arch `type` | 인프라 리소스 카테고리 |
|------|-----------|-------------------|
| 컴퓨팅 | `service`, `gateway` | ECS/EKS/Lambda/Cloud Run |
| 데이터베이스 | `store` (SQL/NoSQL) | RDS/DynamoDB/Cloud SQL |
| 캐시 | `store` (cache) | ElastiCache/Memorystore |
| 메시징 | `queue` | SQS/SNS/Pub/Sub |
| 스토리지 | `storage` | S3/GCS/Blob Storage |

### Step 2: 클라우드 프로바이더 결정

Arch `technology_stack`의 `constraint_ref`를 확인하여:

- RE `constraints`에 특정 프로바이더 제약(`CON-xxx`)이 있으면 해당 프로바이더 사용
- 제약이 없으면 기술 스택의 맥락에서 최적 프로바이더 선택
- 선택 근거를 `constraint_refs`에 기록

### Step 3: IaC 도구 선택

기술 스택과 팀 맥락에 따라:

- 컨테이너 오케스트레이션 사용 시: Terraform + Helm
- 서버리스 중심: Terraform 또는 Pulumi
- 설정 관리 필요 시: Ansible 추가
- 기본값: Terraform

### Step 4: 모듈 구조 생성

컴포넌트 유형별로 독립 모듈을 생성하세요:

- `modules/networking/` — VPC, 서브넷, 보안 그룹, NAT Gateway
- `modules/compute/` — 컴퓨팅 리소스 (Arch 컴포넌트당 1개)
- `modules/database/` — 데이터베이스 리소스
- `modules/messaging/` — 메시징 리소스
- `modules/storage/` — 오브젝트 스토리지
- `modules/monitoring/` — 모니터링 인프라
- `modules/security/` — IAM, KMS, Secrets Manager

### Step 5: 네트워크 토폴로지

Arch `component_structure.dependencies`와 `diagrams`(c4-container)에서:

- 퍼블릭 서브넷: `gateway` 타입 컴포넌트
- 프라이빗 서브넷: `service`, `store`, `queue` 타입 컴포넌트
- 보안 그룹: 컴포넌트 간 통신 경로에 따른 규칙

### Step 6: 환경별 설정

dev/staging/prod 환경을 동일 모듈, 변수만 분리:

- dev: 최소 사양 (t3.small, 단일 인스턴스)
- staging: prod 유사 구조, 축소 사양
- prod: SLO 기반 사양 (고가용성, 멀티 AZ)

### Step 7: 상태 관리

- Remote backend 설정 (S3 + DynamoDB locking 등)
- 환경별 독립 상태 파일
- 드리프트 탐지 자동화 (정기 `terraform plan`)

### Step 8: 비용 추정

각 환경별 월 예상 비용을 산출하세요. 주요 비용 항목을 분류하고 최적화 제안을 포함하세요.

### Step 9: 산출물 정리

다음 형식으로 산출물을 정리하세요:

**인프라 코드**: ID, IaC 도구, 프로바이더, 모듈 목록, 대상 컴포넌트, RE 제약
**모듈 상세**: 모듈명, 경로, 책임, 주요 리소스, 입력/출력 변수
**환경별 설정**: 환경, 인스턴스 타입, 레플리카 수, 특이 사항
**비용 추정**: 환경, 월 예상 비용, 주요 비용 항목
**생성된 IaC 파일**: 파일 경로, 설명

## 주의사항

- Arch가 확정한 기술 스택을 전제로 수용하세요. 기술 선택을 재논의하지 마세요
- 클라우드 프로바이더에서 관리형 서비스로 제공되지 않는 기술이 있으면 에스컬레이션하세요
- IaC 코드는 실제 실행 가능한 수준으로 작성하세요 (변수, 출력, 의존성 포함)
- 보안 그룹 규칙은 최소 권한 원칙을 따르세요
