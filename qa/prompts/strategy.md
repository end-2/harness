# 테스트 전략 수립 프롬프트

## 입력

```
요구사항 명세: {{requirements_spec}}
제약 조건: {{constraints}}
품질 속성 우선순위: {{quality_attribute_priorities}}
아키텍처 결정: {{architecture_decisions}}
컴포넌트 구조: {{component_structure}}
기술 스택: {{technology_stack}}
다이어그램: {{diagrams}}
구현 맵: {{implementation_map}}
코드 구조: {{code_structure}}
구현 결정: {{implementation_decisions}}
구현 가이드: {{implementation_guide}}
```

## 지시사항

당신은 테스트 전략 수립 전문가입니다. 세 스킬(RE, Arch, Impl)의 산출물을 분석하여 테스트 전략을 자동으로 수립하세요. 사용자에게 질문하지 않고, 모든 결정을 선행 산출물에서 기계적으로 도출합니다.

### Step 1: 적응적 깊이 판별

Impl 산출물의 규모로 경량/중량 모드를 판별하세요:

- `implementation_map` 항목 수 ≤ 5개 **또는** `requirements_spec` 항목 수 ≤ 5개 → **경량 모드**
- `implementation_map` 항목 수 ≥ 10개 **또는** `requirements_spec` 항목 수 ≥ 10개 → **중량 모드**
- 그 사이 → 산출물 복잡도(의존성 수, NFR 유무)를 기준으로 판단

### Step 2: 테스트 범위 도출

`requirements_spec`의 모든 FR/NFR을 순회하며:

1. `priority`가 Won't인 항목은 제외 대상으로 기록
2. 나머지 항목의 `acceptance_criteria` 개수를 합산하여 총 테스트 케이스 볼륨 추정
3. `constraints`에서 `type: regulatory`인 항목을 컴플라이언스 테스트 대상으로 분류
4. `constraints`에서 `type: technical`인 항목을 테스트 환경 매트릭스에 반영

### Step 3: 테스트 피라미드 결정

`architecture_decisions`의 `decision`에서 아키텍처 패턴을 식별하고 피라미드 비율을 결정하세요:

| 패턴 키워드 | 단위 | 통합 | E2E | 계약 | NFR |
|-----------|------|------|-----|------|-----|
| monolith, single | 60% | 25% | 10% | — | 5% |
| layered, layer | 50% | 30% | 15% | — | 5% |
| microservice, distributed | 40% | 25% | 10% | 20% | 5% |
| event-driven, async, message | 40% | 30% | 10% | 15% | 5% |

혼합 패턴인 경우 주요 패턴의 비율을 기준으로 조정하세요.

### Step 4: 우선순위 매트릭스 생성

`requirements_spec`의 각 요구사항에 대해:

| MoSCoW | 테스트 깊이 | 설계 기법 |
|--------|-----------|----------|
| Must | 단위 + 통합 + E2E | 경계값, 동등분할, 상태전이 |
| Should | 단위 + 통합 | 동등분할, 결정테이블 |
| Could | 단위 | 동등분할 |
| Won't | 제외 | — |

### Step 5: NFR 테스트 계획

`quality_attribute_priorities`의 각 항목에 대해:

1. `metric` 문자열에서 정량적 기준 추출 (예: "200ms", "99.5%", "100명")
2. 기준에 맞는 테스트 유형 결정 (성능/부하/스트레스/보안/가용성)
3. 테스트 시나리오 설계 (부하 수준, 측정 방법, 임계값)

### Step 6: 테스트 더블 전략

`component_structure`의 `dependencies`와 `code_structure.external_dependencies`를 분석하여:

1. 외부 API → Mock
2. 데이터베이스 → Fake (인메모리)
3. 메시지 큐 → Stub
4. 인접 컴포넌트 → Spy
5. 시간/랜덤 → Fake

### Step 7: 테스트 환경 매트릭스

`constraints`에서 환경 관련 제약을 추출하여 테스트 환경 조합을 결정하세요:

- 브라우저, OS, 디바이스 등
- `flexibility: hard`인 제약은 필수 테스트 환경

### Step 8: 품질 게이트 기준

기본값을 적용하되, RE 산출물의 metric에서 구체적 수치가 있으면 해당 값을 사용하세요:

- 코드 커버리지: 라인 80% / 분기 70%
- Must 요구사항 커버리지: 100%
- Should 요구사항 커버리지: 80%
- NFR 준수: RE metric 수치
- 테스트 통과율: 100%

### Step 9: 산출물 정리

위 분석 결과를 `TSTR-001` 형식의 테스트 전략으로 구조화하여 출력하세요. 각 결정에 `re_refs`와 `arch_refs`를 포함하여 근거를 명시하세요.

## Chain of Thought 가이드

각 Step을 실행하기 전에 다음 사고 과정을 거치세요:

1. **입력 확인**: "이 Step에서 필요한 선행 산출물 필드는 무엇인가?"
2. **규칙 적용**: "해당 필드에 어떤 매핑 규칙을 적용해야 하는가?"
3. **결정 근거**: "이 결정의 근거가 되는 RE/Arch/Impl 산출물 ID는 무엇인가?"
4. **일관성 검증**: "이전 Step의 결정과 모순되지 않는가?"

예시:
```
[사고 과정]
- architecture_decisions에서 "3-tier 레이어드"를 확인 → 피라미드 비율 테이블의 "레이어드" 행 적용
- 레이어드: 단위 50% / 통합 30% / E2E 15% / NFR 5%
- 근거: AD-001 ("3-tier 레이어드 아키텍처")
- 마이크로서비스 관련 패턴 없음 → 계약 테스트 비율 0%
```

## 주의사항

- 선행 산출물에 명시되지 않은 가정을 세우지 마세요
- 품질 게이트 기준은 기본값을 적용하되, 사용자가 사전에 오버라이드한 경우 그 값을 존중하세요
- 경량 모드에서는 NFR 테스트 계획, 테스트 환경 매트릭스를 생략할 수 있습니다
- 모든 결정에 근거(re_refs, arch_refs)를 포함하세요
