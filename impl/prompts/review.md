# 코드 리뷰 프롬프트

## 입력

```
생성된 코드: {{generated_code}}
구현 맵: {{implementation_map}}
구현 결정: {{implementation_decisions}}
아키텍처 결정: {{architecture_decisions}}
컴포넌트 구조: {{component_structure}}
기술 스택: {{technology_stack}}
```

## 지시사항

시스템 프롬프트에 정의된 역할과 규칙을 따라 생성된 코드를 Arch 결정 준수 여부와 클린 코드 원칙 두 축으로 리뷰하세요. 자동 수정 가능한 이슈는 `refactor` 에이전트로 전달하고, Arch 계약 위반만 사용자에게 에스컬레이션합니다.

### Step 1: 구현 맵 기반 모듈 순회

`implementation_map`의 각 항목에 대해 순서대로 모듈을 순회하며 리뷰합니다.

```
IM-001: COMP-001 → <module_path>
  → Arch 준수 검증
  → 클린 코드 검증
  → 보안 기본 검증
```

### Step 2: Arch 결정 준수 검증

시스템 프롬프트 **"리뷰 축 1: Arch 결정 준수 검증"** 표(컴포넌트 경계, 아키텍처 패턴, 기술 스택)에 따라 각 모듈이 `COMP.responsibility`/`COMP.dependencies`/`COMP.interfaces`, `AD.decision` 패턴, `TS.choice`/`TS.constraint_ref`를 준수하는지 검증합니다.

### Step 3: 클린 코드 원칙 검증

시스템 프롬프트 **"리뷰 축 2: 클린 코드 원칙 검증"** 표(SOLID 원칙, 코드 품질)에 따라 SRP/OCP/LSP/ISP/DIP, 가독성, 복잡도, 중복, 네이밍 일관성, 에러 처리를 검증합니다.

### Step 4: 보안 기본 검증

시스템 프롬프트 **"리뷰 축 3: 보안 기본 검증"** 표(인젝션, 인증/인가, 민감 데이터, 입력 검증)에 따라 OWASP Top 10 수준의 코드 레벨 이슈를 탐지합니다.

### Step 5: 이슈 분류 및 판정

발견된 이슈를 심각도별로 분류합니다:

| 심각도 | 기준 | 처리 |
|-------|------|------|
| `critical` | Arch 계약 위반 | 에스컬레이션 |
| `high` | 보안 이슈, 버그 가능성 | refactor 자동 수정 |
| `medium` | SOLID 위반, 높은 복잡도 | refactor 자동 수정 |
| `low` | 네이밍, 스타일 이슈 | refactor 자동 수정 |
| `info` | 개선 가능 영역 | 리포트에 기록만 |

시스템 프롬프트 **"리뷰 프로세스 → 단계 5: 판정"** 기준으로 `PASS` / `FIX_REQUIRED` / `ESCALATE`를 결정합니다.

### Step 6: 리뷰 리포트 작성 및 출력

시스템 프롬프트 **"출력 형식"** 및 **"출력 프로토콜"**에 따라 리뷰 리포트를 `meta.json`/`body.md`에 기록합니다. 추가로 요약 섹션을 포함합니다:

```yaml
review_report:
  summary:
    total_modules: <수>
    compliant_modules: <수>
    issues_found: <수>
    auto_fixable: <수>
    escalations: <수>
  arch_compliance: [...]
  clean_code_issues: [...]
  security_issues: [...]
  verdict: PASS | FIX_REQUIRED | ESCALATE
```

에스컬레이션이 있으면 시스템 프롬프트 **"에스컬레이션 조건"** 형식에 따라 먼저 제시합니다. 최종 판정은 출력 프로토콜의 `--verdict` 단계로 기록합니다.

## 주의사항

- 코드 스타일 선호는 리뷰 대상이 아닙니다 (기술 스택 관용구를 따르면 충분)
- 테스트 코드 부재를 이슈로 보고하지 마세요 (qa 스킬의 영역)
- 배포/인프라 설정은 리뷰 대상이 아닙니다 (deployment 스킬의 영역)
- Arch 결정에 대한 의문은 Arch 스킬의 영역입니다. 여기서는 "결정이 코드에 반영되었는가"만 검증합니다
