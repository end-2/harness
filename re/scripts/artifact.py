#!/usr/bin/env python3
"""Artifact manager for the RE skill.

Single entry point for workflow metadata manipulation. The RE skill must not
edit script-managed fields in `*.meta.yaml` files directly — it calls this
script instead so that schema, phase transitions, traceability, and audit
history are enforced consistently.
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

SECTIONS = ("requirements", "constraints", "quality-attributes")

PHASES = ("draft", "in_review", "revising", "approved", "superseded")
PHASE_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"in_review", "superseded"},
    "in_review": {"revising", "superseded"},
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

MOSCOW_PRIORITIES = {"Must", "Should", "Could", "Won't"}
CONSTRAINT_TYPES = {"technical", "business", "regulatory", "environmental"}
CONSTRAINT_FLEXIBILITY = {"hard", "soft", "negotiable"}
FR_ID_RE = re.compile(r"^FR-\d{3}$")
NFR_ID_RE = re.compile(r"^NFR-\d{3}$")
CON_ID_RE = re.compile(r"^CON-\d{3}$")


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
        base = Path.cwd() / "artifacts" / "re"
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


def _has_measurement(text: str) -> bool:
    return bool(re.search(r"\d", text) and re.search(r"[A-Za-z%]", text))


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


# ---------------------------------------------------------------------------
# ID allocation
# ---------------------------------------------------------------------------


def next_artifact_id(section: str) -> str:
    prefix = {
        "requirements": "RE-REQ",
        "constraints": "RE-CON",
        "quality-attributes": "RE-QA",
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
            sys.stderr.write(
                "error: artifact is not approval-ready; fix validation errors "
                "first\n"
            )
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
        print(f"{aid:<{width}}  {section:<18}  {phase:<10}  {approval}")
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


def _validate_requirements(
    data: dict[str, Any], path: Path, *, strict: bool
) -> list[str]:
    errors: list[str] = []
    frs = data.get("functional_requirements")
    nfrs = data.get("non_functional_requirements")

    if not isinstance(frs, list):
        errors.append(f"{path.name}: functional_requirements must be a list")
        frs = []
    if not isinstance(nfrs, list):
        errors.append(f"{path.name}: non_functional_requirements must be a list")
        nfrs = []
    if strict and not frs and not nfrs:
        errors.append(
            f"{path.name}: in_review requirements artifacts must contain at least "
            "one FR or NFR"
        )

    errors.extend(_validate_id_sequence(frs, key="id", pattern=FR_ID_RE, path=path))
    errors.extend(
        _validate_id_sequence(nfrs, key="id", pattern=NFR_ID_RE, path=path)
    )

    for item in frs:
        if not isinstance(item, dict):
            errors.append(f"{path.name}: functional_requirements rows must be mappings")
            continue
        for field in ("title", "description", "source"):
            if not _is_non_empty_string(item.get(field)):
                errors.append(f"{path.name}: {item.get('id', '?')} missing {field}")
        if item.get("priority") not in MOSCOW_PRIORITIES:
            errors.append(
                f"{path.name}: {item.get('id', '?')} has invalid priority "
                f"{item.get('priority')!r}"
            )
        if not _is_string_list(item.get("acceptance_criteria"), min_items=1):
            errors.append(
                f"{path.name}: {item.get('id', '?')} must have at least one "
                "acceptance criterion"
            )
        dependencies = item.get("dependencies", [])
        if dependencies != [] and not _is_string_list(dependencies):
            errors.append(
                f"{path.name}: {item.get('id', '?')} dependencies must be a list "
                "of non-empty strings"
            )

    for item in nfrs:
        if not isinstance(item, dict):
            errors.append(
                f"{path.name}: non_functional_requirements rows must be mappings"
            )
            continue
        for field in ("category", "title", "description", "source"):
            if not _is_non_empty_string(item.get(field)):
                errors.append(f"{path.name}: {item.get('id', '?')} missing {field}")
        if item.get("priority") not in MOSCOW_PRIORITIES:
            errors.append(
                f"{path.name}: {item.get('id', '?')} has invalid priority "
                f"{item.get('priority')!r}"
            )
        criteria = item.get("acceptance_criteria")
        if not _is_string_list(criteria, min_items=1):
            errors.append(
                f"{path.name}: {item.get('id', '?')} must have at least one "
                "acceptance criterion"
            )
        else:
            assert isinstance(criteria, list)
            if not any(_has_measurement(criterion) for criterion in criteria):
                errors.append(
                    f"{path.name}: {item.get('id', '?')} must include a measurable "
                    "acceptance criterion"
                )

    return errors


def _validate_constraints(
    data: dict[str, Any], path: Path, *, strict: bool
) -> list[str]:
    errors: list[str] = []
    constraints = data.get("constraints")
    if not isinstance(constraints, list):
        errors.append(f"{path.name}: constraints must be a list")
        constraints = []
    if strict and not constraints:
        errors.append(
            f"{path.name}: in_review constraints artifacts must contain at least "
            "one constraint"
        )

    errors.extend(
        _validate_id_sequence(constraints, key="id", pattern=CON_ID_RE, path=path)
    )
    for item in constraints:
        if not isinstance(item, dict):
            errors.append(f"{path.name}: constraint rows must be mappings")
            continue
        for field in ("title", "description", "rationale", "impact"):
            if not _is_non_empty_string(item.get(field)):
                errors.append(f"{path.name}: {item.get('id', '?')} missing {field}")
        if item.get("type") not in CONSTRAINT_TYPES:
            errors.append(
                f"{path.name}: {item.get('id', '?')} has invalid type "
                f"{item.get('type')!r}"
            )
        if item.get("flexibility") not in CONSTRAINT_FLEXIBILITY:
            errors.append(
                f"{path.name}: {item.get('id', '?')} has invalid flexibility "
                f"{item.get('flexibility')!r}"
            )
    return errors


def _validate_quality_attributes(
    data: dict[str, Any], path: Path, *, strict: bool
) -> list[str]:
    errors: list[str] = []
    attributes = data.get("quality_attributes")
    if not isinstance(attributes, list):
        errors.append(f"{path.name}: quality_attributes must be a list")
        attributes = []
    if strict and not attributes:
        errors.append(
            f"{path.name}: in_review quality-attributes artifacts must contain "
            "at least one quality attribute"
        )

    priorities: set[int] = set()
    for index, item in enumerate(attributes, start=1):
        if not isinstance(item, dict):
            errors.append(f"{path.name}: quality_attributes rows must be mappings")
            continue
        for field in ("attribute", "description", "metric", "trade_off_notes"):
            if not _is_non_empty_string(item.get(field)):
                errors.append(
                    f"{path.name}: quality_attributes row {index} missing {field}"
                )
        priority = item.get("priority")
        if not isinstance(priority, int) or priority <= 0:
            errors.append(
                f"{path.name}: quality_attributes row {index} has invalid priority "
                f"{priority!r}"
            )
        elif priority in priorities:
            errors.append(
                f"{path.name}: duplicate quality attribute priority {priority}"
            )
        else:
            priorities.add(priority)
        metric = item.get("metric")
        if _is_non_empty_string(metric) and not _has_measurement(str(metric)):
            errors.append(
                f"{path.name}: quality_attributes row {index} metric must be "
                "measurable"
            )
    return errors


def _validate_section_payload(
    data: dict[str, Any], path: Path, *, strict: bool
) -> list[str]:
    section = data.get("section")
    if section == "requirements":
        return _validate_requirements(data, path, strict=strict)
    if section == "constraints":
        return _validate_constraints(data, path, strict=strict)
    if section == "quality-attributes":
        return _validate_quality_attributes(data, path, strict=strict)
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

SKILL_NAME = "re"

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
        help="workflow stage producing the report (e.g. analyze, review)",
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
