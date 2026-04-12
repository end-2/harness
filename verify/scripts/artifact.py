#!/usr/bin/env python3
"""Artifact manager for the Verify skill.

Single entry point for all metadata manipulation. The Verify skill must not edit
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

SECTIONS = (
    "environment",
    "scenario",
    "report",
)

PHASES = ("draft", "in_review", "revising", "approved", "superseded")
PHASE_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"in_review", "superseded"},
    "in_review": {"revising", "approved", "superseded"},
    "revising": {"in_review", "superseded"},
    "approved": {"superseded"},
    "superseded": set(),
}

APPROVAL_STATES = ("pending", "approved", "rejected", "changes_requested")
APPROVAL_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"approved", "rejected", "changes_requested"},
    "changes_requested": {"pending", "approved", "rejected"},
    "rejected": {"pending"},
    "approved": set(),
}

REQUIRED_META_FIELDS = (
    "artifact_id",
    "section",
    "phase",
    "progress",
    "approval",
    "upstream_refs",
    "downstream_refs",
    "document_path",
    "created_at",
    "updated_at",
)

SCENARIO_CATEGORIES = (
    "integration",
    "failure",
    "load",
    "observability",
)

SECTION_PAYLOAD_KEYS = {
    "environment": "environment_config",
    "scenario": "verification_scenarios",
    "report": "verification_report",
}


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
        base = Path.cwd() / "artifacts" / "verify"
    base.mkdir(parents=True, exist_ok=True)
    return base


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


SECTION_PREFIX = {
    "environment": "VERIFY-ENV",
    "scenario": "VERIFY-SC",
    "report": "VERIFY-RPT",
}


def next_artifact_id(section: str) -> str:
    prefix = SECTION_PREFIX[section]
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
    approval["state"] = target_state
    approval["approver"] = args.approver
    approval["notes"] = args.notes
    if target_state == "approved":
        approval["approved_at"] = ts
        data["phase"] = "approved"
    history = approval.setdefault("history", [])
    history.append(
        {
            "state": target_state,
            "approver": args.approver,
            "at": ts,
            "notes": args.notes,
        }
    )
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

    # Bidirectional integrity: update the other side if locally resolvable
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
        print(f"{aid:<{width}}  {section:<14}  {phase:<10}  {approval}")
    return 0


def _validate_meta(data: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_META_FIELDS:
        if field not in data:
            errors.append(f"{path.name}: missing field {field!r}")
    artifact_id = data.get("artifact_id")
    section = data.get("section")
    if not isinstance(artifact_id, str) or not artifact_id.strip():
        errors.append(f"{path.name}: artifact_id must be a non-empty string")
    elif section in SECTION_PREFIX:
        prefix = SECTION_PREFIX[section]
        if not artifact_id.startswith(prefix + "-"):
            errors.append(
                f"{path.name}: artifact_id {artifact_id!r} does not match "
                f"section prefix {prefix!r}"
            )
    phase = data.get("phase")
    if phase not in PHASES:
        errors.append(f"{path.name}: unknown phase {phase!r}")
    if section not in SECTIONS:
        errors.append(f"{path.name}: unknown section {section!r}")
    errors.extend(_validate_progress(data.get("progress"), path.name))
    errors.extend(_validate_approval(data.get("approval"), phase, path.name))
    errors.extend(_validate_timestamp("created_at", data.get("created_at"), path.name))
    errors.extend(_validate_timestamp("updated_at", data.get("updated_at"), path.name))
    errors.extend(_validate_ref_list("upstream_refs", data.get("upstream_refs"), path.name))
    errors.extend(
        _validate_ref_list("downstream_refs", data.get("downstream_refs"), path.name)
    )
    doc_rel = data.get("document_path")
    if doc_rel and isinstance(doc_rel, str):
        doc_path = path.parent / doc_rel
        if not doc_path.exists():
            errors.append(f"{path.name}: document_path missing: {doc_rel}")
    elif doc_rel is not None:
        errors.append(f"{path.name}: document_path must be a string")
    errors.extend(_validate_section_payload(data, path.name))
    return errors


def _validate_timestamp(
    field_name: str,
    value: Any,
    context: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{context}: {field_name} must be a non-empty string")
        return errors
    try:
        dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        errors.append(
            f"{context}: {field_name} must be an ISO 8601 UTC timestamp "
            f"(YYYY-MM-DDTHH:MM:SSZ)"
        )
    return errors


def _validate_ref_list(
    field_name: str,
    value: Any,
    context: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, list):
        return [f"{context}: {field_name} must be a list"]
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(
                f"{context}: {field_name}[{idx}] must be a non-empty string"
            )
    return errors


def _validate_progress(progress: Any, context: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(progress, dict):
        return [f"{context}: progress must be a mapping"]
    completed = progress.get("section_completed")
    total = progress.get("section_total")
    percent = progress.get("percent")
    for field_name, value in (
        ("section_completed", completed),
        ("section_total", total),
        ("percent", percent),
    ):
        if not isinstance(value, int):
            errors.append(f"{context}: progress.{field_name} must be an integer")
    if errors:
        return errors
    if total < 0:
        errors.append(f"{context}: progress.section_total must be >= 0")
    if completed < 0:
        errors.append(f"{context}: progress.section_completed must be >= 0")
    if total == 0:
        if completed != 0 or percent != 0:
            errors.append(
                f"{context}: zero-total progress must stay at 0/0 (0%) until work starts"
            )
        return errors
    if completed > total:
        errors.append(
            f"{context}: progress.section_completed must be <= progress.section_total"
        )
    expected_percent = int(round(100 * completed / total))
    if percent != expected_percent:
        errors.append(
            f"{context}: progress.percent must equal {expected_percent} for "
            f"{completed}/{total}"
        )
    return errors


def _validate_approval(approval: Any, phase: Any, context: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(approval, dict):
        return [f"{context}: approval must be a mapping"]
    state = approval.get("state")
    if state not in APPROVAL_STATES:
        errors.append(f"{context}: unknown approval state {state!r}")
    approver = approval.get("approver")
    if approver is not None and not isinstance(approver, str):
        errors.append(f"{context}: approval.approver must be a string or null")
    approved_at = approval.get("approved_at")
    if approved_at is not None:
        errors.extend(_validate_timestamp("approval.approved_at", approved_at, context))
    notes = approval.get("notes")
    if notes is not None and not isinstance(notes, str):
        errors.append(f"{context}: approval.notes must be a string or null")
    history = approval.get("history")
    if not isinstance(history, list):
        errors.append(f"{context}: approval.history must be a list")
    else:
        for idx, item in enumerate(history):
            if not isinstance(item, dict):
                errors.append(f"{context}: approval.history[{idx}] must be a mapping")
                continue
            item_state = item.get("state")
            if item_state not in APPROVAL_STATES:
                errors.append(
                    f"{context}: approval.history[{idx}].state has invalid value "
                    f"{item_state!r}"
                )
            if not isinstance(item.get("approver"), str) or not item["approver"].strip():
                errors.append(
                    f"{context}: approval.history[{idx}].approver must be a "
                    "non-empty string"
                )
            errors.extend(
                _validate_timestamp(
                    f"approval.history[{idx}].at",
                    item.get("at"),
                    context,
                )
            )
            if item.get("notes") is not None and not isinstance(item.get("notes"), str):
                errors.append(
                    f"{context}: approval.history[{idx}].notes must be a string or null"
                )
    if state == "approved":
        if phase != "approved":
            errors.append(
                f"{context}: approval.state 'approved' requires phase 'approved'"
            )
        if approved_at is None:
            errors.append(
                f"{context}: approval.approved_at is required when state is 'approved'"
            )
    elif phase == "approved":
        errors.append(
            f"{context}: phase 'approved' requires approval.state 'approved'"
        )
    return errors


def _validate_string_list(
    field_name: str,
    value: Any,
    context: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, list):
        return [f"{context}: {field_name} must be a list"]
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            errors.append(f"{context}: {field_name}[{idx}] must be a non-empty string")
    return errors


def _validate_section_payload(data: dict[str, Any], context: str) -> list[str]:
    errors: list[str] = []
    section = data.get("section")
    payload_key = SECTION_PAYLOAD_KEYS.get(section)
    if payload_key is None:
        return errors
    if payload_key not in data:
        return [f"{context}: missing section payload {payload_key!r}"]
    payload = data.get(payload_key)
    if section == "environment":
        errors.extend(_validate_environment_payload(payload, context))
    elif section == "scenario":
        errors.extend(_validate_scenario_payload(payload, context))
    elif section == "report":
        errors.extend(_validate_report_payload(payload, context))
    return errors


def _validate_environment_payload(payload: Any, context: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{context}: environment_config must be a mapping"]
    mode = payload.get("mode")
    if mode is not None and mode not in ("light", "heavy"):
        errors.append(f"{context}: environment_config.mode must be light, heavy, or null")
    compose_file = payload.get("compose_file")
    if compose_file is not None and not isinstance(compose_file, str):
        errors.append(f"{context}: environment_config.compose_file must be a string or null")
    if not isinstance(payload.get("services"), list):
        errors.append(f"{context}: environment_config.services must be a list")
    if not isinstance(payload.get("observability_stack"), dict):
        errors.append(
            f"{context}: environment_config.observability_stack must be a mapping"
        )
    network_topology = payload.get("network_topology")
    if not isinstance(network_topology, dict):
        errors.append(
            f"{context}: environment_config.network_topology must be a mapping"
        )
    else:
        if not isinstance(network_topology.get("networks"), list):
            errors.append(
                f"{context}: environment_config.network_topology.networks must be a list"
            )
        if not isinstance(network_topology.get("exposed_ports"), list):
            errors.append(
                f"{context}: environment_config.network_topology.exposed_ports "
                "must be a list"
            )
    if not isinstance(payload.get("startup_order"), list):
        errors.append(f"{context}: environment_config.startup_order must be a list")
    if not isinstance(payload.get("instrumentation_status"), dict):
        errors.append(
            f"{context}: environment_config.instrumentation_status must be a mapping"
        )
    for refs_field in ("impl_refs", "devops_refs", "arch_refs"):
        errors.extend(
            _validate_string_list(
                f"environment_config.{refs_field}",
                payload.get(refs_field),
                context,
            )
        )
    return errors


def _validate_scenario_payload(payload: Any, context: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, list):
        return [f"{context}: verification_scenarios must be a list"]
    for idx, item in enumerate(payload):
        if not isinstance(item, dict):
            errors.append(f"{context}: verification_scenarios[{idx}] must be a mapping")
            continue
        for field_name in (
            "id",
            "category",
            "title",
            "description",
            "preconditions",
            "steps",
            "expected_results",
            "evidence_type",
        ):
            if field_name not in item:
                errors.append(
                    f"{context}: verification_scenarios[{idx}] missing field "
                    f"{field_name!r}"
                )
        category = item.get("category")
        if category not in SCENARIO_CATEGORIES:
            errors.append(
                f"{context}: verification_scenarios[{idx}].category has invalid "
                f"value {category!r}"
            )
        for field_name in (
            "preconditions",
            "steps",
            "expected_results",
            "evidence_type",
        ):
            if field_name in item and not isinstance(item.get(field_name), list):
                errors.append(
                    f"{context}: verification_scenarios[{idx}].{field_name} must be a list"
                )
        for refs_field in ("arch_refs", "re_refs", "slo_refs"):
            if refs_field in item:
                errors.extend(
                    _validate_string_list(
                        f"verification_scenarios[{idx}].{refs_field}",
                        item.get(refs_field),
                        context,
                    )
                )
    return errors


def _validate_report_payload(payload: Any, context: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return [f"{context}: verification_report must be a mapping"]
    verdict = payload.get("verdict")
    if verdict is not None and verdict not in ("pass", "pass_with_issues", "fail"):
        errors.append(
            f"{context}: verification_report.verdict must be pass, "
            "pass_with_issues, fail, or null"
        )
    for field_name in (
        "scenario_results",
        "evidence_artifacts",
        "issues",
        "slo_validation",
        "feedback",
        "arch_refs",
        "impl_refs",
        "devops_refs",
        "re_refs",
    ):
        if not isinstance(payload.get(field_name), list):
            errors.append(f"{context}: verification_report.{field_name} must be a list")
    environment_health = payload.get("environment_health")
    if not isinstance(environment_health, dict):
        errors.append(
            f"{context}: verification_report.environment_health must be a mapping"
        )
    elif not isinstance(environment_health.get("services"), list):
        errors.append(
            f"{context}: verification_report.environment_health.services must be a list"
        )
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
# Report (subagent → main handoff)
# ---------------------------------------------------------------------------

SKILL_NAME = "verify"

REPORT_KINDS = (
    "scenario",
    "report",
)
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
REPORT_ITEM_CLASSIFICATIONS = {
    "scenario": {
        "content_draft",
        "coverage_gap",
        "source_ambiguity",
    },
    "report": {
        "verdict_summary",
        "impl_feedback",
        "devops_feedback",
        "arch_feedback",
        "traceability_gap",
        "slo_gap",
    },
}
REPORT_META_OPS = (
    "set-progress",
    "set-phase",
    "link",
    "approve",
)


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
    if "report_id" in fm and (
        not isinstance(fm["report_id"], str) or not fm["report_id"].strip()
    ):
        errors.append("report_id must be a non-empty string")
    if "stage" in fm and (not isinstance(fm["stage"], str) or not fm["stage"].strip()):
        errors.append("stage must be a non-empty string")
    if "created_at" in fm:
        errors.extend(_validate_timestamp("created_at", fm["created_at"], p.name))
    if "target_refs" in fm:
        errors.extend(_validate_ref_list("target_refs", fm["target_refs"], p.name))
    proposed_meta_ops = fm.get("proposed_meta_ops")
    if proposed_meta_ops is not None:
        if not isinstance(proposed_meta_ops, list):
            errors.append("proposed_meta_ops must be a list")
        else:
            for idx, op in enumerate(proposed_meta_ops):
                if not isinstance(op, dict):
                    errors.append(f"proposed_meta_ops[{idx}] must be a mapping")
                    continue
                cmd = op.get("cmd")
                if cmd not in REPORT_META_OPS:
                    errors.append(
                        f"proposed_meta_ops[{idx}].cmd has invalid value {cmd!r}"
                    )
    items = fm.get("items")
    if items is not None:
        if not isinstance(items, list):
            errors.append("items must be a list")
        else:
            allowed_classifications = REPORT_ITEM_CLASSIFICATIONS.get(
                fm.get("kind"),
                set(),
            )
            for idx, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(f"items[{idx}] must be a mapping")
                    continue
                classification = item.get("classification")
                if classification not in allowed_classifications:
                    errors.append(
                        f"items[{idx}].classification has invalid value "
                        f"{classification!r} for kind {fm.get('kind')!r}"
                    )
                message = item.get("message")
                if not isinstance(message, str) or not message.strip():
                    errors.append(f"items[{idx}].message must be a non-empty string")
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

    # -- report subcommands --
    sp = sub.add_parser(
        "report",
        help="manage subagent → main handoff reports (file-based)",
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
        help="workflow stage producing the report (e.g. scenario, report)",
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
