# 아키텍처 리뷰 프롬프트

## 입력

```
아키텍처 결정 요약: {{architecture_decisions}}
컴포넌트 구조: {{component_structure}}
기술 스택: {{technology_stack}}
RE 요구사항 명세: {{requirements_spec}}
RE 제약 조건: {{constraints}}
RE 품질 속성 우선순위: {{quality_attribute_priorities}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙을 따라 design 산출물을 RE 품질 속성 메트릭 기반으로 검증하고, 설계의 적합성을 판정하세요.

### Step 1: RE 메트릭 기반 시나리오 검증

시스템 프롬프트 **"검증 영역 → 1. RE 메트릭 기반 시나리오 검증"**의 변환 표를 사용해 각 `quality_attributes.metric`을 시나리오로 변환하고, 관련 컴포넌트·통신 경로를 식별해 PASS/RISK/FAIL을 판정합니다:

```
[SV-001] 시나리오: {{시나리오 설명}}
  RE 근거: {{quality_attribute}} (metric: {{metric}})
  관련 컴포넌트: {{COMP-xxx, COMP-yyy}}
  평가: PASS | RISK | FAIL
  분석: {{분석 내용}}
  권고: {{개선 방안 — RISK/FAIL인 경우}}
```

### Step 2: RE 제약 조건 준수 검증

시스템 프롬프트 **"검증 영역 → 2. RE 제약 조건 준수 검증"**의 형식과 기준에 따라 hard/soft/negotiable 제약을 모두 검사합니다. hard 제약 NON-COMPLIANT는 Critical 이슈, negotiable 완화는 design 에이전트의 사용자 확인 여부를 검증합니다.

### Step 3: 컴포넌트-요구사항 추적성 검증

시스템 프롬프트 **"검증 영역 → 3. 컴포넌트-요구사항 추적성 검증"**의 추적성 매트릭스를 작성합니다. UNCOVERED 요구사항은 Major 이슈, 과도하게 많은 요구사항을 담당하는 컴포넌트는 "God Component" 리스크로 보고합니다.

### Step 4: 아키텍처 리스크 분석

시스템 프롬프트 **"검증 영역 → 4. 아키텍처 기술 부채 식별"**의 체크 목록(SPOF, 순환 의존, 과도한 결합, 확장성 병목, 기술 스택 리스크)을 적용합니다.

### Step 5: 후속 스킬 소비 적합성 판정

시스템 프롬프트 **"검증 영역 → 5. 후속 스킬 소비 적합성"** 표의 체크 항목에 따라 impl:generate / qa:strategy / security:threat-model / deployment:strategy / operation:runbook 각 소비자 스킬에 대해 판정합니다.

### Step 6: 이슈 분류

시스템 프롬프트 **"리뷰 프로세스 → 단계 2: 이슈 분류"** 기준(Critical/Major/Minor/Info)에 따라 발견된 이슈를 분류합니다.

### Step 7: 최종 판정

시스템 프롬프트 **"리뷰 프로세스 → 단계 3/4"** 및 **"출력 형식 → 최종 판정"** 기준에 따라 APPROVED / CONDITIONAL / REJECTED 중 하나를 결정합니다.

### Step 8: 사용자 에스컬레이션

리뷰어가 독단적으로 판단할 수 없는 이슈를 사용자에게 에스컬레이션합니다:

```
[ESC-001] <이슈 설명>
  배경: ...
  리스크: ...
  선택지: A / B
  리뷰어 의견: ...
  → 어떤 방향으로 진행할까요?
```

### Step 9: 산출물 기록

시스템 프롬프트 **"출력 형식"** 표 구조에 맞춰 결과를 정리하고, **"출력 프로토콜"**에 따라 `meta.json`/`body.md`에 기록합니다. 최종 판정은 `scripts/artifact set --verdict`으로 기록합니다.
