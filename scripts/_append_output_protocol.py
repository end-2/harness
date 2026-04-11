#!/usr/bin/env python3
"""Append a uniform Output Protocol block to every skill agent system prompt.

Idempotent: skips files that already contain the marker heading.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# skill -> list of agent file stems (matching files under <skill>/agents/*.md)
AGENTS: dict[str, list[str]] = {
    "ex":     ["scan", "detect", "analyze", "map"],
    "re":     ["elicit", "analyze", "spec", "review"],
    "arch":   ["design", "adr", "diagram", "review"],
    "impl":   ["generate", "pattern", "refactor", "review"],
    "qa":     ["strategy", "generate", "report", "review"],
    "sec":    ["threat-model", "audit", "compliance", "review"],
    "devops": ["slo", "iac", "pipeline", "monitor", "log", "incident", "strategy", "review"],
    "orch":   ["dispatch", "pipeline", "relay", "run", "status", "config"],
}

REVIEW_AGENTS = {
    ("arch", "review"),
    ("impl", "review"),
    ("qa", "review"),
    ("sec", "review"),
    ("devops", "review"),
    ("re", "review"),
}

MARKER = "## 출력 프로토콜 (Output Protocol)"


def block(skill: str, agent: str) -> str:
    is_review = (skill, agent) in REVIEW_AGENTS
    lines: list[str] = []
    lines.append("\n")
    lines.append(MARKER + "\n\n")
    lines.append(
        "모든 산출물은 `meta.json`(구조화 데이터·상태·승인)과 `body.md`(서술)로 분리되어\n"
        "`runs/<run_id>/<skill>/<agent>/` 아래에 저장됩니다. 메타데이터는 반드시\n"
        "`scripts/artifact` CLI를 통해서만 조작하며, 본문은 `body.md`를 직접 편집합니다.\n\n"
    )
    lines.append("### 표준 절차\n\n")
    lines.append(
        f"1. **초기화**: 세션 시작 시 아래 명령으로 산출물 쌍을 생성합니다.\n"
        f"   ```\n"
        f"   ./scripts/artifact init --skill {skill} --agent {agent} \\\n"
        f"       [--run-id <상위 run_id>] --title \"<요약 제목>\"\n"
        f"   ```\n"
        f"   - 파이프라인의 후속 에이전트는 상위 run_id를 전달받아 동일 run에 합류합니다.\n"
        f"   - 명령의 출력(`run_id`, `artifact_id`)을 이후 단계에서 재사용합니다.\n\n"
    )
    lines.append(
        "2. **본문 편집**: `scripts/artifact path <artifact_id> --run-id <id> --body`로\n"
        "   받은 경로의 `body.md`에 분석, 근거, 트레이드오프, 다이어그램 등\n"
        "   사람이 읽는 맥락을 작성합니다. machine-readable 데이터는 본문에\n"
        "   중복 기록하지 않습니다.\n\n"
    )
    lines.append(
        "3. **구조화 데이터 기록**: 이 스킬의 `skills.yaml` `output:` 스키마에 해당하는\n"
        "   JSON 객체를 임시 파일로 저장하고 다음 명령으로 `meta.json`의 `data:`에\n"
        "   병합합니다.\n"
        "   ```\n"
        "   ./scripts/artifact set <artifact_id> --run-id <id> --data-file patch.json\n"
        "   ```\n\n"
    )
    lines.append(
        "4. **추적성**: RE 산출물 및 상류 산출물을 참조로 연결합니다.\n"
        "   ```\n"
        "   ./scripts/artifact set <artifact_id> --run-id <id> \\\n"
        "       --ref-re FR-001 --ref-re NFR-002 --ref-upstream <상류 artifact_id>\n"
        "   ```\n\n"
    )
    lines.append(
        "5. **진행 상태**: 작업 단계에 따라 `progress`를 전이합니다\n"
        "   (`draft` → `in_progress` → `review` → `approved`/`rejected`).\n"
        "   ```\n"
        "   ./scripts/artifact set <artifact_id> --run-id <id> --progress review\n"
        "   ```\n\n"
    )
    if is_review:
        lines.append(
            "6. **승인 판정(리뷰 에이전트 전용)**: 검증 완료 후 최종 판정을 기록합니다.\n"
            "   ```\n"
            "   ./scripts/artifact set <artifact_id> --run-id <id> \\\n"
            "       --verdict APPROVED --approver <이름> --notes \"<요약>\"\n"
            "   ```\n"
            "   판정은 `APPROVED | CONDITIONAL | REJECTED` 중 하나이며, 대상 산출물의\n"
            "   `progress`도 같은 CLI 호출로 `approved` 또는 `rejected`로 갱신합니다.\n\n"
        )
    lines.append(
        "### 중요 규칙\n\n"
        "- `meta.json`을 에디터로 직접 수정하지 않습니다. 반드시 `scripts/artifact set`을\n"
        "  사용합니다.\n"
        "- `body.md`에는 YAML/JSON 블록으로 구조화 데이터를 중복 기록하지 않습니다.\n"
        "  구조화 데이터는 `meta.json.data`가 유일한 출처입니다.\n"
        "- `scripts/artifact validate <artifact_id> --run-id <id>`로 종료 전 필수\n"
        "  필드 누락 여부를 확인합니다.\n"
    )
    return "".join(lines)


def main() -> None:
    updated = 0
    for skill, agents in AGENTS.items():
        for agent in agents:
            path = REPO_ROOT / skill / "agents" / f"{agent}.md"
            if not path.is_file():
                print(f"missing: {path}")
                continue
            text = path.read_text()
            if MARKER in text:
                continue
            if not text.endswith("\n"):
                text += "\n"
            text += block(skill, agent)
            path.write_text(text)
            updated += 1
            print(f"updated {path.relative_to(REPO_ROOT)}")
    print(f"done: {updated} file(s) updated")


if __name__ == "__main__":
    main()
