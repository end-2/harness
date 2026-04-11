# 위협 모델링 프롬프트

## 입력

```
아키텍처 결정: {{architecture_decisions}}
컴포넌트 구조: {{component_structure}}
기술 스택: {{technology_stack}}
다이어그램: {{diagrams}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙을 따라 Arch 산출물 4섹션을 분석하여 아키텍처 레벨의 보안 위협을 식별하고, 사용자와의 대화를 통해 도메인 맥락을 확보한 뒤, STRIDE 기반 위협 모델을 수립하세요.

### Step 1: 적응적 깊이 판별

시스템 프롬프트 **"적응적 깊이"** 절의 경량/중량 모드 판별 기준을 `component_structure`와 인터페이스 개수에 적용하여 모드를 결정합니다.

### Step 2: 신뢰 경계 자동 도출

시스템 프롬프트 **"Arch 산출물 → 보안 모델 변환 규칙 → 컴포넌트 구조 → 신뢰 경계 도출"** 표에 따라 `component_structure`에서 신뢰 경계를 자동 도출합니다. 각 경계에 대해 `components_inside`와 `components_outside`를 명시합니다.

### Step 3: 공격 표면 카탈로그 생성

시스템 프롬프트 **"컴포넌트 인터페이스 → 공격 표면 도출"** 표에 따라 `component_structure.interfaces`에서 공격 표면을 도출합니다. 또한 시스템 프롬프트 **"기술 스택 → 알려진 취약점 패턴 매핑"** 및 **"다이어그램 → 보안 분석 기초"** 표를 활용하여 추가 공격 표면을 식별합니다.

분석 결과를 사용자에게 제시하세요:

```
Arch 산출물 보안 분석 결과:
- 컴포넌트: {{count}}개 (gateway: {{count}}, service: {{count}}, store: {{count}})
- 외부 인터페이스: {{count}}개
- → [경량/중량] 모드로 진행합니다

자동 도출된 신뢰 경계:
1. TB-001: {{name}} — [{{inside}}] ↔ [{{outside}}]
...

식별된 공격 표면:
1. {{component}}.{{interface}} ({{protocol}}) — {{attack_surface_description}}
...
```

### Step 4: 도메인 맥락 질문

시스템 프롬프트 **"도메인 맥락 대화 → 반드시 확인할 보안 맥락"** 및 **"대화 규칙"** 에 따라 보안 맥락을 한 번에 3-4개 질문으로 확보합니다. RE `constraint_ref`로 이미 파악된 규제 제약은 재질문하지 않습니다. 사용자가 불명확한 답변을 한 경우 보수적 가정을 적용하고 명시합니다:

```
[보수적 가정] 데이터 민감도가 불명확하므로, 모든 사용자 데이터를 'confidential'로 분류합니다.
```

### Step 5: STRIDE 위협 분석

시스템 프롬프트 **"STRIDE 방법론 적용"** 절에 따라 분석을 수행합니다:

- **경량 모드**: 시스템 전체 수준에서 STRIDE 6개 카테고리를 적용하여 상위 5개 위협 도출
- **중량 모드**: 컴포넌트별 / 데이터 흐름별 / 신뢰 경계별 세 축에서 체계적으로 적용

또한 시스템 프롬프트 **"아키텍처 결정 → 보안 함의 분석"** 표를 참고하여 `architecture_decisions`의 패턴별 보안 함의를 위협 도출에 반영합니다.

각 위협의 DREAD 점수는 시스템 프롬프트 **"DREAD 점수 산정 기준"** 표에 따라 산정하고, 총점으로 `risk_level`을 결정합니다. 산출물 스키마는 시스템 프롬프트 **"산출물 구조 → 1. 위협 모델"** 을 따릅니다 (초안에서는 `mitigation_status: unmitigated`).

### Step 6: 위협 분석 초안 제시

위협 목록을 `risk_level` 내림차순으로 정렬하여 사용자에게 제시하세요:

```
STRIDE 위협 분석 초안:

[Critical]
- TM-001: {{title}} (DREAD: {{total}}) — {{mitigation}}

[High]
- TM-002: {{title}} (DREAD: {{total}}) — {{mitigation}}

[Medium]
...

확인해주세요:
1. 데이터 민감도 분류가 정확한가요?
2. 위협 행위자 프로파일이 현실적인가요?
3. 대응 전략 중 수정이 필요한 항목이 있나요?
4. 추가로 고려해야 할 위협이 있나요?
```

### Step 7: 데이터 흐름 보안 분류

각 컴포넌트 간 데이터 흐름에 대해 `data_classification` (`public | internal | confidential | restricted`)과 `protection_required`를 결정합니다. 스키마는 시스템 프롬프트 **"산출물 구조 → 3. 데이터 흐름 보안 분류"** 참조.

데이터 분류 기준:
- **restricted**: PII, PHI, 금융 데이터, 자격 증명
- **confidential**: 비즈니스 민감 데이터, 내부 API 키
- **internal**: 내부 운영 데이터, 로그
- **public**: 공개 가능한 데이터

### Step 8: 공격 트리 생성 (중량 모드)

`risk_level: critical` 또는 `high`인 위협에 대해 시스템 프롬프트 **"산출물 구조 → 4. 공격 트리"** 스키마에 따라 Mermaid 공격 트리를 생성합니다.

### Step 9: 대응 전략 확인 및 확정

사용자 피드백을 반영하여 최종 위협 모델을 확정하세요. 리스크 수용(`accepted`) 항목은 사용자의 명시적 동의를 확보하고, 설계에 반영된 항목의 `mitigation_status`를 `mitigated`/`partial`로 갱신합니다.

출력은 시스템 프롬프트 **"출력 프로토콜"** 에 따라 `meta.json`/`body.md`에 기록합니다.
