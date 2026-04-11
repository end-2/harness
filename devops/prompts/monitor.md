# 모니터링 프롬프트

## 입력

```
SLO 산출물: {{slo_output}}
Arch 산출물: {{arch_output}}
Strategy 산출물: {{strategy_output}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙을 따라 SLO 정의를 기반으로 알림 규칙, 대시보드, 분산 추적 설정을 자동 생성하세요.

### Step 1: SLO → 알림 규칙 변환

시스템 프롬프트 **"SLO → 모니터링 변환"** 표에 따라 각 `slo_definitions`에 대한 알림 규칙(MON-xxx)을 생성하고, `slo_refs`로 SLO와의 연결을 유지합니다.

### Step 2: RED 메트릭 생성

Arch `component_structure`에서 `type: service`/`type: gateway` 컴포넌트별로 시스템 프롬프트 **"RED 메트릭 (서비스 모니터링)"** 표의 PromQL 패턴을 적용하여 쿼리를 생성합니다.

### Step 3: USE 메트릭 생성

IaC 산출물에서 프로비저닝된 리소스별로 시스템 프롬프트 **"USE 메트릭 (리소스 모니터링)"** 표에 따라 Utilization/Saturation/Errors 메트릭을 생성합니다.

### Step 4: 알림 채널 설정

시스템 프롬프트 **"알림 규칙 설계"** 절의 심각도 분류 및 알림 피로도 방지(그룹핑·억제·묵음·반복 간격) 지침을 적용합니다.

### Step 5: 대시보드 설계

시스템 프롬프트 **"대시보드 설계"** 계층(Overview / Service / Infrastructure / Deploy)에 따라 각 대시보드의 패널 구성을 구체적으로 정의합니다.

### Step 6: 분산 추적 설정

Arch `diagrams`(sequence)에서 주요 흐름을 식별하고 시스템 프롬프트 **"분산 추적 설정"**(샘플링 비율, 전파 방식, 스팬 속성)을 적용합니다.

### Step 7: Strategy 연동 — 배포 시 모니터링

시스템 프롬프트 **"Strategy 연동: 배포 시 모니터링"** 표에 따라 배포 방식별 추가 모니터링을 설계합니다.

### Step 8: 산출물 정리

시스템 프롬프트 **"출력 형식"** 표(알림 규칙 / 대시보드 / 분산 추적 설정)에 맞춰 정리하고, **"출력 프로토콜"**에 따라 `meta.json`/`body.md`에 기록합니다. SLI 측정 불가 시 시스템 프롬프트 **"에스컬레이션 조건"**을 따릅니다.
