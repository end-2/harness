# Harness

소프트웨어 공학의 정수를 AI 스킬로 구현한 모노레포입니다.

## 개요

Harness는 소프트웨어 개발 생명주기(SDLC) 전 영역에 걸친 AI 스킬 컬렉션입니다. 각 스킬은 해당 영역의 전문 지식을 기반으로 코드 생성, 리뷰, 분석, 가이드 등의 역할을 수행하며, Claude Code, Codex, Gemini 등 다양한 AI 코딩 도구에서 활용할 수 있습니다.

## 설치

필요한 영역의 스킬을 개별적으로 설치합니다:

```bash
npx skills add re
npx skills add arch
npx skills add impl
npx skills add qa
npx skills add sec
npx skills add devops
npx skills add ex
npx skills add orch
```

모든 스킬을 한번에 설치하려면:

```bash
./scripts/install-all.sh
```

## 스킬 목록

```
harness/
├── re/               # 요구사항 공학
├── arch/             # 소프트웨어 아키텍처
├── impl/             # 구현 및 코딩
├── qa/               # 품질 보증 및 테스팅
├── sec/              # 보안 공학
├── devops/           # 배포, 릴리스, 운영 및 모니터링
├── ex/               # 기존 코드베이스 탐색 및 컨텍스트 추출
└── orch/             # 스킬 오케스트레이션
```

### re — 요구사항 공학

사용자와의 대화형 상호작용을 통해 요구사항을 점진적으로 도출, 분석, 명세, 검증합니다.

| Agent | 설명 |
|-------|------|
| `re:elicit` | 사용자와 multi-turn 대화를 통해 요구사항을 능동적으로 도출 |
| `re:analyze` | 요구사항의 완전성, 일관성, 실현 가능성 분석 및 추가 질문 생성 |
| `re:spec` | 요구사항 명세, 제약 조건, 품질 속성 우선순위로 구성된 명세 문서 생성 |
| `re:review` | 명세 문서의 세 섹션별 리뷰 및 후속 스킬 소비 적합성 검증 |

### arch — 소프트웨어 아키텍처

RE 산출물(요구사항 명세, 제약 조건, 품질 속성 우선순위)을 기반으로 시스템 구조 설계와 기술 의사결정을 수행합니다.

| Agent | 설명 |
|-------|------|
| `arch:design` | RE 산출물 기반 아키텍처 결정, 사용자와의 기술적 맥락 대화를 통해 구조 설계 |
| `arch:review` | design 출력을 RE 품질 속성 메트릭 기반 시나리오로 검증 |
| `arch:adr` | design 과정의 주요 결정을 RE 참조 포함 ADR로 기록 |
| `arch:diagram` | 확정된 설계를 C4, 시퀀스 등 Mermaid 다이어그램으로 시각화 |

### impl — 구현

Arch 산출물(아키텍처 결정, 컴포넌트 구조, 기술 스택, 다이어그램)을 기반으로 설계를 실제 코드로 변환하고, 코드 품질을 검증합니다.

| Agent | 설명 |
|-------|------|
| `impl:generate` | Arch 산출물 기반 코드 스캐폴딩 및 구현, 사용자와의 코드 레벨 맥락 대화를 통해 점진적 구현 |
| `impl:review` | Arch 결정 준수 여부 + 클린 코드 원칙 두 축으로 코드 리뷰 |
| `impl:refactor` | 코드 스멜 탐지 및 Arch 경계를 존중하는 안전한 리팩토링 |
| `impl:pattern` | generate 과정에서 식별된 패턴 적용 기회를 평가하고 Arch 결정 연계하여 적용 |

### qa — 품질 보증

RE/Arch/Impl 산출물을 기반으로 테스트 전략 수립, 테스트 코드 생성, 요구사항 추적 매트릭스(RTM) 생성, 품질 검증을 수행합니다. 모든 테스트는 RE 요구사항까지 역추적 가능합니다.

| Agent | 설명 |
|-------|------|
| `qa:strategy` | RE/Arch/Impl 산출물 분석 기반 테스트 전략 수립, 사용자와의 대화로 테스트 투자 범위 및 품질 게이트 합의 |
| `qa:generate` | acceptance_criteria → 테스트 케이스 변환, 단위/통합/E2E/계약/NFR 테스트 코드 생성 (re_refs 추적성 내장) |
| `qa:review` | 요구사항 커버리지 검증 및 RTM 생성, 테스트 강도 평가, 커버리지 갭 발견 시 generate 재호출 |
| `qa:report` | RE metric 대비 품질 현황 종합, 품질 게이트 판정(pass/fail), 잔여 리스크 식별 |

### sec — 보안

Arch/Impl 산출물을 기반으로 보안 취약점 분석, 위협 모델링, 보안 코드 리뷰, 표준 준수 검증을 수행합니다. 설계와 구현이 보안적으로 안전한지를 검증하며, 모든 보안 산출물은 원천 아키텍처 결정과 요구사항까지 역추적 가능합니다.

| Agent | 설명 |
|-------|------|
| `sec:threat-model` | Arch 산출물 기반 신뢰 경계/공격 표면 자동 도출, 사용자와의 도메인 맥락 대화를 통한 STRIDE 위협 분석 및 DREAD 우선순위 평가 |
| `sec:audit` | Impl 산출물 기반 OWASP Top 10 취약점 자동 탐지, CWE 분류, CVSS 점수 산정, 의존성 CVE 스캔 |
| `sec:review` | 위협 모델 대응 전략의 코드 구현 검증, 인증/인가/입력 검증/세션 관리 등 보안 로직 심층 리뷰 |
| `sec:compliance` | threat-model + audit + review 결과를 OWASP ASVS/PCI DSS/GDPR 등 표준 항목에 매핑, 통합 보안 권고 생성 |

### devops — 배포 및 운영

Arch/Impl 산출물과 RE 품질 속성을 기반으로 인프라, CI/CD 파이프라인, 관찰 가능성을 자동 생성합니다. Deploy → Observe 피드백 루프를 단일 스킬 내에서 연결합니다.

| Agent | 설명 |
|-------|------|
| `devops:slo` | RE 품질 속성 메트릭 → SLI/SLO 변환, 전체 DevOps 파이프라인의 관찰 기준점 수립 |
| `devops:iac` | Arch 컴포넌트 구조 → IaC 모듈 자동 생성 |
| `devops:pipeline` | Impl 코드 구조 + IaC → CI/CD 파이프라인 자동 생성 |
| `devops:strategy` | SLO + Arch 결정 기반 배포 방식/롤백 절차 자동 결정 |
| `devops:monitor` | SLO → 알림 규칙/대시보드/분산 추적 자동 생성 |
| `devops:log` | Arch 컴포넌트 + 보안 제약 → 로깅 표준/설정 자동 생성 |
| `devops:incident` | 배포 전략 + 모니터링 설정 → 인시던트 대응 런북 자동 생성 |
| `devops:review` | 전체 산출물 통합 리뷰, Deploy-Observe 피드백 루프 완전성 검증 |

### ex — 코드베이스 탐색

기존 프로젝트의 코드베이스를 자동 분석하여, LLM 컨텍스트 윈도우에 최적화된 프로젝트 맵을 생성합니다. 순방향 스킬(re, arch)이 "무엇을 어떻게 만들 것인가"를 결정한다면, ex는 역방향으로 "이미 존재하는 코드가 무엇인가"를 추출하여 후속 스킬의 입력으로 주입합니다. 프로젝트 루트 경로만으로 자동 실행되며, 복잡도에 따라 경량/중량 모드로 적응적 분석을 수행합니다.

| Agent | 설명 |
|-------|------|
| `ex:scan` | 디렉토리 구조 스캔, 파일 분류, 진입점 식별, 복잡도 기반 경량/중량 모드 자동 결정 |
| `ex:detect` | 매니페스트/설정 파일 분석 기반 언어/프레임워크/DB/빌드/CI 기술 스택 자동 탐지 및 탐지 근거 기록 |
| `ex:analyze` | import 분석 기반 모듈 의존성 그래프 구축, 컴포넌트 경계 추론, API 표면 식별, 아키텍처 스타일 추론 |
| `ex:map` | scan/detect/analyze 결과를 토큰 예산 내에서 4섹션(구조 맵/기술 스택/컴포넌트 관계/아키텍처 추론) 산출물로 통합 |

### orch — 스킬 오케스트레이션

모든 스킬(re, arch, impl, qa, sec, devops)의 실행을 조율하는 컨트롤 플레인입니다. 사용자는 항상 orch을 통해 통신하며, 개별 스킬을 직접 호출하지 않습니다.

| Agent | 설명 |
|-------|------|
| `orch:dispatch` | 사용자의 유일한 진입점. 자연어 요청을 분석하여 스킬 또는 파이프라인으로 라우팅 |
| `orch:pipeline` | DAG 기반 워크플로 실행, 스킬 간 흐름 제어 (순차/병렬/조건부 분기) |
| `orch:relay` | 실행 중인 스킬 에이전트와 사용자 간의 멀티턴 대화 중계 |
| `orch:run` | 실행(run) 생명주기 관리, 산출물 디렉토리 생성/관리, 상태 추적, 재개 지원 |
| `orch:config` | 스킬 설정, 에이전트 규칙, 파이프라인 템플릿 관리 |
| `orch:status` | 실행 이력 조회, 스킬 상태 확인, 산출물 검색 |

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
