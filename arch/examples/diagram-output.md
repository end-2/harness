# 다이어그램 생성 출력 예시

> 휴가 관리 시스템 — 중량 모드 (C4 Context + Container + Sequence)

---

## 다이어그램 목록

```yaml
- type: c4-context
  title: 휴가 관리 시스템 컨텍스트
  format: mermaid
  code: |
    graph TB
        subgraph boundary ["휴가 관리 시스템 경계"]
            system["휴가 관리 시스템<br/>[Django + React]<br/>직원 휴가 신청/승인/관리"]
        end

        employee["👤 직원<br/>휴가 신청, 잔여 조회"]
        manager["👤 팀장<br/>휴가 승인/반려"]
        hr["👤 HR 담당자<br/>현황 조회, 통계"]

        sso["사내 SSO<br/>[SAML 2.0]<br/>통합 인증 서비스"]
        mail["사내 메일 서버<br/>[SMTP]<br/>이메일 발송"]

        employee -->|"휴가 신청/조회"| system
        manager -->|"승인/반려"| system
        hr -->|"현황 조회/통계"| system
        system -->|"인증 요청"| sso
        system -->|"알림 이메일"| mail
  description: |
    시스템 외부의 사용자(직원, 팀장, HR)와 외부 시스템(SSO, 메일 서버)과의 관계를 보여줍니다.
    세 가지 역할의 사용자가 시스템과 상호작용하며, 시스템은 인증을 위해 SSO,
    알림을 위해 메일 서버와 연동합니다.

- type: c4-container
  title: 휴가 관리 시스템 컨테이너 구조
  format: mermaid
  code: |
    graph TB
        subgraph system ["휴가 관리 시스템"]
            nginx["Nginx<br/>[리버스 프록시]<br/>정적 파일 서빙 + API 프록시"]
            frontend["Web Frontend<br/>[React 18 + TypeScript]<br/>SPA 사용자 인터페이스"]
            api["API Server<br/>[Django 4.2 + DRF]<br/>비즈니스 로직 + REST API"]
            worker["Task Worker<br/>[Celery]<br/>비동기 작업 처리"]
            db[("Database<br/>[PostgreSQL 14]<br/>데이터 영구 저장")]
            redis[("Redis<br/>[Redis 7]<br/>태스크 큐 브로커")]
        end

        user["👤 사용자"] -->|"HTTPS"| nginx
        nginx -->|"정적 파일"| frontend
        nginx -->|"API 프록시"| api
        api -->|"SQL"| db
        api -->|"태스크 발행"| redis
        redis -->|"태스크 소비"| worker
        worker -->|"SMTP"| mail["사내 메일 서버"]
        api -->|"SAML"| sso["사내 SSO"]

        style frontend fill:#4FC3F7,color:#000
        style api fill:#81C784,color:#000
        style db fill:#FFB74D,color:#000
        style redis fill:#FFB74D,color:#000
        style worker fill:#CE93D8,color:#000
  description: |
    시스템 내부의 컨테이너 구조를 보여줍니다.
    Nginx가 프론트엔드(정적 파일)와 API 서버로 요청을 라우팅합니다.
    API 서버는 PostgreSQL에 데이터를 저장하고, Redis를 통해 Celery 워커에
    비동기 작업(이메일 발송)을 위임합니다.

- type: sequence
  title: 휴가 신청 흐름
  format: mermaid
  code: |
    sequenceDiagram
        actor Employee as 직원
        participant Nginx as Nginx
        participant SPA as Web Frontend
        participant API as API Server
        participant DB as PostgreSQL
        participant Redis as Redis
        participant Worker as Celery Worker
        participant Mail as 메일 서버

        Employee->>Nginx: 휴가 신청 페이지 접근
        Nginx->>SPA: SPA 로드
        SPA-->>Employee: 신청 폼 표시

        Employee->>SPA: 휴가 유형/기간/사유 입력
        SPA->>Nginx: POST /api/leaves/
        Nginx->>API: POST /api/leaves/

        API->>DB: 잔여 휴가 조회
        DB-->>API: 잔여 일수

        alt 잔여 휴가 부족
            API-->>Nginx: 400 Bad Request
            Nginx-->>SPA: 에러 응답
            SPA-->>Employee: "잔여 휴가가 부족합니다"
        else 잔여 휴가 충분
            API->>DB: 휴가 신청 저장 (상태: 대기중)
            API->>DB: 감사 로그 기록
            DB-->>API: 저장 완료
            API->>Redis: 알림 태스크 발행
            API-->>Nginx: 201 Created
            Nginx-->>SPA: 성공 응답
            SPA-->>Employee: "신청이 완료되었습니다"

            Redis->>Worker: 태스크 소비
            Worker->>Mail: 팀장에게 승인 요청 이메일
        end
  description: |
    직원이 휴가를 신청하는 전체 흐름을 보여줍니다.
    잔여 휴가 확인 → 신청 저장 → 감사 로그 기록 → 비동기 알림 발송의
    순서로 진행됩니다. 잔여 휴가 부족 시 신청이 차단되는 분기도 포함합니다.

- type: sequence
  title: 휴가 승인 흐름
  format: mermaid
  code: |
    sequenceDiagram
        actor Manager as 팀장
        participant SPA as Web Frontend
        participant API as API Server
        participant DB as PostgreSQL
        participant Redis as Redis
        participant Worker as Celery Worker
        participant Mail as 메일 서버

        Manager->>SPA: 대기중 휴가 목록 조회
        SPA->>API: GET /api/leaves/?status=pending&team=my
        API->>DB: 팀원 대기중 휴가 조회
        DB-->>API: 대기중 목록
        API-->>SPA: 휴가 목록
        SPA-->>Manager: 대기중 휴가 목록 표시

        Manager->>SPA: 승인 버튼 클릭
        SPA->>API: PATCH /api/leaves/{id}/ {status: approved}
        API->>DB: 상태 변경 (대기중 → 승인됨)
        API->>DB: 감사 로그 기록
        DB-->>API: 업데이트 완료
        API->>Redis: 알림 태스크 발행
        API-->>SPA: 200 OK
        SPA-->>Manager: "승인 완료"

        Redis->>Worker: 태스크 소비
        Worker->>Mail: 신청자에게 승인 알림 이메일
  description: |
    팀장이 팀원의 휴가를 승인하는 흐름을 보여줍니다.
    대기중 목록 조회 → 승인 → 상태 변경 + 감사 로그 → 비동기 알림의
    순서로 진행됩니다.
```
