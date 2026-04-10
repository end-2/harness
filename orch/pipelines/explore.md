# 코드베이스 탐색 파이프라인 (Explore)

ex 스킬만 단독 실행하여 기존 프로젝트의 구조화된 컨텍스트 맵을 생성하는 파이프라인입니다. 후속 스킬 연계 없이 코드베이스 이해 목적으로 사용합니다.

## 파이프라인 정의

```yaml
name: explore
description: 코드베이스 탐색 — 기존 프로젝트의 구조/기술/아키텍처 분석
trigger: 코드 분석/탐색 요청

steps:
  - order: 1
    skill: ex
    agent: scan
    mode: auto-execute
    description: 구조 스캔 — 디렉토리 구조, 파일 분류, 적응적 깊이 모드 결정

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
    description: 컨텍스트 맵 생성 — 4섹션 통합 산출물 (토큰 효율 최적화)
    upstream: [ex:scan, ex:detect, ex:analyze]
```

## 데이터 흐름

```
ex:scan → ex:detect → ex:analyze → ex:map
```

## 산출물

| 파일 | 내용 |
|------|------|
| project_structure_map.md | 디렉토리 트리, 파일 분류, 진입점, 설정 파일 |
| technology_stack_detection.md | 언어, 프레임워크, DB, 빌드 도구 등 |
| component_relationship_analysis.md | 모듈, 의존성, API 표면, 패턴 |
| architecture_inference.md | 아키텍처 스타일, 레이어, 통신 패턴 |

## 특징

- 전체 자동 실행 — 사용자 개입 없이 완료 (예외 시에만 에스컬레이션)
- 프로젝트 루트 경로만 입력하면 전체 분석 수행
- 산출물은 후속 파이프라인에서 업스트림으로 재사용 가능
