---
name: re
description: 사용자와의 대화형 상호작용으로 요구사항을 도출·분석·명세·검증한다. '무엇을 만들지 정리', '요구사항 뽑아내기', '스펙 문서', 'FR/NFR', '품질 속성 우선순위', '수용 기준' 등 요구사항 공학 맥락에서 반드시 사용하라. 산출물은 후속 arch/impl/qa 스킬이 그대로 소비 가능한 세 섹션 명세다.
---

# re — Requirements Engineering

## 언제 이 스킬을 사용하는가

사용자와의 대화형 상호작용으로 요구사항을 도출·분석·명세·검증한다. '무엇을 만들지 정리', '요구사항 뽑아내기', '스펙 문서', 'FR/NFR', '품질 속성 우선순위', '수용 기준' 등 요구사항 공학 맥락에서 반드시 사용하라. 산출물은 후속 arch/impl/qa 스킬이 그대로 소비 가능한 세 섹션 명세다.

## 에이전트 구성

이 스킬은 다음 에이전트들로 구성된다. 각 에이전트의 전체 시스템 프롬프트는
`agents/<name>.md`에 있으며, Claude Code subagent 프런트매터가 포함되어 있어
`Task` 도구로 직접 스폰할 수 있다.

| 에이전트 | 역할 |
|---|---|
| [`re:elicit`](agents/elicit.md) | 사용자와 multi-turn 대화로 모호한 요구를 구조화된 요구사항으로 점진적으로 도출 |
| [`re:analyze`](agents/analyze.md) | 요구사항의 완전성·일관성·실현 가능성을 분석하고 추가 질문을 생성 |
| [`re:spec`](agents/spec.md) | 분석 결과를 후속 스킬이 소비할 수 있는 세 섹션 명세 문서로 구조화 |
| [`re:review`](agents/review.md) | 명세 문서의 섹션별 리뷰 및 후속 스킬 소비 적합성 검증 |

## 파이프라인

기본 실행 순서:

```
elicit → analyze → spec → review
```

상세한 단계별 입출력 계약, 체크포인트, 의존성, 에스컬레이션 조건은
[`skills.yaml`](skills.yaml)에 정의되어 있다. 파이프라인을 오케스트레이션할
때는 반드시 `skills.yaml`을 참조해 upstream/consumers 관계를 맞춰야 한다.

## 산출물 규칙

모든 에이전트 산출물은 `meta.json`(구조화 데이터)과 `body.md`(서술)의 쌍으로
`runs/<run_id>/re/<agent>[-NN]/` 하위에 생성된다. `meta.json`은 반드시
`scripts/artifact` CLI를 통해서만 조작한다. 본 스킬 디렉터리의
[`scripts/artifact`](scripts/artifact)는 루트 CLI를 감싼 래퍼로, `--skill
re`을 자동으로 주입한다.

```bash
# 새 산출물 생성 (--skill 자동 주입)
./scripts/artifact init --agent elicit --title "예시"

# 본문 경로 획득
./scripts/artifact path re-elicit-01 --run-id <id> --body

# 진행 상태 및 데이터 갱신
./scripts/artifact set re-elicit-01 --run-id <id> \
    --progress review --data-file patch.json
```

`body.md`의 골격은 [`templates/re/`](../templates/re/)에 위치한
템플릿에서 생성된다.

## 참고 자료

- 에이전트 시스템 프롬프트: [`agents/`](agents/)
- 프롬프트 템플릿: [`prompts/`](prompts/)
- 입출력 예시: [`examples/`](examples/)
- 파이프라인·의존성 정의: [`skills.yaml`](skills.yaml)
- 스킬별 산출물 래퍼: [`scripts/artifact`](scripts/artifact)
