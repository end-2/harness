# 의존성/아키텍처 분석 입력 예시

> Task Manager API — scan + detect 에이전트 출력을 입력으로 수신

---

## 입력

scan 에이전트의 전체 출력 (`scan-output.md` 참조)과 detect 에이전트의 전체 출력 (`detect-output.md` 참조)이 각각 `{{scan_output}}`과 `{{detect_output}}`으로 전달됩니다.

핵심 참조 포인트:

```yaml
# scan 출력에서 analyze가 주로 참조하는 필드

depth_mode:
  mode: heavyweight  # → 전체 분석 수행

directory_tree: |
  src/
  ├── controllers/  (3 files)
  ├── services/     (3 files)
  ├── repositories/  (2 files)
  ├── middlewares/   (3 files)
  ├── models/       (2 files)
  ├── routes/       (3 files)
  ├── utils/        (2 files)
  ├── types/        (1 file)
  ├── app.ts
  └── server.ts

entry_points:
  - path: src/server.ts
    role: "HTTP 서버 시작점"
  - path: src/app.ts
    role: "Express 애플리케이션 설정"

# detect 출력에서 analyze가 주로 참조하는 필드

tech_stack:
  - TS-001: TypeScript (주 개발 언어)
  - TS-002: Express (REST API 프레임워크)
  - TS-003: Prisma (ORM)
  - TS-004: PostgreSQL (데이터베이스)
```
