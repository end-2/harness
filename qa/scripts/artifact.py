#!/usr/bin/env python3
"""Artifact manager for the QA skill.

Single entry point for all metadata manipulation. The QA skill must not edit
`*.meta.yaml` files directly — it calls this script instead so that schema,
phase transitions, traceability, RTM rows, and the quality-gate verdict are
enforced consistently.
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

SKILL_NAME = "qa"

SECTIONS = (
    "test-strategy",
    "test-suite",
    "rtm",
    "quality-report",
)

SECTION_PREFIX = {
    "test-strategy": "QA-STRATEGY",
    "test-suite": "QA-SUITE",
    "rtm": "QA-RTM",
    "quality-report": "QA-REPORT",
}

PHASES = ("draft", "in_review", "revising", "approved", "superseded")
PHASE_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"in_review", "superseded"},
    "in_review": {"revising", "approved", "superseded"},
    "revising": {"in_review", "superseded"},
    "approved": {"superseded"},
    "superseded": set(),
}

# QA adds `escalated` for unresolved Must coverage gaps that require user input.
APPROVAL_STATES = (
    "pending",
    "approved",
    "rejected",
    "changes_requested",
    "escalated",
)
APPROVAL_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"approved", "rejected", "changes_requested", "escalated"},
    "changes_requested": {"pending", "approved", "rejected", "escalated"},
    "rejected": {"pending"},
    "escalated": {"pending", "approved", "rejected", "changes_requested"},
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

COVERAGE_STATUSES = ("covered", "partial", "uncovered")

STRATEGY_MODES = ("light", "heavy")
TEST_TYPES = ("unit", "integration", "e2e", "contract", "nfr")
TEST_TECHNIQUES = (
    "boundary_value",
    "equivalence_partition",
    "decision_table",
    "state_transition",
    "property_based",
    "example_based",
)

SETTABLE_FIELDS: dict[str, str] = {
    "test_strategy": "test-strategy",
    "test_suite": "test-suite",
    "quality_report": "quality-report",
    "quality_gate.criteria": "quality-report",
    "quality_gate.actuals": "quality-report",
}

# MoSCoW priorities recognised in RTM rows. The script does not enforce a
# value here — it just bins by whatever priority a row carries — but the
# canonical set is documented for reference.
MOSCOW_PRIORITIES = ("must", "should", "could", "wont")

REVIEW_GAP_TYPES = (
    "missing_test",
    "partial_criteria",
    "weak_assertion",
    "missing_nfr_scenario",
    "traceability_break",
    "flaky_pattern",
)
REPORT_KIND_BY_STAGE = {
    "review": "review",
    "report": "report",
}
REPORT_ALLOWED_OPS_BY_STAGE = {
    "review": {"rtm-upsert"},
    "report": {"write-quality-report-actuals", "gate-evaluate"},
}


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def skill_dir() -> Path:
    env = os.environ.get("SKILL_DIR") or os.environ.get("SKILL_DIR")
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
        base = Path.cwd() / "artifacts" / "qa"
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


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _load_structured_value(
    *,
    from_path: str | None,
    raw_value: str | None,
) -> Any:
    if bool(from_path) == bool(raw_value):
        raise ValueError("provide exactly one of --from or --value")
    if from_path:
        text = Path(from_path).read_text(encoding="utf-8")
    else:
        text = raw_value or ""
    return yaml.safe_load(text)


def _extract_field_payload(payload: Any, field: str) -> Any:
    if not isinstance(payload, dict):
        return payload
    current: Any = payload
    found = True
    for part in field.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            found = False
            break
    if found:
        return current
    leaf = field.rsplit(".", 1)[-1]
    if leaf in payload:
        return payload[leaf]
    return payload


def _set_nested_value(root: dict[str, Any], field: str, value: Any) -> None:
    parts = field.split(".")
    current = root
    for part in parts[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            current[part] = next_value
        current = next_value
    current[parts[-1]] = value


def find_rtm_meta() -> Path | None:
    for p in all_meta_files():
        try:
            data = load_meta(p)
        except Exception:
            continue
        if data.get("section") == "rtm":
            return p
    return None


def find_section_meta(section: str) -> list[Path]:
    out: list[Path] = []
    for p in all_meta_files():
        try:
            data = load_meta(p)
        except Exception:
            continue
        if data.get("section") == section:
            out.append(p)
    return out


# ---------------------------------------------------------------------------
# ID allocation
# ---------------------------------------------------------------------------


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

    # Only one RTM artifact per project — refuse a second init.
    if section == "rtm" and find_rtm_meta() is not None:
        sys.stderr.write(
            "error: an rtm artifact already exists in this project; "
            "RTM is a single project-wide artifact, use rtm-upsert to add rows\n"
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

    # Quality reports may only transition through gate-evaluate. Direct
    # approve calls are refused so the verdict always reflects measured
    # results, never a manual override.
    if data.get("section") == "quality-report":
        sys.stderr.write(
            "error: quality-report approval is driven by gate-evaluate; "
            "use `artifact.py gate-evaluate <id>` instead\n"
        )
        return 2

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


def cmd_set_block(args: argparse.Namespace) -> int:
    expected_section = SETTABLE_FIELDS[args.field]
    meta_path = find_meta_by_id(args.artifact_id)
    data = load_meta(meta_path)
    if data.get("section") != expected_section:
        sys.stderr.write(
            f"error: field {args.field!r} belongs to section "
            f"{expected_section!r}, but {args.artifact_id} is "
            f"{data.get('section')!r}\n"
        )
        return 2

    payload = _load_structured_value(
        from_path=args.from_path,
        raw_value=args.value,
    )
    payload = _extract_field_payload(payload, args.field)
    _set_nested_value(data, args.field, payload)

    errors = _validate_meta(data, meta_path)
    if errors:
        for error in errors:
            sys.stderr.write(f"error: {error}\n")
        return 2

    save_meta(meta_path, data)
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "field": args.field,
                "meta_path": str(meta_path),
            },
            indent=2,
        )
    )
    return 0


def _validate_progress(progress: Any, path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(progress, dict):
        return [f"{path.name}: progress must be a mapping"]

    completed = progress.get("section_completed")
    total = progress.get("section_total")
    percent = progress.get("percent")
    if not isinstance(completed, int) or not isinstance(total, int) or not isinstance(
        percent, int
    ):
        return [
            f"{path.name}: progress must contain integer section_completed, "
            "section_total, and percent"
        ]
    if completed < 0 or total < 0:
        errors.append(
            f"{path.name}: progress counts must be non-negative "
            f"(got {completed}/{total})"
        )
        return errors
    if total == 0:
        if completed != 0 or percent != 0:
            errors.append(
                f"{path.name}: progress with section_total 0 must be 0/0 (0%)"
            )
        return errors
    if completed > total:
        errors.append(
            f"{path.name}: progress section_completed {completed} exceeds "
            f"section_total {total}"
        )
    expected_percent = int(round(100 * completed / total))
    if percent != expected_percent:
        errors.append(
            f"{path.name}: progress percent {percent} does not match "
            f"{completed}/{total} ({expected_percent})"
        )
    return errors


def _validate_strategy_block(data: dict[str, Any], path: Path) -> list[str]:
    block = data.get("test_strategy")
    if not isinstance(block, dict):
        return [f"{path.name}: missing test_strategy block"]

    errors: list[str] = []
    mode = block.get("mode")
    if mode is not None and mode not in STRATEGY_MODES:
        errors.append(f"{path.name}: test_strategy.mode invalid: {mode!r}")

    scope = block.get("scope")
    if not isinstance(scope, dict):
        errors.append(f"{path.name}: test_strategy.scope must be a mapping")
    else:
        for key in ("in", "out"):
            if key not in scope:
                errors.append(f"{path.name}: test_strategy.scope missing {key!r}")
            elif not isinstance(scope[key], list):
                errors.append(
                    f"{path.name}: test_strategy.scope.{key} must be a list"
                )

    for key in (
        "pyramid",
        "nfr_test_plan",
        "environment_matrix",
        "test_double_strategy",
    ):
        value = block.get(key)
        if value is None:
            errors.append(f"{path.name}: test_strategy missing {key!r}")
        elif not isinstance(value, list):
            errors.append(f"{path.name}: test_strategy.{key} must be a list")

    criteria = block.get("quality_gate_criteria")
    if not isinstance(criteria, dict):
        errors.append(
            f"{path.name}: test_strategy.quality_gate_criteria must be a mapping"
        )
    else:
        for key in (
            "code_coverage_min",
            "requirements_coverage_must_min",
            "max_failed_tests",
            "nfr_metric_refs",
        ):
            if key not in criteria:
                errors.append(
                    f"{path.name}: test_strategy.quality_gate_criteria missing "
                    f"{key!r}"
                )
        for key in ("code_coverage_min", "requirements_coverage_must_min"):
            value = criteria.get(key)
            if value is not None and not _is_number(value):
                errors.append(
                    f"{path.name}: test_strategy.quality_gate_criteria.{key} "
                    "must be numeric or null"
                )
        max_failed = criteria.get("max_failed_tests")
        if max_failed is not None and not isinstance(max_failed, int):
            errors.append(
                f"{path.name}: test_strategy.quality_gate_criteria."
                "max_failed_tests must be an int"
            )
        nfr_refs = criteria.get("nfr_metric_refs")
        if nfr_refs is not None and not _is_string_list(nfr_refs):
            errors.append(
                f"{path.name}: test_strategy.quality_gate_criteria."
                "nfr_metric_refs must be a list of strings"
            )
    return errors


def _validate_suite_block(data: dict[str, Any], path: Path) -> list[str]:
    block = data.get("test_suite")
    if not isinstance(block, list):
        return [f"{path.name}: missing test_suite block"]

    errors: list[str] = []
    if data.get("phase") in ("in_review", "approved") and not block:
        errors.append(
            f"{path.name}: in_review test-suite artifacts must contain at least "
            "one suite"
        )

    for index, suite in enumerate(block):
        label = f"{path.name}: test_suite[{index}]"
        if not isinstance(suite, dict):
            errors.append(f"{label} must be a mapping")
            continue
        for key in (
            "id",
            "title",
            "target_module",
            "framework",
        ):
            value = suite.get(key)
            if value is not None and not _is_non_empty_string(value):
                errors.append(f"{label}.{key} must be a non-empty string")
        suite_type = suite.get("type")
        if suite_type is not None and suite_type not in TEST_TYPES:
            errors.append(f"{label}.type invalid: {suite_type!r}")
        for key in ("test_files", "re_refs", "arch_refs", "impl_refs"):
            value = suite.get(key)
            if value is not None and not _is_string_list(value, min_items=1):
                errors.append(f"{label}.{key} must be a non-empty list of strings")
        cases = suite.get("test_cases")
        if cases is not None and not isinstance(cases, list):
            errors.append(f"{label}.test_cases must be a list")
            continue
        if isinstance(cases, list):
            for case_index, case in enumerate(cases):
                case_label = f"{label}.test_cases[{case_index}]"
                if not isinstance(case, dict):
                    errors.append(f"{case_label} must be a mapping")
                    continue
                for key in (
                    "case_id",
                    "description",
                    "acceptance_criteria_ref",
                    "given",
                    "when",
                    "then",
                ):
                    value = case.get(key)
                    if value is not None and not _is_non_empty_string(value):
                        errors.append(f"{case_label}.{key} must be a non-empty string")
                technique = case.get("technique")
                if technique is not None and technique not in TEST_TECHNIQUES:
                    errors.append(
                        f"{case_label}.technique invalid: {technique!r}"
                    )
                test_node = case.get("test_node")
                if test_node is not None and not _is_non_empty_string(test_node):
                    errors.append(f"{case_label}.test_node must be a non-empty string")
    return errors


def _validate_rtm_block(data: dict[str, Any], path: Path) -> list[str]:
    rows = data.get("rtm_rows")
    if rows is None:
        return [f"{path.name}: missing rtm_rows block"]
    if not isinstance(rows, list):
        return [f"{path.name}: rtm_rows must be a list"]

    errors: list[str] = []
    for index, row in enumerate(rows):
        label = f"{path.name}: rtm_rows[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label} must be a mapping")
            continue
        if not _is_non_empty_string(row.get("re_id")):
            errors.append(f"{label} missing re_id")
        status = row.get("coverage_status")
        if status not in COVERAGE_STATUSES:
            errors.append(f"{label} coverage_status invalid: {status!r}")
        test_refs = row.get("test_refs")
        if status != "uncovered" and not _is_string_list(test_refs, min_items=1):
            errors.append(
                f"{label} test_refs must be a non-empty list when status is "
                f"{status!r}"
            )
        gap = row.get("gap_description")
        if status in ("partial", "uncovered") and not _is_non_empty_string(gap):
            errors.append(
                f"{label} gap_description must be a non-empty string when status "
                f"is {status!r}"
            )
    return errors


def _validate_quality_report_block(data: dict[str, Any], path: Path) -> list[str]:
    report = data.get("quality_report")
    gate = data.get("quality_gate")
    errors: list[str] = []

    if not isinstance(report, dict):
        errors.append(f"{path.name}: missing quality_report block")
    else:
        code_coverage = report.get("code_coverage")
        if code_coverage is None:
            errors.append(f"{path.name}: quality_report missing 'code_coverage'")
        elif not isinstance(code_coverage, dict):
            errors.append(f"{path.name}: quality_report.code_coverage must be a mapping")
        requirements_coverage = report.get("requirements_coverage")
        if requirements_coverage is None:
            errors.append(
                f"{path.name}: quality_report missing 'requirements_coverage'"
            )
        elif not isinstance(requirements_coverage, dict):
            errors.append(
                f"{path.name}: quality_report.requirements_coverage must be a mapping"
            )
        for key in ("nfr_results", "residual_risks", "recommendations"):
            value = report.get(key)
            if value is None:
                errors.append(f"{path.name}: quality_report missing {key!r}")
            elif not isinstance(value, list):
                errors.append(f"{path.name}: quality_report.{key} must be a list")

    if not isinstance(gate, dict):
        errors.append(f"{path.name}: missing quality_gate block")
    else:
        criteria = gate.get("criteria")
        actuals = gate.get("actuals")
        if not isinstance(criteria, dict):
            errors.append(f"{path.name}: quality_gate.criteria must be a mapping")
        else:
            for key in (
                "code_coverage_min",
                "requirements_coverage_must_min",
                "max_failed_tests",
            ):
                if key not in criteria:
                    errors.append(
                        f"{path.name}: quality_gate.criteria missing {key!r}"
                    )
        if not isinstance(actuals, dict):
            errors.append(f"{path.name}: quality_gate.actuals must be a mapping")
        else:
            nfr_results = actuals.get("nfr_results")
            if nfr_results is not None and not isinstance(nfr_results, list):
                errors.append(
                    f"{path.name}: quality_gate.actuals.nfr_results must be a list"
                )
    return errors


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
    errors.extend(_validate_progress(data.get("progress"), path))
    doc_rel = data.get("document_path")
    if doc_rel:
        doc_path = path.parent / doc_rel
        if not doc_path.exists():
            errors.append(f"{path.name}: document_path missing: {doc_rel}")
    if section == "test-strategy":
        errors.extend(_validate_strategy_block(data, path))
    elif section == "test-suite":
        errors.extend(_validate_suite_block(data, path))
    elif section == "rtm":
        errors.extend(_validate_rtm_block(data, path))
    elif section == "quality-report":
        errors.extend(_validate_quality_report_block(data, path))
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
# RTM commands
# ---------------------------------------------------------------------------


def _split_csv(values: list[str] | None) -> list[str]:
    """Accept either repeated --x flags or a single comma-separated value."""
    if not values:
        return []
    out: list[str] = []
    for v in values:
        for piece in v.split(","):
            piece = piece.strip()
            if piece:
                out.append(piece)
    return out


def cmd_rtm_upsert(args: argparse.Namespace) -> int:
    rtm_path = find_rtm_meta()
    if rtm_path is None:
        sys.stderr.write(
            "error: no RTM artifact exists; run `artifact.py init --section rtm` "
            "first\n"
        )
        return 2
    data = load_meta(rtm_path)
    rows = data.setdefault("rtm_rows", [])
    if not isinstance(rows, list):
        sys.stderr.write("error: rtm_rows is not a list — meta is corrupt\n")
        return 2

    re_id = args.re_id
    status = args.status
    if status not in COVERAGE_STATUSES:
        sys.stderr.write(
            f"error: --status must be one of {COVERAGE_STATUSES}\n"
        )
        return 2

    arch_refs = _split_csv(args.arch_refs)
    impl_refs = _split_csv(args.impl_refs)
    test_refs = _split_csv(args.test_refs)

    existing = None
    for row in rows:
        if isinstance(row, dict) and row.get("re_id") == re_id:
            existing = row
            break

    if existing is None:
        existing = {
            "re_id": re_id,
            "re_title": args.re_title,
            "re_priority": args.re_priority,
            "arch_refs": [],
            "impl_refs": [],
            "test_refs": [],
            "coverage_status": status,
            "gap_description": args.gap,
        }
        rows.append(existing)
    else:
        if args.re_title is not None:
            existing["re_title"] = args.re_title
        if args.re_priority is not None:
            existing["re_priority"] = args.re_priority
        if args.gap is not None:
            existing["gap_description"] = args.gap
        existing["coverage_status"] = status

    def _merge(target_key: str, additions: list[str]) -> None:
        if not additions:
            return
        cur = existing.setdefault(target_key, [])
        if not isinstance(cur, list):
            cur = []
        for ref in additions:
            if ref not in cur:
                cur.append(ref)
        existing[target_key] = cur

    _merge("arch_refs", arch_refs)
    _merge("impl_refs", impl_refs)
    _merge("test_refs", test_refs)

    save_meta(rtm_path, data)
    print(
        f"{data.get('artifact_id', 'rtm')}: row {re_id} -> {status} "
        f"({len(existing.get('test_refs', []))} test refs)"
    )
    return 0


def _bin_rows_by_priority(
    rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    bins: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        prio = (r.get("re_priority") or "unknown").lower()
        bins.setdefault(prio, []).append(r)
    return bins


def cmd_rtm_gap_report(_args: argparse.Namespace) -> int:
    rtm_path = find_rtm_meta()
    if rtm_path is None:
        print("(no RTM yet)")
        return 0
    data = load_meta(rtm_path)
    rows = data.get("rtm_rows") or []
    if not isinstance(rows, list) or not rows:
        print("(RTM has no rows yet)")
        return 0

    total = len(rows)
    by_status: dict[str, int] = {s: 0 for s in COVERAGE_STATUSES}
    for r in rows:
        if not isinstance(r, dict):
            continue
        st = r.get("coverage_status")
        if st in by_status:
            by_status[st] += 1

    print(f"RTM: {data.get('artifact_id', '?')} ({total} rows)")
    for st in COVERAGE_STATUSES:
        n = by_status[st]
        pct = int(round(100 * n / total)) if total else 0
        print(f"  {st:<10} {n:>4}  ({pct:>3}%)")
    print()

    gaps = [
        r
        for r in rows
        if isinstance(r, dict) and r.get("coverage_status") in ("partial", "uncovered")
    ]
    if not gaps:
        print("No coverage gaps.")
        return 0

    bins = _bin_rows_by_priority(gaps)
    print("Gaps by MoSCoW priority:")
    # Stable order: must, should, could, wont, then anything else.
    order = list(MOSCOW_PRIORITIES) + sorted(
        k for k in bins if k not in MOSCOW_PRIORITIES
    )
    for prio in order:
        if prio not in bins:
            continue
        print(f"  [{prio}] ({len(bins[prio])})")
        for r in bins[prio]:
            re_id = r.get("re_id", "?")
            status = r.get("coverage_status", "?")
            title = r.get("re_title") or ""
            gap = r.get("gap_description") or ""
            line = f"    {re_id:<10} {status:<10} {title}"
            if gap:
                line += f"  — {gap}"
            print(line)

    must_uncovered = [
        r
        for r in gaps
        if (r.get("re_priority") or "").lower() == "must"
        and r.get("coverage_status") == "uncovered"
    ]
    if must_uncovered:
        print()
        print(
            f"WARNING: {len(must_uncovered)} Must requirement(s) are uncovered."
        )
    return 0 if not must_uncovered else 1


# ---------------------------------------------------------------------------
# Quality gate evaluation
# ---------------------------------------------------------------------------


def _evaluate_gate(
    criteria: dict[str, Any] | None,
    actuals: dict[str, Any] | None,
    rtm_rows: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    """Compute gate verdict.

    Returns (verdict, reasons) where verdict is one of:
        - "pass"
        - "fail"
        - "escalated"  (a Must requirement remains uncovered with no fix)
    """
    criteria = criteria or {}
    actuals = actuals or {}
    reasons: list[str] = []

    must_uncovered = [
        r
        for r in rtm_rows
        if isinstance(r, dict)
        and (r.get("re_priority") or "").lower() == "must"
        and r.get("coverage_status") == "uncovered"
    ]
    if must_uncovered:
        ids = ", ".join(r.get("re_id", "?") for r in must_uncovered)
        reasons.append(f"Must requirements still uncovered: {ids}")
        return "escalated", reasons

    fails: list[str] = []

    code_target = criteria.get("code_coverage_min")
    code_actual = actuals.get("code_coverage")
    if code_target is not None and code_actual is not None:
        try:
            if float(code_actual) + 1e-9 < float(code_target):
                fails.append(
                    f"code coverage {code_actual} < target {code_target}"
                )
        except (TypeError, ValueError):
            fails.append(
                f"code coverage values not numeric: target={code_target} "
                f"actual={code_actual}"
            )

    must_target = criteria.get("requirements_coverage_must_min")
    must_actual = actuals.get("requirements_coverage_must")
    if must_target is not None and must_actual is not None:
        try:
            if float(must_actual) + 1e-9 < float(must_target):
                fails.append(
                    f"Must requirement coverage {must_actual} < target "
                    f"{must_target}"
                )
        except (TypeError, ValueError):
            fails.append(
                f"requirements coverage values not numeric: target={must_target} "
                f"actual={must_actual}"
            )

    failed_tests = actuals.get("failed_tests")
    max_failed = criteria.get("max_failed_tests", 0)
    if isinstance(failed_tests, int) and failed_tests > int(max_failed):
        fails.append(f"failed tests {failed_tests} > allowed {max_failed}")

    nfr_results = actuals.get("nfr_results") or []
    if isinstance(nfr_results, list):
        for nr in nfr_results:
            if not isinstance(nr, dict):
                continue
            if nr.get("pass") is False:
                metric_id = nr.get("metric_id") or nr.get("re_id") or "?"
                fails.append(
                    f"NFR {metric_id} failed: target={nr.get('target')!r} "
                    f"actual={nr.get('actual')!r}"
                )

    if fails:
        reasons.extend(fails)
        return "fail", reasons

    reasons.append("all gate criteria satisfied")
    return "pass", reasons


def cmd_gate_evaluate(args: argparse.Namespace) -> int:
    meta_path = find_meta_by_id(args.artifact_id)
    data = load_meta(meta_path)
    if data.get("section") != "quality-report":
        sys.stderr.write(
            f"error: {args.artifact_id} is not a quality-report artifact\n"
        )
        return 2

    quality_gate = data.setdefault("quality_gate", {})
    criteria = quality_gate.get("criteria") or {}
    actuals = quality_gate.get("actuals") or {}

    rtm_rows: list[dict[str, Any]] = []
    rtm_path = find_rtm_meta()
    if rtm_path is not None:
        rtm_data = load_meta(rtm_path)
        rows = rtm_data.get("rtm_rows") or []
        if isinstance(rows, list):
            rtm_rows = [r for r in rows if isinstance(r, dict)]

    verdict, reasons = _evaluate_gate(criteria, actuals, rtm_rows)
    quality_gate["verdict"] = verdict
    quality_gate["reasons"] = reasons
    quality_gate["evaluated_at"] = now_iso()

    approval = data.setdefault(
        "approval",
        {"state": "pending", "history": []},
    )
    current_state = approval.get("state", "pending")

    # Map verdict → approval state. The transitions follow APPROVAL_TRANSITIONS,
    # so a Quality Report can move from pending → approved/rejected/escalated and
    # later be re-evaluated after a fix.
    if verdict == "pass":
        target_state = "approved"
    elif verdict == "escalated":
        target_state = "escalated"
    else:
        target_state = "rejected"

    if (
        target_state not in APPROVAL_TRANSITIONS.get(current_state, set())
        and target_state != current_state
    ):
        sys.stderr.write(
            f"error: gate verdict {verdict!r} would require illegal "
            f"approval transition {current_state!r} -> {target_state!r}; "
            "reset the report to `pending` first if needed\n"
        )
        save_meta(meta_path, data)  # persist verdict even if state stuck
        return 2

    if target_state == "approved" and data.get("phase") != "in_review":
        # Allow auto-promotion from draft → in_review when the gate runs
        # against a draft, since the gate itself is the review.
        if data.get("phase") in ("draft", "revising"):
            data["phase"] = "in_review"
        else:
            sys.stderr.write(
                "error: report must be in_review (or draft/revising) before "
                "the gate can approve it\n"
            )
            save_meta(meta_path, data)
            return 2

    ts = now_iso()
    approval["state"] = target_state
    approval["approver"] = "auto:gate-evaluator"
    approval["notes"] = "; ".join(reasons)
    if target_state == "approved":
        approval["approved_at"] = ts
        data["phase"] = "approved"
    history = approval.setdefault("history", [])
    history.append(
        {
            "state": target_state,
            "approver": "auto:gate-evaluator",
            "at": ts,
            "notes": "; ".join(reasons),
            "verdict": verdict,
        }
    )

    save_meta(meta_path, data)
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "verdict": verdict,
                "approval_state": target_state,
                "reasons": reasons,
            },
            indent=2,
        )
    )
    return 0 if verdict == "pass" else 1


# ---------------------------------------------------------------------------
# Report (subagent → main handoff)
# ---------------------------------------------------------------------------

REPORT_KINDS = (
    "review",
    "report",
)
REPORT_VERDICTS = ("pass", "at_risk", "fail", "escalated", "n/a")
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


def _validate_review_item(item: dict[str, Any], index: int, errors: list[str]) -> None:
    label = f"items[{index}]"
    if not _is_non_empty_string(item.get("re_id")):
        errors.append(f"{label} missing re_id")
    if not _is_non_empty_string(item.get("priority")):
        errors.append(f"{label} missing priority")
    gap_type = item.get("gap_type")
    if not _is_non_empty_string(gap_type):
        errors.append(f"{label} missing gap_type")
    elif gap_type not in REVIEW_GAP_TYPES:
        errors.append(f"{label} has invalid gap_type {gap_type!r}")
    for key in ("description", "suggested_fix"):
        if not _is_non_empty_string(item.get(key)):
            errors.append(f"{label} missing {key}")
    if not isinstance(item.get("auto_fixable"), bool):
        errors.append(f"{label} auto_fixable must be a boolean")
    related = item.get("related_test_refs")
    if related is not None and not _is_string_list(related):
        errors.append(f"{label} related_test_refs must be a list of strings")


def _validate_report_item(item: dict[str, Any], index: int, errors: list[str]) -> None:
    label = f"items[{index}]"
    kind = item.get("kind")
    if kind is not None and not _is_non_empty_string(kind):
        errors.append(f"{label} kind must be a non-empty string")
    if kind == "failed_test":
        if not _is_non_empty_string(item.get("test_node")):
            errors.append(f"{label} failed_test requires test_node")
        if not _is_non_empty_string(item.get("failure")):
            errors.append(f"{label} failed_test requires failure")


def _validate_report_meta_op(
    op: dict[str, Any],
    *,
    stage: str | None,
    index: int,
    errors: list[str],
) -> None:
    label = f"proposed_meta_ops[{index}]"
    name = op.get("op")
    if not _is_non_empty_string(name):
        errors.append(f"{label} missing op")
        return

    allowed = REPORT_ALLOWED_OPS_BY_STAGE.get(stage)
    if allowed is not None and name not in allowed:
        errors.append(
            f"{label} op {name!r} is not allowed for stage {stage!r}"
        )
        return

    if not _is_non_empty_string(op.get("artifact_id")) and name != "rtm-upsert":
        errors.append(f"{label} {name} requires artifact_id")

    if name == "rtm-upsert":
        if not _is_non_empty_string(op.get("re_id")):
            errors.append(f"{label} rtm-upsert requires re_id")
        status = op.get("status")
        if status not in COVERAGE_STATUSES:
            errors.append(f"{label} rtm-upsert requires valid status")
        for key in ("arch_refs", "impl_refs", "test_refs"):
            value = op.get(key)
            if value is not None and not _is_string_list(value):
                errors.append(f"{label} rtm-upsert {key} must be a list of strings")
    elif name == "write-quality-report-actuals":
        if not isinstance(op.get("quality_report"), dict):
            errors.append(
                f"{label} write-quality-report-actuals requires quality_report"
            )
        quality_gate = op.get("quality_gate")
        if not isinstance(quality_gate, dict):
            errors.append(
                f"{label} write-quality-report-actuals requires quality_gate"
            )
        elif not isinstance(quality_gate.get("actuals"), dict):
            errors.append(
                f"{label} write-quality-report-actuals requires "
                "quality_gate.actuals"
            )
    elif name == "gate-evaluate":
        # artifact_id presence already checked above.
        pass


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
    if fm.get("verdict") == "n/a":
        errors.append("verdict 'n/a' is only allowed in the initial stub")
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
        for index, ref in enumerate(target_refs):
            if not _is_non_empty_string(ref):
                errors.append(f"target_refs[{index}] must be a non-empty string")

    proposed_meta_ops = fm.get("proposed_meta_ops")
    if proposed_meta_ops is not None and not isinstance(proposed_meta_ops, list):
        errors.append("proposed_meta_ops must be a list")
        proposed_meta_ops = []

    items = fm.get("items")
    if items is not None and not isinstance(items, list):
        errors.append("items must be a list")
        items = []
    elif stage in {"review"} and fm.get("verdict") in {"at_risk", "fail", "escalated"}:
        if isinstance(items, list) and not items:
            errors.append(
                f"{stage} reports with verdict {fm.get('verdict')!r} must include "
                "at least one item"
            )

    if isinstance(items, list):
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"items[{index}] must be a mapping")
                continue
            if stage == "review":
                _validate_review_item(item, index, errors)
            elif stage == "report":
                _validate_report_item(item, index, errors)

    if isinstance(proposed_meta_ops, list):
        for index, op in enumerate(proposed_meta_ops):
            if not isinstance(op, dict):
                errors.append(f"proposed_meta_ops[{index}] must be a mapping")
                continue
            _validate_report_meta_op(op, stage=stage, index=index, errors=errors)

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

    sp = sub.add_parser(
        "set-block",
        help="replace a script-managed structured metadata block from YAML/JSON",
    )
    sp.add_argument("artifact_id")
    sp.add_argument("--field", required=True, choices=sorted(SETTABLE_FIELDS))
    sp.add_argument("--from", dest="from_path", default=None)
    sp.add_argument("--value", default=None)
    sp.set_defaults(func=cmd_set_block)

    sp = sub.add_parser("validate", help="validate schema and traceability")
    sp.add_argument("artifact_id", nargs="?", default=None)
    sp.set_defaults(func=cmd_validate)

    sp = sub.add_parser(
        "rtm-upsert",
        help="insert or update an RTM row for a single requirement",
    )
    sp.add_argument("--re-id", required=True)
    sp.add_argument("--re-title", default=None)
    sp.add_argument(
        "--re-priority",
        default=None,
        help="MoSCoW priority of the requirement (must/should/could/wont)",
    )
    sp.add_argument(
        "--arch-refs",
        action="append",
        default=None,
        help="comma-separated or repeatable Arch ids",
    )
    sp.add_argument(
        "--impl-refs",
        action="append",
        default=None,
        help="comma-separated or repeatable Impl ids",
    )
    sp.add_argument(
        "--test-refs",
        action="append",
        default=None,
        help="comma-separated or repeatable test refs (e.g. QA-SUITE-001:TS-001-C01)",
    )
    sp.add_argument(
        "--status",
        required=True,
        choices=COVERAGE_STATUSES,
    )
    sp.add_argument("--gap", default=None, help="gap description if not covered")
    sp.set_defaults(func=cmd_rtm_upsert)

    sp = sub.add_parser(
        "rtm-gap-report",
        help="print the RTM coverage roll-up grouped by MoSCoW priority",
    )
    sp.set_defaults(func=cmd_rtm_gap_report)

    sp = sub.add_parser(
        "gate-evaluate",
        help="evaluate a quality-report's quality_gate block and transition approval",
    )
    sp.add_argument("artifact_id")
    sp.set_defaults(func=cmd_gate_evaluate)

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
        help="workflow stage producing the report (e.g. review, report)",
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
