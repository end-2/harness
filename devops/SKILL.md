---
name: devops
description: Arch/Impl 산출물과 RE 품질 속성으로 인프라, CI/CD 파이프라인, 관찰 가능성, 운영 런북을 자동 생성한다. 'IaC', 'CI/CD', 'SLO/SLI', '모니터링', '알림', '대시보드', '로그', '배포 전략', '인시던트 런북' 같은 맥락에서 반드시 사용하라. Deploy-Observe 피드백 루프를 단일 스킬 안에서 연결한다.
---

# devops — Deploy & Operate

## 언제 이 스킬을 사용하는가

Arch/Impl 산출물과 RE 품질 속성으로 인프라, CI/CD 파이프라인, 관찰 가능성, 운영 런북을 자동 생성한다. 'IaC', 'CI/CD', 'SLO/SLI', '모니터링', '알림', '대시보드', '로그', '배포 전략', '인시던트 런북' 같은 맥락에서 반드시 사용하라. Deploy-Observe 피드백 루프를 단일 스킬 안에서 연결한다.

## 에이전트 구성

이 스킬은 다음 에이전트들로 구성된다. 각 에이전트의 전체 시스템 프롬프트는
`agents/<name>.md`에 있으며, Claude Code subagent 프런트매터가 포함되어 있어
`Task` 도구로 직접 스폰할 수 있다.

| 에이전트 | 역할 |
|---|---|
| [`devops:slo`](agents/slo.md) | RE 품질 속성 메트릭 → SLI/SLO 변환, 전체 파이프라인의 관찰 기준점 수립 |
| [`devops:iac`](agents/iac.md) | Arch 컴포넌트 구조 + 기술 스택 → IaC 모듈 자동 생성 |
| [`devops:pipeline`](agents/pipeline.md) | Impl 코드 구조 + IaC → CI/CD 파이프라인 자동 생성 |
| [`devops:strategy`](agents/strategy.md) | SLO + Arch 결정 → 배포 방식 / 롤백 절차 자동 결정 |
| [`devops:monitor`](agents/monitor.md) | SLO → 알림 규칙 / 대시보드 / 분산 추적 자동 생성 |
| [`devops:log`](agents/log.md) | Arch 컴포넌트 + 보안 제약 → 로깅 표준 / 설정 자동 생성 |
| [`devops:incident`](agents/incident.md) | 배포 전략 + 모니터링 설정 → 인시던트 대응 런북 자동 생성 |
| [`devops:review`](agents/review.md) | 전체 산출물 통합 리뷰, Deploy-Observe 피드백 루프 완전성 검증 |

## 파이프라인

기본 실행 순서:

```
slo → iac → pipeline → strategy → monitor → log → incident → review
```

상세한 단계별 입출력 계약, 체크포인트, 의존성, 에스컬레이션 조건은
[`skills.yaml`](skills.yaml)에 정의되어 있다. 파이프라인을 오케스트레이션할
때는 반드시 `skills.yaml`을 참조해 upstream/consumers 관계를 맞춰야 한다.

## 산출물 규칙

모든 에이전트 산출물은 `meta.json`(구조화 데이터)과 `body.md`(서술)의 쌍으로
`runs/<run_id>/devops/<agent>[-NN]/` 하위에 생성된다. `meta.json`은 반드시
`scripts/artifact` CLI를 통해서만 조작한다. 본 스킬 디렉터리의
[`scripts/artifact`](scripts/artifact)는 루트 CLI를 감싼 래퍼로, `--skill
devops`을 자동으로 주입한다.

```bash
# 새 산출물 생성 (--skill 자동 주입)
./scripts/artifact init --agent slo --title "예시"

# 본문 경로 획득
./scripts/artifact path devops-slo-01 --run-id <id> --body

# 진행 상태 및 데이터 갱신
./scripts/artifact set devops-slo-01 --run-id <id> \
    --progress review --data-file patch.json
```

`body.md`의 골격은 [`templates/devops/`](../templates/devops/)에 위치한
템플릿에서 생성된다.

## 참고 자료

- 에이전트 시스템 프롬프트: [`agents/`](agents/)
- 프롬프트 템플릿: [`prompts/`](prompts/)
- 입출력 예시: [`examples/`](examples/)
- 파이프라인·의존성 정의: [`skills.yaml`](skills.yaml)
- 스킬별 산출물 래퍼: [`scripts/artifact`](scripts/artifact)
