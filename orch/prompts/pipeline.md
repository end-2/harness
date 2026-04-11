# 파이프라인 프롬프트

## 입력

```
파이프라인: {{pipeline_name}}
파이프라인 정의: {{pipeline_definition}}
Run ID: {{run_id}}
산출물 경로: {{output_path}}
재개 모드: {{resume_mode}}
재개 시작점: {{resume_from}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙을 따라 `{{pipeline_definition}}`을 실행하세요.

### Step 1: 파이프라인 로드

`{{pipeline_definition}}`에서 실행할 스킬 목록과 순서를 파악합니다. 사전 정의 파이프라인 흐름은 시스템 프롬프트 **"사전 정의 파이프라인"** 표 참조.

재개 모드(`{{resume_mode}}` = true)인 경우, 시스템 프롬프트 **"체크포인트 및 재개"** 절차에 따라 `{{output_path}}/run.meta.md`에서 상태를 확인하고 `{{resume_from}}`부터 재개합니다.

### Step 2: 각 스킬 실행

시스템 프롬프트 **"에이전트 스폰 프로토콜"** 8단계를 그대로 따릅니다. 업스트림 입력은 시스템 프롬프트 **"업스트림 입력 조립"** 표에 정의된 소비 스킬별 전달 데이터만 선별합니다.

### Step 3: 병렬 실행

`parallel: true` 그룹은 동시에 에이전트를 스폰합니다. 실패 처리는 시스템 프롬프트 **"오류 처리"** 규칙을 따릅니다.

### Step 4: 상태 업데이트

시스템 프롬프트 **"상태 관리"**에 정의된 전이(`running` → `dialogue` → `completed` / `failed`)를 run 에이전트에 위임합니다.

### Step 5: 대화 릴레이

스킬이 `needs_user_input`을 반환하면 시스템 프롬프트 **"대화 릴레이 통합"** 절차에 따라 relay 에이전트에 위임합니다.

### Step 6: 완료 문서 생성

모든 스킬 완료 후 시스템 프롬프트 **"완료 문서 생성"** 절차에 따라 `project-structure.md`, `release-note.md`를 생성하고 run 에이전트에 최종 정리를 위임합니다.

### Step 7: 결과 출력

시스템 프롬프트 **"출력"** 스키마(`pipeline_result`)에 `{{pipeline_name}}`과 `{{run_id}}`를 채워 출력합니다.

시스템 프롬프트 **"출력 프로토콜"**에 따라 `meta.json`/`body.md`에 기록합니다.
