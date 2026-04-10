# 기술 스택 탐지 출력 예시

> Task Manager API — 기술 스택 탐지 결과

---

```yaml
tech_stack:
  - id: TS-001
    category: language
    name: TypeScript
    version: "5.3.3"
    evidence: "package.json devDependencies에서 'typescript: ^5.3.3' 탐지 + tsconfig.json 존재"
    role: "주 개발 언어"
    config_location: tsconfig.json

  - id: TS-002
    category: framework
    name: Express
    version: "4.18.2"
    evidence: "package.json dependencies에서 'express: ^4.18.2' 탐지 + src/app.ts에서 import express 패턴"
    role: "HTTP 웹 프레임워크 (REST API 서버)"
    config_location: src/app.ts

  - id: TS-003
    category: database
    name: Prisma
    version: "5.7.1"
    evidence: "package.json dependencies에서 '@prisma/client: ^5.7.1' 탐지 + prisma/schema.prisma 존재"
    role: "ORM / 데이터베이스 스키마 관리 / 마이그레이션"
    config_location: prisma/schema.prisma

  - id: TS-004
    category: database
    name: PostgreSQL
    version: "미확인"
    evidence: "prisma/schema.prisma에서 provider = 'postgresql' 탐지 + docker-compose.yml에서 postgres:15 이미지"
    role: "주 데이터베이스"
    config_location: prisma/schema.prisma

  - id: TS-005
    category: build
    name: tsc (TypeScript Compiler)
    version: "5.3.3"
    evidence: "package.json scripts에서 'build: tsc' 탐지 + tsconfig.json 존재"
    role: "TypeScript → JavaScript 컴파일"
    config_location: tsconfig.json

  - id: TS-006
    category: test
    name: Jest
    version: "29.7.0"
    evidence: "package.json devDependencies에서 'jest: ^29.7.0', 'ts-jest: ^29.1.1' 탐지 + jest.config.ts 존재"
    role: "단위/통합 테스트 프레임워크"
    config_location: jest.config.ts

  - id: TS-007
    category: test
    name: Supertest
    version: "6.3.3"
    evidence: "package.json devDependencies에서 'supertest: ^6.3.3' 탐지 + tests/integration/api.test.ts에서 import"
    role: "HTTP 통합 테스트 유틸리티"
    config_location: null

  - id: TS-008
    category: lint
    name: ESLint
    version: "8.56.0"
    evidence: "package.json devDependencies에서 'eslint: ^8.56.0' 탐지 + .eslintrc.json 존재"
    role: "코드 품질 린터"
    config_location: .eslintrc.json

  - id: TS-009
    category: lint
    name: Prettier
    version: "3.2.4"
    evidence: "package.json devDependencies에서 'prettier: ^3.2.4' 탐지 + .prettierrc 존재"
    role: "코드 포매터"
    config_location: .prettierrc

  - id: TS-010
    category: ci
    name: GitHub Actions
    version: "미확인"
    evidence: ".github/workflows/ci.yml 존재"
    role: "CI/CD 파이프라인 (lint → test → build)"
    config_location: .github/workflows/ci.yml

  - id: TS-011
    category: container
    name: Docker
    version: "미확인"
    evidence: "Dockerfile 존재 (node:20-alpine 베이스 이미지)"
    role: "컨테이너화 / 배포 패키징"
    config_location: Dockerfile

  - id: TS-012
    category: container
    name: Docker Compose
    version: "미확인"
    evidence: "docker-compose.yml 존재 (app + postgres 서비스 정의)"
    role: "로컬 개발 환경 오케스트레이션"
    config_location: docker-compose.yml

tech_relationships:
  - "TypeScript 프로젝트에서 Express를 REST API 프레임워크로, Prisma를 ORM으로, PostgreSQL을 데이터베이스로 사용하는 백엔드 API 구성"
  - "Jest + ts-jest로 TypeScript 테스트, Supertest로 HTTP 통합 테스트를 수행하는 이중 테스트 전략"
  - "ESLint + Prettier 조합으로 코드 품질과 포매팅을 관리"
  - "Docker + Docker Compose로 로컬 개발 환경 구성, GitHub Actions로 CI 자동화"
```
