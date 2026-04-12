#!/usr/bin/env python3
"""Run lifecycle manager for the Orch skill.

Single entry point for all run metadata manipulation. Orch must not edit
`run.meta.yaml` or `pipeline.meta.yaml` directly — it calls this script
instead so that schema validation, state transitions, timestamps, and
audit history are enforced consistently.

Subcommands:
    init-run      Create a new run with directory structure and metadata
    update-state  Update a step's status within a run
    complete      Mark a run as completed and generate reports
    cancel        Cancel a run with a reason
    list          List all runs
    show          Show details of a single run
    validate      Validate run metadata schema and integrity
    observe       Scan child skill .meta.yaml files, summarise state
    next          Return the next executable step
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

# Ensure lib/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.meta_io import (
    load_yaml,
    save_yaml,
    now_iso,
    validate_run_meta,
    check_run_transition,
    check_step_transition,
    RUN_STATUSES,
    STEP_STATUSES,
)
from lib.refs import is_valid_run_id

try:
    import yaml
except ImportError:
    sys.stderr.write("PyYAML is required. Install with: pip install pyyaml\n")
    sys.exit(2)


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
    h = hashlib.sha256(f"{ts}-{os.getpid()}".encode()).hexdigest()[:4]
    return f"{ts}-{h}"


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
# Subcommands
# ---------------------------------------------------------------------------

def cmd_init_run(args: argparse.Namespace) -> None:
    """Create a new run directory with initialised metadata."""
    root = output_root(args.output_root)
    rid = generate_run_id()
    rdir = run_dir(root, rid)

    # Create directory structure
    rdir.mkdir(parents=True, exist_ok=True)
    for skill in ("ex", "re", "arch", "impl", "qa", "sec", "devops", "verify"):
        (rdir / skill).mkdir(exist_ok=True)

    # Build steps from pipeline definition
    steps = _build_steps(args.pipeline)

    # Create run.meta.yaml
    meta: dict[str, Any] = {
        "run_id": rid,
        "pipeline": args.pipeline,
        "output_root": str(root),
        "status": "pending",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "steps": steps,
        "dialogue_history": [],
        "errors": [],
    }
    save_yaml(run_meta_path(root, rid), meta, auto_timestamp=False)

    # Create calls.log
    log_path = rdir / "calls.log"
    log_path.write_text(
        f"# Orch call log — run {rid}\n"
        f"# Created: {now_iso()}\n"
        f"# Pipeline: {args.pipeline}\n\n",
        encoding="utf-8",
    )

    # Render current-run.md
    _render_current_run(root, meta)

    # Render run.meta.md
    _render_run_meta_md(root, rid, meta)

    # Output
    result = {"run_id": rid, "run_dir": str(rdir), "pipeline": args.pipeline}
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

    # Auto-update run status
    if target == "running" and meta["status"] == "pending":
        meta["status"] = "running"
    elif target == "failed":
        meta["status"] = "failed"

    save_yaml(meta_path, meta)
    _render_current_run(root, meta)
    _render_run_meta_md(root, args.run, meta)
    print(json.dumps({"step": idx, "status": target, "run_status": meta["status"]}))


def cmd_complete(args: argparse.Namespace) -> None:
    """Mark a run as completed."""
    root = output_root(args.output_root)
    meta_path = run_meta_path(root, args.run)
    meta = load_yaml(meta_path)

    if not check_run_transition(meta["status"], "completed"):
        _err(f"Cannot complete run in status '{meta['status']}'")

    meta["status"] = "completed"
    meta["ended_at"] = now_iso()
    save_yaml(meta_path, meta)

    # Update current-run.md to idle
    cr = current_run_path(root)
    cr.write_text(
        f"status: idle — no active run\n\n"
        f"Last completed run: {args.run}\n"
        f"Completed at: {now_iso()}\n",
        encoding="utf-8",
    )

    _render_run_meta_md(root, args.run, meta)
    print(json.dumps({"run_id": args.run, "status": "completed"}))


def cmd_cancel(args: argparse.Namespace) -> None:
    """Cancel a run with a reason."""
    root = output_root(args.output_root)
    meta_path = run_meta_path(root, args.run)
    meta = load_yaml(meta_path)

    if not check_run_transition(meta["status"], "cancelled"):
        _err(f"Cannot cancel run in status '{meta['status']}'")

    meta["status"] = "cancelled"
    meta["ended_at"] = now_iso()
    meta.setdefault("errors", []).append({
        "type": "cancellation",
        "reason": args.reason,
        "timestamp": now_iso(),
    })
    save_yaml(meta_path, meta)

    cr = current_run_path(root)
    cr.write_text(
        f"status: idle — no active run\n\n"
        f"Last run: {args.run} (cancelled)\n"
        f"Reason: {args.reason}\n",
        encoding="utf-8",
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
    for d in sorted(rd.iterdir(), reverse=True):
        mp = d / "run.meta.yaml"
        if mp.exists():
            try:
                meta = load_yaml(mp)
                runs.append({
                    "run_id": meta.get("run_id", d.name),
                    "pipeline": meta.get("pipeline", "unknown"),
                    "status": meta.get("status", "unknown"),
                    "created_at": meta.get("created_at", ""),
                })
            except Exception:
                runs.append({"run_id": d.name, "status": "error_reading"})
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
        targets = [d.name for d in sorted(rd.iterdir()) if (d / "run.meta.yaml").exists()] if rd.exists() else []

    all_errors: dict[str, list[str]] = {}
    for rid in targets:
        mp = run_meta_path(root, rid)
        if not mp.exists():
            all_errors[rid] = [f"run.meta.yaml not found"]
            continue
        meta = load_yaml(mp)
        errors = validate_run_meta(meta)
        if errors:
            all_errors[rid] = errors

    if all_errors:
        print(json.dumps({"valid": False, "errors": all_errors}, indent=2))
        sys.exit(1)
    else:
        print(json.dumps({"valid": True, "runs_checked": len(targets)}))


def cmd_observe(args: argparse.Namespace) -> None:
    """Scan child skill .meta.yaml files and summarise phase/approval."""
    root = output_root(args.output_root)
    rdir = run_dir(root, args.run)
    if not rdir.exists():
        _err(f"Run directory not found: {args.run}")

    skills_summary: dict[str, list[dict[str, Any]]] = {}
    for skill in ("ex", "re", "arch", "impl", "qa", "sec", "devops", "verify"):
        skill_path = rdir / skill
        if not skill_path.exists():
            continue
        artifacts = []
        for mp in sorted(skill_path.glob("*.meta.yaml")):
            try:
                data = load_yaml(mp)
                artifacts.append({
                    "artifact_id": data.get("artifact_id", mp.stem),
                    "phase": data.get("phase", "unknown"),
                    "approval": data.get("approval", {}).get("state", "unknown"),
                })
            except Exception as e:
                artifacts.append({"file": mp.name, "error": str(e)})
        if artifacts:
            skills_summary[skill] = artifacts

    print(json.dumps({"run_id": args.run, "skills": skills_summary}, indent=2))


def cmd_next(args: argparse.Namespace) -> None:
    """Return the next executable step based on current state."""
    root = output_root(args.output_root)
    meta_path = run_meta_path(root, args.run)
    meta = load_yaml(meta_path)

    steps = meta.get("steps", [])
    for i, step in enumerate(steps):
        if step.get("status") == "pending":
            print(json.dumps({"next_step": i, "skill": step.get("skill"), "agent": step.get("agent", "")}))
            return

    # All steps done or no pending
    running = [i for i, s in enumerate(steps) if s.get("status") == "running"]
    if running:
        print(json.dumps({"waiting_on": running, "message": "Steps still running"}))
    else:
        print(json.dumps({"message": "All steps completed or no pending steps"}))


def cmd_render(args: argparse.Namespace) -> None:
    """Regenerate run.meta.md and current-run.md from run.meta.yaml."""
    root = output_root(args.output_root)
    meta_path = run_meta_path(root, args.run)
    meta = load_yaml(meta_path)

    _render_current_run(root, meta)
    _render_run_meta_md(root, args.run, meta)
    print(json.dumps({"rendered": True, "run_id": args.run}))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

PIPELINE_STEPS: dict[str, list[dict[str, str]]] = {
    "full-sdlc": [
        {"skill": "re", "agent": "elicit"}, {"skill": "re", "agent": "analyze"},
        {"skill": "re", "agent": "spec"}, {"skill": "arch", "agent": "design"},
        {"skill": "impl", "agent": "generate"},
        {"skill": "qa", "agent": "generate", "parallel_group": "post-impl"},
        {"skill": "sec", "agent": "audit", "parallel_group": "post-impl"},
        {"skill": "devops", "agent": "pipeline", "parallel_group": "post-impl"},
        {"skill": "verify", "agent": "provision"}, {"skill": "verify", "agent": "execute"},
    ],
    "full-sdlc-existing": [
        {"skill": "ex", "agent": "scan"}, {"skill": "ex", "agent": "detect"},
        {"skill": "ex", "agent": "analyze"}, {"skill": "ex", "agent": "map"},
        {"skill": "re", "agent": "elicit"}, {"skill": "re", "agent": "analyze"},
        {"skill": "re", "agent": "spec"}, {"skill": "arch", "agent": "design"},
        {"skill": "impl", "agent": "generate"},
        {"skill": "qa", "agent": "generate", "parallel_group": "post-impl"},
        {"skill": "sec", "agent": "audit", "parallel_group": "post-impl"},
        {"skill": "devops", "agent": "pipeline", "parallel_group": "post-impl"},
        {"skill": "verify", "agent": "provision"}, {"skill": "verify", "agent": "execute"},
    ],
    "new-feature": [
        {"skill": "re", "agent": "elicit"}, {"skill": "re", "agent": "spec"},
        {"skill": "arch", "agent": "design"}, {"skill": "impl", "agent": "generate"},
        {"skill": "qa", "agent": "generate"},
    ],
    "new-feature-existing": [
        {"skill": "ex", "agent": "scan"}, {"skill": "ex", "agent": "detect"},
        {"skill": "ex", "agent": "analyze"}, {"skill": "ex", "agent": "map"},
        {"skill": "re", "agent": "elicit"}, {"skill": "re", "agent": "spec"},
        {"skill": "arch", "agent": "design"}, {"skill": "impl", "agent": "generate"},
        {"skill": "qa", "agent": "generate"},
    ],
    "security-gate": [
        {"skill": "sec", "agent": "threat-model"}, {"skill": "sec", "agent": "audit"},
        {"skill": "sec", "agent": "compliance"},
    ],
    "security-gate-existing": [
        {"skill": "ex", "agent": "scan"}, {"skill": "ex", "agent": "detect"},
        {"skill": "ex", "agent": "analyze"}, {"skill": "ex", "agent": "map"},
        {"skill": "sec", "agent": "threat-model"}, {"skill": "sec", "agent": "audit"},
        {"skill": "sec", "agent": "compliance"},
    ],
    "quick-review": [
        {"skill": "re", "agent": "review"}, {"skill": "arch", "agent": "review"},
        {"skill": "impl", "agent": "review"},
    ],
    "explore": [
        {"skill": "ex", "agent": "scan"}, {"skill": "ex", "agent": "detect"},
        {"skill": "ex", "agent": "analyze"}, {"skill": "ex", "agent": "map"},
    ],
    "integration-verify": [
        {"skill": "verify", "agent": "provision"}, {"skill": "verify", "agent": "instrument"},
        {"skill": "verify", "agent": "scenario"}, {"skill": "verify", "agent": "execute"},
        {"skill": "verify", "agent": "diagnose"}, {"skill": "verify", "agent": "report"},
    ],
    "integration-verify-existing": [
        {"skill": "ex", "agent": "scan"}, {"skill": "ex", "agent": "detect"},
        {"skill": "ex", "agent": "analyze"}, {"skill": "ex", "agent": "map"},
        {"skill": "verify", "agent": "provision"}, {"skill": "verify", "agent": "instrument"},
        {"skill": "verify", "agent": "scenario"}, {"skill": "verify", "agent": "execute"},
        {"skill": "verify", "agent": "diagnose"}, {"skill": "verify", "agent": "report"},
    ],
}


def _build_steps(pipeline: str) -> list[dict[str, Any]]:
    if pipeline in PIPELINE_STEPS:
        steps = []
        for i, raw in enumerate(PIPELINE_STEPS[pipeline]):
            step: dict[str, Any] = {
                "index": i,
                "skill": raw["skill"],
                "agent": raw.get("agent", ""),
                "status": "pending",
                "artifacts": [],
            }
            if "parallel_group" in raw:
                step["parallel_group"] = raw["parallel_group"]
            steps.append(step)
        return steps
    elif pipeline.startswith("single:"):
        parts = pipeline.split(":")
        skill = parts[1] if len(parts) > 1 else "unknown"
        agent = parts[2] if len(parts) > 2 else ""
        return [{"index": 0, "skill": skill, "agent": agent, "status": "pending", "artifacts": []}]
    else:
        return [{"index": 0, "skill": "unknown", "agent": "", "status": "pending", "artifacts": []}]


def _render_current_run(root: Path, meta: dict[str, Any]) -> None:
    """Render current-run.md from run metadata."""
    root.mkdir(parents=True, exist_ok=True)
    cr = current_run_path(root)

    rid = meta.get("run_id", "unknown")
    pipeline = meta.get("pipeline", "unknown")
    status = meta.get("status", "unknown")
    steps = meta.get("steps", [])

    lines = [
        f"# Active Run: {rid}\n",
        f"- **Pipeline**: {pipeline}",
        f"- **Status**: {status}",
        f"- **Created**: {meta.get('created_at', '')}",
        f"- **Updated**: {meta.get('updated_at', '')}\n",
        "## Steps\n",
        "| # | Skill | Agent | Status |",
        "|---|-------|-------|--------|",
    ]
    for step in steps:
        idx = step.get("index", "?")
        skill = step.get("skill", "")
        agent = step.get("agent", "")
        st = step.get("status", "pending")
        icon = {"completed": "done", "running": ">>", "failed": "FAIL", "skipped": "skip"}.get(st, "...")
        lines.append(f"| {idx} | {skill} | {agent} | {icon} {st} |")

    errors = meta.get("errors", [])
    if errors:
        lines.append("\n## Errors\n")
        for e in errors:
            lines.append(f"- [{e.get('type', 'error')}] {e.get('reason', e.get('message', str(e)))}")

    cr.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _render_run_meta_md(root: Path, rid: str, meta: dict[str, Any]) -> None:
    """Render run.meta.md (human-readable view of run.meta.yaml)."""
    rdir = run_dir(root, rid)
    md_path = rdir / "run.meta.md"

    steps = meta.get("steps", [])
    total = len(steps)
    completed = sum(1 for s in steps if s.get("status") == "completed")
    failed = sum(1 for s in steps if s.get("status") == "failed")

    lines = [
        f"# Run {rid}\n",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Pipeline | {meta.get('pipeline', '')} |",
        f"| Status | {meta.get('status', '')} |",
        f"| Progress | {completed}/{total} completed{f', {failed} failed' if failed else ''} |",
        f"| Created | {meta.get('created_at', '')} |",
        f"| Updated | {meta.get('updated_at', '')} |",
    ]
    if meta.get("ended_at"):
        lines.append(f"| Ended | {meta['ended_at']} |")

    lines.extend([
        "\n## Steps\n",
        "| # | Skill | Agent | Status | Artifacts |",
        "|---|-------|-------|--------|-----------|",
    ])
    for step in steps:
        arts = ", ".join(step.get("artifacts", [])) or "—"
        pg = f" [{step['parallel_group']}]" if step.get("parallel_group") else ""
        lines.append(
            f"| {step.get('index', '?')} | {step.get('skill', '')}{pg} | "
            f"{step.get('agent', '')} | {step.get('status', '')} | {arts} |"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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

    # init-run
    p_init = sub.add_parser("init-run", help="Create a new run")
    p_init.add_argument("--pipeline", required=True, help="Pipeline name or single:<skill>[:<agent>]")

    # update-state
    p_upd = sub.add_parser("update-state", help="Update step status")
    p_upd.add_argument("--run", required=True, help="Run ID")
    p_upd.add_argument("--step", type=int, required=True, help="Step index")
    p_upd.add_argument("--status", required=True, choices=STEP_STATUSES, help="New status")

    # complete
    p_comp = sub.add_parser("complete", help="Mark run completed")
    p_comp.add_argument("--run", required=True, help="Run ID")

    # cancel
    p_canc = sub.add_parser("cancel", help="Cancel a run")
    p_canc.add_argument("--run", required=True, help="Run ID")
    p_canc.add_argument("--reason", required=True, help="Cancellation reason")

    # list
    sub.add_parser("list", help="List all runs")

    # show
    p_show = sub.add_parser("show", help="Show run details")
    p_show.add_argument("--run", required=True, help="Run ID")

    # validate
    p_val = sub.add_parser("validate", help="Validate run metadata")
    p_val.add_argument("--run", default=None, help="Specific run ID (optional)")

    # observe
    p_obs = sub.add_parser("observe", help="Observe child skill states")
    p_obs.add_argument("--run", required=True, help="Run ID")

    # next
    p_next = sub.add_parser("next", help="Get next executable step")
    p_next.add_argument("--run", required=True, help="Run ID")

    # render
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
