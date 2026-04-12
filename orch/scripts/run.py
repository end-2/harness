#!/usr/bin/env python3
"""Run lifecycle manager for the Orch skill.

Single entry point for all run metadata manipulation. Orch must not edit
`run.meta.yaml` or `pipeline.meta.yaml` directly. It calls this script instead
so that schema validation, state transitions, timestamps, and audit history are
enforced consistently.

Subcommands:
    init-run      Create a new run with directory structure and metadata
    update-state  Update a step's status within a run
    complete      Mark a run as completed and generate reports
    cancel        Cancel a run with a reason
    list          List all runs
    show          Show details of a single run
    validate      Validate run metadata schema and integrity
    observe       Scan child skill .meta.yaml files, summarise state
    next          Return the next executable step or step group
    render        Regenerate human-readable files from run.meta.yaml
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

# Ensure lib/ is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.meta_io import (  # noqa: E402
    STEP_STATUSES,
    check_step_transition,
    load_yaml,
    now_iso,
    save_yaml,
    validate_run_meta,
)
VALID_SKILLS = (
    "ex",
    "re",
    "arch",
    "impl",
    "qa",
    "sec",
    "devops",
    "verify",
)

SKILL_AGENTS: dict[str, tuple[str, ...]] = {
    "ex": ("scan", "detect", "analyze", "map"),
    "re": ("elicit", "analyze", "spec", "review"),
    "arch": ("design", "adr", "diagram", "review"),
    "impl": ("generate", "pattern", "review", "refactor"),
    "qa": ("strategy", "generate", "trace", "report"),
    "sec": ("threat-model", "audit", "compliance"),
    "devops": ("pipeline", "iac", "observe", "runbook"),
    "verify": ("provision", "instrument", "scenario", "execute", "diagnose", "report"),
}

DEFAULT_AGENT_BY_SKILL: dict[str, str] = {
    "ex": "scan",
    "re": "elicit",
    "arch": "design",
    "impl": "generate",
    "qa": "generate",
    "sec": "audit",
    "devops": "pipeline",
    "verify": "execute",
}

TERMINAL_STEP_STATUSES = {"completed", "skipped"}
ACTIVE_RUN_STATUSES = {"pending", "running", "paused", "failed"}
TERMINAL_RUN_STATUSES = {"completed", "cancelled"}

PIPELINE_STEPS: dict[str, list[dict[str, str]]] = {
    "full-sdlc": [
        {"skill": "re", "agent": "elicit"},
        {"skill": "re", "agent": "analyze"},
        {"skill": "re", "agent": "spec"},
        {"skill": "arch", "agent": "design"},
        {"skill": "impl", "agent": "generate"},
        {"skill": "qa", "agent": "generate", "parallel_group": "post-impl"},
        {"skill": "sec", "agent": "audit", "parallel_group": "post-impl"},
        {"skill": "devops", "agent": "pipeline", "parallel_group": "post-impl"},
        {"skill": "verify", "agent": "provision"},
        {"skill": "verify", "agent": "execute"},
    ],
    "full-sdlc-existing": [
        {"skill": "ex", "agent": "scan"},
        {"skill": "ex", "agent": "detect"},
        {"skill": "ex", "agent": "analyze"},
        {"skill": "ex", "agent": "map"},
        {"skill": "re", "agent": "elicit"},
        {"skill": "re", "agent": "analyze"},
        {"skill": "re", "agent": "spec"},
        {"skill": "arch", "agent": "design"},
        {"skill": "impl", "agent": "generate"},
        {"skill": "qa", "agent": "generate", "parallel_group": "post-impl"},
        {"skill": "sec", "agent": "audit", "parallel_group": "post-impl"},
        {"skill": "devops", "agent": "pipeline", "parallel_group": "post-impl"},
        {"skill": "verify", "agent": "provision"},
        {"skill": "verify", "agent": "execute"},
    ],
    "new-feature": [
        {"skill": "re", "agent": "elicit"},
        {"skill": "re", "agent": "spec"},
        {"skill": "arch", "agent": "design"},
        {"skill": "impl", "agent": "generate"},
        {"skill": "qa", "agent": "generate"},
    ],
    "new-feature-existing": [
        {"skill": "ex", "agent": "scan"},
        {"skill": "ex", "agent": "detect"},
        {"skill": "ex", "agent": "analyze"},
        {"skill": "ex", "agent": "map"},
        {"skill": "re", "agent": "elicit"},
        {"skill": "re", "agent": "spec"},
        {"skill": "arch", "agent": "design"},
        {"skill": "impl", "agent": "generate"},
        {"skill": "qa", "agent": "generate"},
    ],
    "security-gate": [
        {"skill": "sec", "agent": "threat-model"},
        {"skill": "sec", "agent": "audit"},
        {"skill": "sec", "agent": "compliance"},
    ],
    "security-gate-existing": [
        {"skill": "ex", "agent": "scan"},
        {"skill": "ex", "agent": "detect"},
        {"skill": "ex", "agent": "analyze"},
        {"skill": "ex", "agent": "map"},
        {"skill": "sec", "agent": "threat-model"},
        {"skill": "sec", "agent": "audit"},
        {"skill": "sec", "agent": "compliance"},
    ],
    "quick-review": [
        {"skill": "re", "agent": "review"},
        {"skill": "arch", "agent": "review"},
        {"skill": "impl", "agent": "review"},
    ],
    "explore": [
        {"skill": "ex", "agent": "scan"},
        {"skill": "ex", "agent": "detect"},
        {"skill": "ex", "agent": "analyze"},
        {"skill": "ex", "agent": "map"},
    ],
    "integration-verify": [
        {"skill": "verify", "agent": "provision"},
        {"skill": "verify", "agent": "instrument"},
        {"skill": "verify", "agent": "scenario"},
        {"skill": "verify", "agent": "execute"},
        {"skill": "verify", "agent": "diagnose"},
        {"skill": "verify", "agent": "report"},
    ],
    "integration-verify-existing": [
        {"skill": "ex", "agent": "scan"},
        {"skill": "ex", "agent": "detect"},
        {"skill": "ex", "agent": "analyze"},
        {"skill": "ex", "agent": "map"},
        {"skill": "verify", "agent": "provision"},
        {"skill": "verify", "agent": "instrument"},
        {"skill": "verify", "agent": "scenario"},
        {"skill": "verify", "agent": "execute"},
        {"skill": "verify", "agent": "diagnose"},
        {"skill": "verify", "agent": "report"},
    ],
}


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def skill_dir() -> Path:
    env = os.environ.get("SKILL_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent


def templates_dir() -> Path:
    return skill_dir() / "assets" / "templates"


def output_root(override: str | None = None) -> Path:
    if override:
        return Path(override)
    env = os.environ.get("HARNESS_OUTPUT_ROOT")
    if env:
        return Path(env)
    return Path.cwd() / "harness-output"


def runs_dir(root: Path) -> Path:
    return root / "runs"


def run_dir(root: Path, run_id: str) -> Path:
    return runs_dir(root) / run_id


def run_meta_path(root: Path, run_id: str) -> Path:
    return run_dir(root, run_id) / "run.meta.yaml"


def current_run_path(root: Path) -> Path:
    return root / "current-run.md"


def pipeline_meta_path(root: Path) -> Path:
    return root / "pipeline.meta.yaml"


# ---------------------------------------------------------------------------
# Run ID generation
# ---------------------------------------------------------------------------


def generate_run_id() -> str:
    """Generate a run ID in format YYYYMMDD-HHmmss-<4hex>."""
    now = dt.datetime.now(dt.timezone.utc)
    ts = now.strftime("%Y%m%d-%H%M%S")
    digest = hashlib.sha256(f"{ts}-{os.getpid()}".encode()).hexdigest()[:4]
    return f"{ts}-{digest}"


# ---------------------------------------------------------------------------
# Pipeline config helpers
# ---------------------------------------------------------------------------


def _default_pipeline_meta(root: Path) -> dict[str, Any]:
    return {
        "output_root": str(root),
        "disabled_skills": [],
        "default_pipeline": "full-sdlc",
        "custom_pipelines": {},
        "active_run": None,
    }


def ensure_pipeline_meta(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    path = pipeline_meta_path(root)
    if path.exists():
        data = load_yaml(path)
    else:
        data = {}

    defaults = _default_pipeline_meta(root)
    changed = not path.exists()
    for key, value in defaults.items():
        if key not in data:
            data[key] = value
            changed = True

    if data.get("output_root") != str(root):
        data["output_root"] = str(root)
        changed = True
    if not isinstance(data.get("disabled_skills"), list):
        data["disabled_skills"] = []
        changed = True
    if not isinstance(data.get("custom_pipelines"), dict):
        data["custom_pipelines"] = {}
        changed = True
    if not isinstance(data.get("default_pipeline"), str):
        data["default_pipeline"] = "full-sdlc"
        changed = True

    if changed:
        save_yaml(path, data)
    return data


def set_active_run(root: Path, run_id: str | None) -> None:
    data = ensure_pipeline_meta(root)
    if data.get("active_run") == run_id and data.get("output_root") == str(root):
        return
    data["active_run"] = run_id
    data["output_root"] = str(root)
    save_yaml(pipeline_meta_path(root), data)


def active_run_id(root: Path) -> str | None:
    data = ensure_pipeline_meta(root)
    active = data.get("active_run")
    if isinstance(active, str) and active.strip():
        return active
    return None


def active_run_conflict(root: Path) -> tuple[str, dict[str, Any]] | None:
    active = active_run_id(root)
    if not active:
        return None

    meta_path = run_meta_path(root, active)
    if not meta_path.exists():
        set_active_run(root, None)
        return None

    meta = load_yaml(meta_path)
    if meta.get("status") in ACTIVE_RUN_STATUSES:
        return active, meta

    set_active_run(root, None)
    return None


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------


def render_template(template_name: str, context: dict[str, Any]) -> str:
    tmpl_path = templates_dir() / template_name
    if not tmpl_path.exists():
        raise FileNotFoundError(f"Template not found: {tmpl_path}")
    content = tmpl_path.read_text(encoding="utf-8")
    for key, value in context.items():
        content = content.replace(f"{{{{{key}}}}}", str(value))
    return content


# ---------------------------------------------------------------------------
# Pipeline helpers
# ---------------------------------------------------------------------------


def _validate_skill_agent(skill: str, agent: str) -> None:
    if skill not in VALID_SKILLS:
        raise ValueError(f"Unknown skill: {skill}")
    if agent and agent not in SKILL_AGENTS[skill]:
        raise ValueError(f"Unknown agent for {skill}: {agent}")


def _load_custom_pipeline_steps(root: Path, pipeline: str) -> list[dict[str, str]]:
    data = ensure_pipeline_meta(root)
    custom = data.get("custom_pipelines", {})
    spec = custom.get(pipeline)
    if spec is None:
        raise ValueError(f"Unknown pipeline: {pipeline}")
    if not isinstance(spec, dict):
        raise ValueError(f"Custom pipeline {pipeline!r} must be a mapping")
    raw_steps = spec.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ValueError(f"Custom pipeline {pipeline!r} must define a non-empty steps list")
    return raw_steps


def _build_steps(root: Path, pipeline: str) -> list[dict[str, Any]]:
    if pipeline in PIPELINE_STEPS:
        raw_steps = PIPELINE_STEPS[pipeline]
    elif pipeline.startswith("single:"):
        _, _, rest = pipeline.partition(":")
        skill, _, agent = rest.partition(":")
        if not skill:
            raise ValueError("Single-dispatch pipeline must include a skill")
        if not agent:
            agent = DEFAULT_AGENT_BY_SKILL.get(skill, "")
        _validate_skill_agent(skill, agent)
        raw_steps = [{"skill": skill, "agent": agent}]
    else:
        raw_steps = _load_custom_pipeline_steps(root, pipeline)

    steps: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_steps):
        if not isinstance(raw, dict):
            raise ValueError(f"Pipeline step {index} must be a mapping")
        skill = raw.get("skill", "")
        agent = raw.get("agent", "")
        if not isinstance(skill, str) or not skill:
            raise ValueError(f"Pipeline step {index} is missing a skill")
        if not isinstance(agent, str):
            raise ValueError(f"Pipeline step {index} has a non-string agent")
        _validate_skill_agent(skill, agent)

        step: dict[str, Any] = {
            "index": index,
            "skill": skill,
            "agent": agent,
            "status": "pending",
            "artifacts": [],
        }
        parallel_group = raw.get("parallel_group")
        if parallel_group:
            if not isinstance(parallel_group, str):
                raise ValueError(f"Pipeline step {index} has a non-string parallel_group")
            step["parallel_group"] = parallel_group
        steps.append(step)

    return steps


def _group_bounds(steps: list[dict[str, Any]], index: int) -> tuple[int, int]:
    group = steps[index].get("parallel_group")
    if not group:
        return index, index

    start = index
    while start > 0 and steps[start - 1].get("parallel_group") == group:
        start -= 1

    end = index
    while end + 1 < len(steps) and steps[end + 1].get("parallel_group") == group:
        end += 1

    return start, end


def _ready_steps(meta: dict[str, Any]) -> dict[str, Any]:
    steps = meta.get("steps", [])
    running = [step["index"] for step in steps if step.get("status") == "running"]
    if running:
        return {"waiting_on": running, "message": "Steps still running"}

    failed = [step["index"] for step in steps if step.get("status") == "failed"]
    if failed:
        return {
            "blocked_on_failed": failed,
            "message": "Retry or skip the failed step(s) before continuing",
        }

    for index, step in enumerate(steps):
        if step.get("status") != "pending":
            continue

        start, end = _group_bounds(steps, index)
        blockers = [
            steps[i]["index"]
            for i in range(start)
            if steps[i].get("status") not in TERMINAL_STEP_STATUSES
        ]
        if blockers:
            return {
                "blocked_on": blockers,
                "message": "Previous steps are not complete yet",
            }

        ready = []
        for candidate in range(start, end + 1):
            if steps[candidate].get("status") == "pending":
                ready.append(
                    {
                        "step": steps[candidate]["index"],
                        "skill": steps[candidate].get("skill"),
                        "agent": steps[candidate].get("agent", ""),
                    }
                )
        if ready:
            result: dict[str, Any] = {"ready_steps": ready}
            if len(ready) == 1:
                result["next_step"] = ready[0]["step"]
                result["skill"] = ready[0]["skill"]
                result["agent"] = ready[0]["agent"]
            return result

    return {"message": "All steps completed or no pending steps"}


def _recompute_run_status(meta: dict[str, Any]) -> str:
    statuses = [step.get("status") for step in meta.get("steps", [])]
    if any(status == "failed" for status in statuses):
        return "failed"
    if any(status in {"running", "completed", "skipped"} for status in statuses):
        return "running"
    return "pending"


# ---------------------------------------------------------------------------
# Artifact observation and reporting
# ---------------------------------------------------------------------------


def _observe_run_data(rdir: Path) -> dict[str, list[dict[str, Any]]]:
    skills_summary: dict[str, list[dict[str, Any]]] = {}
    for skill in VALID_SKILLS:
        skill_path = rdir / skill
        if not skill_path.exists():
            continue

        artifacts: list[dict[str, Any]] = []
        for meta_path in sorted(skill_path.glob("*.meta.yaml")):
            try:
                data = load_yaml(meta_path)
                artifacts.append(
                    {
                        "artifact_id": data.get("artifact_id", meta_path.stem),
                        "section": data.get("section", ""),
                        "phase": data.get("phase", "unknown"),
                        "approval": data.get("approval", {}).get("state", "unknown"),
                        "document_path": data.get("document_path", ""),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                artifacts.append({"file": meta_path.name, "error": str(exc)})

        if artifacts:
            skills_summary[skill] = artifacts

    return skills_summary


def _render_directory_tree(root: Path) -> str:
    lines: list[str] = [root.name]

    def walk(path: Path, prefix: str = "") -> None:
        entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
        for idx, entry in enumerate(entries):
            connector = "`-- " if idx == len(entries) - 1 else "|-- "
            lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                extension = "    " if idx == len(entries) - 1 else "|   "
                walk(entry, prefix + extension)

    walk(root)
    return "\n".join(lines)


def _artifacts_for_section(
    skills_summary: dict[str, list[dict[str, Any]]],
    *,
    skill: str,
    section: str | None = None,
) -> list[dict[str, Any]]:
    items = skills_summary.get(skill, [])
    if section is None:
        return items
    return [item for item in items if item.get("section") == section]


def _format_artifact_listing(artifacts: list[dict[str, Any]], empty_text: str) -> str:
    if not artifacts:
        return empty_text
    lines = []
    for artifact in artifacts:
        artifact_id = artifact.get("artifact_id", "unknown")
        section = artifact.get("section") or "unknown-section"
        phase = artifact.get("phase", "unknown")
        approval = artifact.get("approval", "unknown")
        lines.append(f"- {artifact_id} ({section}, phase={phase}, approval={approval})")
    return "\n".join(lines)


def _format_skill_summary(skills_summary: dict[str, list[dict[str, Any]]]) -> str:
    if not skills_summary:
        return "- No child skill artifacts were recorded."

    lines = []
    for skill in VALID_SKILLS:
        artifacts = skills_summary.get(skill)
        if not artifacts:
            continue
        approved = sum(1 for item in artifacts if item.get("approval") == "approved")
        lines.append(f"- {skill}: {len(artifacts)} artifact(s), {approved} approved")
    return "\n".join(lines)


def _format_traceability(meta: dict[str, Any]) -> str:
    lines = []
    for step in meta.get("steps", []):
        artifacts = ", ".join(step.get("artifacts", [])) or "no recorded artifacts"
        lines.append(
            f"- Step {step.get('index', '?')}: "
            f"{step.get('skill', '')}:{step.get('agent', '')} -> {artifacts}"
        )
    return "\n".join(lines) if lines else "- No step traceability recorded."


def _generate_completion_reports(root: Path, run_id: str, meta: dict[str, Any]) -> None:
    rdir = run_dir(root, run_id)
    skills_summary = _observe_run_data(rdir)

    project_context = {
        "run_id": run_id,
        "directory_tree": _render_directory_tree(rdir),
        "tech_stack": _format_artifact_listing(
            _artifacts_for_section(skills_summary, skill="arch", section="tech-stack"),
            "No architecture tech-stack artifacts were recorded.",
        ),
        "components": _format_artifact_listing(
            _artifacts_for_section(skills_summary, skill="arch", section="components"),
            "No architecture component artifacts were recorded.",
        ),
        "prerequisites": _format_artifact_listing(
            _artifacts_for_section(skills_summary, skill="impl", section="implementation-guide"),
            "See the impl artifacts for prerequisites.",
        ),
        "build_commands": "# See impl artifacts for exact build commands.",
        "run_commands": "# See impl artifacts for exact run commands.",
        "infrastructure": _format_artifact_listing(
            skills_summary.get("devops", []),
            "No DevOps artifacts were recorded.",
        ),
        "dependencies": _format_skill_summary(skills_summary),
    }
    (rdir / "project-structure.md").write_text(
        render_template("project-structure.md.tmpl", project_context),
        encoding="utf-8",
    )

    release_context = {
        "run_id": run_id,
        "pipeline": meta.get("pipeline", ""),
        "created_at": meta.get("created_at", ""),
        "ended_at": meta.get("ended_at", ""),
        "total_steps": len(meta.get("steps", [])),
        "completed_steps": sum(
            1
            for step in meta.get("steps", [])
            if step.get("status") in TERMINAL_STEP_STATUSES
        ),
        "skills_summary": _format_skill_summary(skills_summary),
        "key_decisions": _format_artifact_listing(
            _artifacts_for_section(skills_summary, skill="arch", section="decisions")
            + _artifacts_for_section(skills_summary, skill="impl", section="implementation-decisions"),
            "No explicit decision artifacts were recorded.",
        ),
        "quality_results": _format_artifact_listing(
            skills_summary.get("qa", []),
            "No QA artifacts were recorded.",
        ),
        "security_findings": _format_artifact_listing(
            skills_summary.get("sec", []),
            "No security artifacts were recorded.",
        ),
        "verification_verdict": _format_artifact_listing(
            skills_summary.get("verify", []),
            "No verification artifacts were recorded.",
        ),
        "known_limitations": (
            "\n".join(
                f"- [{item.get('type', 'error')}] {item.get('reason', item.get('message', item))}"
                for item in meta.get("errors", [])
            )
            if meta.get("errors")
            else "- No run-level limitations were recorded."
        ),
        "traceability_details": _format_traceability(meta),
    }
    (rdir / "release-note.md").write_text(
        render_template("completion-report.md.tmpl", release_context),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------


def _format_step_status(status: str) -> str:
    icon = {
        "completed": "done",
        "running": ">>",
        "failed": "FAIL",
        "skipped": "skip",
    }.get(status, "...")
    return f"{icon} {status}"


def _write_idle_current_run(
    root: Path,
    *,
    run_id: str,
    status: str,
    reason: str | None = None,
) -> None:
    lines = ["status: idle - no active run", ""]
    if status == "completed":
        lines.append(f"Last completed run: {run_id}")
        lines.append(f"Completed at: {now_iso()}")
    elif status == "cancelled":
        lines.append(f"Last run: {run_id} (cancelled)")
        if reason:
            lines.append(f"Reason: {reason}")
    else:
        lines.append(f"Last run: {run_id}")
    current_run_path(root).write_text("\n".join(lines) + "\n", encoding="utf-8")


def _render_current_run(root: Path, meta: dict[str, Any]) -> None:
    status = meta.get("status", "unknown")
    if status in TERMINAL_RUN_STATUSES:
        _write_idle_current_run(root, run_id=meta.get("run_id", "unknown"), status=status)
        return

    rows = []
    for step in meta.get("steps", []):
        rows.append(
            "| {index} | {skill} | {agent} | {status} |".format(
                index=step.get("index", "?"),
                skill=step.get("skill", ""),
                agent=step.get("agent", ""),
                status=_format_step_status(step.get("status", "pending")),
            )
        )

    content = render_template(
        "current-run.md.tmpl",
        {
            "run_id": meta.get("run_id", "unknown"),
            "pipeline": meta.get("pipeline", "unknown"),
            "status": status,
            "created_at": meta.get("created_at", ""),
            "updated_at": meta.get("updated_at", ""),
            "steps": "\n".join(rows),
        },
    )
    current_run_path(root).write_text(content, encoding="utf-8")


def _render_run_meta_md(root: Path, run_id: str, meta: dict[str, Any]) -> None:
    rows = []
    for step in meta.get("steps", []):
        artifacts = ", ".join(step.get("artifacts", [])) or "-"
        skill = step.get("skill", "")
        if step.get("parallel_group"):
            skill = f"{skill} [{step['parallel_group']}]"
        rows.append(
            "| {index} | {skill} | {agent} | {status} | {artifacts} |".format(
                index=step.get("index", "?"),
                skill=skill,
                agent=step.get("agent", ""),
                status=step.get("status", ""),
                artifacts=artifacts,
            )
        )

    dialogue_history = meta.get("dialogue_history", [])
    if isinstance(dialogue_history, list) and dialogue_history:
        dialogue_text = "\n".join(f"- {item}" for item in dialogue_history)
    else:
        dialogue_text = "- No dialogue recorded."

    errors = meta.get("errors", [])
    if isinstance(errors, list) and errors:
        error_text = "\n".join(
            f"- [{item.get('type', 'error')}] {item.get('reason', item.get('message', item))}"
            for item in errors
        )
    else:
        error_text = "- No run-level errors recorded."

    total = len(meta.get("steps", []))
    completed = sum(
        1 for step in meta.get("steps", []) if step.get("status") in TERMINAL_STEP_STATUSES
    )
    failed = sum(1 for step in meta.get("steps", []) if step.get("status") == "failed")
    progress = f"{completed}/{total} completed"
    if failed:
        progress += f", {failed} failed"

    content = render_template(
        "run.meta.md.tmpl",
        {
            "run_id": run_id,
            "pipeline": meta.get("pipeline", ""),
            "status": meta.get("status", ""),
            "progress": progress,
            "created_at": meta.get("created_at", ""),
            "updated_at": meta.get("updated_at", ""),
            "steps": "\n".join(rows),
            "dialogue_history": dialogue_text,
            "errors": error_text,
        },
    )
    (run_dir(root, run_id) / "run.meta.md").write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_pipeline_reference(root: Path, pipeline: Any) -> list[str]:
    if not isinstance(pipeline, str) or not pipeline:
        return ["'pipeline' must be a non-empty string"]
    try:
        _build_steps(root, pipeline)
    except ValueError as exc:
        return [str(exc)]
    return []


def _find_artifact_meta_path(rdir: Path, skill: str, artifact_id: str) -> Path | None:
    skill_dir_path = rdir / skill
    if not skill_dir_path.exists():
        return None

    for meta_path in skill_dir_path.glob("*.meta.yaml"):
        try:
            data = load_yaml(meta_path)
        except Exception:  # noqa: BLE001
            continue
        if data.get("artifact_id") == artifact_id:
            return meta_path
    return None


def _validate_run_integrity(root: Path, run_id: str, meta: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    meta_run_id = meta.get("run_id")
    if isinstance(meta_run_id, str) and meta_run_id != run_id:
        errors.append(
            f"Run id mismatch: directory is {run_id}, metadata says {meta_run_id}"
        )

    errors.extend(_validate_pipeline_reference(root, meta.get("pipeline")))

    steps = meta.get("steps", [])
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        skill = step.get("skill")
        agent = step.get("agent", "")
        if isinstance(skill, str) and skill in VALID_SKILLS and isinstance(agent, str):
            try:
                _validate_skill_agent(skill, agent)
            except ValueError as exc:
                errors.append(f"Step {index}: {exc}")

        artifacts = step.get("artifacts", [])
        if not isinstance(artifacts, list):
            continue
        for artifact_id in artifacts:
            if not isinstance(artifact_id, str):
                errors.append(f"Step {index}: artifact ref must be a string")
                continue
            if _find_artifact_meta_path(run_dir(root, run_id), str(skill), artifact_id) is None:
                errors.append(
                    f"Step {index}: artifact {artifact_id!r} is not present in {skill}/"
                )

    status = meta.get("status")
    if status == "completed":
        unfinished = [
            step.get("index", i)
            for i, step in enumerate(steps)
            if step.get("status") not in TERMINAL_STEP_STATUSES
        ]
        if unfinished:
            errors.append(
                "Completed run still has unfinished steps: "
                + ", ".join(str(item) for item in unfinished)
            )
        if not meta.get("ended_at"):
            errors.append("Completed run is missing ended_at")

    return errors


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_init_run(args: argparse.Namespace) -> None:
    """Create a new run directory with initialised metadata."""
    root = output_root(args.output_root)
    conflict = active_run_conflict(root)
    if conflict and not args.force:
        active_id, active_meta = conflict
        _err(
            "Active run already exists: "
            f"{active_id} ({active_meta.get('pipeline', 'unknown')}, "
            f"status={active_meta.get('status', 'unknown')}). "
            "Cancel or complete it first, or pass --force."
        )

    try:
        steps = _build_steps(root, args.pipeline)
    except ValueError as exc:
        _err(str(exc))
    run_id = generate_run_id()
    rdir = run_dir(root, run_id)

    rdir.mkdir(parents=True, exist_ok=True)
    for skill in VALID_SKILLS:
        (rdir / skill).mkdir(exist_ok=True)

    meta: dict[str, Any] = {
        "run_id": run_id,
        "pipeline": args.pipeline,
        "output_root": str(root),
        "status": "pending",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "steps": steps,
        "dialogue_history": [],
        "errors": [],
    }
    save_yaml(run_meta_path(root, run_id), meta, auto_timestamp=False)

    (rdir / "calls.log").write_text(
        f"# Orch call log - run {run_id}\n"
        f"# Created: {now_iso()}\n"
        f"# Pipeline: {args.pipeline}\n\n",
        encoding="utf-8",
    )

    ensure_pipeline_meta(root)
    set_active_run(root, run_id)
    _render_current_run(root, meta)
    _render_run_meta_md(root, run_id, meta)

    result = {"run_id": run_id, "run_dir": str(rdir), "pipeline": args.pipeline}
    print(json.dumps(result, indent=2))


def cmd_update_state(args: argparse.Namespace) -> None:
    """Update a step's status within a run."""
    root = output_root(args.output_root)
    meta_path = run_meta_path(root, args.run)
    meta = load_yaml(meta_path)

    steps = meta.get("steps", [])
    idx = args.step
    if idx < 0 or idx >= len(steps):
        _err(f"Step index {idx} out of range (0..{len(steps) - 1})")

    current = steps[idx].get("status", "pending")
    target = args.status
    if not check_step_transition(current, target):
        _err(f"Invalid step transition: {current} -> {target}")

    steps[idx]["status"] = target
    steps[idx]["updated_at"] = now_iso()
    meta["status"] = _recompute_run_status(meta)

    save_yaml(meta_path, meta)
    set_active_run(root, args.run)
    _render_current_run(root, meta)
    _render_run_meta_md(root, args.run, meta)
    print(json.dumps({"step": idx, "status": target, "run_status": meta["status"]}))


def cmd_complete(args: argparse.Namespace) -> None:
    """Mark a run as completed."""
    root = output_root(args.output_root)
    meta_path = run_meta_path(root, args.run)
    meta = load_yaml(meta_path)

    unfinished = [
        step.get("index", i)
        for i, step in enumerate(meta.get("steps", []))
        if step.get("status") not in TERMINAL_STEP_STATUSES
    ]
    if unfinished:
        _err(
            "Cannot complete run with unfinished steps: "
            + ", ".join(str(item) for item in unfinished)
        )

    if meta.get("status") in {"completed", "cancelled"}:
        _err(f"Cannot complete run in status '{meta['status']}'")

    meta["status"] = "completed"
    meta["ended_at"] = now_iso()
    save_yaml(meta_path, meta)

    _generate_completion_reports(root, args.run, meta)
    set_active_run(root, None)
    _write_idle_current_run(root, run_id=args.run, status="completed")
    _render_run_meta_md(root, args.run, meta)
    print(json.dumps({"run_id": args.run, "status": "completed"}))


def cmd_cancel(args: argparse.Namespace) -> None:
    """Cancel a run with a reason."""
    root = output_root(args.output_root)
    meta_path = run_meta_path(root, args.run)
    meta = load_yaml(meta_path)

    if meta.get("status") in TERMINAL_RUN_STATUSES:
        _err(f"Cannot cancel run in status '{meta['status']}'")

    meta["status"] = "cancelled"
    meta["ended_at"] = now_iso()
    meta.setdefault("errors", []).append(
        {
            "type": "cancellation",
            "reason": args.reason,
            "timestamp": now_iso(),
        }
    )
    save_yaml(meta_path, meta)

    set_active_run(root, None)
    _write_idle_current_run(
        root,
        run_id=args.run,
        status="cancelled",
        reason=args.reason,
    )
    _render_run_meta_md(root, args.run, meta)
    print(json.dumps({"run_id": args.run, "status": "cancelled"}))


def cmd_list(args: argparse.Namespace) -> None:
    """List all runs."""
    root = output_root(args.output_root)
    rd = runs_dir(root)
    if not rd.exists():
        print(json.dumps({"runs": []}))
        return

    runs: list[dict[str, Any]] = []
    for directory in sorted(rd.iterdir(), reverse=True):
        meta_path = directory / "run.meta.yaml"
        if not meta_path.exists():
            continue
        try:
            meta = load_yaml(meta_path)
            runs.append(
                {
                    "run_id": meta.get("run_id", directory.name),
                    "pipeline": meta.get("pipeline", "unknown"),
                    "status": meta.get("status", "unknown"),
                    "created_at": meta.get("created_at", ""),
                }
            )
        except Exception:  # noqa: BLE001
            runs.append({"run_id": directory.name, "status": "error_reading"})
    print(json.dumps({"runs": runs}, indent=2))


def cmd_show(args: argparse.Namespace) -> None:
    """Show single run details."""
    root = output_root(args.output_root)
    meta_path = run_meta_path(root, args.run)
    if not meta_path.exists():
        _err(f"Run not found: {args.run}")
    meta = load_yaml(meta_path)
    print(json.dumps(meta, indent=2, default=str))


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate run metadata schema and integrity."""
    root = output_root(args.output_root)

    if args.run:
        targets = [args.run]
    else:
        rd = runs_dir(root)
        targets = [
            directory.name
            for directory in sorted(rd.iterdir())
            if (directory / "run.meta.yaml").exists()
        ] if rd.exists() else []

    all_errors: dict[str, list[str]] = {}
    for run_id in targets:
        meta_path = run_meta_path(root, run_id)
        if not meta_path.exists():
            all_errors[run_id] = ["run.meta.yaml not found"]
            continue
        meta = load_yaml(meta_path)
        errors = validate_run_meta(meta)
        errors.extend(_validate_run_integrity(root, run_id, meta))
        if errors:
            all_errors[run_id] = errors

    if all_errors:
        print(json.dumps({"valid": False, "errors": all_errors}, indent=2))
        sys.exit(1)

    print(json.dumps({"valid": True, "runs_checked": len(targets)}))


def cmd_observe(args: argparse.Namespace) -> None:
    """Scan child skill .meta.yaml files and summarise phase/approval."""
    root = output_root(args.output_root)
    rdir = run_dir(root, args.run)
    if not rdir.exists():
        _err(f"Run directory not found: {args.run}")

    print(json.dumps({"run_id": args.run, "skills": _observe_run_data(rdir)}, indent=2))


def cmd_next(args: argparse.Namespace) -> None:
    """Return the next executable step based on current state."""
    root = output_root(args.output_root)
    meta = load_yaml(run_meta_path(root, args.run))
    print(json.dumps(_ready_steps(meta), indent=2))


def cmd_render(args: argparse.Namespace) -> None:
    """Regenerate run.meta.md and current-run.md from run.meta.yaml."""
    root = output_root(args.output_root)
    meta = load_yaml(run_meta_path(root, args.run))

    if meta.get("status") in TERMINAL_RUN_STATUSES:
        set_active_run(root, None)
        _write_idle_current_run(root, run_id=args.run, status=meta.get("status", "completed"))
    else:
        set_active_run(root, args.run)
        _render_current_run(root, meta)
    _render_run_meta_md(root, args.run, meta)
    print(json.dumps({"rendered": True, "run_id": args.run}))


def _err(msg: str) -> None:
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# CLI parser
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Orch run lifecycle manager")
    parser.add_argument("--output-root", default=None, help="Override output root path")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init-run", help="Create a new run")
    p_init.add_argument("--pipeline", required=True, help="Pipeline name or single:<skill>[:<agent>]")
    p_init.add_argument("--force", action="store_true", help="Allow a new run even if another run is active")

    p_upd = sub.add_parser("update-state", help="Update step status")
    p_upd.add_argument("--run", required=True, help="Run ID")
    p_upd.add_argument("--step", type=int, required=True, help="Step index")
    p_upd.add_argument("--status", required=True, choices=STEP_STATUSES, help="New status")

    p_comp = sub.add_parser("complete", help="Mark run completed")
    p_comp.add_argument("--run", required=True, help="Run ID")

    p_canc = sub.add_parser("cancel", help="Cancel a run")
    p_canc.add_argument("--run", required=True, help="Run ID")
    p_canc.add_argument("--reason", required=True, help="Cancellation reason")

    sub.add_parser("list", help="List all runs")

    p_show = sub.add_parser("show", help="Show run details")
    p_show.add_argument("--run", required=True, help="Run ID")

    p_val = sub.add_parser("validate", help="Validate run metadata")
    p_val.add_argument("--run", default=None, help="Specific run ID (optional)")

    p_obs = sub.add_parser("observe", help="Observe child skill states")
    p_obs.add_argument("--run", required=True, help="Run ID")

    p_next = sub.add_parser("next", help="Get next executable step")
    p_next.add_argument("--run", required=True, help="Run ID")

    p_rend = sub.add_parser("render", help="Regenerate human-readable files")
    p_rend.add_argument("--run", required=True, help="Run ID")

    args = parser.parse_args()
    cmd_map = {
        "init-run": cmd_init_run,
        "update-state": cmd_update_state,
        "complete": cmd_complete,
        "cancel": cmd_cancel,
        "list": cmd_list,
        "show": cmd_show,
        "validate": cmd_validate,
        "observe": cmd_observe,
        "next": cmd_next,
        "render": cmd_render,
    }
    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
