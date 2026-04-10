# 요구사항 도출 입력 예시

## 예시 1: heavyweight 모드 (모호한 고수준 입력)

```yaml
user_request: "사내 직원들이 사용할 휴가 관리 시스템을 만들어주세요"
```

## 예시 2: lightweight 모드 (특정 기능/기술을 언급하는 중간 수준 입력)

```yaml
user_request: |
  React + Node.js로 REST API 기반의 할일 관리 앱을 만들고 싶습니다.
  Google 로그인을 지원하고, 할일에 태그와 마감일을 설정할 수 있어야 합니다.
```

## 예시 3: lightweight 모드 (구체적 스펙이 포함된 상세 입력)

```yaml
user_request: |
  실시간 채팅 시스템을 구축해야 합니다.

  - WebSocket 기반 1:1 및 그룹 채팅 (최대 100명)
  - 메시지 암호화 (E2E encryption)
  - 파일 첨부 (이미지, 문서, 최대 10MB)
  - 메시지 검색 (최근 1년)
  - 읽음 확인
  - PostgreSQL + Redis
  - 동시 접속자 10,000명 지원
  - 배포: AWS ECS

  기존 사내 SSO와 연동해야 하며, GDPR 준수가 필요합니다.
```
