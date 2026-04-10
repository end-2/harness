# 대화 릴레이 예시

## 시나리오

arch:design 에이전트가 기술 스택 선택에 대해 사용자와 대화하는 과정입니다.

---

## Turn 1: 에이전트 → 사용자

### 에이전트의 needs_user_input

```markdown
## needs_user_input
- skill: "arch:design"
- turn: 1
- questions:
    - id: "q1"
      text: "백엔드 프레임워크를 선택해주세요."
      context: "실시간 WebSocket 지원이 핵심이며, 팀의 기술 역량도 고려해야 합니다."
      type: choice
      options: ["Node.js (Express/Fastify)", "Go (Gin/Fiber)", "Java (Spring Boot)", "Python (FastAPI)"]
      default: "Node.js (Express/Fastify)"
    - id: "q2"
      text: "데이터베이스 전략을 선택해주세요."
      context: "채팅 메시지 저장은 쓰기 성능이 중요하며, 사용자 데이터는 관계형이 적합합니다."
      type: choice
      options: ["PostgreSQL + Redis", "MongoDB + Redis", "PostgreSQL + MongoDB + Redis"]
      default: "PostgreSQL + Redis"
    - id: "q3"
      text: "메시지 브로커가 필요한가요?"
      context: "1만 명 동시 접속 시 서버 간 메시지 동기화를 위해 메시지 브로커를 권장합니다."
      type: confirmation
      default: "yes"
- partial_output:
    architecture_style: "이벤트 기반 마이크로서비스"
    layers: ["API Gateway", "Chat Service", "User Service", "Notification Service"]
```

### relay 변환 → 사용자에게 전달

```
[arch:design — 아키텍처 설계 (1/2 턴)]

요구사항을 바탕으로 아키텍처를 설계하고 있습니다. 기술 스택을 결정해야 합니다.

1. 백엔드 프레임워크를 선택해주세요.
   → 실시간 WebSocket 지원이 핵심이며, 팀 역량도 고려됩니다.
   [a] Node.js (Express/Fastify)  [b] Go (Gin/Fiber)  [c] Java (Spring Boot)  [d] Python (FastAPI)
   (기본값: Node.js)

2. 데이터베이스 전략을 선택해주세요.
   → 채팅 메시지는 쓰기 성능, 사용자 데이터는 관계형이 적합합니다.
   [a] PostgreSQL + Redis  [b] MongoDB + Redis  [c] PostgreSQL + MongoDB + Redis
   (기본값: PostgreSQL + Redis)

3. 메시지 브로커가 필요한가요?
   → 1만 명 동시 접속 시 서버 간 메시지 동기화에 권장됩니다.
   (기본값: 예)

(건너뛰려면 "건너뛰기"라고 답해주세요)
```

### 사용자 응답

```
Node.js로 하고, DB는 PostgreSQL + Redis로 할게. 메시지 브로커는 추천대로.
```

### relay 패키징 → 에이전트에 전달

```markdown
## user_response
- skill: "arch:design"
- turn: 1
- answers:
    - question_id: "q1"
      response: "Node.js (Express/Fastify)"
    - question_id: "q2"
      response: "PostgreSQL + Redis"
    - question_id: "q3"
      response: "__DEFAULT__"
- conversation_summary: "백엔드: Node.js(Express/Fastify), DB: PostgreSQL+Redis, 메시지 브로커: 사용(권장 수용)"
```

---

## Turn 2: 에이전트 → 사용자

### 에이전트의 needs_user_input

```markdown
## needs_user_input
- skill: "arch:design"
- turn: 2
- questions:
    - id: "q4"
      text: "프론트엔드 아키텍처를 확인해주세요."
      context: "웹(React) + 모바일(React Native) 공유 코드 전략이 필요합니다."
      type: confirmation
      default: "yes"
    - id: "q5"
      text: "인증 방식을 선택해주세요."
      context: "채팅 앱의 실시간 연결 인증에 영향을 줍니다."
      type: choice
      options: ["JWT + Refresh Token", "세션 기반", "OAuth 2.0 + JWT"]
      default: "JWT + Refresh Token"
```

### 사용자 응답

```
전부 기본값으로 해줘
```

### relay 매핑

```markdown
## user_response
- skill: "arch:design"
- turn: 2
- answers: "__SKIP_ALL__"
- conversation_summary: "백엔드: Node.js(Express/Fastify), DB: PostgreSQL+Redis, 메시지 브로커: 사용. 프론트엔드: React+React Native(기본값 수용), 인증: JWT+Refresh Token(기본값 수용)"
```

`__SKIP_ALL__`이 아닌 `__DEFAULT__`로 처리할 수도 있지만, "전부 기본값으로"라는 표현은 모든 질문을 건너뛰는 의도이므로 `__SKIP_ALL__`로 매핑합니다. 에이전트는 각 질문의 default 값을 사용합니다.

---

## Turn 2 이후: 에이전트 complete

```markdown
## complete
- skill: "arch:design"
- total_turns: 2
- output_sections: [architecture_decisions, component_structure, technology_stack, diagrams]
```
