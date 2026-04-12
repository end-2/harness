#!/usr/bin/env python3
"""Artifact manager for the Arch skill.

Single entry point for all metadata manipulation. The Arch skill must not edit
`*.meta.yaml` files directly — it calls this script instead so that schema,
phase transitions, traceability, and audit history are enforced consistently.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
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

SECTIONS = ("decisions", "components", "tech-stack", "diagrams")

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

DECISION_STATUSES = {"Proposed", "Accepted", "Deprecated"}
COMPONENT_TYPES = {"service", "library", "gateway", "store", "queue", "job"}
INTERFACE_DIRECTIONS = {"inbound", "outbound"}
TECH_CATEGORIES = {
    "language",
    "framework",
    "database",
    "messaging",
    "infra",
    "observability",
    "auth",
    "other",
}
DIAGRAM_TYPES = {"c4-context", "c4-container", "sequence", "data-flow"}
DIAGRAM_FORMATS = {"mermaid"}

ARCH_ARTIFACT_ID_RE = re.compile(r"^ARCH-(DEC|COMP|TECH|DIAG)-\d{3}$")
AD_ID_RE = re.compile(r"^AD-\d{3}$")
COMP_ID_RE = re.compile(r"^COMP-\d{3}$")
CON_ID_RE = re.compile(r"^CON-\d{3}$")
SUPERSEDED_STATUS_RE = re.compile(r"^Superseded by AD-\d{3}$")


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
        base = Path.cwd() / "artifacts" / "arch"
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


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_string_list(value: Any, *, min_items: int = 0) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= min_items
        and all(_is_non_empty_string(item) for item in value)
    )


def _validate_id_sequence(
    values: list[dict[str, Any]],
    *,
    key: str,
    pattern: re.Pattern[str],
    path: Path,
) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(values, start=1):
        if not isinstance(item, dict):
            errors.append(f"{path.name}: row {index} must be a mapping")
            continue
        raw_id = item.get(key)
        if not _is_non_empty_string(raw_id):
            errors.append(f"{path.name}: row {index} missing {key!r}")
            continue
        assert isinstance(raw_id, str)
        if not pattern.match(raw_id):
            errors.append(f"{path.name}: invalid {key} {raw_id!r}")
        if raw_id in seen:
            errors.append(f"{path.name}: duplicate {key} {raw_id!r}")
        seen.add(raw_id)
    return errors


def _is_decision_status(value: Any) -> bool:
    return isinstance(value, str) and (
        value in DECISION_STATUSES or bool(SUPERSEDED_STATUS_RE.match(value))
    )


def _is_internal_arch_ref(ref: Any) -> bool:
    return isinstance(ref, str) and bool(ARCH_ARTIFACT_ID_RE.match(ref))


def _load_internal_ref(ref: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        other_path = find_meta_by_id(ref)
    except FileNotFoundError:
        return None, f"{ref!r} points to a missing arch artifact"
    try:
        return load_meta(other_path), None
    except Exception as e:  # noqa: BLE001
        return None, f"{ref!r} could not be loaded ({e})"


# ---------------------------------------------------------------------------
# ID allocation
# ---------------------------------------------------------------------------


def next_artifact_id(section: str) -> str:
    prefix = {
        "decisions": "ARCH-DEC",
        "components": "ARCH-COMP",
        "tech-stack": "ARCH-TECH",
        "diagrams": "ARCH-DIAG",
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
    if target_state == "approved":
        errors = _validate_artifact(data, meta_path, strict=True)
        if errors:
            sys.stderr.write("error: artifact is not review-ready:\n")
            for error in errors:
                sys.stderr.write(f"  - {error}\n")
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
    errors: list[str] = []
    for direction, ref in (("upstream", args.upstream), ("downstream", args.downstream)):
        if not ref:
            continue
        if ref == args.artifact_id:
            errors.append(f"{direction} ref cannot point to itself: {ref!r}")
            continue
        if _is_internal_arch_ref(ref):
            _other, load_error = _load_internal_ref(ref)
            if load_error:
                errors.append(f"{direction} {load_error}")
    if errors:
        for error in errors:
            sys.stderr.write(f"error: {error}\n")
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
        print(f"{aid:<{width}}  {section:<12}  {phase:<10}  {approval}")
    return 0


def _validate_meta(data: dict[str, Any], path: Path, *, strict: bool) -> list[str]:
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

    approval = data.get("approval")
    if not isinstance(approval, dict):
        errors.append(f"{path.name}: approval must be a mapping")
        approval = {}
    state = approval.get("state")
    if state and state not in APPROVAL_STATES:
        errors.append(f"{path.name}: unknown approval state {state!r}")
    history = approval.get("history")
    if history is not None and not isinstance(history, list):
        errors.append(f"{path.name}: approval.history must be a list")
    if state == "approved":
        if phase != "approved":
            errors.append(
                f"{path.name}: approval.state=approved requires phase=approved"
            )
        if not _is_non_empty_string(approval.get("approver")):
            errors.append(
                f"{path.name}: approval.approver is required when approved"
            )
        if not _is_non_empty_string(approval.get("approved_at")):
            errors.append(
                f"{path.name}: approval.approved_at is required when approved"
            )
    elif phase == "approved":
        errors.append(
            f"{path.name}: phase=approved requires approval.state=approved"
        )

    progress = data.get("progress")
    if not isinstance(progress, dict):
        errors.append(f"{path.name}: progress must be a mapping")
    else:
        completed = progress.get("section_completed")
        total = progress.get("section_total")
        percent = progress.get("percent")
        if not isinstance(completed, int):
            errors.append(f"{path.name}: progress.section_completed must be an int")
        if not isinstance(total, int):
            errors.append(f"{path.name}: progress.section_total must be an int")
        if not isinstance(percent, int):
            errors.append(f"{path.name}: progress.percent must be an int")
        if isinstance(completed, int) and completed < 0:
            errors.append(f"{path.name}: progress.section_completed must be >= 0")
        if isinstance(total, int) and total < 0:
            errors.append(f"{path.name}: progress.section_total must be >= 0")
        if isinstance(completed, int) and isinstance(total, int):
            if completed > total:
                errors.append(
                    f"{path.name}: progress.section_completed cannot exceed "
                    "section_total"
                )
            if strict and total <= 0:
                errors.append(
                    f"{path.name}: progress.section_total must be > 0 once in review"
                )
            if phase == "approved" and completed != total:
                errors.append(
                    f"{path.name}: approved artifacts must have completed==total"
                )
        if (
            isinstance(completed, int)
            and isinstance(total, int)
            and isinstance(percent, int)
        ):
            expected = int(round(100 * completed / total)) if total > 0 else 0
            if percent != expected:
                errors.append(
                    f"{path.name}: progress.percent must be {expected}, got {percent}"
                )

    upstream_refs = data.get("upstream_refs")
    if not isinstance(upstream_refs, list):
        errors.append(f"{path.name}: upstream_refs must be a list")
    downstream_refs = data.get("downstream_refs")
    if not isinstance(downstream_refs, list):
        errors.append(f"{path.name}: downstream_refs must be a list")

    doc_rel = data.get("document_path")
    if doc_rel and not isinstance(doc_rel, str):
        errors.append(f"{path.name}: document_path must be a string")
    elif doc_rel:
        doc_path = path.parent / doc_rel
        if not doc_path.exists():
            errors.append(f"{path.name}: document_path missing: {doc_rel}")
    return errors


def _validate_decisions(
    data: dict[str, Any], path: Path, *, strict: bool
) -> list[str]:
    errors: list[str] = []
    decisions = data.get("architecture_decisions")
    if not isinstance(decisions, list):
        errors.append(f"{path.name}: architecture_decisions must be a list")
        decisions = []
    if strict and not decisions:
        errors.append(
            f"{path.name}: in_review decisions artifacts must contain at least "
            "one decision"
        )

    errors.extend(
        _validate_id_sequence(decisions, key="id", pattern=AD_ID_RE, path=path)
    )
    for item in decisions:
        if not isinstance(item, dict):
            errors.append(f"{path.name}: decision rows must be mappings")
            continue
        for field in ("title", "decision", "rationale", "trade_offs"):
            if not _is_non_empty_string(item.get(field)):
                errors.append(f"{path.name}: {item.get('id', '?')} missing {field}")
        if not _is_decision_status(item.get("status")):
            errors.append(
                f"{path.name}: {item.get('id', '?')} has invalid status "
                f"{item.get('status')!r}"
            )
        alternatives = item.get("alternatives_considered")
        if not isinstance(alternatives, list):
            errors.append(
                f"{path.name}: {item.get('id', '?')} alternatives_considered "
                "must be a list"
            )
            alternatives = []
        elif strict and not alternatives:
            errors.append(
                f"{path.name}: {item.get('id', '?')} must record at least one "
                "alternative"
            )
        for index, alt in enumerate(alternatives, start=1):
            if not isinstance(alt, dict):
                errors.append(
                    f"{path.name}: {item.get('id', '?')} alternative {index} "
                    "must be a mapping"
                )
                continue
            if not _is_non_empty_string(alt.get("option")):
                errors.append(
                    f"{path.name}: {item.get('id', '?')} alternative {index} "
                    "missing option"
                )
            if not _is_string_list(alt.get("pros"), min_items=1):
                errors.append(
                    f"{path.name}: {item.get('id', '?')} alternative {index} "
                    "must include at least one pro"
                )
            if not _is_string_list(alt.get("cons"), min_items=1):
                errors.append(
                    f"{path.name}: {item.get('id', '?')} alternative {index} "
                    "must include at least one con"
                )
            if not _is_non_empty_string(alt.get("rejected_reason")):
                errors.append(
                    f"{path.name}: {item.get('id', '?')} alternative {index} "
                    "missing rejected_reason"
                )
        if not _is_string_list(item.get("re_refs"), min_items=1):
            errors.append(
                f"{path.name}: {item.get('id', '?')} must cite at least one RE ref"
            )
    return errors


def _validate_components(
    data: dict[str, Any], path: Path, *, strict: bool
) -> list[str]:
    errors: list[str] = []
    components = data.get("components")
    if not isinstance(components, list):
        errors.append(f"{path.name}: components must be a list")
        components = []
    if strict and not components:
        errors.append(
            f"{path.name}: in_review components artifacts must contain at least "
            "one component"
        )

    errors.extend(
        _validate_id_sequence(components, key="id", pattern=COMP_ID_RE, path=path)
    )
    component_ids = {
        item["id"]
        for item in components
        if isinstance(item, dict) and _is_non_empty_string(item.get("id"))
    }
    dependency_checks: list[tuple[str, str]] = []

    for item in components:
        if not isinstance(item, dict):
            errors.append(f"{path.name}: component rows must be mappings")
            continue
        for field in ("name", "responsibility"):
            if not _is_non_empty_string(item.get(field)):
                errors.append(f"{path.name}: {item.get('id', '?')} missing {field}")
        if item.get("type") not in COMPONENT_TYPES:
            errors.append(
                f"{path.name}: {item.get('id', '?')} has invalid type "
                f"{item.get('type')!r}"
            )
        interfaces = item.get("interfaces")
        if not isinstance(interfaces, list) or not interfaces:
            errors.append(
                f"{path.name}: {item.get('id', '?')} must list at least one interface"
            )
            interfaces = []
        for index, interface in enumerate(interfaces, start=1):
            if not isinstance(interface, dict):
                errors.append(
                    f"{path.name}: {item.get('id', '?')} interface {index} "
                    "must be a mapping"
                )
                continue
            for field in ("name", "protocol", "description"):
                if not _is_non_empty_string(interface.get(field)):
                    errors.append(
                        f"{path.name}: {item.get('id', '?')} interface {index} "
                        f"missing {field}"
                    )
            if interface.get("direction") not in INTERFACE_DIRECTIONS:
                errors.append(
                    f"{path.name}: {item.get('id', '?')} interface {index} has "
                    f"invalid direction {interface.get('direction')!r}"
                )
        dependencies = item.get("dependencies")
        if dependencies != [] and not _is_string_list(dependencies):
            errors.append(
                f"{path.name}: {item.get('id', '?')} dependencies must be a list "
                "of non-empty strings"
            )
        else:
            assert dependencies == [] or isinstance(dependencies, list)
            for dependency in dependencies or []:
                if not COMP_ID_RE.match(dependency):
                    errors.append(
                        f"{path.name}: {item.get('id', '?')} has invalid dependency "
                        f"{dependency!r}"
                    )
                else:
                    dependency_checks.append((item.get("id", "?"), dependency))
        if not _is_string_list(item.get("re_refs"), min_items=1):
            errors.append(
                f"{path.name}: {item.get('id', '?')} must cite at least one FR/NFR ref"
            )

    for component_id, dependency in dependency_checks:
        if dependency == component_id:
            errors.append(f"{path.name}: {component_id} cannot depend on itself")
        elif dependency not in component_ids:
            errors.append(
                f"{path.name}: {component_id} depends on missing component "
                f"{dependency!r}"
            )
    return errors


def _validate_tech_stack(
    data: dict[str, Any], path: Path, *, strict: bool
) -> list[str]:
    errors: list[str] = []
    stack = data.get("technology_stack")
    if not isinstance(stack, list):
        errors.append(f"{path.name}: technology_stack must be a list")
        stack = []
    if strict and not stack:
        errors.append(
            f"{path.name}: in_review tech-stack artifacts must contain at least "
            "one technology row"
        )

    for index, item in enumerate(stack, start=1):
        if not isinstance(item, dict):
            errors.append(f"{path.name}: technology_stack rows must be mappings")
            continue
        row_label = f"technology_stack row {index}"
        if item.get("category") not in TECH_CATEGORIES:
            errors.append(
                f"{path.name}: {row_label} has invalid category "
                f"{item.get('category')!r}"
            )
        for field in ("choice", "rationale"):
            if not _is_non_empty_string(item.get(field)):
                errors.append(f"{path.name}: {row_label} missing {field}")
        decision_ref = item.get("decision_ref")
        constraint_ref = item.get("constraint_ref")
        has_decision_ref = _is_non_empty_string(decision_ref)
        has_constraint_ref = _is_non_empty_string(constraint_ref)
        if not has_decision_ref and not has_constraint_ref:
            errors.append(
                f"{path.name}: {row_label} must set decision_ref or constraint_ref"
            )
        if has_decision_ref and not AD_ID_RE.match(str(decision_ref)):
            errors.append(
                f"{path.name}: {row_label} has invalid decision_ref "
                f"{decision_ref!r}"
            )
        if has_constraint_ref and not CON_ID_RE.match(str(constraint_ref)):
            errors.append(
                f"{path.name}: {row_label} has invalid constraint_ref "
                f"{constraint_ref!r}"
            )
    return errors


def _validate_diagrams(
    data: dict[str, Any], path: Path, *, strict: bool
) -> list[str]:
    errors: list[str] = []
    diagrams = data.get("diagrams")
    if not isinstance(diagrams, list):
        errors.append(f"{path.name}: diagrams must be a list")
        diagrams = []
    if strict and not diagrams:
        errors.append(
            f"{path.name}: in_review diagrams artifacts must contain at least "
            "one diagram"
        )

    for index, item in enumerate(diagrams, start=1):
        if not isinstance(item, dict):
            errors.append(f"{path.name}: diagrams rows must be mappings")
            continue
        row_label = f"diagrams row {index}"
        if item.get("type") not in DIAGRAM_TYPES:
            errors.append(
                f"{path.name}: {row_label} has invalid type {item.get('type')!r}"
            )
        if item.get("format") not in DIAGRAM_FORMATS:
            errors.append(
                f"{path.name}: {row_label} has invalid format {item.get('format')!r}"
            )
        for field in ("title", "description"):
            if not _is_non_empty_string(item.get(field)):
                errors.append(f"{path.name}: {row_label} missing {field}")
        if not _is_string_list(item.get("re_refs"), min_items=1):
            errors.append(
                f"{path.name}: {row_label} must cite at least one RE/AD ref"
            )
    return errors


def _validate_section_payload(
    data: dict[str, Any], path: Path, *, strict: bool
) -> list[str]:
    section = data.get("section")
    if section == "decisions":
        return _validate_decisions(data, path, strict=strict)
    if section == "components":
        return _validate_components(data, path, strict=strict)
    if section == "tech-stack":
        return _validate_tech_stack(data, path, strict=strict)
    if section == "diagrams":
        return _validate_diagrams(data, path, strict=strict)
    return []


def _validate_artifact(
    data: dict[str, Any], path: Path, *, strict: bool | None = None
) -> list[str]:
    approval = data.get("approval") or {}
    if strict is None:
        strict = (
            data.get("phase") in {"in_review", "approved"}
            or approval.get("state") == "approved"
        )
    errors = _validate_meta(data, path, strict=strict)
    errors.extend(_validate_section_payload(data, path, strict=strict))
    return errors


def _validate_traceability(all_data: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    ids = set(all_data.keys())
    for aid, data in all_data.items():
        for ref in data.get("downstream_refs") or []:
            if not _is_non_empty_string(ref):
                errors.append(f"{aid}: downstream_ref contains a blank value")
                continue
            if _is_internal_arch_ref(ref):
                other, load_error = (
                    (all_data[ref], None)
                    if ref in ids
                    else _load_internal_ref(ref)
                )
                if load_error:
                    errors.append(f"{aid}: downstream_ref {load_error}")
                    continue
                assert other is not None
                if aid not in (other.get("upstream_refs") or []):
                    errors.append(
                        f"{aid}: downstream_ref {ref!r} lacks reciprocal upstream"
                    )
        for ref in data.get("upstream_refs") or []:
            if not _is_non_empty_string(ref):
                errors.append(f"{aid}: upstream_ref contains a blank value")
                continue
            if _is_internal_arch_ref(ref):
                other, load_error = (
                    (all_data[ref], None)
                    if ref in ids
                    else _load_internal_ref(ref)
                )
                if load_error:
                    errors.append(f"{aid}: upstream_ref {load_error}")
                    continue
                assert other is not None
                if aid not in (other.get("downstream_refs") or []):
                    errors.append(
                        f"{aid}: upstream_ref {ref!r} lacks reciprocal downstream"
                    )
    return errors


def cmd_validate(args: argparse.Namespace) -> int:
    if args.artifact_id:
        try:
            files = [find_meta_by_id(args.artifact_id)]
        except FileNotFoundError as e:
            sys.stderr.write(f"error: {e}\n")
            return 2
    else:
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
        errors.extend(_validate_artifact(data, p))
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

SKILL_NAME = "arch"

REPORT_KINDS = (
    "analyze",
    "review",
    "adr-draft",
    "diagram-draft",
    "refactor",
    "spec-review",
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
REPORT_ITEM_SEVERITIES = {"high", "med", "low", "info"}
REPORT_KIND_BY_STAGE = {
    "adr": "adr-draft",
    "diagram": "diagram-draft",
    "review": "review",
}
REPORT_CLASSIFICATIONS_BY_STAGE = {
    "adr": {
        "adr_drafted",
        "context_missing",
        "alternatives_missing",
        "consequences_missing",
    },
    "diagram": {"diagram_drafted", "caption_missing", "driver_untraced"},
    "review": {
        "scenario_pass",
        "scenario_failure",
        "hard_constraint_unsatisfied",
        "traceability_gap",
        "escalation",
    },
}
REPORT_ALLOWED_OPS_BY_STAGE = {
    "adr": {"link", "set-progress"},
    "diagram": {"link", "set-progress", "set-phase"},
    "review": {"link", "set-progress"},
}


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
    stage = fm.get("stage")
    expected_kind = REPORT_KIND_BY_STAGE.get(stage)
    if expected_kind and fm.get("kind") != expected_kind:
        errors.append(
            f"kind/stage mismatch: stage {stage!r} expects kind "
            f"{expected_kind!r}, got {fm.get('kind')!r}"
        )
    target_refs = fm.get("target_refs")
    if target_refs is not None and not isinstance(target_refs, list):
        errors.append("target_refs must be a list")
        target_refs = []
    elif isinstance(target_refs, list):
        for index, ref in enumerate(target_refs, start=1):
            if not _is_non_empty_string(ref):
                errors.append(f"target_refs[{index}] must be a non-empty string")
    if stage in {"adr", "review"} and isinstance(target_refs, list) and not target_refs:
        errors.append(f"{stage} reports must include at least one target_ref")

    proposed_meta_ops = fm.get("proposed_meta_ops")
    if proposed_meta_ops is not None and not isinstance(proposed_meta_ops, list):
        errors.append("proposed_meta_ops must be a list")
        proposed_meta_ops = []

    items = fm.get("items")
    if items is not None and not isinstance(items, list):
        errors.append("items must be a list")
        items = []
    elif stage in REPORT_CLASSIFICATIONS_BY_STAGE and isinstance(items, list) and not items:
        errors.append(f"{stage} reports must include at least one item")

    allowed_classifications = REPORT_CLASSIFICATIONS_BY_STAGE.get(stage)
    if isinstance(items, list):
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                errors.append(f"items[{index}] must be a mapping")
                continue
            classification = item.get("classification")
            if not _is_non_empty_string(classification):
                errors.append(f"items[{index}] missing classification")
            elif (
                allowed_classifications is not None
                and classification not in allowed_classifications
            ):
                errors.append(
                    f"items[{index}] has invalid classification "
                    f"{classification!r} for stage {stage!r}"
                )
            severity = item.get("severity")
            if severity is not None and severity not in REPORT_ITEM_SEVERITIES:
                errors.append(
                    f"items[{index}] has invalid severity {severity!r}"
                )

    allowed_ops = REPORT_ALLOWED_OPS_BY_STAGE.get(stage)
    if isinstance(proposed_meta_ops, list):
        for index, op in enumerate(proposed_meta_ops, start=1):
            if not isinstance(op, dict):
                errors.append(f"proposed_meta_ops[{index}] must be a mapping")
                continue
            cmd = op.get("cmd")
            if not _is_non_empty_string(cmd):
                errors.append(f"proposed_meta_ops[{index}] missing cmd")
                continue
            if allowed_ops is not None and cmd not in allowed_ops:
                errors.append(
                    f"proposed_meta_ops[{index}] command {cmd!r} is not allowed "
                    f"for stage {stage!r}"
                )
                continue
            if cmd == "link":
                if not _is_non_empty_string(op.get("artifact_id")):
                    errors.append(
                        f"proposed_meta_ops[{index}] link requires artifact_id"
                    )
                if not _is_non_empty_string(op.get("upstream")) and not _is_non_empty_string(
                    op.get("downstream")
                ):
                    errors.append(
                        f"proposed_meta_ops[{index}] link requires upstream or downstream"
                    )
            elif cmd == "set-progress":
                completed = op.get("completed")
                total = op.get("total")
                if not _is_non_empty_string(op.get("artifact_id")):
                    errors.append(
                        f"proposed_meta_ops[{index}] set-progress requires artifact_id"
                    )
                if not isinstance(completed, int) or not isinstance(total, int):
                    errors.append(
                        f"proposed_meta_ops[{index}] set-progress requires integer "
                        "completed and total"
                    )
                elif completed < 0 or total <= 0 or completed > total:
                    errors.append(
                        f"proposed_meta_ops[{index}] set-progress has invalid "
                        f"completed/total values ({completed}/{total})"
                    )
            elif cmd == "set-phase":
                if not _is_non_empty_string(op.get("artifact_id")):
                    errors.append(
                        f"proposed_meta_ops[{index}] set-phase requires artifact_id"
                    )
                phase = op.get("phase")
                if phase != "in_review":
                    errors.append(
                        f"proposed_meta_ops[{index}] set-phase may only request "
                        f"'in_review', got {phase!r}"
                    )
    if not (fm.get("summary") or "").strip():
        errors.append("summary is empty (subagent must write a one-line summary)")
    stripped_body = "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith("#")
    ).strip()
    if not stripped_body:
        errors.append("body has no content beyond the header")
    if stage == "review":
        for heading in (
            "## Summary",
            "## Scenarios",
            "## Constraints",
            "## Traceability",
            "## Risks and open items",
        ):
            if heading not in body:
                errors.append(f"review body missing heading {heading!r}")
    elif stage == "adr" and "### AD-" not in body:
        errors.append("adr body must include at least one ADR heading")
    elif stage == "diagram" and "```mermaid" not in body:
        errors.append("diagram body must include at least one mermaid block")
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
        help="workflow stage producing the report (e.g. adr, diagram, review)",
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
