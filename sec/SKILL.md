---
name: sec
description: Arch/Impl 산출물 기반으로 위협 모델링, 코드 보안 감사, 보안 리뷰, 표준 준수 검증을 수행한다. 'STRIDE', '공격 표면', 'OWASP', 'CVE 스캔', '보안 리뷰', '컴플라이언스' 같은 보안 맥락에서 반드시 사용하라. 모든 보안 산출물은 원천 아키텍처 결정과 요구사항까지 역추적 가능하다.
---

# sec — Security Engineering

## 언제 이 스킬을 사용하는가

Arch/Impl 산출물 기반으로 위협 모델링, 코드 보안 감사, 보안 리뷰, 표준 준수 검증을 수행한다. 'STRIDE', '공격 표면', 'OWASP', 'CVE 스캔', '보안 리뷰', '컴플라이언스' 같은 보안 맥락에서 반드시 사용하라. 모든 보안 산출물은 원천 아키텍처 결정과 요구사항까지 역추적 가능하다.

## 에이전트 구성

이 스킬은 다음 에이전트들로 구성된다. 각 에이전트의 전체 시스템 프롬프트는
`agents/<name>.md`에 있으며, Claude Code subagent 프런트매터가 포함되어 있어
`Task` 도구로 직접 스폰할 수 있다.

| 에이전트 | 역할 |
|---|---|
| [`sec:threat-model`](agents/threat-model.md) | Arch 산출물 기반 신뢰 경계/공격 표면 도출, STRIDE 위협 분석, DREAD 우선순위 평가 |
| [`sec:audit`](agents/audit.md) | Impl 산출물 기반 OWASP Top 10 자동 탐지, CWE 분류, CVSS 점수, 의존성 CVE 스캔 |
| [`sec:review`](agents/review.md) | 위협 모델 대응 전략의 코드 구현 검증, 인증/인가/입력 검증/세션 관리 심층 리뷰 |
| [`sec:compliance`](agents/compliance.md) | threat-model + audit + review 결과를 ASVS/PCI DSS/GDPR 등 표준 항목에 매핑 |

## 파이프라인

기본 실행 순서:

```
threat-model → audit → review → compliance
```

상세한 단계별 입출력 계약, 체크포인트, 의존성, 에스컬레이션 조건은
[`skills.yaml`](skills.yaml)에 정의되어 있다. 파이프라인을 오케스트레이션할
때는 반드시 `skills.yaml`을 참조해 upstream/consumers 관계를 맞춰야 한다.

## 산출물 규칙

모든 에이전트 산출물은 `meta.json`(구조화 데이터)과 `body.md`(서술)의 쌍으로
`runs/<run_id>/sec/<agent>[-NN]/` 하위에 생성된다. `meta.json`은 반드시
`scripts/artifact` CLI를 통해서만 조작한다. 본 스킬 디렉터리의
[`scripts/artifact`](scripts/artifact)는 루트 CLI를 감싼 래퍼로, `--skill
sec`을 자동으로 주입한다.

```bash
# 새 산출물 생성 (--skill 자동 주입)
./scripts/artifact init --agent threat-model --title "예시"

# 본문 경로 획득
./scripts/artifact path sec-threat-model-01 --run-id <id> --body

# 진행 상태 및 데이터 갱신
./scripts/artifact set sec-threat-model-01 --run-id <id> \
    --progress review --data-file patch.json
```

`body.md`의 골격은 [`templates/sec/`](../templates/sec/)에 위치한
템플릿에서 생성된다.

## 참고 자료

- 에이전트 시스템 프롬프트: [`agents/`](agents/)
- 프롬프트 템플릿: [`prompts/`](prompts/)
- 입출력 예시: [`examples/`](examples/)
- 파이프라인·의존성 정의: [`skills.yaml`](skills.yaml)
- 스킬별 산출물 래퍼: [`scripts/artifact`](scripts/artifact)
