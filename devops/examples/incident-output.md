# 인시던트 대응 출력 예시

> 온라인 주문 처리 시스템의 런북 자동 생성 결과

## 런북 목록

| ID | 제목 | 트리거 | 심각도 | 관련 알림 | 관련 SLO |
|----|------|--------|--------|----------|---------|
| RB-001 | API 응답시간 SLO 위반 대응 | MON-001 발동 | critical | MON-001 | SLO-001 |
| RB-002 | 시스템 가용성 SLO 위반 대응 | MON-003 발동 | critical | MON-003 | SLO-002 |
| RB-003 | 데이터 손실 인시던트 대응 | MON-006 발동 | critical | MON-006 | SLO-004 |
| RB-004 | RDS 연결 풀 소진 대응 | MON-009 발동 | high | MON-009 | - |
| RB-005 | RabbitMQ 메시지 적체 대응 | MON-012 발동 | high | MON-012, MON-013 | SLO-003 |
| RB-006 | 서비스 리소스 부족 대응 | MON-007 발동 | medium | MON-007, MON-008 | - |
| RB-007 | 배포 롤백 대응 | 배포 중 롤백 트리거 발동 | critical | MON-015, MON-016 | SLO-002 |

## 런북 상세

### RB-001: API 응답시간 SLO 위반 대응

**트리거 조건**
- 알림: MON-001 — SLO-001 응답시간 p99 번-레이트 14.4x (1h/5m 윈도우)

**증상**
- [ ] API 응답 시간이 평소보다 현저히 느림
- [ ] 사용자 불만 보고 (선택적)
- [ ] SLO 에러 버짓 빠르게 소진 중

**진단 절차**

1. 어떤 서비스에서 레이턴시가 발생하는지 확인:
   ```bash
   # 서비스별 p99 응답시간 확인 (Prometheus)
   curl -s "http://prometheus:9090/api/v1/query?query=histogram_quantile(0.99,rate(http_request_duration_seconds_bucket[5m]))" | jq '.data.result[] | {service: .metric.service, p99: .value[1]}'
   ```

2. 해당 서비스의 최근 로그 확인:
   ```bash
   aws logs filter-log-events \
     --log-group-name /ecs/order-system-prod/order-service \
     --start-time $(date -d '10 minutes ago' +%s000) \
     --filter-pattern '{ $.level = "ERROR" }'
   ```

3. 리소스 사용량 확인:
   ```bash
   aws ecs describe-services --cluster order-system-prod \
     --services order-service --query 'services[0].{running: runningCount, desired: desiredCount}'
   ```

4. 대시보드 확인: DASH-003 (order-service) — 응답시간 분포, 에러율

5. 의존성 서비스 상태 확인:
   - order-db: RDS 연결 수, 슬로우 쿼리
   - message-queue: 큐 길이, 소비자 수

**조치 절차**

**자동 조치** (이미 설정됨):
- 없음 (응답시간 SLO 위반은 자동 롤백 대상이 아님)

**수동 조치**:
1. 원인이 최근 배포라면:
   ```bash
   # 블루/그린 롤백 실행
   ./scripts/blue-green-switch.sh order-service --rollback
   ```

2. 원인이 DB 슬로우 쿼리라면:
   ```sql
   -- 슬로우 쿼리 식별
   SELECT pid, query, state, query_start FROM pg_stat_activity 
   WHERE state = 'active' AND query_start < now() - interval '1 second';
   -- 필요시 문제 쿼리 kill
   SELECT pg_cancel_backend(pid);
   ```

3. 원인이 리소스 부족이라면:
   ```bash
   # ECS 서비스 스케일 아웃
   aws ecs update-service --cluster order-system-prod \
     --service order-service --desired-count 5
   ```

4. 조치 후 메트릭 정상화 확인 (10분 관찰)

**에스컬레이션**

| 시간 | 담당 | 채널 |
|------|------|------|
| 0-15분 | 온콜 엔지니어 | Slack #incidents |
| 15-30분 | 백엔드 팀 리드 | 전화 호출 |
| 30분+ | 엔지니어링 매니저 | 전화 + 이메일 |

---

### RB-007: 배포 롤백 대응

**트리거 조건**
- 배포 중 롤백 트리거 발동 (SLO 번-레이트, 헬스 체크 실패, 에러율 급증)

**증상**
- [ ] 배포 후 서비스 에러율 증가
- [ ] 헬스 체크 연속 실패
- [ ] SLO 번-레이트 알림 발동

**진단 절차**

1. 롤백 트리거 확인:
   ```bash
   # 최근 알림 확인
   curl -s "http://alertmanager:9093/api/v2/alerts?filter=alertname=~'deploy.*'" | jq '.'
   ```

2. 배포 이벤트 확인:
   ```bash
   aws ecs describe-services --cluster order-system-prod \
     --services order-service \
     --query 'services[0].deployments'
   ```

**조치 절차**

**자동 조치** (이미 설정됨):
- ALB 타겟 그룹이 블루 환경으로 자동 전환
- Slack #deployments에 롤백 알림 발송

**수동 조치** (자동 롤백 실패 시):
1. ALB 타겟 그룹 수동 전환:
   ```bash
   ./scripts/blue-green-switch.sh order-service --rollback --force
   ```

2. 블루 환경 헬스 확인:
   ```bash
   curl -f http://order-service-blue:3000/healthz
   ```

3. 그린 환경 태스크 종료:
   ```bash
   aws ecs update-service --cluster order-system-prod \
     --service order-service-green --desired-count 0
   ```

4. 원인 분석 시작 (코드 변경 리뷰, 로그 분석)

**에스컬레이션**

| 시간 | 담당 | 채널 |
|------|------|------|
| 0분 | 배포 담당자 + 온콜 | Slack #deployments |
| 5분 (자동 롤백 실패 시) | 팀 리드 | 전화 호출 |
| 15분+ | 엔지니어링 매니저 | 전화 + 이메일 |

## 에스컬레이션 매트릭스

| 심각도 | 초기 대응 | 15분 미해결 | 30분 미해결 | 1시간 미해결 |
|--------|----------|-----------|-----------|------------|
| critical | 온콜 + 팀 리드 | 엔지니어링 매니저 | VP of Engineering | CTO |
| high | 온콜 엔지니어 | 팀 리드 | 엔지니어링 매니저 | - |
| medium | 담당 개발자 | 팀 리드 | - | - |
| low | 백로그 등록 | - | - | - |

## 커뮤니케이션 템플릿

### 내부 공지

```
🔴 인시던트 발생 — [Critical/High]

영향: [주문 처리 서비스 / 전체 시스템]
시작 시간: [2024-01-15 10:30 KST]
현재 상태: 조사 중
담당: [온콜 엔지니어명]

원인: [조사 중 / 최근 배포 관련 / DB 이슈]
조치: [롤백 진행 중 / 스케일 아웃 진행 중]

다음 업데이트: 15분 후
```

### 외부 상태 페이지

```
주문 처리 서비스 — 성능 저하

현재 주문 처리 서비스에 영향을 미치는 문제를 조사하고 있습니다.
일부 사용자에게 주문 처리 지연이 발생할 수 있습니다.

마지막 업데이트: 2024-01-15 10:35 KST
```

### 사후 분석 (Postmortem) 템플릿

```markdown
# 사후 분석: [인시던트 제목]

## 요약
- **영향**: [영향 범위] / [지속 시간]
- **근본 원인**: [한 문장 요약]
- **탐지**: [MON-xxx] 알림 → [자동/수동] 감지
- **해결**: [조치 요약]

## 타임라인
| 시간 (KST) | 이벤트 |
|------------|--------|
| 10:30 | 배포 시작 (order-service v1.2.3) |
| 10:32 | MON-001 발동 (응답시간 SLO 번-레이트 14.4x) |
| 10:33 | 자동 롤백 실행 (블루 환경 전환) |
| 10:34 | 헬스 체크 확인 — 정상 |
| 10:35 | 인시던트 종료 선언 |

## 근본 원인 분석
1. Why: 응답시간이 급증했는가? → 새 버전의 DB 쿼리가 느림
2. Why: DB 쿼리가 느린가? → 인덱스 없는 테이블 풀 스캔
3. Why: 인덱스가 없는가? → 마이그레이션에서 인덱스 추가 누락
4. Why: 누락이 발견되지 않았는가? → staging에서 데이터 볼륨이 적어 감지 불가
5. Why: staging 데이터가 적은가? → staging 데이터 시딩 정책 미비

## 교훈
### 잘 된 점
- 자동 롤백이 1분 내에 정상적으로 실행됨
- 알림이 즉시 발동하여 빠른 인지 가능

### 개선할 점
- staging 환경의 데이터 볼륨을 prod에 근접하게 유지
- 마이그레이션 리뷰에 쿼리 실행 계획 검증 추가

## 후속 조치
| 항목 | 담당 | 기한 | 우선순위 |
|------|------|------|----------|
| staging 데이터 시딩 자동화 | DevOps 팀 | 2주 | High |
| 마이그레이션 CI에 EXPLAIN 검증 추가 | 백엔드 팀 | 1주 | High |
| 슬로우 쿼리 알림 임계값 강화 | SRE 팀 | 1주 | Medium |
```
