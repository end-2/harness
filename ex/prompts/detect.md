# 기술 스택 탐지 프롬프트

## 입력

```
scan 에이전트 출력: {{scan_output}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙에 따라 `{{scan_output}}`을 기계적으로 분석하세요. 사용자에게 질문하지 말고 결과만 출력합니다.

### Step 1: 매니페스트 파일 분석

`{{scan_output}}`의 `config_files`에서 `category: package`인 파일을 우선 분석합니다. 시스템 프롬프트 **"매니페스트 파일 분석"** 표(언어별 매니페스트, package.json 심층 분석)에 따라 언어와 버전을 확정합니다.

### Step 2: 프레임워크 탐지

시스템 프롬프트 **"프레임워크 탐지 시그니처 → 웹 프레임워크"**, **"데이터베이스/ORM"** 표의 시그니처를 사용하여 프레임워크와 ORM을 식별합니다. 각 탐지마다 `evidence` 필드에 탐지 근거를 기록합니다:

```
evidence: "package.json dependencies에서 'next: ^14.0.0' 탐지 + next.config.mjs 존재"
```

### Step 3: 개발/빌드 도구 탐지

시스템 프롬프트 **"테스트 프레임워크"**, **"빌드 도구"**, **"린터/포매터"** 표의 시그니처에 따라 탐지합니다. `devDependencies`에만 있는 기술은 개발/빌드 도구로 분류합니다.

### Step 4: 인프라/배포 도구 탐지

시스템 프롬프트 **"CI/CD"**, **"컨테이너/인프라"** 표의 시그니처에 따라 탐지합니다. `{{scan_output}}`의 `config_files`에서 `category: ci`, `category: container`에 해당하는 파일도 함께 확인합니다.

### Step 5: 역할 추론

각 탐지된 기술에 대해 프로젝트 내 역할을 추론합니다:

```
예시:
- TS-001: TypeScript → "주 개발 언어"
- TS-002: Next.js → "풀스택 웹 프레임워크 (SSR + API Routes)"
- TS-003: Prisma → "ORM / 데이터베이스 스키마 관리"
- TS-004: Jest → "단위/통합 테스트 프레임워크"
```

### Step 6: 기술 간 관계 기술

시스템 프롬프트 **"기술 간 관계 추론"** 지침에 따라 탐지된 기술 간의 관계를 자연어로 요약합니다.

### Step 7: ID 부여 및 결과 출력

각 기술에 `TS-001`부터 순차적으로 ID를 부여합니다. 카테고리 순서: `language` → `framework` → `database` → `messaging` → `build` → `test` → `lint` → `ci` → `container` → `infra`.

시스템 프롬프트 **"산출물 구조"**에 맞춰 YAML로 출력하고, **"출력 프로토콜"**에 따라 `meta.json`/`body.md`에 기록합니다.
