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

시스템 프롬프트에 정의된 역할과 규칙에 따라 선행 산출물에서 전략을 기계적으로 도출하세요. 사용자에게 질문하지 마세요.

### Step 1: 적응적 깊이 판별

시스템 프롬프트 **"적응적 깊이"** 기준으로 경량/중량 모드를 결정합니다. 경계 영역에서는 의존성 수, NFR 유무 등 산출물 복잡도를 근거로 판단합니다.

### Step 2: 테스트 범위 도출

1. `requirements_spec`의 모든 FR/NFR을 순회하며 `priority: Won't`는 제외 대상으로 기록
2. 나머지 항목의 `acceptance_criteria` 개수를 합산하여 총 테스트 케이스 볼륨 추정
3. `constraints`의 `type: regulatory`를 컴플라이언스 테스트 대상으로, `type: technical`을 환경 매트릭스에 반영

### Step 3: 테스트 피라미드 결정

`architecture_decisions`의 아키텍처 패턴을 식별하여 시스템 프롬프트 **"테스트 피라미드 비율 자동 결정"** 표에 따라 비율을 배정합니다. 혼합 패턴인 경우 주요 패턴의 비율을 기준으로 조정합니다.

### Step 4: 우선순위 매트릭스 생성

`requirements_spec`의 각 요구사항에 대해 시스템 프롬프트 **"RE 산출물 해석 → 테스트 범위 자동 도출"**의 MoSCoW 규칙에 따라 테스트 깊이를 결정하고, 다음 설계 기법 매핑을 적용합니다:

| MoSCoW | 설계 기법 |
|--------|----------|
| Must | 경계값, 동등분할, 상태전이 |
| Should | 동등분할, 결정테이블 |
| Could | 동등분할 |
| Won't | — |

### Step 5: NFR 테스트 계획

`quality_attribute_priorities`의 각 항목에 대해:

1. `metric` 문자열에서 정량 기준 추출 (예: "200ms", "99.5%", "100명")
2. 기준에 맞는 테스트 유형 결정 (성능/부하/스트레스/보안/가용성)
3. 테스트 시나리오 설계 (부하 수준, 측정 방법, 임계값)

### Step 6: 테스트 더블 전략

`component_structure.dependencies`와 `code_structure.external_dependencies`를 분석하여 시스템 프롬프트 **"테스트 더블 전략 수립"** 표에 따라 각 의존성에 더블 유형을 배정합니다.

### Step 7: 테스트 환경 매트릭스

`constraints`에서 환경 관련 제약(브라우저, OS, 디바이스 등)을 추출합니다. `flexibility: hard`인 제약은 필수 테스트 환경으로 지정합니다.

### Step 8: 품질 게이트 기준

시스템 프롬프트 **"품질 게이트 기준 자동 설정"** 기본값을 적용하되, RE 산출물의 `metric`에 구체적 수치가 있으면 해당 값을 사용합니다.

### Step 9: 산출물 정리

시스템 프롬프트 **"출력 형식 → 테스트 전략"** YAML 스키마에 맞춰 `TSTR-001` 형식으로 구조화합니다. 각 결정에 `re_refs`와 `arch_refs`를 포함하여 근거를 명시하고, **"출력 프로토콜"**에 따라 `meta.json`/`body.md`에 기록합니다.

## 주의사항

- 선행 산출물에 명시되지 않은 가정을 세우지 마세요
- 경량 모드에서는 NFR 테스트 계획, 테스트 환경 매트릭스를 생략할 수 있습니다
- 모든 결정에 근거(re_refs, arch_refs)를 포함하세요
