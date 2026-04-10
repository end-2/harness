# 산출물 형식 규약 (Output Format Rules)

모든 스킬 에이전트가 생성하는 산출물의 형식을 정의합니다.

---

## 1. 파일 형식

- 모든 산출물은 **Markdown(.md)** 파일입니다
- 각 섹션은 **독립된 파일**로 저장됩니다
- 파일명은 스킬의 `skills.yaml`에 정의된 output 키를 snake_case로 사용합니다

## 2. 메타데이터 헤더

모든 산출물 파일 상단에 YAML 프론트매터 형식의 메타데이터를 포함합니다:

```markdown
---
skill: <스킬명>
agent: <에이전트명>
run_id: <실행 ID>
timestamp: <ISO 8601 타임스탬프>
upstream_refs: [<참조한 업스트림 산출물 ID 목록>]
---
```

### 필드 설명

| 필드 | 필수 | 설명 | 예시 |
|------|------|------|------|
| skill | O | 스킬 식별자 | `re`, `arch`, `impl`, `ex` |
| agent | O | 에이전트 식별자 | `elicit`, `design`, `scan` |
| run_id | O | 실행 ID | `20260410-143022-a7f3` |
| timestamp | O | 생성 시각 (ISO 8601) | `2026-04-10T14:35:12+09:00` |
| upstream_refs | O | 참조한 업스트림 ID 목록 (없으면 빈 배열) | `[FR-001, FR-003]` |

## 3. 본문 구조

- 메타데이터 헤더 직후에 `# <섹션 제목>`으로 시작합니다
- 스킬의 PLAN.md에 정의된 필드 테이블을 스키마로 사용합니다
- 정의되지 않은 섹션을 임의로 추가하지 마세요

## 4. ID 체계

각 스킬이 생성하는 항목에는 고유 ID를 부여합니다:

| 스킬 | 접두사 | 예시 |
|------|--------|------|
| ex (구조 스캔) | — | (ID 없음, 파일 경로로 식별) |
| ex (기술 스택) | TS- | TS-001, TS-002 |
| ex (컴포넌트) | CM- | CM-001, CM-002 |
| re (요구사항) | FR-, NFR- | FR-001, NFR-001 |
| re (제약조건) | CON- | CON-001 |
| arch (아키텍처 결정) | AD- | AD-001 |
| arch (컴포넌트) | AC- | AC-001 |
| impl (구현 결정) | ID- | ID-001 |
| qa (테스트 케이스) | TC- | TC-001 |
| sec (위협) | TH- | TH-001 |
| sec (취약점) | VUL- | VUL-001 |
| devops (SLO) | SLO- | SLO-001 |

## 5. 교차 참조

- 다른 스킬의 산출물을 참조할 때는 해당 ID를 정확히 기재합니다
- 형식: `<접두사>-<번호>` (예: `FR-001`, `AD-003`)
- 메타데이터의 `upstream_refs`에도 참조한 ID를 기록합니다

## 6. 저장 경로

```
<output-root>/runs/<run-id>/<skill>/<산출물_파일명>.md
```

예시:
```
./harness-output/runs/20260410-143022-a7f3/re/requirements_spec.md
./harness-output/runs/20260410-143022-a7f3/arch/architecture_decisions.md
./harness-output/runs/20260410-143022-a7f3/ex/project_structure_map.md
```
