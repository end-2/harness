#!/usr/bin/env python3
"""One-shot generator for per-agent body templates.

Run once to scaffold templates/<skill>/<agent>.md for every known agent.
Existing files are left untouched so manual edits are preserved.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_ROOT = REPO_ROOT / "templates"

# (skill, agent, [section headings])
AGENTS: list[tuple[str, str, list[str]]] = [
    # ex — codebase exploration
    ("ex", "scan", ["대상 저장소", "스캔 범위", "발견한 루트 산출물", "특이 사항"]),
    ("ex", "detect", ["언어/런타임 감지", "프레임워크/라이브러리 감지", "빌드·패키지 시스템", "근거"]),
    ("ex", "analyze", ["의존성 그래프 요약", "핫스팟·리스크", "결합도·응집도", "개선 힌트"]),
    ("ex", "map", ["프로젝트 구조 개요", "주요 모듈·컴포넌트", "아키텍처 추론", "열린 질문"]),

    # re — requirements engineering
    ("re", "elicit", ["사용자 요청 요약", "열린 질문·가정", "요구사항 후보 (FR/NFR)", "제약 힌트"]),
    ("re", "analyze", ["요구사항 분류", "우선순위 근거", "충돌·중복", "품질 속성 힌트"]),
    ("re", "spec", ["요구사항 명세", "제약 조건", "품질 속성 우선순위", "수용 기준"]),
    ("re", "review", ["검증 방법", "발견한 이슈", "리스크", "권장 조치"]),

    # arch — architecture
    ("arch", "design", ["RE 산출물 분석 결과", "아키텍처 드라이버", "아키텍처 결정 요약", "컴포넌트 구조", "기술 스택", "트레이드오프"]),
    ("arch", "adr", ["상태", "컨텍스트", "결정", "대안 비교", "결과 및 트레이드오프", "RE 근거"]),
    ("arch", "diagram", ["다이어그램 개요", "C4 Context", "C4 Container", "시퀀스"]),
    ("arch", "review", ["검증 전제", "시나리오 검증", "제약 준수", "추적성", "강점·약점·리스크", "개선 제안", "최종 판정"]),

    # impl — implementation
    ("impl", "generate", ["구현 맵 개요", "코드 구조", "주요 인터페이스", "구현 결정 (IDR)", "추적성"]),
    ("impl", "pattern", ["적용 패턴", "근거", "대안", "적용 범위"]),
    ("impl", "refactor", ["현재 상태", "목표 상태", "리팩터링 단계", "리스크·롤백"]),
    ("impl", "review", ["검토 범위", "발견한 이슈", "준수·일탈", "권장 조치", "최종 판정"]),

    # qa — quality
    ("qa", "strategy", ["테스트 전략 개요", "범위와 층위", "품질 목표 매핑", "도구·환경"]),
    ("qa", "generate", ["테스트 스위트 개요", "주요 시나리오", "데이터 설계", "RE 추적성"]),
    ("qa", "report", ["실행 요약", "커버리지", "결함·이슈", "개선 제안"]),
    ("qa", "review", ["검토 범위", "전략 적합성", "공백·중복", "권장 조치", "최종 판정"]),

    # sec — security
    ("sec", "threat-model", ["시스템 범위", "자산과 신뢰 경계", "STRIDE 분석", "DREAD 점수", "완화 조치"]),
    ("sec", "audit", ["감사 범위", "발견 사항", "증거", "권장 조치"]),
    ("sec", "compliance", ["적용 규정", "항목별 평가", "증거", "개선 계획", "전반적 판정"]),
    ("sec", "review", ["검토 범위", "발견 사항", "리스크", "권장 조치", "최종 판정"]),

    # devops
    ("devops", "slo", ["서비스 맥락", "SLI 정의", "SLO 목표", "에러 버짓"]),
    ("devops", "iac", ["대상 인프라", "리소스 구성", "환경 분리", "보안·비용"]),
    ("devops", "pipeline", ["파이프라인 개요", "단계 정의", "트리거·승인", "품질 게이트"]),
    ("devops", "monitor", ["관측 대상", "지표와 로그", "알림 규칙", "대시보드"]),
    ("devops", "log", ["로그 정책", "구조화 필드", "수집·보관", "검색 질의 예시"]),
    ("devops", "incident", ["사건 개요", "탐지·완화 절차", "롤백 계획", "사후 조치"]),
    ("devops", "strategy", ["전략 개요", "현재 상태", "목표 상태", "로드맵"]),
    ("devops", "review", ["검토 범위", "발견 사항", "권장 조치", "최종 판정"]),

    # orch — orchestration
    ("orch", "dispatch", ["요청 요약", "라우팅 결정", "대상 스킬·에이전트", "전달 페이로드"]),
    ("orch", "pipeline", ["파이프라인 DAG", "단계·체크포인트", "입출력 계약", "실패 복구"]),
    ("orch", "relay", ["사용자 의도", "대화 요약", "열린 결정", "다음 조치"]),
    ("orch", "run", ["실행 개요", "단계별 상태", "산출물 인덱스", "이슈·블로커"]),
    ("orch", "status", ["현재 상태 요약", "산출물 롤업", "승인 현황", "다음 조치"]),
    ("orch", "config", ["구성 맥락", "적용 값", "변경 이력", "검증 결과"]),
]


HEADER = """\
# {{title}}

> {{skill}}/{{agent}} · `{{artifact_id}}` · run `{{run_id}}`

구조화 데이터(상태, 승인, 참조, 데이터 페이로드)는 동일 디렉터리의
`meta.json`에 저장됩니다. 본 문서는 서술/근거/다이어그램 등
사람이 읽는 맥락만 포함합니다.

---

"""


FOOTER = """
---

## 메타데이터 메모

- 진행 상태와 승인 결과는 `scripts/artifact set`로 갱신합니다.
- 구조화 산출물은 `scripts/artifact set --data-file patch.json`으로 기록합니다.
- 이 본문(`body.md`)에는 machine-readable 데이터를 중복 복사하지 않습니다.
"""


def main() -> None:
    for skill, agent, sections in AGENTS:
        path = TEMPLATES_ROOT / skill / f"{agent}.md"
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        body = HEADER
        for section in sections:
            body += f"## {section}\n\n_TBD_\n\n"
        body += FOOTER
        path.write_text(body)
        print(f"wrote {path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
