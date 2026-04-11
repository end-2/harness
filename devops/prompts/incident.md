# 인시던트 대응 프롬프트

## 입력

```
Strategy 산출물: {{strategy_output}}
Monitor 산출물: {{monitor_output}}
Arch 산출물: {{arch_output}}
IaC 산출물: {{iac_output}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙을 따라 Strategy의 롤백 절차와 Monitor의 알림 규칙을 기반으로 인시던트 대응 런북을 자동 생성하세요.

### Step 1: 알림 규칙 분석

Monitor `monitoring_rules`에서 모든 알림 규칙의 `id`, `condition`, `severity`, `slo_refs`를 추출하고 심각도별로 분류합니다.

### Step 2: 롤백 절차 분석

Strategy 산출물에서 `rollback_trigger`, `rollback_procedure`, `health_checks`를 추출합니다.

### Step 3: 장애 시나리오 도출

Arch `component_structure`의 컴포넌트 유형별로 시스템 프롬프트 **"장애 유형별 런북"** 표에 따라 장애 시나리오를 도출합니다.

### Step 4: 알림별 런북 생성

시스템 프롬프트 **"Strategy + Monitor → 런북 자동 생성"** 매핑 표와 **"런북 구조"** 템플릿에 따라 각 알림에 대응하는 런북을 생성합니다. 알림-런북 1:1 매핑을 유지합니다.

### Step 5: 진단 명령어 생성

IaC 산출물에서 인프라 접근 방법(namespace, 호스트, 큐 URL 등)을 추출하여 런북의 진단 절차에 구체적 명령어를 포함합니다.

### Step 6: 에스컬레이션 경로 설정

시스템 프롬프트 **"에스컬레이션 경로"** 표의 심각도별 매트릭스를 적용합니다.

### Step 7: 커뮤니케이션 템플릿

시스템 프롬프트 **"커뮤니케이션 템플릿"** 및 **"사후 분석 (Postmortem) 템플릿"**을 사용하여 내부 공지·외부 상태·사후 분석 템플릿을 생성합니다.

### Step 8: 산출물 정리

시스템 프롬프트 **"출력 형식"** 표(런북 목록 / 에스컬레이션 매트릭스 / 커뮤니케이션 템플릿)에 맞춰 정리하고, **"출력 프로토콜"**에 따라 `meta.json`/`body.md`에 기록합니다.
