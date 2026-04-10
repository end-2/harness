# 에스컬레이션 예시

## 시나리오

자동 실행 스킬(impl:generate)이 아키텍처 결정을 코드로 실현할 수 없는 예외 상황에서 사용자 개입을 요청합니다.

---

## 상황

- 파이프라인: `full-sdlc`
- 현재 단계: `impl:generate` (자동 실행 스킬)
- arch:design에서 "이벤트 소싱 패턴"을 결정했으나, 선택된 기술 스택(Express.js)에서 네이티브 이벤트 소싱 지원이 부족

## 에이전트의 needs_user_input

```markdown
## needs_user_input
- skill: "impl:generate"
- turn: 1
- questions:
    - id: "q1"
      text: "아키텍처에서 결정된 이벤트 소싱 패턴을 Express.js로 구현하기 어렵습니다. 대안을 선택해주세요."
      context: "Express.js 생태계에는 성숙한 이벤트 소싱 프레임워크가 없습니다. 이벤트 소싱의 핵심 이점(이벤트 재생, 감사 로그)을 부분적으로 구현하거나, 대안 패턴을 사용할 수 있습니다."
      type: choice
      options:
        - "CQRS로 대체 — 이벤트 소싱 없이 명령/조회 분리만 적용"
        - "단순화된 이벤트 로깅 — 이벤트 테이블에 변경 이력만 기록 (재생 불가)"
        - "기술 스택 변경 검토 — NestJS로 전환하여 이벤트 소싱 지원 활용"
      default: "CQRS로 대체 — 이벤트 소싱 없이 명령/조회 분리만 적용"
- partial_output:
    completed_sections: [implementation_map, code_structure]
    blocked_section: implementation_decisions
    reason: "AD-003(이벤트 소싱 패턴)이 현재 기술 스택으로 실현 불가"
```

## relay → 사용자

```
[impl:generate — 구현 생성 (예외 발생)]

⚠ 자동 실행 중 사용자 확인이 필요한 상황이 발생했습니다.

아키텍처에서 결정된 이벤트 소싱 패턴(AD-003)을 Express.js로 구현하기 어렵습니다.
Express.js 생태계에 성숙한 이벤트 소싱 프레임워크가 없기 때문입니다.

1. 대안을 선택해주세요:
   [a] CQRS로 대체 — 이벤트 소싱 없이 명령/조회 분리만 적용
   [b] 단순화된 이벤트 로깅 — 이벤트 테이블에 변경 이력만 기록 (재생 불가)
   [c] 기술 스택 변경 검토 — NestJS로 전환하여 이벤트 소싱 지원 활용
   (기본값: [a] CQRS로 대체)

이미 구현 맵과 코드 구조는 완성되어 있으며, 구현 결정 섹션에서 이 부분이 차단되어 있습니다.
```

## 사용자 응답

```
CQRS로 대체하되, 나중에 이벤트 소싱으로 전환할 수 있도록 인터페이스는 분리해줘
```

## relay → 에이전트

```markdown
## user_response
- skill: "impl:generate"
- turn: 1
- answers:
    - question_id: "q1"
      response: "CQRS로 대체 — 이벤트 소싱 없이 명령/조회 분리만 적용. 단, 이벤트 소싱 전환을 고려하여 인터페이스 분리 필요"
- conversation_summary: "impl:generate 예외 — AD-003 이벤트 소싱을 CQRS로 대체, 향후 전환을 위한 인터페이스 분리 요청"
```

## 에이전트: 이후 처리

에이전트는 사용자의 추가 요구(인터페이스 분리)를 반영하여 구현 결정을 완성합니다. `partial_output`의 `completed_sections`에 이어서 나머지 섹션을 생성합니다.

```markdown
## complete
- skill: "impl:generate"
- total_turns: 1
- output_sections: [implementation_map, code_structure, implementation_decisions, implementation_guide]
```

## 핵심 포인트

1. **자동 실행 스킬도 예외 시 에스컬레이션 가능** — impl:generate는 기본적으로 사용자 개입 없이 동작하지만, 아키텍처 결정이 기술적으로 불가능할 때 에스컬레이션합니다
2. **partial_output 포함** — 에스컬레이션 시점까지의 진행 상황을 명시하여 사용자가 맥락을 파악할 수 있게 합니다
3. **사용자의 추가 조건 반영** — 단순 선택지 외에 사용자가 추가 조건을 부여할 수 있습니다
