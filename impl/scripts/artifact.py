#!/usr/bin/env python3
"""Artifact manager for the Impl skill.

Single entry point for all metadata manipulation. The Impl skill must not edit
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

SECTIONS = (
    "implementation-map",
    "code-structure",
    "implementation-decisions",
    "implementation-guide",
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
        base = Path.cwd() / "artifacts" / "impl"
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


# ---------------------------------------------------------------------------
# ID allocation
# ---------------------------------------------------------------------------


SECTION_PREFIX = {
    "implementation-map": "IMPL-MAP",
    "code-structure": "IMPL-CODE",
    "implementation-decisions": "IMPL-IDR",
    "implementation-guide": "IMPL-GUIDE",
}
ARTIFACT_ID_PATTERNS = {
    "implementation-map": re.compile(r"^IMPL-MAP-\d{3}$"),
    "code-structure": re.compile(r"^IMPL-CODE-\d{3}$"),
    "implementation-decisions": re.compile(r"^IMPL-IDR-\d{3}$"),
    "implementation-guide": re.compile(r"^IMPL-GUIDE-\d{3}$"),
}
IMPL_MAP_ENTRY_RE = re.compile(r"^IM-\d{3}$")
IDR_ENTRY_RE = re.compile(r"^IDR-\d{3}$")
ARCH_COMPONENT_RE = re.compile(r"^ARCH-COMP-\d{3}$")
ARCH_TECH_RE = re.compile(r"^ARCH-TECH-\d{3}$")
ARCH_REF_RE = re.compile(r"^ARCH-(DEC|COMP|TECH|DIAG)-\d{3}$")
RE_REF_RE = re.compile(r"^(FR|NFR|CON)-\d{3}$")
ISO_8601_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
MODULE_DEPENDENCY_KINDS = {"import", "runtime", "build", "test"}


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


def _validate_timestamp(
    value: Any,
    *,
    field: str,
    path: Path,
) -> list[str]:
    if not _is_non_empty_string(value):
        return [f"{path.name}: {field} must be a non-empty ISO 8601 UTC string"]
    if not ISO_8601_UTC_RE.match(value):
        return [f"{path.name}: {field} must match YYYY-MM-DDTHH:MM:SSZ"]
    return []


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
            errors.append(
                f"{path.name}: row {index} has invalid {key} {raw_id!r}"
            )
        elif raw_id in seen:
            errors.append(f"{path.name}: duplicate {key} {raw_id!r}")
        seen.add(raw_id)
    return errors


def _validate_ref_list(
    value: Any,
    *,
    field_name: str,
    path: Path,
    min_items: int = 0,
    pattern: re.Pattern[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    expected = "at least one" if min_items else "a"
    if not _is_string_list(value, min_items=min_items):
        errors.append(
            f"{path.name}: {field_name} must be {expected} list of non-empty strings"
        )
        return errors
    assert isinstance(value, list)
    if pattern is not None:
        for item in value:
            if not pattern.match(item):
                errors.append(
                    f"{path.name}: {field_name} has invalid ref {item!r}"
                )
    return errors


def _validate_implementation_map(
    data: dict[str, Any], path: Path, *, strict: bool
) -> list[str]:
    errors: list[str] = []
    rows = data.get("implementation_map")
    if not isinstance(rows, list):
        return [f"{path.name}: implementation_map must be a list"]
    if strict and not rows:
        errors.append(
            f"{path.name}: in_review implementation-map artifacts must contain "
            "at least one mapping"
        )

    errors.extend(
        _validate_id_sequence(rows, key="id", pattern=IMPL_MAP_ENTRY_RE, path=path)
    )
    for item in rows:
        if not isinstance(item, dict):
            errors.append(f"{path.name}: implementation_map rows must be mappings")
            continue
        row_id = item.get("id", "?")
        component_ref = item.get("component_ref")
        if not _is_non_empty_string(component_ref):
            errors.append(f"{path.name}: {row_id} missing component_ref")
        elif not ARCH_COMPONENT_RE.match(component_ref):
            errors.append(
                f"{path.name}: {row_id} has invalid component_ref {component_ref!r}"
            )
        for field in ("module_path", "entry_point", "internal_structure"):
            if not _is_non_empty_string(item.get(field)):
                errors.append(f"{path.name}: {row_id} missing {field}")
        interfaces = item.get("interfaces_implemented")
        if not isinstance(interfaces, list) or not interfaces:
            errors.append(
                f"{path.name}: {row_id} must list at least one implemented interface"
            )
            interfaces = []
        for index, interface in enumerate(interfaces, start=1):
            if not isinstance(interface, dict):
                errors.append(
                    f"{path.name}: {row_id} interface {index} must be a mapping"
                )
                continue
            for field in ("arch_interface", "file"):
                if not _is_non_empty_string(interface.get(field)):
                    errors.append(
                        f"{path.name}: {row_id} interface {index} missing {field}"
                    )
            notes = interface.get("notes")
            if notes is not None and not _is_non_empty_string(notes):
                errors.append(
                    f"{path.name}: {row_id} interface {index} notes must be null or "
                    "a non-empty string"
                )
        errors.extend(
            _validate_ref_list(
                item.get("arch_refs"),
                field_name=f"{row_id}.arch_refs",
                path=path,
                min_items=1,
                pattern=ARCH_REF_RE,
            )
        )
        re_refs = item.get("re_refs")
        if re_refs is not None:
            errors.extend(
                _validate_ref_list(
                    re_refs,
                    field_name=f"{row_id}.re_refs",
                    path=path,
                    pattern=RE_REF_RE,
                )
            )
    return errors


def _validate_code_structure(
    data: dict[str, Any], path: Path, *, strict: bool
) -> list[str]:
    errors: list[str] = []
    payload = data.get("code_structure")
    if not isinstance(payload, dict):
        return [f"{path.name}: code_structure must be a mapping"]

    for field in ("project_root", "directory_layout"):
        value = payload.get(field)
        if strict:
            if not _is_non_empty_string(value):
                errors.append(f"{path.name}: code_structure missing {field}")
        elif value is not None and not _is_non_empty_string(value):
            errors.append(
                f"{path.name}: code_structure.{field} must be null or a "
                "non-empty string"
            )

    module_dependencies = payload.get("module_dependencies")
    if not isinstance(module_dependencies, list):
        errors.append(f"{path.name}: code_structure.module_dependencies must be a list")
        module_dependencies = []
    for index, dependency in enumerate(module_dependencies, start=1):
        if not isinstance(dependency, dict):
            errors.append(
                f"{path.name}: module_dependencies row {index} must be a mapping"
            )
            continue
        for field in ("from", "to"):
            if not _is_non_empty_string(dependency.get(field)):
                errors.append(
                    f"{path.name}: module_dependencies row {index} missing {field}"
                )
        kind = dependency.get("kind")
        if kind not in MODULE_DEPENDENCY_KINDS:
            errors.append(
                f"{path.name}: module_dependencies row {index} has invalid kind "
                f"{kind!r}"
            )

    external_dependencies = payload.get("external_dependencies")
    if not isinstance(external_dependencies, list):
        errors.append(
            f"{path.name}: code_structure.external_dependencies must be a list"
        )
        external_dependencies = []
    for index, dependency in enumerate(external_dependencies, start=1):
        if not isinstance(dependency, dict):
            errors.append(
                f"{path.name}: external_dependencies row {index} must be a mapping"
            )
            continue
        for field in ("name", "version", "purpose"):
            if not _is_non_empty_string(dependency.get(field)):
                errors.append(
                    f"{path.name}: external_dependencies row {index} missing {field}"
                )
        tech_stack_ref = dependency.get("tech_stack_ref")
        if not _is_non_empty_string(tech_stack_ref):
            errors.append(
                f"{path.name}: external_dependencies row {index} missing "
                "tech_stack_ref"
            )
        elif not ARCH_TECH_RE.match(tech_stack_ref):
            errors.append(
                f"{path.name}: external_dependencies row {index} has invalid "
                f"tech_stack_ref {tech_stack_ref!r}"
            )

    build_config = payload.get("build_config")
    if not isinstance(build_config, list):
        errors.append(f"{path.name}: code_structure.build_config must be a list")
        build_config = []
    elif strict and not build_config:
        errors.append(
            f"{path.name}: in_review code-structure artifacts must contain at least "
            "one build_config row"
        )
    for index, entry in enumerate(build_config, start=1):
        if not isinstance(entry, dict):
            errors.append(f"{path.name}: build_config row {index} must be a mapping")
            continue
        for field in ("file", "purpose"):
            if not _is_non_empty_string(entry.get(field)):
                errors.append(
                    f"{path.name}: build_config row {index} missing {field}"
                )

    environment_config = payload.get("environment_config")
    if environment_config is not None and not isinstance(environment_config, list):
        errors.append(
            f"{path.name}: code_structure.environment_config must be a list"
        )
        environment_config = []
    for index, entry in enumerate(environment_config or [], start=1):
        if not isinstance(entry, dict):
            errors.append(
                f"{path.name}: environment_config row {index} must be a mapping"
            )
            continue
        for field in ("name", "purpose"):
            if not _is_non_empty_string(entry.get(field)):
                errors.append(
                    f"{path.name}: environment_config row {index} missing {field}"
                )
        if not isinstance(entry.get("required"), bool):
            errors.append(
                f"{path.name}: environment_config row {index} required must be bool"
            )
    return errors


def _validate_implementation_decisions(data: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    rows = data.get("implementation_decisions")
    if not isinstance(rows, list):
        return [f"{path.name}: implementation_decisions must be a list"]

    errors.extend(
        _validate_id_sequence(rows, key="id", pattern=IDR_ENTRY_RE, path=path)
    )
    for item in rows:
        if not isinstance(item, dict):
            errors.append(
                f"{path.name}: implementation_decisions rows must be mappings"
            )
            continue
        row_id = item.get("id", "?")
        for field in ("title", "decision", "rationale"):
            if not _is_non_empty_string(item.get(field)):
                errors.append(f"{path.name}: {row_id} missing {field}")
        alternatives = item.get("alternatives_considered")
        if alternatives is not None and not isinstance(alternatives, list):
            errors.append(f"{path.name}: {row_id} alternatives_considered must be a list")
            alternatives = []
        for index, alternative in enumerate(alternatives or [], start=1):
            if not isinstance(alternative, dict):
                errors.append(
                    f"{path.name}: {row_id} alternative {index} must be a mapping"
                )
                continue
            for field in ("option", "rejected_reason"):
                if not _is_non_empty_string(alternative.get(field)):
                    errors.append(
                        f"{path.name}: {row_id} alternative {index} missing {field}"
                    )
            for field in ("pros", "cons"):
                if not _is_string_list(alternative.get(field), min_items=1):
                    errors.append(
                        f"{path.name}: {row_id} alternative {index} {field} must "
                        "list at least one non-empty string"
                    )
        pattern_applied = item.get("pattern_applied")
        if pattern_applied is not None and not _is_non_empty_string(pattern_applied):
            errors.append(
                f"{path.name}: {row_id} pattern_applied must be null or a "
                "non-empty string"
            )
        errors.extend(
            _validate_ref_list(
                item.get("arch_refs"),
                field_name=f"{row_id}.arch_refs",
                path=path,
                min_items=1,
                pattern=ARCH_REF_RE,
            )
        )
        re_refs = item.get("re_refs")
        if re_refs is not None:
            errors.extend(
                _validate_ref_list(
                    re_refs,
                    field_name=f"{row_id}.re_refs",
                    path=path,
                    pattern=RE_REF_RE,
                )
            )
    return errors


def _validate_implementation_guide(
    data: dict[str, Any], path: Path, *, strict: bool
) -> list[str]:
    errors: list[str] = []
    payload = data.get("implementation_guide")
    if not isinstance(payload, dict):
        return [f"{path.name}: implementation_guide must be a mapping"]

    prerequisites = payload.get("prerequisites")
    if not isinstance(prerequisites, list):
        errors.append(f"{path.name}: implementation_guide.prerequisites must be a list")
        prerequisites = []
    for index, item in enumerate(prerequisites, start=1):
        if not isinstance(item, dict):
            errors.append(f"{path.name}: prerequisite row {index} must be a mapping")
            continue
        for field in ("tool", "version"):
            if not _is_non_empty_string(item.get(field)):
                errors.append(f"{path.name}: prerequisite row {index} missing {field}")
        notes = item.get("notes")
        if notes is not None and not _is_non_empty_string(notes):
            errors.append(
                f"{path.name}: prerequisite row {index} notes must be null or a "
                "non-empty string"
            )

    for field in ("setup_steps", "build_commands", "run_commands"):
        value = payload.get(field)
        if not isinstance(value, list):
            errors.append(f"{path.name}: implementation_guide.{field} must be a list")
            continue
        if strict and not value:
            errors.append(
                f"{path.name}: in_review implementation-guide artifacts must contain "
                f"at least one {field} entry"
            )
        for index, item in enumerate(value, start=1):
            if not _is_non_empty_string(item):
                errors.append(
                    f"{path.name}: implementation_guide.{field}[{index}] must be a "
                    "non-empty string"
                )

    conventions = payload.get("conventions")
    if not isinstance(conventions, dict):
        errors.append(f"{path.name}: implementation_guide.conventions must be a mapping")
    elif strict and not conventions:
        errors.append(
            f"{path.name}: in_review implementation-guide artifacts must record "
            "detected conventions"
        )
    else:
        for key, value in conventions.items():
            if not _is_non_empty_string(key):
                errors.append(f"{path.name}: implementation_guide.conventions has empty key")
            if not _is_non_empty_string(value):
                errors.append(
                    f"{path.name}: implementation_guide.conventions[{key!r}] must be "
                    "a non-empty string"
                )

    extension_points = payload.get("extension_points")
    if extension_points is not None and not isinstance(extension_points, list):
        errors.append(
            f"{path.name}: implementation_guide.extension_points must be a list"
        )
        extension_points = []
    for index, item in enumerate(extension_points or [], start=1):
        if not isinstance(item, dict):
            errors.append(
                f"{path.name}: extension_points row {index} must be a mapping"
            )
            continue
        for field in ("goal", "touch_point"):
            if not _is_non_empty_string(item.get(field)):
                errors.append(
                    f"{path.name}: extension_points row {index} missing {field}"
                )
        notes = item.get("notes")
        if notes is not None and not _is_non_empty_string(notes):
            errors.append(
                f"{path.name}: extension_points row {index} notes must be null or "
                "a non-empty string"
            )
    return errors


def _validate_section_payload(data: dict[str, Any], path: Path) -> list[str]:
    section = data.get("section")
    phase = data.get("phase")
    strict = phase in {"in_review", "revising", "approved"}

    if section == "implementation-map":
        return _validate_implementation_map(data, path, strict=strict)
    if section == "code-structure":
        return _validate_code_structure(data, path, strict=strict)
    if section == "implementation-decisions":
        return _validate_implementation_decisions(data, path)
    if section == "implementation-guide":
        return _validate_implementation_guide(data, path, strict=strict)
    return []


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
        print(f"{aid:<{width}}  {section:<24}  {phase:<10}  {approval}")
    return 0


def _validate_meta(data: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_META_FIELDS:
        if field not in data:
            errors.append(f"{path.name}: missing field {field!r}")

    artifact_id = data.get("artifact_id")
    if not _is_non_empty_string(artifact_id):
        errors.append(f"{path.name}: artifact_id must be a non-empty string")
    phase = data.get("phase")
    if phase not in PHASES:
        errors.append(f"{path.name}: unknown phase {phase!r}")
    section = data.get("section")
    if section not in SECTIONS:
        errors.append(f"{path.name}: unknown section {section!r}")
    elif _is_non_empty_string(artifact_id):
        assert isinstance(artifact_id, str)
        pattern = ARTIFACT_ID_PATTERNS[section]
        if not pattern.match(artifact_id):
            errors.append(
                f"{path.name}: artifact_id {artifact_id!r} does not match "
                f"section {section!r}"
            )

    errors.extend(_validate_timestamp(data.get("created_at"), field="created_at", path=path))
    errors.extend(_validate_timestamp(data.get("updated_at"), field="updated_at", path=path))

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
            if phase in {"in_review", "revising", "approved"} and total <= 0:
                errors.append(
                    f"{path.name}: progress.section_total must be > 0 once the "
                    "artifact leaves draft"
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

    approval = data.get("approval") or {}
    if not isinstance(approval, dict):
        errors.append(f"{path.name}: approval must be a mapping")
        approval = {}
    state = approval.get("state")
    if state and state not in APPROVAL_STATES:
        errors.append(f"{path.name}: unknown approval state {state!r}")
    if state == "approved" and phase != "approved":
        errors.append(
            f"{path.name}: approval.state cannot be 'approved' while phase is "
            f"{phase!r}"
        )
    if phase == "approved" and state != "approved":
        errors.append(f"{path.name}: phase 'approved' requires approval.state 'approved'")
    approver = approval.get("approver")
    if state in {"approved", "rejected", "changes_requested"} and not _is_non_empty_string(
        approver
    ):
        errors.append(
            f"{path.name}: approval.approver must be set when approval.state is "
            f"{state!r}"
        )
    approved_at = approval.get("approved_at")
    if state == "approved":
        errors.extend(
            _validate_timestamp(approved_at, field="approval.approved_at", path=path)
        )
    elif approved_at not in (None, ""):
        errors.append(
            f"{path.name}: approval.approved_at must be null unless state is "
            "'approved'"
        )
    history = approval.get("history")
    if history is not None and not isinstance(history, list):
        errors.append(f"{path.name}: approval.history must be a list")

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

    errors.extend(_validate_section_payload(data, path))
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

SKILL_NAME = "impl"

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
REPORT_KIND_BY_STAGE = {"review": "review", "refactor": "refactor"}
REPORT_CLASSIFICATIONS_BY_STAGE = {
    "review": {
        "contract_violation",
        "clean_code",
        "security_baseline",
        "traceability_gap",
        "escalation",
    },
    "refactor": {"refactor_applied", "idr_added", "boundary_escalation"},
}
REPORT_ALLOWED_OPS_BY_STAGE = {
    "review": {"link"},
    "refactor": {"link", "set-progress"},
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


def _validate_report_item(
    item: Any,
    *,
    index: int,
    stage: str | None,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(item, dict):
        return [f"items[{index}] must be a mapping"]

    item_id = item.get("id")
    if not (isinstance(item_id, int) or _is_non_empty_string(item_id)):
        errors.append(f"items[{index}] missing id")

    classification = item.get("classification")
    allowed_classifications = REPORT_CLASSIFICATIONS_BY_STAGE.get(stage)
    if not _is_non_empty_string(classification):
        errors.append(f"items[{index}] missing classification")
    elif (
        allowed_classifications is not None
        and classification not in allowed_classifications
    ):
        errors.append(
            f"items[{index}] has invalid classification {classification!r} for "
            f"stage {stage!r}"
        )

    severity = item.get("severity")
    if stage == "review":
        if severity not in REPORT_ITEM_SEVERITIES:
            errors.append(
                f"items[{index}] has invalid severity {severity!r} for review stage"
            )
    elif severity is not None and severity not in REPORT_ITEM_SEVERITIES:
        errors.append(f"items[{index}] has invalid severity {severity!r}")

    location = item.get("location")
    if stage == "review":
        if not _is_non_empty_string(location):
            errors.append(f"items[{index}] missing location")
    elif location is not None and not _is_non_empty_string(location):
        errors.append(f"items[{index}] location must be a non-empty string")

    message = item.get("message")
    if not _is_non_empty_string(message):
        errors.append(f"items[{index}] missing message")

    suggested_fix = item.get("suggested_fix")
    if stage == "review":
        if not _is_non_empty_string(suggested_fix):
            errors.append(f"items[{index}] missing suggested_fix")
    elif suggested_fix is not None and not _is_non_empty_string(suggested_fix):
        errors.append(
            f"items[{index}] suggested_fix must be a non-empty string when set"
        )

    arch_ref = item.get("arch_ref")
    if arch_ref is not None and not _is_non_empty_string(arch_ref):
        errors.append(f"items[{index}] arch_ref must be a non-empty string when set")
    return errors


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
    errors.extend(
        _validate_timestamp(fm.get("created_at"), field="created_at", path=p)
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
    if stage in REPORT_KIND_BY_STAGE and isinstance(target_refs, list) and not target_refs:
        errors.append(f"{stage} reports must include at least one target_ref")

    proposed_meta_ops = fm.get("proposed_meta_ops")
    if proposed_meta_ops is not None and not isinstance(proposed_meta_ops, list):
        errors.append("proposed_meta_ops must be a list")
        proposed_meta_ops = []

    items = fm.get("items")
    if items is not None and not isinstance(items, list):
        errors.append("items must be a list")
        items = []
    elif isinstance(items, list):
        for index, item in enumerate(items, start=1):
            errors.extend(_validate_report_item(item, index=index, stage=stage))

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
        help="workflow stage producing the report (e.g. review, refactor)",
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
