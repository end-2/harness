# 대화 프로토콜 (Dialogue Protocol)

스킬 에이전트와 사용자 간의 멀티턴 대화에서 사용되는 `needs_user_input` / `user_response` 신호의 정확한 구조를 정의합니다.

---

## 1. 스킬 에이전트 → Orchestration: `needs_user_input`

스킬 에이전트가 사용자 입력이 필요할 때 반환하는 구조화된 신호입니다.

```markdown
## needs_user_input
- skill: "<스킬명>:<에이전트명>"
- turn: <대화 턴 번호 (1부터 시작)>
- questions:
    - id: "<q1>"
      text: "<사람이 읽을 수 있는 질문>"
      context: "<왜 이 정보가 필요한지 — 어떤 결정에 영향을 주는지>"
      type: open
    - id: "<q2>"
      text: "<선택형 질문>"
      type: choice
      options: ["옵션 A", "옵션 B", "옵션 C"]
      default: "옵션 A"
    - id: "<q3>"
      text: "<확인 질문>"
      type: confirmation
      default: "yes"
- partial_output: { <현재까지의 부분 산출물 — 생략 가능> }
```

### 필드 규칙

| 필드 | 필수 | 설명 |
|------|------|------|
| skill | O | `<스킬명>:<에이전트명>` 형식 |
| turn | O | 해당 스킬 에이전트 내 대화 턴 번호 (1부터 증가) |
| questions | O | 질문 배열 (1개 이상) |
| questions[].id | O | 질문 고유 ID (해당 턴 내에서 유일) |
| questions[].text | O | 사람이 읽을 수 있는 질문 텍스트 |
| questions[].context | O | 질문의 맥락 — 왜 필요한지 |
| questions[].type | O | `open`, `choice`, `confirmation` 중 하나 |
| questions[].options | choice만 | 선택지 배열 |
| questions[].default | 선택 | 기본값 제안 |
| partial_output | 선택 | 현재까지 생성된 부분 산출물 |

## 2. Orchestration → 스킬 에이전트: `user_response`

relay 에이전트가 사용자 응답을 수집하여 스킬 에이전트에 재전달하는 구조입니다.

```markdown
## user_response
- skill: "<스킬명>:<에이전트명>"
- turn: <응답하는 턴 번호 — needs_user_input의 turn과 일치>
- answers:
    - question_id: "<q1>"
      response: "<사용자의 자유 텍스트 응답>"
    - question_id: "<q2>"
      response: "<선택한 옵션>"
    - question_id: "<q3>"
      response: "yes"
- conversation_summary: "<이전 턴들의 대화 요약 — relay가 관리>"
```

### 필드 규칙

| 필드 | 필수 | 설명 |
|------|------|------|
| skill | O | `<스킬명>:<에이전트명>` 형식 |
| turn | O | 응답 대상 턴 번호 |
| answers | O | 응답 배열 |
| answers[].question_id | O | `needs_user_input`의 질문 ID와 일치 |
| answers[].response | O | 사용자의 응답 텍스트 |
| conversation_summary | O | 이전 턴들의 누적 대화 요약 (첫 턴이면 빈 문자열) |

## 3. 특수 응답

사용자가 질문에 직접 답하지 않는 경우의 처리:

### 건너뛰기 (Skip)

```markdown
- answers:
    - question_id: "q1"
      response: "__SKIP__"
```

스킬 에이전트는 건너뛴 질문에 대해 합리적인 기본값을 사용하거나, 해당 정보 없이 진행합니다.

### 기본값 수용 (Accept Defaults)

```markdown
- answers:
    - question_id: "q1"
      response: "__DEFAULT__"
```

스킬 에이전트는 `default` 필드에 제안한 값을 사용합니다.

### 전체 건너뛰기

```markdown
- answers: "__SKIP_ALL__"
```

모든 질문을 건너뛰고, 스킬 에이전트는 최선의 판단으로 진행합니다.

## 4. 완료 신호

스킬 에이전트가 더 이상 사용자 입력이 필요 없고 산출물을 완성했을 때:

```markdown
## complete
- skill: "<스킬명>:<에이전트명>"
- total_turns: <총 대화 턴 수>
- output_sections: [<생성된 산출물 섹션 목록>]
```

이 신호를 받으면 pipeline 에이전트는 run 에이전트에 산출물 검증/저장을 위임합니다.

## 5. 대화 이력 관리

- relay 에이전트가 `conversation_summary`를 관리합니다
- 전체 원본 대화가 아닌 **요약본**을 전달합니다
- 요약에는 핵심 결정사항과 사용자의 선호/제약만 포함합니다
- 턴이 누적될수록 이전 턴의 요약은 더 간결해집니다
