# {{title}}

> {{skill}}/{{agent}} · `{{artifact_id}}` · run `{{run_id}}`

구조화 데이터(상태, 승인, 참조, 데이터 페이로드)는 동일 디렉터리의
`meta.json`에 저장됩니다. 본 문서는 서술/근거/다이어그램 등
사람이 읽는 맥락만 포함합니다.

---

## 구성 맥락

_TBD_

## 적용 값

_TBD_

## 변경 이력

_TBD_

## 검증 결과

_TBD_


---

## 메타데이터 메모

- 진행 상태와 승인 결과는 `scripts/artifact set`로 갱신합니다.
- 구조화 산출물은 `scripts/artifact set --data-file patch.json`으로 기록합니다.
- 이 본문(`body.md`)에는 machine-readable 데이터를 중복 복사하지 않습니다.
