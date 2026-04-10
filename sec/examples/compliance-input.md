# 컴플라이언스 검증 입력 예시

> 휴가 관리 시스템의 세 에이전트(threat-model, audit, review) 결과를 기반으로 컴플라이언스 검증을 수행하는 입력 예시입니다.

## 위협 모델

> threat-model-output.md의 `threat_model` 섹션 참조 (TM-001 ~ TM-007)

## 신뢰 경계

> threat-model-output.md의 `trust_boundaries` 섹션 참조 (TB-001 ~ TB-003)

## 취약점 보고서

> audit-output.md의 `vulnerability_report` 섹션 참조 (VA-001 ~ VA-008)

## 보안 리뷰

> review-output.md의 `security_review` 섹션 참조 (SRV-001 ~ SRV-005)

## 대응 전략 매트릭스

> review-output.md의 `mitigation_matrix` 섹션 참조 (TM-001 ~ TM-007)

## 기술 스택

> threat-model-input.md의 `technology_stack` 섹션 참조

## 컴포넌트 구조

> threat-model-input.md의 `component_structure` 섹션 참조

## RE 제약 조건 (간접 참조)

```yaml
# Arch technology_stack의 constraint_ref를 통해 간접 참조
constraints:
  - id: CON-001
    type: regulatory
    title: "개인정보보호법 준수"
    description: "직원 개인정보(이름, 이메일, 부서) 처리 시 개인정보보호법 준수 필요"
    flexibility: hard
  - id: CON-002
    type: technical
    title: "PostgreSQL 14 이상 사용"
    description: "사내 표준 DBMS"
    flexibility: hard
```

> 규제 제약으로 개인정보보호법(GDPR 유사)이 `hard`로 지정되어 있으므로, OWASP ASVS Level 2를 적용합니다.
