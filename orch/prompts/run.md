# 실행 관리 프롬프트

## 입력

```
액션: {{action}}
파이프라인: {{pipeline_name}}
출력 루트: {{output_root}}
Run ID: {{run_id}}
스킬 산출물: {{skill_output}}
스킬 정보: {{skill_info}}
```

## 지시사항

당신은 실행(run)의 생명주기 관리자입니다. 요청된 액션에 따라 실행을 관리하세요.

### Action: init (초기화)

새 실행을 초기화합니다:

1. **run-id 생성**: 현재 시각 기반 `YYYYMMDD-HHmmss-<4자리 해시>`
2. **디렉토리 생성**: 
   ```
   {{output_root}}/runs/<run-id>/
   ```
   파이프라인에 포함된 스킬별 하위 디렉토리도 생성
3. **run.meta.md 작성**:
   ```markdown
   # Run: <run-id>
   
   ## Configuration
   - Pipeline: {{pipeline_name}}
   - Output root: {{output_root}}
   - Created: <ISO 8601>
   - Status: running
   
   ## Pipeline Status
   | Step | Skill | Status | Started | Completed | Output |
   |------|-------|--------|---------|-----------|--------|
   (파이프라인 단계별 초기 행 — 모두 pending)
   
   ## Dialogue History
   (없음)
   
   ## Errors
   (없음)
   ```
4. **current-run.md 갱신**:
   ```markdown
   # Current Run State
   
   ## Active Run
   - run_id: <run-id>
   - pipeline: {{pipeline_name}}
   - status: running
   - current_step: <첫 번째 스킬>
   - current_step_status: running
   - last_updated: <ISO 8601>
   
   ## Quick Context
   - completed: []
   - pending: [<전체 스킬 목록>]
   - user_action_needed: false
   ```

### Action: update_status (상태 업데이트)

스킬 상태를 업데이트합니다:

1. `run.meta.md`의 Pipeline Status 테이블에서 해당 스킬의 상태 갱신
2. `current-run.md` 동기화 — current_step, completed, pending 목록 갱신
3. `dialogue` 상태인 경우 `user_action_needed: true` 설정

### Action: validate_and_save (산출물 검증/저장)

`{{skill_output}}`를 검증하고 저장합니다:

1. **필수 섹션 검증**: 해당 스킬의 필수 파일이 모두 있는지 확인
2. **메타데이터 검증**: 각 파일에 프론트매터 헤더가 있는지 확인
3. **저장**: `{{output_root}}/runs/{{run_id}}/{{skill_info}}/` 에 각 파일 저장
4. 검증 실패 시: 오류를 `run.meta.md`의 Errors에 기록

### Action: generate_docs (완료 문서 생성)

파이프라인 완료 후 문서를 생성합니다:

1. **project-structure.md**: 전체 산출물을 종합한 프로젝트 구조 문서
2. **release-note.md**: 작업 내역 릴리스 노트
3. 두 파일을 `{{output_root}}/runs/{{run_id}}/` 루트에 저장

### Action: cleanup (정리)

실행 완료 후 정리합니다:

1. `run.meta.md`의 Status를 `completed`로 갱신
2. `current-run.md`를 idle 상태로 갱신:
   ```markdown
   ## Active Run
   - run_id: (none)
   - status: idle
   - last_completed_run: {{run_id}}
   - last_updated: <ISO 8601>
   ```

### Action: resume (재개 정보 로드)

중단된 실행의 재개 정보를 로드합니다:

1. `current-run.md`에서 활성 run-id 확인
2. `run.meta.md`에서 상세 파이프라인 상태 로드
3. 중단 지점(running/dialogue 상태의 스킬) 식별
4. 기존 산출물 경로 목록 반환
