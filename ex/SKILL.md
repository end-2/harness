---
name: ex
description: 기존 코드베이스를 자동 분석하여 LLM 컨텍스트에 최적화된 프로젝트 맵을 만든다. 사용자가 '이 레포 훑어줘', '프로젝트 구조 파악', '기술 스택 뭐 쓰는지', '아키텍처 추론', '온보딩 가이드', '기존 코드 분석' 같은 말을 하면 반드시 이 스킬을 사용하라. 후속 스킬(re/arch/impl/qa/sec/devops)이 소비할 4섹션 산출물을 생성한다.
---

# ex — Project Explorer

## 언제 이 스킬을 사용하는가

기존 코드베이스를 자동 분석하여 LLM 컨텍스트에 최적화된 프로젝트 맵을 만든다. 사용자가 '이 레포 훑어줘', '프로젝트 구조 파악', '기술 스택 뭐 쓰는지', '아키텍처 추론', '온보딩 가이드', '기존 코드 분석' 같은 말을 하면 반드시 이 스킬을 사용하라. 후속 스킬(re/arch/impl/qa/sec/devops)이 소비할 4섹션 산출물을 생성한다.

## 에이전트 구성

이 스킬은 다음 에이전트들로 구성된다. 각 에이전트의 전체 시스템 프롬프트는
`agents/<name>.md`에 있으며, Claude Code subagent 프런트매터가 포함되어 있어
`Task` 도구로 직접 스폰할 수 있다.

| 에이전트 | 역할 |
|---|---|
| [`ex:scan`](agents/scan.md) | 프로젝트 디렉토리 구조 스캔, 파일 분류, 진입점 식별, 적응적 깊이 모드 결정 |
| [`ex:detect`](agents/detect.md) | 매니페스트·설정 파일·코드 패턴을 분석하여 기술 스택을 자동 탐지 |
| [`ex:analyze`](agents/analyze.md) | import/require 분석으로 의존성 그래프·컴포넌트 경계·아키텍처 스타일 추론 |
| [`ex:map`](agents/map.md) | scan+detect+analyze 결과를 토큰 효율적으로 4섹션 최종 산출물로 통합 |

## 파이프라인

기본 실행 순서:

```
scan → detect → analyze → map
```

상세한 단계별 입출력 계약, 체크포인트, 의존성, 에스컬레이션 조건은
[`skills.yaml`](skills.yaml)에 정의되어 있다. 파이프라인을 오케스트레이션할
때는 반드시 `skills.yaml`을 참조해 upstream/consumers 관계를 맞춰야 한다.

## 산출물 규칙

모든 에이전트 산출물은 `meta.json`(구조화 데이터)과 `body.md`(서술)의 쌍으로
`runs/<run_id>/ex/<agent>[-NN]/` 하위에 생성된다. `meta.json`은 반드시
`scripts/artifact` CLI를 통해서만 조작한다. 본 스킬 디렉터리의
[`scripts/artifact`](scripts/artifact)는 루트 CLI를 감싼 래퍼로, `--skill
ex`을 자동으로 주입한다.

```bash
# 새 산출물 생성 (--skill 자동 주입)
./scripts/artifact init --agent scan --title "예시"

# 본문 경로 획득
./scripts/artifact path ex-scan-01 --run-id <id> --body

# 진행 상태 및 데이터 갱신
./scripts/artifact set ex-scan-01 --run-id <id> \
    --progress review --data-file patch.json
```

`body.md`의 골격은 [`templates/ex/`](../templates/ex/)에 위치한
템플릿에서 생성된다.

## 참고 자료

- 에이전트 시스템 프롬프트: [`agents/`](agents/)
- 프롬프트 템플릿: [`prompts/`](prompts/)
- 입출력 예시: [`examples/`](examples/)
- 파이프라인·의존성 정의: [`skills.yaml`](skills.yaml)
- 스킬별 산출물 래퍼: [`scripts/artifact`](scripts/artifact)
