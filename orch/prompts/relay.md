# 릴레이 프롬프트

## 입력

```
needs_user_input 신호: {{needs_user_input}}
대화 이력 요약: {{conversation_summary}}
스킬 정보: {{skill_info}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙을 따라 스킬 에이전트와 사용자 간 대화를 중계하세요.

### Step 1: 질문 변환

시스템 프롬프트 **"질문 변환 (스킬 → 사용자)"** 규칙과 **"변환 예시"** 형식에 따라 `{{needs_user_input}}`의 각 질문을 사용자 친화적 한국어로 변환합니다. 예외 에스컬레이션인 경우 시스템 프롬프트 **"예외 에스컬레이션 중계"** 형식을 따릅니다.

헤더에는 `{{skill_info}}`와 진행 턴을 표시합니다.

### Step 2: 사용자 응답 수집

사용자의 자연어 응답을 수신합니다.

### Step 3: 응답 매핑

사용자 응답을 각 질문별로 매핑합니다. 시스템 프롬프트 **"특수 응답 인식"** 표에 따라 `__SKIP__` / `__DEFAULT__` / `__SKIP_ALL__`을 인식합니다. 여러 질문에 한 번에 답한 경우 각각 분리합니다.

### Step 4: 대화 요약 갱신

시스템 프롬프트 **"대화 이력 관리"** 및 **"요약 규칙"**에 따라 `{{conversation_summary}}`에 이번 턴의 핵심 결정사항/선호/제약/건너뛴 항목을 누적 추가합니다.

### Step 5: user_response 패키징

다음 형식으로 스킬 방향 출력을 패키징합니다:

```markdown
## user_response
- skill: "{{skill_info}}"
- turn: <턴 번호>
- answers:
    - question_id: "<id>"
      response: "<응답>"
- conversation_summary: "<갱신된 대화 요약>"
```

시스템 프롬프트 **"출력 프로토콜"**에 따라 `meta.json`/`body.md`에 기록합니다.
