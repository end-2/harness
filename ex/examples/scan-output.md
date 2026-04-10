# 구조 스캔 출력 예시

> Task Manager API — 중량 모드

---

```yaml
directory_tree: |
  task-manager-api/
  ├── src/
  │   ├── controllers/
  │   │   ├── taskController.ts
  │   │   ├── userController.ts
  │   │   └── authController.ts
  │   ├── services/
  │   │   ├── taskService.ts
  │   │   ├── userService.ts
  │   │   └── authService.ts
  │   ├── repositories/
  │   │   ├── taskRepository.ts
  │   │   └── userRepository.ts
  │   ├── middlewares/
  │   │   ├── auth.ts
  │   │   ├── errorHandler.ts
  │   │   └── validator.ts
  │   ├── models/
  │   │   ├── task.ts
  │   │   └── user.ts
  │   ├── routes/
  │   │   ├── taskRoutes.ts
  │   │   ├── userRoutes.ts
  │   │   └── index.ts
  │   ├── utils/
  │   │   ├── logger.ts
  │   │   └── config.ts
  │   ├── types/
  │   │   └── index.ts
  │   ├── app.ts
  │   └── server.ts
  ├── tests/
  │   ├── controllers/
  │   │   ├── taskController.test.ts
  │   │   └── userController.test.ts
  │   ├── services/
  │   │   ├── taskService.test.ts
  │   │   └── userService.test.ts
  │   ├── integration/
  │   │   └── api.test.ts
  │   └── setup.ts
  ├── prisma/
  │   ├── schema.prisma
  │   └── migrations/ (3 migrations)
  ├── .github/
  │   └── workflows/
  │       └── ci.yml
  ├── package.json
  ├── tsconfig.json
  ├── jest.config.ts
  ├── Dockerfile
  ├── docker-compose.yml
  ├── .env.example
  ├── .eslintrc.json
  ├── .prettierrc
  ├── .gitignore
  └── README.md

file_classification:
  source:
    - src/controllers/taskController.ts
    - src/controllers/userController.ts
    - src/controllers/authController.ts
    - src/services/taskService.ts
    - src/services/userService.ts
    - src/services/authService.ts
    - src/repositories/taskRepository.ts
    - src/repositories/userRepository.ts
    - src/middlewares/auth.ts
    - src/middlewares/errorHandler.ts
    - src/middlewares/validator.ts
    - src/models/task.ts
    - src/models/user.ts
    - src/routes/taskRoutes.ts
    - src/routes/userRoutes.ts
    - src/routes/index.ts
    - src/utils/logger.ts
    - src/utils/config.ts
    - src/types/index.ts
    - src/app.ts
    - src/server.ts
  config:
    - package.json
    - tsconfig.json
    - jest.config.ts
    - .eslintrc.json
    - .prettierrc
    - .env.example
    - prisma/schema.prisma
  test:
    - tests/controllers/taskController.test.ts
    - tests/controllers/userController.test.ts
    - tests/services/taskService.test.ts
    - tests/services/userService.test.ts
    - tests/integration/api.test.ts
    - tests/setup.ts
  doc:
    - README.md
  build:
    - Dockerfile
    - docker-compose.yml
    - .github/workflows/ci.yml
  static: []

entry_points:
  - path: src/server.ts
    role: "HTTP 서버 시작점 (Express 앱 리스닝)"
  - path: src/app.ts
    role: "Express 애플리케이션 설정 및 미들웨어 등록"

config_files:
  - path: package.json
    role: "npm 패키지 매니페스트 (의존성, 스크립트)"
    category: package
  - path: tsconfig.json
    role: "TypeScript 컴파일러 설정"
    category: build
  - path: jest.config.ts
    role: "Jest 테스트 프레임워크 설정"
    category: test
  - path: .eslintrc.json
    role: "ESLint 코드 린팅 규칙"
    category: lint
  - path: .prettierrc
    role: "Prettier 코드 포매팅 설정"
    category: lint
  - path: .env.example
    role: "환경 변수 템플릿 (DATABASE_URL, JWT_SECRET 등)"
    category: env
  - path: prisma/schema.prisma
    role: "Prisma ORM 데이터 모델 스키마"
    category: other
  - path: Dockerfile
    role: "Docker 컨테이너 이미지 빌드 정의"
    category: container
  - path: docker-compose.yml
    role: "Docker Compose 로컬 개발 환경 (app + postgres)"
    category: container
  - path: .github/workflows/ci.yml
    role: "GitHub Actions CI 파이프라인 (lint, test, build)"
    category: ci

depth_mode:
  mode: heavyweight
  evidence:
    file_count: 38  # 소스 파일 21 + 테스트 6 + 설정 7 + 문서 1 + 빌드 3
    language_count: 1  # TypeScript
    framework_count: 2  # Express, Prisma
    max_directory_depth: 4  # src/controllers/taskController.ts

ignored_patterns:
  - node_modules/
  - dist/
  - .git/
  - coverage/
  - "*.log"
  - .env
```

### 디렉토리 규칙 탐지 (중량 모드)

```yaml
directory_conventions:
  - "Layer-based 구조: src/ 하위에 controllers/, services/, repositories/, models/ 계층 분리"
  - "테스트 미러링: tests/ 하위에 controllers/, services/ 구조가 src/를 미러링"
  - "미들웨어 분리: src/middlewares/에 횡단 관심사(인증, 에러, 검증) 집중"
  - "라우트 집중: src/routes/에 HTTP 라우트 정의 분리"
```
