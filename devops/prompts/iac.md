# Infrastructure as Code 프롬프트

## 입력

```
Arch 산출물: {{arch_output}}
SLO 산출물: {{slo_output}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙을 따라 Arch 컴포넌트 구조와 기술 스택을 기반으로 모듈화된 인프라 코드를 자동 생성하세요.

### Step 1: 컴포넌트 분석

Arch `component_structure`에서 모든 컴포넌트를 추출하고, 시스템 프롬프트 **"Arch 컴포넌트 → 클라우드 리소스 매핑"** 표에 따라 유형별로 분류합니다.

### Step 2: 클라우드 프로바이더 결정

Arch `technology_stack.constraint_ref`를 통해 RE `constraints`의 프로바이더 제약(`CON-xxx`)을 확인합니다. 제약이 없으면 기술 스택 맥락에서 최적 프로바이더를 선택하고, 선택 근거를 `constraint_refs`에 기록합니다.

### Step 3: IaC 도구 선택

기술 스택과 팀 맥락에 따라 선택합니다:

- 컨테이너 오케스트레이션: Terraform + Helm
- 서버리스 중심: Terraform 또는 Pulumi
- 설정 관리 필요: Ansible 추가
- 기본값: Terraform

### Step 4: 모듈 구조 생성

시스템 프롬프트 **"모듈 구조 생성"** 구조에 맞춰 컴포넌트 유형별 독립 모듈을 생성합니다.

### Step 5: 네트워크 토폴로지

Arch `component_structure.dependencies`와 `diagrams`(c4-container)에서 시스템 프롬프트 **"네트워크 토폴로지 생성"** 지침에 따라 VPC/서브넷/보안 그룹/DNS를 구성합니다.

### Step 6: 환경별 설정

dev/staging/prod 환경을 동일 모듈·변수 분리 패턴으로 생성합니다:

- dev: 최소 사양 (t3.small, 단일 인스턴스)
- staging: prod 유사 구조, 축소 사양
- prod: SLO 기반 사양 (고가용성, 멀티 AZ)

### Step 7: 상태 관리

시스템 프롬프트 **"상태 관리"** 절에 따라 Remote backend, 환경별 독립 상태 파일, 드리프트 탐지를 설정합니다.

### Step 8: 비용 추정

시스템 프롬프트 **"비용 최적화"** 원칙에 따라 각 환경별 월 예상 비용을 산출하고 최적화 제안을 포함합니다.

### Step 9: 산출물 정리

시스템 프롬프트 **"출력 형식"** 표(인프라 코드 / 모듈 상세 / 환경별 설정 / 비용 추정)에 맞춰 정리하고, **"출력 프로토콜"**에 따라 `meta.json`/`body.md`에 기록합니다. 에스컬레이션이 필요한 경우 시스템 프롬프트 **"에스컬레이션 조건"**을 따릅니다.
