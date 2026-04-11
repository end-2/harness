---
name: qa
description: RE/Arch/Impl 산출물 기반으로 테스트 전략 수립, 테스트 코드 생성, 요구사항 추적 매트릭스(RTM) 검증, 품질 리포트를 생성한다. '테스트 전략', '테스트 코드 생성', '커버리지', 'RTM', '품질 게이트', 'NFR 검증' 같은 품질 보증 맥락에서 반드시 사용하라. 모든 테스트는 RE 요구사항까지 역추적된다.
---

# qa — Quality Assurance

## 언제 이 스킬을 사용하는가

RE/Arch/Impl 산출물 기반으로 테스트 전략 수립, 테스트 코드 생성, 요구사항 추적 매트릭스(RTM) 검증, 품질 리포트를 생성한다. '테스트 전략', '테스트 코드 생성', '커버리지', 'RTM', '품질 게이트', 'NFR 검증' 같은 품질 보증 맥락에서 반드시 사용하라. 모든 테스트는 RE 요구사항까지 역추적된다.

## 에이전트 구성

이 스킬은 다음 에이전트들로 구성된다. 각 에이전트의 전체 시스템 프롬프트는
`agents/<name>.md`에 있으며, Claude Code subagent 프런트매터가 포함되어 있어
`Task` 도구로 직접 스폰할 수 있다.

| 에이전트 | 역할 |
|---|---|
| [`qa:strategy`](agents/strategy.md) | RE/Arch/Impl 산출물 분석 기반 테스트 범위·피라미드·우선순위·NFR 계획 수립 |
| [`qa:generate`](agents/generate.md) | acceptance_criteria → 테스트 케이스 변환, 단위/통합/E2E/계약/NFR 테스트 코드 생성(re_refs 내장) |
| [`qa:review`](agents/review.md) | 요구사항 커버리지 검증, RTM 생성, 커버리지 갭 발견 시 generate 재호출 |
| [`qa:report`](agents/report.md) | RE 메트릭 대비 품질 현황 종합, 품질 게이트 판정, 잔여 리스크 식별 |

## 파이프라인

기본 실행 순서:

```
strategy → generate → review → report
```

상세한 단계별 입출력 계약, 체크포인트, 의존성, 에스컬레이션 조건은
[`skills.yaml`](skills.yaml)에 정의되어 있다. 파이프라인을 오케스트레이션할
때는 반드시 `skills.yaml`을 참조해 upstream/consumers 관계를 맞춰야 한다.

## 산출물 규칙

모든 에이전트 산출물은 `meta.json`(구조화 데이터)과 `body.md`(서술)의 쌍으로
`runs/<run_id>/qa/<agent>[-NN]/` 하위에 생성된다. `meta.json`은 반드시
`scripts/artifact` CLI를 통해서만 조작한다. 본 스킬 디렉터리의
[`scripts/artifact`](scripts/artifact)는 루트 CLI를 감싼 래퍼로, `--skill
qa`을 자동으로 주입한다.

```bash
# 새 산출물 생성 (--skill 자동 주입)
./scripts/artifact init --agent strategy --title "예시"

# 본문 경로 획득
./scripts/artifact path qa-strategy-01 --run-id <id> --body

# 진행 상태 및 데이터 갱신
./scripts/artifact set qa-strategy-01 --run-id <id> \
    --progress review --data-file patch.json
```

`body.md`의 골격은 [`templates/qa/`](../templates/qa/)에 위치한
템플릿에서 생성된다.

## 참고 자료

- 에이전트 시스템 프롬프트: [`agents/`](agents/)
- 프롬프트 템플릿: [`prompts/`](prompts/)
- 입출력 예시: [`examples/`](examples/)
- 파이프라인·의존성 정의: [`skills.yaml`](skills.yaml)
- 스킬별 산출물 래퍼: [`scripts/artifact`](scripts/artifact)
