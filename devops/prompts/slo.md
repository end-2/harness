# SLO 정의 프롬프트

## 입력

```
Arch 산출물: {{arch_output}}
Impl 산출물: {{impl_output}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙을 따라 Arch 산출물의 `re_refs`와 `constraint_ref`를 통해 RE 품질 속성 메트릭을 추출하고, 측정 가능한 SLI/SLO로 변환하세요.

### Step 1: RE 품질 속성 메트릭 추출

Arch 산출물에서 다음 경로로 RE 품질 속성을 간접 참조합니다:

- `architecture_decisions[].re_refs` → `QA:performance`, `QA:availability` 등
- `technology_stack[].constraint_ref` → `CON-xxx`
- `component_structure[].re_refs` → `FR-xxx`, `NFR-xxx`

각 품질 속성의 `metric` 필드를 추출하고 정량적/정성적 여부를 판별합니다.

### Step 2: SLI 변환

시스템 프롬프트 **"RE 품질 속성 → SLI 변환"** 표의 변환 패턴에 따라 각 메트릭을 측정 가능한 SLI로 변환합니다. 정성적 메트릭은 정량적 프록시 지표로 변환을 시도하고, 불가능하면 에스컬레이션합니다.

### Step 3: SLO 목표 설정

시스템 프롬프트 **"SLO 목표 수립"** 절에 따라 각 SLI의 목표치(RE 메트릭 직접 도출), 측정 기간(기본 30일 롤링), 에러 버짓(`1 - target`)을 설정합니다.

### Step 4: 컴포넌트별 SLO 분배

Arch `component_structure.dependencies`를 분석하여 시스템 프롬프트 **"컴포넌트별 SLO 분배"** 규칙(직렬/병렬/크리티컬 경로)을 적용합니다.

### Step 5: 번-레이트 알림 설계

시스템 프롬프트 **"번-레이트 알림"** 표(긴급 14.4x / 경고 6x / 알림 3x, 각 윈도우)에 따라 멀티 윈도우·멀티 번-레이트 알림을 설계합니다.

### Step 6: 에러 버짓 정책

시스템 프롬프트 **"에러 버짓 정책"** 표의 잔량 구간별 운영 정책을 적용합니다.

### Step 7: 산출물 정리

시스템 프롬프트 **"출력 형식"** 표(SLO 정의 / 에러 버짓 정책 / SLA-SLO 매핑)에 맞춰 정리하고, **"출력 프로토콜"**에 따라 `meta.json`/`body.md`에 기록합니다.
