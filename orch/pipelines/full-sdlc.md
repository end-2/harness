# 전체 SDLC 파이프라인 (Full SDLC)

새로운 시스템/애플리케이션을 처음부터 설계하고 구현하는 전체 소프트웨어 개발 생명주기 파이프라인입니다.

## 파이프라인 정의

```yaml
name: full-sdlc
description: 새 시스템의 전체 SDLC — 요구사항부터 배포까지
trigger: 새 시스템/앱 개발 요청 (기존 프로젝트 없음)

steps:
  - order: 1
    skill: re
    agent: elicit
    mode: dialogue
    description: 요구사항 도출 — 사용자와 대화하여 핵심 요구사항 수집

  - order: 2
    skill: re
    agent: analyze
    mode: dialogue
    description: 요구사항 분석 — 수집된 요구사항의 충돌 해결 및 우선순위 결정
    upstream: [re:elicit]

  - order: 3
    skill: re
    agent: spec
    mode: dialogue
    description: 요구사항 명세 — 구조화된 명세서 초안 작성 및 확인
    upstream: [re:elicit, re:analyze]

  - order: 4
    skill: arch
    agent: design
    mode: dialogue
    description: 아키텍처 설계 — 기술 스택 선택, 컴포넌트 구조, 아키텍처 결정
    upstream: [re:spec]

  - order: 5
    skill: impl
    agent: generate
    mode: auto-execute
    description: 구현 생성 — 아키텍처에 기반한 구현 가이드 및 코드 구조
    upstream: [arch:design]

  - order: 6
    parallel: true
    description: 품질/보안/운영 — 구현 결과를 기반으로 병렬 실행
    upstream: [impl:generate]
    steps:
      - skill: qa
        agent: generate
        mode: auto-execute
        description: 테스트 생성 — 테스트 전략 및 테스트 코드
      - skill: sec
        agent: audit
        mode: auto-execute
        description: 보안 감사 — 위협 모델링, 취약점 분석
      - skill: devops
        agent: pipeline
        mode: auto-execute
        description: 배포 파이프라인 — CI/CD, 인프라 구성
```

## 데이터 흐름

```
re:elicit ──→ re:analyze ──→ re:spec ──→ arch:design ──→ impl:generate ──┬→ qa:generate
                                                                          ├→ sec:audit
                                                                          └→ devops:pipeline
```

## 예상 산출물

| 스킬 | 산출물 |
|------|--------|
| re | requirements_spec.md, constraints.md, quality_attribute_priorities.md |
| arch | architecture_decisions.md, component_structure.md, technology_stack.md, diagrams.md |
| impl | implementation_map.md, code_structure.md, implementation_decisions.md, implementation_guide.md |
| qa | test_strategy.md, test_suite.md, requirements_traceability_matrix.md, quality_report.md |
| sec | threat_model.md, vulnerability_report.md, security_recommendations.md, compliance_status.md |
| devops | pipeline_config.md, infrastructure_code.md, observability_config.md, operational_runbooks.md |

## 완료 시 생성

- `project-structure.md` — 프로젝트 전체 구조 문서
- `release-note.md` — 릴리스 노트
