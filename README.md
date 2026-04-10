# Harness

소프트웨어 공학의 정수를 AI 스킬로 구현한 모노레포입니다.

## 개요

Harness는 소프트웨어 개발 생명주기(SDLC) 전 영역에 걸친 AI 스킬 컬렉션입니다. 각 스킬은 해당 영역의 전문 지식을 기반으로 코드 생성, 리뷰, 분석, 가이드 등의 역할을 수행하며, Claude Code, Codex, Gemini 등 다양한 AI 코딩 도구에서 활용할 수 있습니다.

## 설치

필요한 영역의 스킬을 개별적으로 설치합니다:

```bash
npx skills add requirements
npx skills add architecture
npx skills add implementation
npx skills add qa
npx skills add security
npx skills add deployment
npx skills add operation
npx skills add management
```

모든 스킬을 한번에 설치하려면:

```bash
./scripts/install-all.sh
```

## 스킬 목록

```
harness/
├── requirements/     # 요구사항 공학
├── architecture/     # 소프트웨어 아키텍처
├── implementation/   # 구현 및 코딩
├── qa/               # 품질 보증 및 테스팅
├── security/         # 보안 공학
├── deployment/       # 배포 및 릴리스
├── operation/        # 운영 및 모니터링
├── management/       # 프로젝트 관리
└── orchestration/    # 스킬 오케스트레이션
```

### requirements — 요구사항 공학

요구사항의 도출, 분석, 명세, 검증을 수행합니다.

| Agent | 설명 |
|-------|------|
| `requirements:elicit` | 이해관계자 요구를 구조화된 요구사항으로 도출 |
| `requirements:analyze` | 요구사항의 완전성, 일관성, 실현 가능성 분석 |
| `requirements:spec` | 기능/비기능 요구사항 명세서 생성 |
| `requirements:review` | 요구사항 문서 리뷰 및 개선점 피드백 |

### architecture — 소프트웨어 아키텍처

시스템 구조 설계와 기술 의사결정을 지원합니다.

| Agent | 설명 |
|-------|------|
| `architecture:design` | 아키텍처 패턴 선정 및 구조 설계 |
| `architecture:review` | 기존 아키텍처의 품질 속성 및 트레이드오프 분석 |
| `architecture:adr` | Architecture Decision Record 생성 |
| `architecture:diagram` | 아키텍처 다이어그램 생성 (C4, UML 등) |

### implementation — 구현

코드 작성, 리뷰, 리팩토링을 수행합니다.

| Agent | 설명 |
|-------|------|
| `implementation:generate` | 설계 기반 코드 스캐폴딩 및 구현 |
| `implementation:review` | 클린 코드 원칙 기반 코드 리뷰 |
| `implementation:refactor` | 코드 스멜 탐지 및 리팩토링 제안 |
| `implementation:pattern` | 적절한 디자인 패턴 추천 및 적용 |

### qa — 품질 보증

테스트 전략 수립과 품질 검증을 수행합니다.

| Agent | 설명 |
|-------|------|
| `qa:strategy` | 테스트 전략 및 계획 수립 |
| `qa:generate` | 단위/통합/E2E 테스트 코드 생성 |
| `qa:review` | 테스트 커버리지 분석 및 테스트 리뷰 |
| `qa:metric` | 코드 품질 지표 측정 및 리포트 |

### security — 보안

보안 취약점 분석과 보안 설계를 지원합니다.

| Agent | 설명 |
|-------|------|
| `security:audit` | 코드 보안 취약점 정적 분석 |
| `security:threat-model` | 위협 모델링 수행 (STRIDE 등) |
| `security:review` | 인증/인가, 입력 검증 등 보안 코드 리뷰 |
| `security:compliance` | OWASP Top 10 등 보안 표준 준수 검증 |

### deployment — 배포

CI/CD 파이프라인 구성과 배포 전략을 지원합니다.

| Agent | 설명 |
|-------|------|
| `deployment:pipeline` | CI/CD 파이프라인 설정 파일 생성 |
| `deployment:strategy` | 배포 전략 수립 (블루/그린, 카나리 등) |
| `deployment:iac` | Infrastructure as Code 작성 |
| `deployment:review` | 배포 설정 리뷰 및 최적화 |

### operation — 운영

시스템 운영과 관찰 가능성을 지원합니다.

| Agent | 설명 |
|-------|------|
| `operation:monitor` | 모니터링 및 알림 설정 생성 |
| `operation:incident` | 인시던트 대응 런북 생성 |
| `operation:log` | 로깅 전략 수립 및 로그 분석 |
| `operation:slo` | SLI/SLO/SLA 정의 및 관리 |

### management — 프로젝트 관리

프로젝트 계획, 리스크 관리, 팀 운영을 지원합니다.

| Agent | 설명 |
|-------|------|
| `management:plan` | 프로젝트 계획 및 일정 수립 |
| `management:risk` | 리스크 식별, 분석, 대응 전략 |
| `management:retrospective` | 회고 진행 및 개선 항목 도출 |
| `management:report` | 프로젝트 현황 리포트 생성 |

### orchestration — 스킬 오케스트레이션

개별 스킬의 실행을 조율하고 워크플로를 관리하는 컨트롤 플레인입니다.

| Agent | 설명 |
|-------|------|
| `orchestration:pipeline` | 여러 스킬을 순차/병렬로 조합하여 워크플로 실행 |
| `orchestration:dispatch` | 사용자 요청을 분석하여 적절한 스킬과 에이전트로 라우팅 |
| `orchestration:config` | 스킬 설정, 활성화/비활성화, 우선순위 관리 |
| `orchestration:status` | 설치된 스킬 현황 조회 및 실행 결과 집계 |

## 스킬 내부 구조

각 스킬은 다음 표준 구조를 따릅니다:

```
<skill>/
├── skills.yaml          # 스킬 메타데이터 및 설정
├── agents/              # 에이전트 정의
│   ├── <role>.md        # 역할별 시스템 프롬프트
│   └── ...
├── prompts/             # 프롬프트 템플릿
│   ├── <action>.md      # 작업별 프롬프트
│   └── ...
└── examples/            # 입출력 예시
    └── ...
```

## 호환성

| AI 도구 | 지원 |
|---------|------|
| Claude Code | ✅ |
| OpenAI Codex | ✅ |
| Gemini | ✅ |

## 라이선스

MIT
