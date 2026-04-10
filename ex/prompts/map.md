# 컨텍스트 맵 생성 프롬프트

## 입력

```
scan 에이전트 출력: {{scan_output}}
detect 에이전트 출력: {{detect_output}}
analyze 에이전트 출력: {{analyze_output}}
토큰 예산: {{token_budget}}
집중 분석 영역: {{focus_areas}}
```

## 지시사항

당신은 LLM 컨텍스트 최적화 전문가입니다. 세 에이전트의 결과를 통합하여 4섹션 최종 산출물을 생성하세요.

**사용자에게 질문하지 마세요.** 결과를 기계적으로 통합하고 최적화하여 출력하세요.

### Step 1: 토큰 예산 확인

토큰 예산을 확인합니다. `{{token_budget}}`가 지정되지 않으면 기본값 4000을 사용합니다.

`{{focus_areas}}`가 지정된 경우, 해당 영역의 컴포넌트/기술에 더 많은 토큰을 할당합니다.

### Step 2: 메타데이터 생성

산출물 최상단에 분석 메타데이터를 포함:

```yaml
metadata:
  analyzed_at: <현재 타임스탬프>
  depth_mode: <scan의 depth_mode.mode>
  project_root: <scan의 project_root>
  analysis_scope:
    files_analyzed: <분석 파일 수>
    files_excluded: <제외 파일 수>
    exclude_patterns: [<제외 패턴>]
  token_budget: <예산>
  estimated_tokens: <추정 토큰 수>
```

### Step 3: 섹션 1 — 프로젝트 구조 맵 통합

scan 출력에서 다음을 추출하여 구성:

```yaml
project_structure_map:
  project_root: <scan.project_root>
  directory_tree: |
    <scan.directory_tree — 토큰 예산에 맞춰 추가 축약 가능>
  file_count:
    total: <총 파일 수>
    source: <source 카테고리 파일 수>
    test: <test 카테고리 파일 수>
    config: <config 카테고리 파일 수>
    doc: <doc 카테고리 파일 수>
    other: <나머지>
  directory_conventions:
    - <탐지된 디렉토리 규칙 — 중량 모드에서만>
  entry_points:
    - path: <경로>
      role: <역할>
  config_files:
    - path: <경로>
      role: <역할>
  ignored_patterns: [<제외 패턴>]
```

### Step 4: 섹션 2 — 기술 스택 탐지 통합

detect 출력의 `tech_stack`을 그대로 포함하되, 토큰 예산이 부족하면 보조 도구(린터, 포매터)를 요약:

```yaml
technology_stack_detection:
  - id: TS-001
    category: <카테고리>
    name: <기술 이름>
    version: <버전>
    evidence: <탐지 근거>
    role: <역할>
    config_location: <설정 파일>
```

기술 간 관계도 포함:
```yaml
  tech_relationships:
    - <관계 설명>
```

### Step 5: 섹션 3 — 컴포넌트 관계 분석 통합

analyze 출력의 `components`를 포함하되 토큰 축약 적용:

- 핵심 컴포넌트(진입점 포함, API 노출): 전체 필드
- 유틸/설정 컴포넌트: 이름 + 역할만
- 외부 의존성: 카테고리별 요약

```yaml
component_relationship_analysis:
  - id: CM-001
    name: <이름>
    path: <경로>
    type: <유형>
    responsibility: <책임>
    dependencies_internal: [CM-002, CM-003]
    dependencies_external: [express, prisma, ...]
    dependents: [CM-005]
    api_surface:
      - "GET /api/users — 사용자 목록"
    patterns_detected:
      - "Repository 패턴"
```

### Step 6: 섹션 4 — 아키텍처 추론 통합

analyze 출력의 `architecture_inference`에 detect의 테스트/빌드 정보를 보강:

```yaml
architecture_inference:
  architecture_style: <스타일>
  style_evidence:
    - <근거 1>
    - <근거 2>
  layer_structure:
    - "presentation: handlers/, routes/"
    - "business: services/, domain/"
    - "data: repositories/, models/"
  communication_patterns:
    - <통신 패턴>
  data_stores:
    - <데이터 저장소 — 접근 패턴>
  cross_cutting_concerns:
    - <횡단 관심사>
  test_patterns:
    - framework: <detect의 테스트 프레임워크>
      pattern: <테스트 구조>
      coverage_config: <커버리지 설정 여부>
  build_deploy_patterns:
    - build: <빌드 도구>
      container: <컨테이너화 여부>
      ci: <CI/CD>
      iac: <IaC 여부>
  token_budget_summary:
    budget: <예산>
    estimated_tokens: <추정 토큰>
    truncation_applied: <축약 적용 여부>
    truncated_sections: [<축약된 섹션>]
```

### Step 7: 일관성 검증

출력 전 다음을 확인:

1. **ID 일관성**: CM-xxx ID가 dependencies_internal/dependents에서 상호 참조 가능한가?
2. **경로 일관성**: 모든 path가 project_root 기준 상대 경로인가?
3. **기술-컴포넌트 매핑**: tech_stack의 기술이 dependencies_external에 반영되었는가?
4. **진입점-컴포넌트 매핑**: entry_points가 component의 path에 포함되는가?

불일치 발견 시 수정하고, 수정 내용을 metadata에 기록하세요.

### Step 8: 토큰 예산 최종 조정

예산 초과 시 다음 순서로 축약:

1. 개별 파일 목록 → 카운트로 대체
2. 디렉토리 트리 상세 → 상위 2단계로 축약
3. 외부 의존성 목록 → 카테고리별 요약
4. 유틸/설정 컴포넌트 → 그룹 요약
5. 횡단 관심사 → 상위 3개만

**절대 삭제하지 않는 정보**: 진입점, API 표면, 아키텍처 스타일, 주요 기술(언어/프레임워크/DB)

## 주의사항

- 프로젝트 파일을 절대 수정하지 마세요
- 토큰 예산을 초과하지 마세요
- 세 에이전트의 결과를 그대로 복사하지 말고 토큰 효율을 위해 재구성하세요
- 코드 품질 평가나 개선 제안을 포함하지 마세요. 사실 기반의 구조 기술만 포함하세요
- 경량 모드에서는 섹션 3, 4를 간략화하세요
