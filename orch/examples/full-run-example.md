# 전체 SDLC 실행 예시

## 시나리오

사용자가 실시간 채팅 애플리케이션의 개발을 요청합니다.

---

## 실행 흐름

### 1. 사용자 요청

```
"실시간 채팅 애플리케이션을 만들고 싶어"
```

### 2. DISPATCH: 의도 분석

```markdown
## dispatch_result
- action: new_pipeline
- pipeline: full-sdlc
- user_request: "실시간 채팅 애플리케이션을 만들고 싶어"
- project_root: ""
- parameters:
    output_root: "./harness-output/"
```

판단 근거: 새 시스템 개발 요청, 기존 프로젝트 경로 없음 → `full-sdlc`

### 3. RUN: 초기화

```markdown
# Run: 20260410-143022-a7f3

## Configuration
- Pipeline: full-sdlc
- Output root: ./harness-output/
- Created: 2026-04-10T14:30:22+09:00
- Status: running

## Pipeline Status
| Step | Skill | Status | Started | Completed | Output |
|------|-------|--------|---------|-----------|--------|
| 1 | re:elicit | pending | - | - | - |
| 2 | re:analyze | pending | - | - | - |
| 3 | re:spec | pending | - | - | - |
| 4 | arch:design | pending | - | - | - |
| 5 | impl:generate | pending | - | - | - |
| 6a | qa:generate | pending | - | - | - |
| 6b | sec:audit | pending | - | - | - |
| 6c | devops:pipeline | pending | - | - | - |
```

### 4. PIPELINE: Step 1 — re:elicit (대화형)

**에이전트 스폰**:
- 시스템 프롬프트: `re/agents/elicit.md`
- 규칙: `orch/rules/base.md` + `orch/rules/output-format.md`
- 업스트림: 없음 (첫 단계)
- 사용자 요청: "실시간 채팅 애플리케이션을 만들고 싶어"

**Turn 1 — 에이전트 → needs_user_input**:
```markdown
## needs_user_input
- skill: "re:elicit"
- turn: 1
- questions:
    - id: "q1"
      text: "타겟 플랫폼은 무엇인가요?"
      context: "웹, 모바일, 데스크톱에 따라 기술 스택과 아키텍처가 달라집니다."
      type: choice
      options: ["웹만", "모바일만", "웹 + 모바일", "전체 (웹 + 모바일 + 데스크톱)"]
    - id: "q2"
      text: "예상 동시 접속자 수는 얼마인가요?"
      context: "확장성 관련 아키텍처 결정에 영향을 줍니다."
      type: open
    - id: "q3"
      text: "주요 기능 외에 파일 전송, 화상 통화 등의 부가 기능이 필요한가요?"
      context: "기능 범위에 따라 복잡도가 크게 달라집니다."
      type: open
```

**RELAY → 사용자**:
```
[re:elicit — 요구사항 도출 (1/3 턴)]

채팅 애플리케이션의 핵심 방향을 정하기 위해 몇 가지 여쭤볼게요.

1. 타겟 플랫폼은 무엇인가요?
   → 기술 스택과 아키텍처 선택에 영향을 줍니다.
   [a] 웹만  [b] 모바일만  [c] 웹 + 모바일  [d] 전체

2. 예상 동시 접속자 수는 얼마인가요?
   → 확장성 설계에 영향을 줍니다.

3. 파일 전송, 화상 통화 등 부가 기능이 필요한가요?
   → 기능 범위와 복잡도를 결정합니다.

(건너뛰려면 "건너뛰기"라고 답해주세요)
```

**사용자 응답**: "웹과 모바일 둘 다, 피크 시 약 1만 명, 파일 전송은 필요하고 화상은 나중에"

**RELAY → 에이전트**:
```markdown
## user_response
- skill: "re:elicit"
- turn: 1
- answers:
    - question_id: "q1"
      response: "웹 + 모바일"
    - question_id: "q2"
      response: "피크 시 약 10,000명"
    - question_id: "q3"
      response: "파일 전송 필요, 화상 통화는 후속 버전에서"
- conversation_summary: ""
```

**(Turn 2~3 반복 후 완료)**

**에이전트 → complete**:
```markdown
## complete
- skill: "re:elicit"
- total_turns: 3
- output_sections: [requirements_spec, constraints, quality_attribute_priorities]
```

**RUN: 검증 + 저장**:
- `./harness-output/runs/20260410-143022-a7f3/re/requirements_spec.md` ✓
- `./harness-output/runs/20260410-143022-a7f3/re/constraints.md` ✓
- `./harness-output/runs/20260410-143022-a7f3/re/quality_attribute_priorities.md` ✓

### 5. PIPELINE: Step 2~3 — re:analyze, re:spec

(유사 패턴 — 대화형 실행, 산출물 검증/저장)

### 6. PIPELINE: Step 4 — arch:design (대화형)

**에이전트 스폰**:
- 업스트림: `runs/<id>/re/requirements_spec.md`, `runs/<id>/re/constraints.md`
- 기술 스택 선택, 아키텍처 결정을 사용자와 논의

### 7. PIPELINE: Step 5 — impl:generate (자동 실행)

**에이전트 스폰**:
- 업스트림: `runs/<id>/arch/architecture_decisions.md`, `runs/<id>/arch/component_structure.md`
- 사용자 개입 없이 완료

### 8. PIPELINE: Step 6 — 병렬 실행

3개 에이전트 동시 스폰:
- `qa:generate` — 테스트 전략 및 테스트 코드
- `sec:audit` — 위협 모델링, 취약점 분석
- `devops:pipeline` — CI/CD, 인프라 구성

각각 독립적으로 완료 → RUN 검증/저장

### 9. 완료 문서 생성

- `project-structure.md` — 전체 프로젝트 구조 문서
- `release-note.md` — 릴리스 노트

### 10. 정리

```markdown
# Current Run State

## Active Run
- run_id: (none)
- status: idle
- last_completed_run: 20260410-143022-a7f3
- last_updated: 2026-04-10T15:45:30+09:00
```

### 11. 최종 보고

```markdown
## pipeline_result
- pipeline: full-sdlc
- run_id: 20260410-143022-a7f3
- status: completed
- steps_completed: 8
- steps_total: 8
- summary: "실시간 채팅 앱의 요구사항 도출(3턴), 분석, 명세, 아키텍처 설계(WebSocket + React/React Native), 구현 가이드, 테스트/보안/배포 구성을 완료했습니다."
```
