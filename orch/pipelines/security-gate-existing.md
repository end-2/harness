# 기존 프로젝트 보안 게이트 파이프라인 (Security Gate — Existing)

기존 코드베이스를 먼저 분석하여 컴포넌트와 API 표면을 추출한 후, 보안 점검을 수행하는 파이프라인입니다.

## 파이프라인 정의

```yaml
name: security-gate-existing
description: 기존 프로젝트 보안 게이트 — 코드 분석 후 보안 점검
trigger: 보안 점검/감사 요청 (기존 프로젝트 있음)

steps:
  - order: 1
    skill: ex
    agent: scan
    mode: auto-execute
    description: 구조 스캔

  - order: 2
    skill: ex
    agent: detect
    mode: auto-execute
    description: 기술 스택 탐지
    upstream: [ex:scan]

  - order: 3
    skill: ex
    agent: analyze
    mode: auto-execute
    description: 의존성/아키텍처 분석
    upstream: [ex:scan, ex:detect]

  - order: 4
    skill: ex
    agent: map
    mode: auto-execute
    description: 컨텍스트 맵 생성
    upstream: [ex:scan, ex:detect, ex:analyze]

  - order: 5
    skill: sec
    agent: threat-model
    mode: dialogue
    description: 위협 모델링 — ex 산출물로 공격 표면 식별 강화
    upstream: [ex:map]

  - order: 6
    skill: sec
    agent: audit
    mode: auto-execute
    description: 보안 감사
    upstream: [sec:threat-model, ex:map]

  - order: 7
    skill: sec
    agent: compliance
    mode: auto-execute
    description: 규정 준수
    upstream: [sec:threat-model, sec:audit]
```

## 데이터 흐름

```
ex:scan → ex:detect → ex:analyze → ex:map ──→ sec:threat-model → sec:audit → sec:compliance
                                       │                              ↑
                                       └──────────────────────────────┘
                                       (ex 산출물이 sec에 공격 표면/컴포넌트 정보 제공)
```
