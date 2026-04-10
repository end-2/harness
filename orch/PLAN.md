# Orch (Orchestration) Skill 구현 계획

## 개요

모든 스킬(re, arch, impl, qa, sec, devops)의 실행을 조율하는 **컨트롤 플레인**입니다.
사용자는 항상 이 orchestration을 통해 통신하며, 개별 스킬을 직접 호출하지 않습니다.

**핵심 책임**:
- 사용자 요청을 분석하여 적절한 스킬/파이프라인으로 라우팅
- 에이전트를 통한 스킬 실행 및 흐름 제어 (순차/병렬)
- 실행(run)별 산출물 디렉토리 관리 및 저장 위치 지정
- 스킬 에이전트의 사용자 개입 요청을 중계 (relay)
- 에이전트 규칙(rule) 관리 및 산출물(output) 검증/저장
- 중단된 실행의 재개(resume) 지원
- 파이프라인 완료 후 프로젝트 구조 문서 및 릴리스 노트 자동 생성

## 목표 구조

```
orch/
├── skills.yaml
├── agents/
│   ├── dispatch.md
│   ├── pipeline.md
│   ├── relay.md
│   ├── run.md
│   ├── config.md
│   └── status.md
├── rules/
│   ├── base.md
│   ├── output-format.md
│   ├── escalation-protocol.md
│   └── dialogue-protocol.md
├── pipelines/
│   ├── full-sdlc.md
│   ├── new-feature.md
│   ├── security-gate.md
│   └── quick-review.md
├── prompts/
│   ├── dispatch.md
│   ├── pipeline.md
│   ├── relay.md
│   ├── run.md
│   ├── config.md
│   └── status.md
└── examples/
    ├── full-run-example.md
    ├── dialogue-relay-example.md
    ├── escalation-example.md
    └── resume-example.md
```

---

## 산출물 디렉토리 구조

각 실행(run)은 독립된 디렉토리에 산출물을 저장합니다.
사용자는 출력 루트 경로를 지정할 수 있습니다 (기본값: `./harness-output/`).

```
<output-root>/
└── runs/
    └── <run-id>/                           # 형식: YYYYMMDD-HHmmss-<4자리-해시>
        ├── run.meta.md                     # 실행 메타데이터, 파이프라인 상태
        ├── project-structure.md            # 프로젝트 구조 문서 (완료 시 생성)
        ├── release-note.md                 # 릴리스 노트 (완료 시 생성)
        ├── re/
        │   ├── requirements_spec.md
        │   ├── constraints.md
        │   └── quality_attribute_priorities.md
        ├── arch/
        │   ├── architecture_decisions.md
        │   ├── component_structure.md
        │   ├── technology_stack.md
        │   └── diagrams.md
        ├── impl/
        │   ├── implementation_map.md
        │   ├── code_structure.md
        │   ├── implementation_decisions.md
        │   └── implementation_guide.md
        ├── qa/
        │   ├── test_strategy.md
        │   ├── test_suite.md
        │   ├── requirements_traceability_matrix.md
        │   └── quality_report.md
        ├── sec/
        │   ├── threat_model.md
        │   ├── vulnerability_report.md
        │   ├── security_recommendations.md
        │   └── compliance_status.md
        └── devops/
            ├── pipeline_config.md
            ├── infrastructure_code.md
            ├── observability_config.md
            └── operational_runbooks.md
```

### `run.meta.md` 스키마

```markdown
# Run: <run-id>

## Configuration
- Pipeline: <파이프라인명>
- Output root: <산출물 루트 경로>
- Created: <ISO 8601 타임스탬프>
- Status: <pending | running | paused | completed | failed>

## Pipeline Status
| Step | Skill | Status | Started | Completed | Output |
|------|-------|--------|---------|-----------|--------|
| 1 | re:elicit | completed | 14:30:25 | 14:35:12 | re/ |
| 2 | re:spec | completed | 14:35:13 | 14:36:45 | re/ |
| 3 | arch:design | running | 14:36:46 | - | - |
| 4 | impl:generate | pending | - | - | - |
| 5 | [qa:generate, sec:audit, devops:pipeline] | pending | - | - | - |

## Dialogue History
- re:elicit: 5 turns
- arch:design: 2 turns (진행 중)

## Errors
- (없음)
```

스킬별 상태 값: `pending` | `running` | `dialogue` | `completed` | `failed`

---

## 에이전트 정의

### 1. `dispatch.md` — 디스패치 에이전트

- **역할**: 사용자의 유일한 진입점. 자연어 요청을 분석하여 스킬 또는 파이프라인으로 라우팅
- **핵심 역량**:
  - 자연어 의도 분석 및 스킬/에이전트 매핑
  - 복합 요청의 다중 스킬 분해 → 파이프라인 정의 생성
  - 선행 조건 검증 (예: arch:design 실행 전 RE 산출물 존재 여부 확인)
  - 기존 실행(run) 재개 요청 인식 및 라우팅
  - 컨텍스트 기반 라우팅 (현재 작업 단계 고려)
- **입력**: 사용자 자연어 요청, 현재 run 상태 (재개 시)
- **출력**: 파이프라인 정의 (스킬 목록 + 실행 순서 + 병렬 그룹) 또는 단일 스킬 호출 지시

### 2. `pipeline.md` — 파이프라인 에이전트

- **역할**: DAG 기반 워크플로 실행, 스킬 간 흐름 제어
- **핵심 역량**:
  - 순차 실행, 병렬 실행, 조건부 분기 지원
  - 각 스킬을 에이전트로 스폰하여 실행 (스폰 프로토콜 준수)
  - 대화형 스킬의 `needs_user_input` 신호 감지 → relay 에이전트에 위임
  - 자동 실행 스킬의 예외 에스컬레이션 처리
  - 스킬 완료 시 run 에이전트에 산출물 검증/저장 위임
  - 체크포인트 기록 및 재개 지원
  - 병렬 실행: 의존성 없는 스킬들을 동시에 에이전트 생성하여 병렬 처리
  - 파이프라인 완료 후 프로젝트 문서 생성 트리거
- **에이전트 스폰 프로토콜**:
  ```
  각 스킬 단계마다:
  1. 스킬 시스템 프롬프트 로드: <skill>/agents/<agent>.md
  2. 기본 규칙 로드: orchestration/rules/base.md
  3. 산출물 형식 규칙 로드: orchestration/rules/output-format.md
  4. 업스트림 입력 조립: runs/<run-id>/<prev-skill>/*.md
     (각 스킬이 실제로 소비하는 섹션만 전달 — 전체 업스트림 아님)
  5. 전체 프롬프트 조립 = 기본 규칙 + 스킬 프롬프트 + 업스트림 데이터 + 출력 위치
  6. Agent 도구로 에이전트 스폰
  7. 에이전트 출력 수신
  8. needs_user_input 포함 시 → relay 에이전트에 위임
  9. complete 시 → run 에이전트에 검증/저장 위임
  ```
- **사전 정의 파이프라인**:
  - `full-sdlc`: re:elicit → re:analyze → re:spec → arch:design → impl:generate → [qa:generate, sec:audit, devops:pipeline] (병렬)
  - `new-feature`: re:elicit → re:spec → arch:design → impl:generate → qa:generate
  - `security-gate`: sec:threat-model → sec:audit → sec:compliance
  - `quick-review`: re:review → arch:review → impl:review
- **입력**: 파이프라인 정의 (dispatch 출력), run-id, 산출물 경로
- **출력**: 각 스킬 실행 결과 집계, 전체 워크플로 요약

### 3. `relay.md` — 릴레이 에이전트 (신규)

- **역할**: 실행 중인 스킬 에이전트와 사용자 간의 멀티턴 대화 중계
- **핵심 역량**:
  - 스킬 에이전트의 구조화된 질문(`needs_user_input`)을 사람이 읽기 좋은 형태로 변환
  - 사용자 응답 수집 및 대화 컨텍스트와 함께 패키징
  - 패키징된 응답을 스킬 에이전트에 재전달
  - 대화 이력 관리 (요약 유지 — 전체 원본이 아닌 요약본 전달)
  - 사용자의 "건너뛰기" 또는 "기본값 수용" 의사 인식
  - 자동 실행 스킬의 예외 에스컬레이션도 동일하게 처리
- **대화 프로토콜**:

  **스킬 에이전트 → orchestration**:
  ```markdown
  ## needs_user_input
  - skill: "re:elicit"
  - turn: 3
  - questions:
    - id: "q1"
      text: "예상 동시 접속자 수는 얼마인가요?"
      context: "확장성 관련 아키텍처 결정에 영향을 줍니다."
      type: open          # open | choice | confirmation
    - id: "q2"
      text: "인증 방식을 선택해주세요."
      type: choice
      options: ["OAuth 2.0", "JWT", "세션 기반"]
  - partial_output: { ... }
  ```

  **orchestration → 스킬 에이전트**:
  ```markdown
  ## user_response
  - skill: "re:elicit"
  - turn: 3
  - answers:
    - question_id: "q1"
      response: "피크 시 약 10,000명"
    - question_id: "q2"
      response: "OAuth 2.0"
  - conversation_summary: "... (이전 대화 요약) ..."
  ```

- **입력**: 스킬 에이전트의 `needs_user_input` 신호
- **출력**: 사용자 응답이 포함된 `user_response` 패키지

### 4. `run.md` — 실행 관리 에이전트 (신규)

- **역할**: 실행(run) 생명주기 관리, 산출물 디렉토리 생성/관리, 상태 추적, 재개 지원
- **핵심 역량**:
  - **초기화**: run-id 생성, `<output-root>/runs/<run-id>/` 디렉토리 구조 생성, `run.meta.md` 작성
  - **산출물 저장 위치**: 사용자 설정에서 출력 루트 경로 읽기 (기본: `./harness-output/`)
  - **산출물 검증**: 스킬 완료 시 필수 섹션 존재 여부 검증 (RE=3개, ARCH=4개, IMPL=4개, QA=4개, SEC=4개, DEVOPS=4개)
  - **산출물 저장**: 검증 통과한 산출물을 해당 스킬 디렉토리에 Markdown 파일로 저장
  - **상태 추적**: `run.meta.md`에 각 스킬 상태 실시간 업데이트
  - **재개(resume)**: `run.meta.md`를 읽어 completed 스킬은 건너뛰고 중단 지점부터 재실행
  - **완료 문서 생성**: 파이프라인 완료 후 `project-structure.md`와 `release-note.md` 생성
- **실행 생명주기**:
  ```
  INIT → CONFIGURE → EXECUTE → COLLECT → REPORT
    │        │           │         │         │
    │        │           │         │         └─ 프로젝트 구조/릴리스 노트 생성 + 최종 요약
    │        │           │         └─ 산출물 검증 + 저장
    │        │           └─ 스킬 실행 (대화 릴레이 포함)
    │        └─ 파이프라인 결정, 출력 디렉토리 설정, 규칙 로드
    └─ run 디렉토리 생성, run-id 발급, 메타데이터 기록
  ```
- **입력**: 파이프라인 정의, 출력 설정
- **출력**: run 디렉토리 경로, 상태 업데이트, 완료 보고

### 5. `config.md` — 설정 관리 에이전트

- **역할**: 스킬 설정, 에이전트 규칙, 파이프라인 템플릿 관리
- **핵심 역량**:
  - 설치된 스킬의 활성화/비활성화 관리
  - 스킬별 설정값 조회 및 수정
  - 에이전트 우선순위 및 기본값 관리
  - 산출물 출력 루트 경로 설정
  - 파이프라인 템플릿 관리 (사전 정의 + 사용자 정의)
  - 설정 검증 및 충돌 탐지
  - 프로필 기반 설정 (프로젝트 유형별 사전 설정)
- **입력**: 설정 변경 요청
- **출력**: 설정 변경 결과, 현재 설정 상태

### 6. `status.md` — 현황 조회 에이전트

- **역할**: 실행 이력 조회, 스킬 상태 확인, 산출물 검색
- **핵심 역량**:
  - 설치된 스킬 및 에이전트 목록 조회
  - 각 스킬의 버전 및 상태 확인
  - 실행(run) 이력 및 결과 요약
  - 특정 run의 산출물 내용 조회
  - 스킬 간 의존성 그래프 시각화
  - 사용 통계 및 추천
- **입력**: 조회 조건 (스킬명, run-id, 기간, 상태)
- **출력**: 현황 리포트 (스킬 목록, 상태, 실행 이력, 통계)

---

## 규칙 체계 (`rules/`)

모든 스폰되는 에이전트에 주입되는 행동 규칙입니다.

### `base.md` — 기본 규칙

모든 에이전트에 공통 적용:
- orchestration 실행 내에서 동작하며, 지정된 산출물 형식을 정확히 따름
- 입력 데이터로 해결 불가능한 모호성 발견 시 `needs_user_input` 신호로 에스컬레이션
- 지정된 섹션 외의 산출물 생성 금지
- 업스트림 산출물의 ID를 참조하여 추적성 유지 (예: `FR-001`, `AD-001`)
- 각 산출물 파일에 메타데이터 헤더 포함 (skill, agent, run-id, timestamp)

### `output-format.md` — 산출물 형식 규약

- 모든 산출물은 Markdown(.md) 파일
- 각 섹션은 독립된 파일로 저장
- 스킬의 PLAN.md에 정의된 필드 테이블을 스키마로 사용
- 파일 상단에 메타데이터 블록 포함:
  ```markdown
  ---
  skill: re
  agent: elicit
  run_id: 20260410-143022-a7f3
  timestamp: 2026-04-10T14:35:12+09:00
  upstream_refs: []
  ---
  ```

### `escalation-protocol.md` — 에스컬레이션 규약

- **대화형 스킬** (re:elicit, re:analyze, re:spec, re:review, arch:design, sec:threat-model): 의미 있는 질문 묶음마다 `needs_user_input` 사용
- **자동 실행 스킬** (impl:*, qa:*, sec:audit, sec:review, sec:compliance, devops:*): 예외 조건에서만 `needs_user_input` 사용 (예: 아키텍처 결정이 코드로 실현 불가능한 경우)
- 모든 에스컬레이션에 포함: 질문 텍스트, 맥락(왜 중요한지), 유형(open/choice/confirmation)

### `dialogue-protocol.md` — 대화 프로토콜

`needs_user_input` / `user_response` 신호의 정확한 구조를 정의합니다.
(상세 형식은 relay 에이전트 섹션 참조)

---

## 사전 정의 파이프라인 (`pipelines/`)

각 파이프라인은 독립 파일로 정의되어 pipeline 에이전트가 참조합니다.

### `full-sdlc.md` — 전체 SDLC 파이프라인

```
re:elicit → re:analyze → re:spec → arch:design → impl:generate → [qa:generate, sec:audit, devops:pipeline]
```
- 마지막 3개 스킬은 impl 완료 후 병렬 실행
- 모든 스킬 완료 후 프로젝트 구조 문서 + 릴리스 노트 생성

### `new-feature.md` — 신규 기능 개발 파이프라인

```
re:elicit → re:spec → arch:design → impl:generate → qa:generate
```

### `security-gate.md` — 보안 게이트 파이프라인

```
sec:threat-model → sec:audit → sec:compliance
```

### `quick-review.md` — 빠른 리뷰 파이프라인

```
re:review → arch:review → impl:review
```

---

## 완료 시 문서 생성

파이프라인의 모든 스킬이 완료되면, pipeline 에이전트가 마지막 단계로 다음 문서를 생성합니다:

### `project-structure.md` — 프로젝트 구조 문서

타겟 프로젝트의 전체적인 구조를 사람이 파악할 수 있도록 정리:
- 전체 디렉토리 구조 및 각 모듈/컴포넌트의 역할 설명
- 기술 스택 요약 (arch 산출물 기반)
- 의존성 관계도 (컴포넌트 간, 외부 라이브러리)
- 설정/빌드/실행 가이드 (impl 산출물 기반)

### `release-note.md` — 릴리스 노트

해당 실행의 작업 내역을 사람이 읽을 수 있는 형태로 정리:
- 실행된 스킬 및 각 스킬의 주요 결정 사항 요약
- 요구사항 → 아키텍처 → 구현 간 핵심 추적성 요약
- 품질/보안 검증 결과 요약 (qa, sec 산출물 기반)
- 인프라/배포 구성 요약 (devops 산출물 기반)
- 알려진 제한사항 및 후속 작업 제안

두 문서 모두 `runs/<run-id>/` 루트에 생성됩니다.

---

## 실행 흐름 예시

### 전체 SDLC 파이프라인 (대화 포함)

```
사용자: "실시간 채팅 애플리케이션을 만들고 싶어"

1. DISPATCH: 의도 분석
   → 새 시스템 개발 → full-sdlc 파이프라인 선택
   → 출력: pipeline = [re:elicit, re:analyze, re:spec, arch:design, impl:generate, [qa:generate, sec:audit, devops:pipeline]]

2. RUN: 초기화
   → ./harness-output/runs/20260410-143022-a7f3/ 생성
   → run.meta.md 작성

3. PIPELINE: 실행 시작

   [Step 1] re:elicit (대화형)
   → 에이전트 스폰: base.md + re/agents/elicit.md + 사용자 요청
   → 에이전트 반환: needs_user_input (플랫폼? 사용자 수? ...)
   → RELAY: 사용자에게 질문 전달
   → 사용자: "웹과 모바일, 약 1만 명"
   → RELAY: 응답 패키징 → 에이전트에 재전달
   → ... (반복) ...
   → 에이전트 반환: complete (3개 섹션)
   → RUN: 검증 + runs/<id>/re/ 에 저장

   [Step 2] re:analyze (대화형, 유사 패턴)

   [Step 3] re:spec (대화형, 초안 확인)

   [Step 4] arch:design (대화형)
   → 에이전트 스폰: base.md + arch/agents/design.md + RE 산출물(runs/<id>/re/*.md)
   → 기술 컨텍스트 질문 → relay → 사용자 → relay → 에이전트
   → 완료: 4개 섹션 → RUN 검증/저장

   [Step 5] impl:generate (자동 실행)
   → 에이전트 스폰: base.md + impl/agents/generate.md + Arch 산출물(runs/<id>/arch/*.md)
   → 사용자 개입 없이 완료 (예외 시에만 relay)
   → 4개 섹션 → RUN 검증/저장

   [Step 6] 병렬 실행: qa:generate + sec:audit + devops:pipeline
   → 3개 에이전트 동시 스폰
   → 각각 독립적으로 완료 → RUN 검증/저장

   [Step 7] 완료 문서 생성
   → project-structure.md + release-note.md 생성

4. PIPELINE: 최종 요약을 사용자에게 보고
```

### 실행 재개

```
사용자: "아까 중단된 실행 이어서 해줘"

1. DISPATCH: 재개 요청 인식
   → 최근 미완료 run 검색 → run-id 확인
   → pipeline 에이전트에 재개 모드로 전달

2. PIPELINE: run.meta.md 로드
   → completed 스킬(re:elicit, re:spec) 건너뜀
   → arch:design (dialogue 상태)부터 재실행
   → 이전 산출물은 runs/<id>/ 에서 로드하여 활용
```

---

## 핵심 설계 원칙

1. **단일 진입점**: 사용자는 항상 orchestration을 통해 통신. 개별 스킬 직접 호출 없음
2. **에이전트 기반 실행**: 모든 스킬은 Agent 도구를 통해 에이전트로 스폰되어 실행
3. **실행 격리**: 각 run은 독립된 디렉토리에 산출물 저장. 반복 사용 시 충돌 없음
4. **느슨한 결합**: 각 스킬은 독립적으로 동작 가능하며, orchestration은 조율 역할
5. **자기 기술적 (Self-describing)**: 각 스킬이 자신의 입출력을 명세하여 자동 연결 가능
6. **점진적 복잡성**: 단일 스킬 호출부터 복잡한 파이프라인까지 단계적 사용 가능
7. **관찰 가능성**: 모든 스킬 실행 과정이 `run.meta.md`에 기록되어 추적/디버깅 가능
8. **사용자 개입 중계**: 대화형 스킬의 질문과 자동 실행 스킬의 예외를 통일된 relay 메커니즘으로 전달
9. **재개 가능성**: 중단된 실행을 상태 기반으로 재개 가능

---

## 구현 단계

### 1단계: 규칙 체계 (`rules/`)

- `base.md`: 모든 에이전트 공통 행동 규칙
- `output-format.md`: 산출물 Markdown 형식 계약
- `escalation-protocol.md`: 에스컬레이션 조건 및 방법
- `dialogue-protocol.md`: `needs_user_input` / `user_response` 신호 형식

### 2단계: 핵심 에이전트 (`agents/`)

- `run.md`: 실행 생명주기, 디렉토리 생성, 산출물 검증/저장
- `relay.md`: 사용자 대화 중계
- `pipeline.md`: DAG 실행, 에이전트 스폰, relay 통합, 병렬 실행
- `dispatch.md`: 의도 분석, 라우팅

### 3단계: 설정 및 현황 에이전트

- `config.md`: 설정 관리 (출력 경로, 스킬 활성화, 파이프라인 템플릿)
- `status.md`: 실행 이력 및 현황 조회

### 4단계: 파이프라인 템플릿 (`pipelines/`)

- `full-sdlc.md`, `new-feature.md`, `security-gate.md`, `quick-review.md`

### 5단계: 프롬프트 및 예시

- `prompts/`: 각 에이전트별 프롬프트 템플릿
- `examples/`: 전체 실행, 대화 릴레이, 에스컬레이션, 재개 예시

### 6단계: 스킬 메타데이터 (`skills.yaml`)

- 스킬 이름, 버전, 설명
- 에이전트 목록 및 역할 정의
- 의존하는 모든 하위 스킬 목록
- 파이프라인 실행 엔진 설정
- 라우팅 규칙 설정 스키마
