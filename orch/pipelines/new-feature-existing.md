# 기존 프로젝트 신규 기능 개발 파이프라인 (New Feature — Existing)

기존 프로젝트를 먼저 분석한 후, 기존 구조와 기술 스택을 반영하여 신규 기능을 개발하는 파이프라인입니다.

## 파이프라인 정의

```yaml
name: new-feature-existing
description: 기존 프로젝트에 신규 기능 개발 — 코드 분석 후 설계/구현
trigger: 기능 추가/변경 요청 (기존 프로젝트 있음)

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
    skill: re
    agent: elicit
    mode: dialogue
    description: 요구사항 도출 — 기존 시스템 맥락 반영
    upstream: [ex:map]

  - order: 6
    skill: re
    agent: spec
    mode: dialogue
    description: 요구사항 명세
    upstream: [re:elicit]

  - order: 7
    skill: arch
    agent: design
    mode: dialogue
    description: 아키텍처 설계 — 기존 아키텍처 제약 반영
    upstream: [re:spec, ex:map]

  - order: 8
    skill: impl
    agent: generate
    mode: auto-execute
    description: 구현 생성 — 기존 코드 컨벤션 준수
    upstream: [arch:design, ex:map]

  - order: 9
    skill: qa
    agent: generate
    mode: auto-execute
    description: 테스트 생성
    upstream: [impl:generate]
```

## 데이터 흐름

```
ex:scan → ex:detect → ex:analyze → ex:map ──→ re:elicit → re:spec → arch:design → impl:generate → qa:generate
                                       │                                ↑              ↑
                                       └────────────────────────────────┴──────────────┘
                                       (ex 산출물이 re, arch, impl에 업스트림으로 주입)
```
