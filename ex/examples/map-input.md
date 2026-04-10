# 컨텍스트 맵 생성 입력 예시

> Task Manager API — scan + detect + analyze 에이전트 출력을 입력으로 수신

---

## 입력

세 에이전트의 전체 출력이 각각 전달됩니다:

- `{{scan_output}}`: `scan-output.md` 참조
- `{{detect_output}}`: `detect-output.md` 참조
- `{{analyze_output}}`: `analyze-output.md` 참조

```yaml
token_budget: 4000
focus_areas: []
```

### 통합 시 고려사항

- 토큰 예산 4000 내에서 4섹션 산출물 생성
- 중량 모드이므로 4섹션 모두 상세 포함
- focus_areas가 비어 있으므로 균등 배분
- detect의 기술 12개 중 보조 도구(ESLint, Prettier)는 예산 부족 시 요약 대상
- analyze의 컴포넌트 9개 중 Tests, Utils는 예산 부족 시 요약 대상
