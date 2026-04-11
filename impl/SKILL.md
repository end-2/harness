---
name: impl
description: Arch 산출물을 실제 코드로 변환하고 구현 품질을 검증한다. '코드 생성', '스캐폴딩', '리팩터링', '코드 리뷰', '디자인 패턴 적용' 같은 구현 작업에서 반드시 사용하라. 기존 코드베이스 관용구와 기술 스택의 관행을 준수하며, Arch 결정이 코드 레벨에서 막힐 때만 사용자에게 에스컬레이션한다.
---

# impl — Implementation

## 언제 이 스킬을 사용하는가

Arch 산출물을 실제 코드로 변환하고 구현 품질을 검증한다. '코드 생성', '스캐폴딩', '리팩터링', '코드 리뷰', '디자인 패턴 적용' 같은 구현 작업에서 반드시 사용하라. 기존 코드베이스 관용구와 기술 스택의 관행을 준수하며, Arch 결정이 코드 레벨에서 막힐 때만 사용자에게 에스컬레이션한다.

## 에이전트 구성

이 스킬은 다음 에이전트들로 구성된다. 각 에이전트의 전체 시스템 프롬프트는
`agents/<name>.md`에 있으며, Claude Code subagent 프런트매터가 포함되어 있어
`Task` 도구로 직접 스폰할 수 있다.

| 에이전트 | 역할 |
|---|---|
| [`impl:generate`](agents/generate.md) | Arch 산출물을 기반으로 설계를 실제 코드로 변환 |
| [`impl:pattern`](agents/pattern.md) | generate 과정에서 식별된 패턴 적용 기회를 평가하고 적용 |
| [`impl:refactor`](agents/refactor.md) | 코드 스멜 탐지 및 Arch 경계를 유지하는 안전한 리팩터링 |
| [`impl:review`](agents/review.md) | 생성 코드의 Arch 준수 여부 + 클린 코드 원칙 두 축 리뷰 |

## 파이프라인

기본 실행 순서:

```
generate → pattern → refactor → review
```

상세한 단계별 입출력 계약, 체크포인트, 의존성, 에스컬레이션 조건은
[`skills.yaml`](skills.yaml)에 정의되어 있다. 파이프라인을 오케스트레이션할
때는 반드시 `skills.yaml`을 참조해 upstream/consumers 관계를 맞춰야 한다.

## 산출물 규칙

모든 에이전트 산출물은 `meta.json`(구조화 데이터)과 `body.md`(서술)의 쌍으로
`runs/<run_id>/impl/<agent>[-NN]/` 하위에 생성된다. `meta.json`은 반드시
`scripts/artifact` CLI를 통해서만 조작한다. 본 스킬 디렉터리의
[`scripts/artifact`](scripts/artifact)는 루트 CLI를 감싼 래퍼로, `--skill
impl`을 자동으로 주입한다.

```bash
# 새 산출물 생성 (--skill 자동 주입)
./scripts/artifact init --agent generate --title "예시"

# 본문 경로 획득
./scripts/artifact path impl-generate-01 --run-id <id> --body

# 진행 상태 및 데이터 갱신
./scripts/artifact set impl-generate-01 --run-id <id> \
    --progress review --data-file patch.json
```

`body.md`의 골격은 [`templates/impl/`](../templates/impl/)에 위치한
템플릿에서 생성된다.

## 참고 자료

- 에이전트 시스템 프롬프트: [`agents/`](agents/)
- 프롬프트 템플릿: [`prompts/`](prompts/)
- 입출력 예시: [`examples/`](examples/)
- 파이프라인·의존성 정의: [`skills.yaml`](skills.yaml)
- 스킬별 산출물 래퍼: [`scripts/artifact`](scripts/artifact)
