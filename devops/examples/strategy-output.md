# 배포 전략 출력 예시

> 온라인 주문 처리 시스템의 배포 전략 결정 결과

## 배포 전략 요약

| 항목 | 결정 | 근거 |
|------|------|------|
| 배포 방식 | **블루/그린** | SLO-002 가용성 99.9% (Three 9s), 에러 버짓 100% (초기). 무중단 배포 필수 |
| 롤아웃 단계 | 그린 환경 프로비저닝 → 헬스 체크 → 트래픽 전환 → 블루 유지(30분) → 블루 해제 | 즉각적 롤백 보장 |
| 롤백 방식 | 블루 환경으로 즉시 트래픽 전환 | 롤백 소요 < 1분 |
| 배포 순서 | DB 마이그레이션 → order-service → user-service → api-gateway | 의존성 역순 |

### 배포 방식 선택 근거

```
의사결정 트리 실행:
1. 가용성 목표: 99.9% (Three 9s) ✓
2. 에러 버짓 잔량: 100% (초기) ≥ 20% ✓
3. → 블루/그린 선택

추가 고려:
- AD-001: 마이크로서비스 → 서비스별 독립 블루/그린 배포
- 인프라 비용: ECS Fargate 기반 → 배포 시에만 그린 환경 프로비저닝 (상시 2배 X)
- 비용 수용 가능: 배포 시 ~30분간 추가 인프라 비용 발생 (미미)
```

## 배포 순서

```
1. [DB Migration] order-db 스키마 마이그레이션 (호환 가능한 변경만)
   ├── 검증: 마이그레이션 성공 확인 + 기존 서비스 정상 작동 확인
   └── 롤백: 역방향 마이그레이션 스크립트 실행

2. [Service] order-service 블루/그린 배포
   ├── 그린 태스크 프로비저닝 (3개)
   ├── 헬스 체크 통과 확인 (/healthz, /ready)
   ├── ALB 타겟 그룹 전환
   └── 블루 태스크 30분 유지 후 해제

3. [Service] user-service 블루/그린 배포
   ├── (order-service와 동일 절차)
   └── order-service 정상 상태 재확인

4. [Gateway] api-gateway 블루/그린 배포
   ├── (동일 절차)
   └── 전체 서비스 통합 스모크 테스트
```

## 롤백 트리거

| 트리거 | 조건 | 소스 | 동작 |
|--------|------|------|------|
| SLO 번-레이트 (긴급) | SLO-002 14.4x 번-레이트, 1h/5m | SLO 에이전트 | 즉시 블루 환경으로 트래픽 전환 |
| 헬스 체크 실패 | /healthz 연속 3회 실패 | COMP 인터페이스 | 배포 중단 + 블루 유지 |
| 에러율 급증 | 5xx 비율 > 5% (5분간) | 모니터링 | 즉시 블루 환경으로 트래픽 전환 |

## 롤백 절차

| 단계 | 조치 | 담당 | 예상 소요 |
|------|------|------|----------|
| 1 | ALB 타겟 그룹을 블루 환경으로 전환 | 자동 (ALB 가중치 변경) | 30초 |
| 2 | 그린 환경 트래픽 차단 확인 | 자동 (ALB 메트릭) | 30초 |
| 3 | 헬스 체크 확인 (블루 환경) | 자동 | 1분 |
| 4 | 인시던트 채널 알림 발송 | 자동 (Slack) | 즉시 |
| 5 | 그린 환경 태스크 종료 | 수동 확인 후 실행 | 5분 |
| 6 | 롤백 원인 조사 시작 | 온콜 엔지니어 | - |

## 헬스 체크

| 대상 컴포넌트 | 체크 유형 | 경로 | 간격 | 타임아웃 | 실패 임계 |
|-------------|----------|------|------|---------|----------|
| COMP-001 (api-gateway) | Liveness | /healthz | 10s | 3s | 3회 |
| COMP-001 (api-gateway) | Readiness | /ready | 5s | 3s | 1회 |
| COMP-002 (order-service) | Liveness | /healthz | 10s | 3s | 3회 |
| COMP-002 (order-service) | Readiness | /ready | 5s | 3s | 1회 |
| COMP-003 (user-service) | Liveness | /healthz | 10s | 3s | 3회 |
| COMP-003 (user-service) | Readiness | /ready | 5s | 3s | 1회 |

## Pipeline 역반영

PL-001 Deploy 스테이지에 다음 변경을 반영:

```yaml
# Deploy (prod) 스테이지 업데이트
deploy-prod:
  steps:
    - name: DB Migration
      run: npm run migrate:prod
      
    - name: Deploy Green (order-service)
      run: |
        aws ecs update-service --cluster order-system-prod \
          --service order-service --task-definition order-service:$NEW_VERSION
      
    - name: Health Check (order-service)
      run: ./scripts/health-check.sh order-service 60  # 60초 대기
      
    - name: Switch Traffic (order-service)
      run: ./scripts/blue-green-switch.sh order-service
      
    # user-service, api-gateway 동일 패턴 반복
      
    - name: Smoke Test
      run: npm run test:smoke:prod
      
    - name: Cleanup Blue (30분 후)
      run: ./scripts/cleanup-blue.sh --delay=30m
```
