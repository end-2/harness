# 기술 스택 탐지 입력 예시

> Task Manager API — scan 에이전트 출력을 입력으로 수신

---

## 입력

scan 에이전트의 전체 출력 (`scan-output.md` 참조)이 `{{scan_output}}`으로 전달됩니다.

핵심 참조 포인트:

```yaml
# scan 출력에서 detect가 주로 참조하는 필드

config_files:
  - path: package.json
    category: package
  - path: tsconfig.json
    category: build
  - path: jest.config.ts
    category: test
  - path: .eslintrc.json
    category: lint
  - path: .prettierrc
    category: lint
  - path: prisma/schema.prisma
    category: other
  - path: Dockerfile
    category: container
  - path: docker-compose.yml
    category: container
  - path: .github/workflows/ci.yml
    category: ci

file_classification:
  source: [21개 TypeScript 파일]
  test: [6개 테스트 파일]
  build: [Dockerfile, docker-compose.yml, ci.yml]
```
