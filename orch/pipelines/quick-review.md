# 빠른 리뷰 파이프라인 (Quick Review)

요구사항, 아키텍처, 구현 각각의 리뷰 에이전트를 순차 실행하여 빠르게 전반적인 리뷰를 수행하는 파이프라인입니다.

## 파이프라인 정의

```yaml
name: quick-review
description: 빠른 리뷰 — 요구사항, 아키텍처, 구현 순차 리뷰
trigger: 코드 리뷰 요청

steps:
  - order: 1
    skill: re
    agent: review
    mode: dialogue
    description: 요구사항 리뷰 — 요구사항 명세의 완전성, 일관성, 추적성 검토

  - order: 2
    skill: arch
    agent: review
    mode: dialogue
    description: 아키텍처 리뷰 — 설계 결정의 적절성, 품질 속성 충족 여부 검토
    upstream: [re:review]

  - order: 3
    skill: impl
    agent: review
    mode: dialogue
    description: 구현 리뷰 — 코드 품질, 아키텍처 준수, 패턴 일관성 검토
    upstream: [arch:review]
```

## 데이터 흐름

```
re:review → arch:review → impl:review
```

## 특징

- 모든 단계가 대화형(dialogue) — 리뷰 결과에 대해 사용자와 논의 가능
- 기존 산출물을 입력으로 받아 리뷰 (이전 run의 산출물 참조 가능)
- ex 스킬 선행 없음 — 리뷰 대상 산출물이 이미 존재한다고 가정
