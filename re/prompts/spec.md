# 요구사항 명세 프롬프트

## 입력

```yaml
정제된 요구사항: {{refined_requirements}}        # YAML 배열
검증된 제약 조건: {{validated_constraints}}       # YAML 배열
품질 속성 트레이드오프: {{quality_tradeoffs}}     # YAML 배열
사용자 의사결정 결과: {{user_decisions}}           # YAML 배열
```

## 실행 절차

### Step 1: 명세 모드 판별

입력의 복잡도를 평가하여 명세 모드를 결정하세요:

**경량 모드 조건** (모두 해당):
- 요구사항 7개 이하
- 단일 기능 또는 단순 CRUD
- 제약 조건 3개 이하

**중량 모드 조건** (하나라도 해당):
- 요구사항 8개 이상
- 다수의 하위 시스템
- 복잡한 비기능 요구사항
- 규제/컴플라이언스 요구사항 존재

판별 결과를 사용자에게 제시하세요:
```
분석 결과, 요구사항 {{count}}개, 제약 조건 {{count}}개로 [경량/중량] 모드가 적합합니다.
다른 모드를 원하시면 말씀해주세요.
```

### Step 2: 요구사항 명세 작성 (섹션 1)

각 요구사항을 다음 YAML 형식으로 구조화하세요:

```yaml
- id: FR-001
  category: functional/<subcategory>
  title: <제목>
  description: <상세 설명>
  priority: Must | Should | Could | Won't
  acceptance_criteria:
    - <검증 가능한 기준 1>
    - <검증 가능한 기준 2>
  source: <도출 근거>
  dependencies: [<의존 요구사항 ID>]
```

**체크리스트**:
- [ ] 모든 요구사항에 고유 ID가 부여되었는가
- [ ] acceptance_criteria가 검증 가능한가 (정량적 기준 포함)
- [ ] priority가 MoSCoW 중 하나인가
- [ ] dependencies가 유효한 ID를 참조하는가
- [ ] source가 명확한가

### Step 3: 제약 조건 작성 (섹션 2)

각 제약 조건을 다음 YAML 형식으로 구조화하세요:

```yaml
- id: CON-001
  type: technical | business | regulatory | environmental
  title: <제목>
  description: <상세 설명>
  rationale: <제약 존재 이유>
  impact: <위반 시 영향 범위>
  flexibility: hard | soft | negotiable
```

**체크리스트**:
- [ ] 모든 제약에 유형이 분류되었는가
- [ ] rationale이 충분한가
- [ ] flexibility가 적절한가
- [ ] 요구사항 구현을 불가능하게 하는 제약은 없는가

### Step 4: 품질 속성 우선순위 작성 (섹션 3)

품질 속성을 다음 YAML 형식으로 우선순위를 부여하세요:

```yaml
- attribute: <속성명>
  priority: <순위 (1이 가장 높음)>
  description: <이 프로젝트에서의 구체적 의미>
  metric: <측정 가능한 목표치>
  trade_off_notes: <다른 속성과의 트레이드오프>
```

**체크리스트**:
- [ ] metric이 정량적이고 측정 가능한가
- [ ] 우선순위 간 동률이 없는가 (동률 시 사용자에게 질문하여 해소)
- [ ] trade_off_notes가 실질적인 트레이드오프를 설명하는가
- [ ] NFR의 metric과 일관성이 있는가

### Step 5: 제외 항목 작성

Won't 항목 및 의도적으로 제외된 범위를 다음 형식으로 기록하세요:

```yaml
- id: <원래 ID 또는 신규 부여>
  title: <제목>
  reason: <제외 사유>
  reconsider_trigger: <향후 재검토 조건>
```

### Step 6: 초안 리뷰 요청

네 섹션의 초안을 사용자에게 제시하고 피드백을 요청하세요:

```
[섹션 1: 요구사항 명세]
...

[섹션 2: 제약 조건]
...

[섹션 3: 품질 속성 우선순위]
...

[제외 항목]
...

확인해주실 사항:
1. 빠지거나 잘못된 요구사항이 있나요?
2. 우선순위(MoSCoW)가 적절한가요?
3. acceptance_criteria가 충분히 구체적인가요?
4. 제약 조건의 유연성(hard/soft/negotiable) 분류가 맞나요?
5. 품질 속성 우선순위 순서에 동의하시나요?
6. 제외 항목에 동의하시나요?
```

### Step 7: 피드백 반영 및 최종 확인

사용자 피드백을 반영하여 수정한 후, 최종 확인을 요청하세요.
