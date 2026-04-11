---
name: orch
description: 모든 harness 스킬(ex/re/arch/impl/qa/sec/devops)의 실행을 조율하는 컨트롤 플레인. 사용자 요청이 여러 스킬을 걸쳐야 할 때, '파이프라인', '워크플로', '실행 재개', '산출물 조회', '스킬 상태' 같은 맥락에서 반드시 사용하라. 사용자는 항상 orch을 통해 통신하고, 개별 스킬을 직접 호출하지 않는다.
---

# orch — Skill Orchestration

## 언제 이 스킬을 사용하는가

모든 harness 스킬(ex/re/arch/impl/qa/sec/devops)의 실행을 조율하는 컨트롤 플레인. 사용자 요청이 여러 스킬을 걸쳐야 할 때, '파이프라인', '워크플로', '실행 재개', '산출물 조회', '스킬 상태' 같은 맥락에서 반드시 사용하라. 사용자는 항상 orch을 통해 통신하고, 개별 스킬을 직접 호출하지 않는다.

## 에이전트 구성

이 스킬은 다음 에이전트들로 구성된다. 각 에이전트의 전체 시스템 프롬프트는
`agents/<name>.md`에 있으며, Claude Code subagent 프런트매터가 포함되어 있어
`Task` 도구로 직접 스폰할 수 있다.

| 에이전트 | 역할 |
|---|---|
| [`orch:dispatch`](agents/dispatch.md) | 사용자의 유일한 진입점. 자연어 요청을 분석하여 스킬/파이프라인으로 라우팅 |
| [`orch:pipeline`](agents/pipeline.md) | DAG 기반 워크플로 실행, 스킬 간 흐름 제어(순차/병렬/조건부), 에이전트 스폰 |
| [`orch:relay`](agents/relay.md) | 실행 중인 스킬 에이전트와 사용자 간의 멀티턴 대화 중계 |
| [`orch:run`](agents/run.md) | 실행 생명주기 관리, 산출물 디렉토리 생성·검증, 상태 추적, 재개 지원 |
| [`orch:status`](agents/status.md) | 실행 이력 조회, 스킬 상태 확인, 산출물 검색 |
| [`orch:config`](agents/config.md) | 스킬 설정, 에이전트 규칙, 파이프라인 템플릿 관리 |

## 파이프라인

기본 실행 순서:

```
dispatch → pipeline → relay → run → status → config
```

상세한 단계별 입출력 계약, 체크포인트, 의존성, 에스컬레이션 조건은
[`skills.yaml`](skills.yaml)에 정의되어 있다. 파이프라인을 오케스트레이션할
때는 반드시 `skills.yaml`을 참조해 upstream/consumers 관계를 맞춰야 한다.

## 산출물 규칙

모든 에이전트 산출물은 `meta.json`(구조화 데이터)과 `body.md`(서술)의 쌍으로
`runs/<run_id>/orch/<agent>[-NN]/` 하위에 생성된다. `meta.json`은 반드시
`scripts/artifact` CLI를 통해서만 조작한다. 본 스킬 디렉터리의
[`scripts/artifact`](scripts/artifact)는 루트 CLI를 감싼 래퍼로, `--skill
orch`을 자동으로 주입한다.

```bash
# 새 산출물 생성 (--skill 자동 주입)
./scripts/artifact init --agent dispatch --title "예시"

# 본문 경로 획득
./scripts/artifact path orch-dispatch-01 --run-id <id> --body

# 진행 상태 및 데이터 갱신
./scripts/artifact set orch-dispatch-01 --run-id <id> \
    --progress review --data-file patch.json
```

`body.md`의 골격은 [`templates/orch/`](../templates/orch/)에 위치한
템플릿에서 생성된다.

## 참고 자료

- 에이전트 시스템 프롬프트: [`agents/`](agents/)
- 프롬프트 템플릿: [`prompts/`](prompts/)
- 입출력 예시: [`examples/`](examples/)
- 파이프라인·의존성 정의: [`skills.yaml`](skills.yaml)
- 스킬별 산출물 래퍼: [`scripts/artifact`](scripts/artifact)
