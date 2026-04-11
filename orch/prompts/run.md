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

시스템 프롬프트에 정의된 역할과 생명주기를 따라 `{{action}}`을 처리하세요. 전체 생명주기 흐름은 시스템 프롬프트 **"실행 생명주기"** 참조.

### Action: init (초기화)

시스템 프롬프트 **"초기화 (INIT)"** 절차에 따릅니다:

1. run-id 생성 (`YYYYMMDD-HHmmss-<4자리 해시>`)
2. `{{output_root}}/runs/<run-id>/` 및 `{{pipeline_name}}`에 포함된 스킬별 하위 디렉토리 생성
3. `run.meta.md` 작성 — 스키마는 시스템 프롬프트 **"`run.meta.md` 스키마"** 참조
4. `current-run.md` 갱신 — 스키마는 시스템 프롬프트 **"`current-run.md` 스키마"** 참조

### Action: update_status (상태 업데이트)

시스템 프롬프트 **"상태 추적"**에 따라 `run.meta.md`의 Pipeline Status 테이블과 `current-run.md`를 동기화합니다. `dialogue` 상태인 경우 `user_action_needed: true`로 설정합니다.

### Action: validate_and_save (산출물 검증/저장)

시스템 프롬프트 **"산출물 검증"** 표(스킬별 필수 산출물)와 **"산출물 저장"** 경로 규칙에 따라 `{{skill_output}}`를 검증하고 `{{output_root}}/runs/{{run_id}}/{{skill_info}}/`에 저장합니다. 검증 실패는 `run.meta.md`의 Errors에 기록합니다.

### Action: generate_docs (완료 문서 생성)

시스템 프롬프트 **"완료 문서 생성 (REPORT)"** 절차에 따라 `project-structure.md`와 `release-note.md`를 `{{output_root}}/runs/{{run_id}}/` 루트에 생성합니다.

### Action: cleanup (정리)

시스템 프롬프트 **"정리 (CLEANUP)"** 절차에 따라 `run.meta.md`의 Status를 `completed`로, `current-run.md`를 idle 상태로 갱신하며 `last_completed_run`에 `{{run_id}}`를 기록합니다.

### Action: resume (재개 정보 로드)

시스템 프롬프트 **"재개 (Resume)"** 절차에 따라 `current-run.md`에서 활성 run-id를 확인하고, `run.meta.md`에서 파이프라인 상태를 로드하여 중단 지점과 기존 산출물 경로 목록을 반환합니다.

시스템 프롬프트 **"출력 프로토콜"**에 따라 `meta.json`/`body.md`에 기록합니다.
