# 보안 게이트 파이프라인 (Security Gate)

보안 관점에서 위협 모델링, 취약점 감사, 규정 준수를 순차적으로 수행하는 파이프라인입니다.

## 파이프라인 정의

```yaml
name: security-gate
description: 보안 게이트 — 위협 모델링, 감사, 규정 준수
trigger: 보안 점검/감사 요청 (기존 프로젝트 없음)

steps:
  - order: 1
    skill: sec
    agent: threat-model
    mode: dialogue
    description: 위협 모델링 — 자산 식별, 위협 분석, 공격 표면 매핑
    
  - order: 2
    skill: sec
    agent: audit
    mode: auto-execute
    description: 보안 감사 — 취약점 분석, 코드 리뷰
    upstream: [sec:threat-model]

  - order: 3
    skill: sec
    agent: compliance
    mode: auto-execute
    description: 규정 준수 — 보안 표준 및 규정 준수 상태 확인
    upstream: [sec:threat-model, sec:audit]
```

## 데이터 흐름

```
sec:threat-model → sec:audit → sec:compliance
```
