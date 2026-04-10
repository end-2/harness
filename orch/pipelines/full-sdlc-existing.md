# 기존 프로젝트 전체 SDLC 파이프라인 (Full SDLC — Existing)

기존 코드베이스를 먼저 분석한 후, 전체 SDLC를 진행하는 파이프라인입니다. ex 스킬이 선행하여 기존 시스템의 컨텍스트를 추출합니다.

## 파이프라인 정의

```yaml
name: full-sdlc-existing
description: 기존 프로젝트의 전체 SDLC — 코드 분석 후 요구사항부터 배포까지
trigger: 새 시스템/앱 개발 요청 (기존 프로젝트 있음)

steps:
  - order: 1
    skill: ex
    agent: scan
    mode: auto-execute
    description: 구조 스캔 — 디렉토리 구조 스캔, 파일 분류, 적응적 깊이 모드 결정

  - order: 2
    skill: ex
    agent: detect
    mode: auto-execute
    description: 기술 스택 탐지 — 매니페스트, 설정, 코드 패턴 분석
    upstream: [ex:scan]

  - order: 3
    skill: ex
    agent: analyze
    mode: auto-execute
    description: 의존성/아키텍처 분석 — 모듈 의존성, 컴포넌트 경계, 아키텍처 추론
    upstream: [ex:scan, ex:detect]

  - order: 4
    skill: ex
    agent: map
    mode: auto-execute
    description: 컨텍스트 맵 생성 — 4섹션 통합 산출물
    upstream: [ex:scan, ex:detect, ex:analyze]

  - order: 5
    skill: re
    agent: elicit
    mode: dialogue
    description: 요구사항 도출 — 기존 시스템 맥락이 주입된 상태에서 수집
    upstream: [ex:map]

  - order: 6
    skill: re
    agent: analyze
    mode: dialogue
    description: 요구사항 분석
    upstream: [re:elicit]

  - order: 7
    skill: re
    agent: spec
    mode: dialogue
    description: 요구사항 명세
    upstream: [re:elicit, re:analyze]

  - order: 8
    skill: arch
    agent: design
    mode: dialogue
    description: 아키텍처 설계 — 기존 아키텍처 제약을 전제로 설계
    upstream: [re:spec, ex:map]

  - order: 9
    skill: impl
    agent: generate
    mode: auto-execute
    description: 구현 생성 — 기존 코드 구조/컨벤션 준수
    upstream: [arch:design, ex:map]

  - order: 10
    parallel: true
    description: 품질/보안/운영 병렬 실행
    upstream: [impl:generate]
    steps:
      - skill: qa
        agent: generate
        mode: auto-execute
        description: 테스트 생성
      - skill: sec
        agent: audit
        mode: auto-execute
        description: 보안 감사
      - skill: devops
        agent: pipeline
        mode: auto-execute
        description: 배포 파이프라인
```

## 데이터 흐름

```
ex:scan → ex:detect → ex:analyze → ex:map ──→ re:elicit → re:analyze → re:spec → arch:design → impl:generate ──┬→ qa:generate
                                       │                                    ↑              ↑                     ├→ sec:audit
                                       └────────────────────────────────────┴──────────────┘                     └→ devops:pipeline
                                       (ex 산출물이 re, arch, impl에 업스트림으로 주입)
```

## 핵심 차이점 (vs full-sdlc)

- ex 4단계가 자동 실행으로 기존 코드베이스 컨텍스트 추출
- ex 산출물이 re:elicit에 업스트림 입력으로 주입되어 기존 시스템 맥락 반영
- arch:design이 기존 아키텍처 제약을 전제로 설계
- impl:generate가 기존 코드 구조/컨벤션을 준수
