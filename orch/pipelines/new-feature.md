# 신규 기능 개발 파이프라인 (New Feature)

기존 요구사항 분석을 간소화하고, 설계와 구현에 집중하는 파이프라인입니다. 보안/DevOps 단계를 생략하여 빠르게 기능을 개발합니다.

## 파이프라인 정의

```yaml
name: new-feature
description: 신규 기능 개발 — 요구사항, 설계, 구현, 테스트
trigger: 기능 추가/변경 요청 (기존 프로젝트 없음)

steps:
  - order: 1
    skill: re
    agent: elicit
    mode: dialogue
    description: 요구사항 도출

  - order: 2
    skill: re
    agent: spec
    mode: dialogue
    description: 요구사항 명세
    upstream: [re:elicit]

  - order: 3
    skill: arch
    agent: design
    mode: dialogue
    description: 아키텍처 설계
    upstream: [re:spec]

  - order: 4
    skill: impl
    agent: generate
    mode: auto-execute
    description: 구현 생성
    upstream: [arch:design]

  - order: 5
    skill: qa
    agent: generate
    mode: auto-execute
    description: 테스트 생성
    upstream: [impl:generate]
```

## 데이터 흐름

```
re:elicit → re:spec → arch:design → impl:generate → qa:generate
```

## full-sdlc와의 차이

- `re:analyze` 생략 — 단일 기능이므로 상세 분석 불필요
- `sec`, `devops` 생략 — 기능 개발에 집중
- 모든 단계가 순차 실행 (병렬 없음)
