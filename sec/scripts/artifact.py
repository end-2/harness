#!/usr/bin/env python3
"""Artifact manager for the Sec skill.

Single entry point for all metadata manipulation. The Sec skill must not edit
`*.meta.yaml` files directly — it calls this script instead so that schema,
phase transitions, traceability, and audit history are enforced consistently.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "PyYAML is required. Install with: pip install pyyaml\n"
    )
    sys.exit(2)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKILL_NAME = "sec"

SECTIONS = ("threat-model", "vulnerability-report", "security-advisory", "compliance-report")

PHASES = ("draft", "in_review", "revising", "approved", "superseded")
PHASE_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"in_review", "superseded"},
    "in_review": {"revising", "approved", "superseded"},
    "revising": {"in_review", "superseded"},
    "approved": {"superseded"},
    "superseded": set(),
}

APPROVAL_STATES = ("pending", "approved", "rejected", "changes_requested", "conditionally_approved")
APPROVAL_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"approved", "rejected", "changes_requested", "conditionally_approved"},
    "changes_requested": {"pending", "approved", "rejected"},
    "rejected": {"pending"},
    "approved": set(),
    "conditionally_approved": {"pending", "approved"},
}

REQUIRED_META_FIELDS = (
    "artifact_id",
    "section",
    "phase",
    "progress",
    "approval",
    "upstream_refs",
    "downstream_refs",
    "cross_refs",
    "document_path",
    "updated_at",
)

REPORT_KINDS = ("analyze", "review", "threat-analysis", "audit-scan", "compliance-check")
REPORT_VERDICTS = ("pass", "at_risk", "fail", "n/a")
REPORT_REQUIRED_FIELDS = (
    "report_id",
    "kind",
    "skill",
    "stage",
    "created_at",
    "target_refs",
    "verdict",
    "summary",
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def skill_dir() -> Path:
    env = os.environ.get("SKILL_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent


def templates_dir() -> Path:
    return skill_dir() / "assets" / "templates"


def artifacts_dir() -> Path:
    env = os.environ.get("HARNESS_ARTIFACTS_DIR")
    if env:
        base = Path(env)
    else:
        base = Path.cwd() / "artifacts" / "sec"
    base.mkdir(parents=True, exist_ok=True)
    return base


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _session_id() -> str | None:
    """Return the current CLAUDE_SESSION_ID from the environment, or None."""
    return os.environ.get("CLAUDE_SESSION_ID")


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------


def load_meta(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be a mapping")
    return data


def save_meta(path: Path, data: dict[str, Any]) -> None:
    data["updated_at"] = now_iso()
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
    tmp.replace(path)


def find_meta_by_id(artifact_id: str) -> Path:
    for p in artifacts_dir().glob("*.meta.yaml"):
        try:
            data = load_meta(p)
        except Exception:
            continue
        if data.get("artifact_id") == artifact_id:
            return p
    raise FileNotFoundError(f"No artifact found with id {artifact_id!r}")


def all_meta_files() -> list[Path]:
    return sorted(artifacts_dir().glob("*.meta.yaml"))


# ---------------------------------------------------------------------------
# ID allocation
# ---------------------------------------------------------------------------


def next_artifact_id(section: str) -> str:
    prefix = {
        "threat-model": "SEC-TM",
        "vulnerability-report": "SEC-VA",
        "security-advisory": "SEC-SR",
        "compliance-report": "SEC-CR",
    }[section]
    existing: list[int] = []
    for p in all_meta_files():
        try:
            data = load_meta(p)
        except Exception:
            continue
        aid = data.get("artifact_id", "")
        if isinstance(aid, str) and aid.startswith(prefix + "-"):
            tail = aid.rsplit("-", 1)[-1]
            if tail.isdigit():
                existing.append(int(tail))
    n = (max(existing) + 1) if existing else 1
    return f"{prefix}-{n:03d}"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> int:
    section = args.section
    if section not in SECTIONS:
        sys.stderr.write(
            f"error: --section must be one of {SECTIONS}, got {section!r}\n"
        )
        return 2

    tmpl_md = templates_dir() / f"{section}.md.tmpl"
    tmpl_meta = templates_dir() / f"{section}.meta.yaml.tmpl"
    for t in (tmpl_md, tmpl_meta):
        if not t.exists():
            sys.stderr.write(f"error: template missing: {t}\n")
            return 2

    artifact_id = next_artifact_id(section)
    base = artifacts_dir()
    md_path = base / f"{artifact_id}.md"
    meta_path = base / f"{artifact_id}.meta.yaml"

    if md_path.exists() or meta_path.exists():
        sys.stderr.write(f"error: artifact {artifact_id} already exists\n")
        return 2

    shutil.copy(tmpl_md, md_path)

    meta_raw = tmpl_meta.read_text(encoding="utf-8")
    meta_data = yaml.safe_load(meta_raw) or {}
    meta_data["artifact_id"] = artifact_id
    meta_data["section"] = section
    meta_data.setdefault("phase", "draft")
    meta_data.setdefault(
        "progress", {"section_completed": 0, "section_total": 0, "percent": 0}
    )
    meta_data.setdefault(
        "approval",
        {
            "state": "pending",
            "approver": None,
            "approved_at": None,
            "notes": None,
            "history": [],
        },
    )
    meta_data.setdefault("upstream_refs", [])
    meta_data.setdefault("downstream_refs", [])
    meta_data.setdefault("cross_refs", {"threat_refs": [], "vuln_refs": []})
    meta_data["document_path"] = md_path.name
    meta_data["created_at"] = now_iso()
    save_meta(meta_path, meta_data)

    print(
        json.dumps(
            {
                "artifact_id": artifact_id,
                "section": section,
                "meta_path": str(meta_path),
                "document_path": str(md_path),
            },
            indent=2,
        )
    )
    return 0


def cmd_set_phase(args: argparse.Namespace) -> int:
    meta_path = find_meta_by_id(args.artifact_id)
    data = load_meta(meta_path)
    current = data.get("phase", "draft")
    target = args.phase
    if target not in PHASES:
        sys.stderr.write(f"error: unknown phase {target!r}\n")
        return 2
    if target not in PHASE_TRANSITIONS.get(current, set()) and target != current:
        sys.stderr.write(
            f"error: illegal phase transition {current!r} -> {target!r}\n"
        )
        return 2
    data["phase"] = target
    save_meta(meta_path, data)
    print(f"{args.artifact_id}: phase {current} -> {target}")
    return 0


def cmd_set_progress(args: argparse.Namespace) -> int:
    meta_path = find_meta_by_id(args.artifact_id)
    data = load_meta(meta_path)
    completed = int(args.completed)
    total = int(args.total)
    if total <= 0:
        sys.stderr.write("error: --total must be > 0\n")
        return 2
    if completed < 0 or completed > total:
        sys.stderr.write("error: --completed must be in [0, total]\n")
        return 2
    percent = int(round(100 * completed / total))
    data["progress"] = {
        "section_completed": completed,
        "section_total": total,
        "percent": percent,
    }
    save_meta(meta_path, data)
    print(f"{args.artifact_id}: progress {completed}/{total} ({percent}%)")
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    meta_path = find_meta_by_id(args.artifact_id)
    data = load_meta(meta_path)
    approval = data.setdefault(
        "approval",
        {"state": "pending", "history": []},
    )
    current_state = approval.get("state", "pending")
    target_state = args.state
    if target_state not in APPROVAL_STATES:
        sys.stderr.write(
            f"error: --state must be one of {APPROVAL_STATES}\n"
        )
        return 2
    if (
        target_state not in APPROVAL_TRANSITIONS.get(current_state, set())
        and target_state != current_state
    ):
        sys.stderr.write(
            f"error: illegal approval transition {current_state!r} -> "
            f"{target_state!r}\n"
        )
        return 2

    if target_state == "approved" and data.get("phase") != "in_review":
        sys.stderr.write(
            "error: artifact must be in_review before it can be approved\n"
        )
        return 2

    ts = now_iso()
    sid = _session_id()
    approval["state"] = target_state
    approval["approver"] = args.approver
    approval["notes"] = args.notes
    if target_state == "approved":
        approval["approved_at"] = ts
        data["phase"] = "approved"
    history = approval.setdefault("history", [])
    entry: dict[str, Any] = {
        "state": target_state,
        "approver": args.approver,
        "at": ts,
        "notes": args.notes,
        "session_id": sid,
    }
    history.append(entry)
    save_meta(meta_path, data)
    print(
        f"{args.artifact_id}: approval {current_state} -> {target_state} "
        f"by {args.approver}"
    )
    return 0


def cmd_link(args: argparse.Namespace) -> int:
    meta_path = find_meta_by_id(args.artifact_id)
    data = load_meta(meta_path)
    if not args.upstream and not args.downstream:
        sys.stderr.write("error: provide --upstream or --downstream\n")
        return 2
    if args.upstream:
        refs = data.setdefault("upstream_refs", [])
        if args.upstream not in refs:
            refs.append(args.upstream)
    if args.downstream:
        refs = data.setdefault("downstream_refs", [])
        if args.downstream not in refs:
            refs.append(args.downstream)
    save_meta(meta_path, data)

    if args.downstream:
        try:
            other_path = find_meta_by_id(args.downstream)
            other = load_meta(other_path)
            other_upstream = other.setdefault("upstream_refs", [])
            if args.artifact_id not in other_upstream:
                other_upstream.append(args.artifact_id)
                save_meta(other_path, other)
        except FileNotFoundError:
            pass
    if args.upstream:
        try:
            other_path = find_meta_by_id(args.upstream)
            other = load_meta(other_path)
            other_downstream = other.setdefault("downstream_refs", [])
            if args.artifact_id not in other_downstream:
                other_downstream.append(args.artifact_id)
                save_meta(other_path, other)
        except FileNotFoundError:
            pass

    print(f"{args.artifact_id}: links updated")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    meta_path = find_meta_by_id(args.artifact_id)
    data = load_meta(meta_path)
    print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    files = all_meta_files()
    if not files:
        print("(no artifacts yet)")
        return 0
    rows = []
    for p in files:
        try:
            d = load_meta(p)
        except Exception as e:
            rows.append((p.name, "(unreadable)", str(e), ""))
            continue
        rows.append(
            (
                d.get("artifact_id", "?"),
                d.get("section", "?"),
                d.get("phase", "?"),
                (d.get("approval") or {}).get("state", "?"),
            )
        )
    width = max(len(r[0]) for r in rows)
    for aid, section, phase, approval in rows:
        print(f"{aid:<{width}}  {section:<22}  {phase:<10}  {approval}")
    return 0


def _validate_meta(data: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_META_FIELDS:
        if field not in data:
            errors.append(f"{path.name}: missing field {field!r}")
    phase = data.get("phase")
    if phase not in PHASES:
        errors.append(f"{path.name}: unknown phase {phase!r}")
    section = data.get("section")
    if section not in SECTIONS:
        errors.append(f"{path.name}: unknown section {section!r}")
    approval = data.get("approval") or {}
    state = approval.get("state")
    if state and state not in APPROVAL_STATES:
        errors.append(f"{path.name}: unknown approval state {state!r}")
    doc_rel = data.get("document_path")
    if doc_rel:
        doc_path = path.parent / doc_rel
        if not doc_path.exists():
            errors.append(f"{path.name}: document_path missing: {doc_rel}")
    return errors


def _validate_traceability(all_data: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids = set(all_data.keys())
    for aid, data in all_data.items():
        for ref in data.get("downstream_refs") or []:
            if ref in ids:
                other = all_data[ref]
                if aid not in (other.get("upstream_refs") or []):
                    errors.append(
                        f"{aid}: downstream_ref {ref!r} lacks reciprocal upstream"
                    )
        for ref in data.get("upstream_refs") or []:
            if ref in ids:
                other = all_data[ref]
                if aid not in (other.get("downstream_refs") or []):
                    errors.append(
                        f"{aid}: upstream_ref {ref!r} lacks reciprocal downstream"
                    )
        # Validate cross_refs (threat_refs, vuln_refs)
        cross = data.get("cross_refs") or {}
        for ref_kind in ("threat_refs", "vuln_refs"):
            for ref in cross.get(ref_kind) or []:
                if ref in ids:
                    continue  # exists locally
                # Check cross-skill ref format
                if not any(ref.startswith(p) for p in ("ARCH-", "IMPL-", "RE-", "SEC-")):
                    errors.append(
                        f"{aid}: cross_ref {ref!r} in {ref_kind} has invalid prefix format"
                    )
    return errors


def cmd_validate(args: argparse.Namespace) -> int:
    files = all_meta_files()
    if not files:
        print("(no artifacts yet — nothing to validate)")
        return 0

    loaded: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    for p in files:
        try:
            data = load_meta(p)
        except Exception as e:
            errors.append(f"{p.name}: unreadable ({e})")
            continue
        if args.artifact_id and data.get("artifact_id") != args.artifact_id:
            continue
        errors.extend(_validate_meta(data, p))
        aid = data.get("artifact_id")
        if isinstance(aid, str):
            loaded[aid] = data

    errors.extend(_validate_traceability(loaded))

    print(f"artifacts directory: {artifacts_dir()}")
    print(f"artifacts found: {len(loaded)}")
    for aid, data in sorted(loaded.items()):
        phase = data.get("phase", "?")
        state = (data.get("approval") or {}).get("state", "?")
        section = data.get("section", "?")
        print(f"  {aid}  section={section}  phase={phase}  approval={state}")

    if errors:
        print()
        print(f"validation errors ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("OK")
    return 0


# ---------------------------------------------------------------------------
# Report (subagent -> main handoff)
# ---------------------------------------------------------------------------


def reports_dir() -> Path:
    base = artifacts_dir() / ".reports"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _now_compact() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _parse_report_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    fm_raw = text[4:end]
    body = text[end + 5 :]
    try:
        fm = yaml.safe_load(fm_raw) or {}
    except Exception:
        fm = {}
    if not isinstance(fm, dict):
        fm = {}
    return fm, body


def _all_report_files() -> list[Path]:
    return sorted(reports_dir().glob("*.md"))


def _find_report(report_id: str) -> Path:
    for p in _all_report_files():
        if p.stem == report_id:
            return p
        fm, _ = _parse_report_frontmatter(p)
        if fm.get("report_id") == report_id:
            return p
    raise FileNotFoundError(f"No report found with id {report_id!r}")


def cmd_report_path(args: argparse.Namespace) -> int:
    kind = args.kind
    if kind not in REPORT_KINDS:
        sys.stderr.write(f"error: --kind must be one of {REPORT_KINDS}\n")
        return 2
    stage = args.stage
    targets = args.target or []
    scope_raw = args.scope or ("-".join(targets) if targets else "all")
    scope = "".join(
        c if (c.isalnum() or c in "-_") else "_" for c in scope_raw
    ) or "all"
    ts = _now_compact()
    report_id = f"{stage}-{scope}-{ts}"
    path = reports_dir() / f"{report_id}.md"
    stub = {
        "report_id": report_id,
        "kind": kind,
        "skill": SKILL_NAME,
        "stage": stage,
        "created_at": now_iso(),
        "target_refs": targets,
        "verdict": "n/a",
        "summary": "",
        "proposed_meta_ops": [],
        "items": [],
    }
    fm = yaml.safe_dump(stub, sort_keys=False, allow_unicode=True).rstrip()
    path.write_text(
        f"---\n{fm}\n---\n\n# {kind} report ({SKILL_NAME}/{stage})\n\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"report_id": report_id, "path": str(path)},
            indent=2,
        )
    )
    return 0


def cmd_report_list(args: argparse.Namespace) -> int:
    rows: list[tuple[str, str, str, str, str, str]] = []
    for p in _all_report_files():
        fm, _ = _parse_report_frontmatter(p)
        if args.kind and fm.get("kind") != args.kind:
            continue
        if args.stage and fm.get("stage") != args.stage:
            continue
        if args.target:
            refs = fm.get("target_refs") or []
            if args.target not in refs:
                continue
        rows.append(
            (
                fm.get("report_id", p.stem),
                fm.get("kind", "?"),
                fm.get("stage", "?"),
                fm.get("verdict", "?"),
                (fm.get("summary") or "").strip(),
                str(p),
            )
        )
    if not rows:
        print("(no reports)")
        return 0
    rows.sort(key=lambda r: r[0], reverse=True)
    for rid, kind, stage, verdict, summary, _path in rows:
        s = summary if len(summary) <= 60 else summary[:57] + "..."
        print(
            f"{rid}  kind={kind}  stage={stage}  verdict={verdict}  {s}"
        )
    return 0


def cmd_report_show(args: argparse.Namespace) -> int:
    p = _find_report(args.report_id)
    print(p.read_text(encoding="utf-8"))
    return 0


def cmd_report_validate(args: argparse.Namespace) -> int:
    arg = args.report
    candidate = Path(arg)
    if candidate.is_file():
        p = candidate
    else:
        p = _find_report(arg)
    fm, body = _parse_report_frontmatter(p)
    errors: list[str] = []
    for field in REPORT_REQUIRED_FIELDS:
        if field not in fm:
            errors.append(f"missing field: {field}")
    if "kind" in fm and fm["kind"] not in REPORT_KINDS:
        errors.append(f"unknown kind: {fm['kind']!r}")
    if "verdict" in fm and fm["verdict"] not in REPORT_VERDICTS:
        errors.append(f"unknown verdict: {fm['verdict']!r}")
    if "skill" in fm and fm["skill"] != SKILL_NAME:
        errors.append(
            f"skill mismatch: report says {fm['skill']!r}, "
            f"this script is for {SKILL_NAME!r}"
        )
    if "target_refs" in fm and not isinstance(fm["target_refs"], list):
        errors.append("target_refs must be a list")
    if "proposed_meta_ops" in fm and not isinstance(
        fm["proposed_meta_ops"], list
    ):
        errors.append("proposed_meta_ops must be a list")
    if "items" in fm and not isinstance(fm["items"], list):
        errors.append("items must be a list")
    if not (fm.get("summary") or "").strip():
        errors.append("summary is empty (subagent must write a one-line summary)")
    stripped_body = "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith("#")
    ).strip()
    if not stripped_body:
        errors.append("body has no content beyond the header")
    if errors:
        print(f"{p.name}: INVALID")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"{p.name}: OK")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="artifact.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="create a new artifact from templates")
    sp.add_argument("--section", required=True, choices=SECTIONS)
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("set-phase", help="transition the phase")
    sp.add_argument("artifact_id")
    sp.add_argument("phase", choices=PHASES)
    sp.set_defaults(func=cmd_set_phase)

    sp = sub.add_parser("set-progress", help="update progress counters")
    sp.add_argument("artifact_id")
    sp.add_argument("--completed", required=True, type=int)
    sp.add_argument("--total", required=True, type=int)
    sp.set_defaults(func=cmd_set_progress)

    sp = sub.add_parser("approve", help="transition the approval state")
    sp.add_argument("artifact_id")
    sp.add_argument(
        "--state",
        default="approved",
        choices=APPROVAL_STATES,
    )
    sp.add_argument("--approver", required=True)
    sp.add_argument("--notes", default=None)
    sp.set_defaults(func=cmd_approve)

    sp = sub.add_parser("link", help="add an upstream/downstream reference")
    sp.add_argument("artifact_id")
    sp.add_argument("--upstream", default=None)
    sp.add_argument("--downstream", default=None)
    sp.set_defaults(func=cmd_link)

    sp = sub.add_parser("show", help="pretty-print an artifact's metadata")
    sp.add_argument("artifact_id")
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("list", help="list all artifacts in the project")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("validate", help="validate schema and traceability")
    sp.add_argument("artifact_id", nargs="?", default=None)
    sp.set_defaults(func=cmd_validate)

    sp = sub.add_parser(
        "report",
        help="manage subagent -> main handoff reports (file-based)",
    )
    sp_sub = sp.add_subparsers(dest="report_cmd", required=True)

    rp = sp_sub.add_parser(
        "path",
        help="allocate a fresh report file path and write a stub",
    )
    rp.add_argument("--kind", required=True, choices=REPORT_KINDS)
    rp.add_argument(
        "--stage",
        required=True,
        help="workflow stage producing the report (e.g. threat-model, audit)",
    )
    rp.add_argument(
        "--target",
        action="append",
        default=None,
        help="target artifact id; repeatable for multi-target reports",
    )
    rp.add_argument(
        "--scope",
        default=None,
        help="optional scope name when there is no single target",
    )
    rp.set_defaults(func=cmd_report_path)

    rp = sp_sub.add_parser("list", help="list reports, newest first")
    rp.add_argument("--kind", default=None)
    rp.add_argument("--stage", default=None)
    rp.add_argument("--target", default=None)
    rp.set_defaults(func=cmd_report_list)

    rp = sp_sub.add_parser("show", help="print a report (frontmatter + body)")
    rp.add_argument("report_id")
    rp.set_defaults(func=cmd_report_show)

    rp = sp_sub.add_parser(
        "validate",
        help="validate a report's frontmatter against the contract",
    )
    rp.add_argument("report", help="report id or path")
    rp.set_defaults(func=cmd_report_validate)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as e:
        sys.stderr.write(f"error: {e}\n")
        return 2
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"error: {e}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
