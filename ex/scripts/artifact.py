#!/usr/bin/env python3
"""Artifact manager for the Ex skill.

Single entry point for all metadata manipulation. The Ex skill must not edit
`*.meta.yaml` files directly — it calls this script instead so that schema,
phase transitions, section payload updates, traceability, and audit history are
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
        "PyYAML is required. Install with: pip install -r requirements.txt "
        "or pip install pyyaml\n"
    )
    sys.exit(2)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKILL_NAME = "ex"

SECTIONS = ("structure-map", "tech-stack", "components", "architecture")

SECTION_PREFIX = {
    "structure-map": "EX-STR",
    "tech-stack": "EX-TS",
    "components": "EX-CMP",
    "architecture": "EX-ARC",
}

SECTION_FIELDS: dict[str, tuple[str, ...]] = {
    "structure-map": (
        "project_root",
        "file_count",
        "directory_conventions",
        "entry_points",
        "config_files",
        "ignored_patterns",
        "depth_mode",
        "depth_evidence",
    ),
    "tech-stack": ("technologies",),
    "components": (
        "components",
        "circular_dependencies",
        "cross_cutting_concerns",
    ),
    "architecture": (
        "architecture_style",
        "style_confidence",
        "style_evidence",
        "layer_structure",
        "communication_patterns",
        "data_stores",
        "cross_cutting_concerns",
        "test_patterns",
        "build_deploy_patterns",
        "token_budget_summary",
    ),
}

SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "structure-map": ("structure-map", "structure_map"),
    "tech-stack": ("tech-stack", "tech_stack"),
    "components": ("component_relationships", "components_section"),
    "architecture": ("architecture", "architecture_inference"),
}

DEFAULT_DOWNSTREAM_BY_SECTION: dict[str, tuple[str, ...]] = {
    "structure-map": ("re", "impl", "qa"),
    "tech-stack": ("arch", "impl", "qa"),
    "components": ("arch", "impl", "sec"),
    "architecture": ("re", "arch", "qa"),
}

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

TECH_CATEGORIES = (
    "language",
    "framework",
    "database",
    "messaging",
    "build",
    "test",
    "lint",
    "ci",
    "container",
    "infra",
)

COMPONENT_TYPES = ("service", "library", "handler", "model", "config", "util", "test")
ARCHITECTURE_STYLES = (
    "monolithic",
    "modular-monolith",
    "microservices",
    "serverless",
    "layered",
    "hexagonal",
    "event-driven",
)
STYLE_CONFIDENCES = ("high", "medium", "low")

CLI_ARTIFACTS_DIR: Path | None = None


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


def default_run_label() -> str:
    return (
        os.environ.get("HARNESS_RUN_ID")
        or os.environ.get("SESSION_ID")
        or "standalone"
    )


def default_artifacts_dir() -> Path:
    return skill_dir() / "out" / default_run_label()


def artifacts_dir(*, create: bool = True) -> Path:
    if CLI_ARTIFACTS_DIR is not None:
        base = CLI_ARTIFACTS_DIR
    else:
        env = os.environ.get("HARNESS_ARTIFACTS_DIR")
        if env:
            base = Path(env)
        else:
            # Ex analyzes external codebases, so the standalone fallback must stay
            # outside the target project to preserve the read-only contract.
            base = default_artifacts_dir()
    if create:
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
    for p in all_meta_files():
        try:
            data = load_meta(p)
        except Exception:
            continue
        if data.get("artifact_id") == artifact_id:
            return p
    raise FileNotFoundError(
        f"No artifact found with id {artifact_id!r} in {artifacts_dir(create=False)}"
    )


def all_meta_files() -> list[Path]:
    base = artifacts_dir(create=False)
    if not base.exists():
        return []
    return sorted(base.glob("*.meta.yaml"))


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_string_list(value: Any, *, min_items: int = 0) -> bool:
    return (
        isinstance(value, list)
        and len(value) >= min_items
        and all(_is_non_empty_string(item) for item in value)
    )


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


def _extract_section_payload(section: str, payload: Any) -> dict[str, Any]:
    fields = SECTION_FIELDS[section]

    if isinstance(payload, dict):
        for alias in SECTION_ALIASES.get(section, ()):
            nested = payload.get(alias)
            if isinstance(nested, dict):
                payload = nested
                break

    if section == "tech-stack" and isinstance(payload, list):
        return {"technologies": payload}

    if section == "components" and isinstance(payload, list):
        return {"components": payload}

    if not isinstance(payload, dict):
        raise ValueError(
            f"section payload for {section!r} must be a mapping"
        )

    update = {field: payload[field] for field in fields if field in payload}
    if update:
        return update

    if section == "tech-stack" and "technologies" in payload:
        return {"technologies": payload["technologies"]}
    if section == "components" and "components" in payload:
        return {"components": payload["components"]}

    raise ValueError(
        f"payload does not contain any {section!r} fields "
        f"({', '.join(fields)})"
    )


def _add_unique_ref(refs: list[str], value: str) -> None:
    if value not in refs:
        refs.append(value)


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


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_progress(progress: Any, path: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(progress, dict):
        return [f"{path.name}: progress must be a mapping"]

    completed = progress.get("section_completed")
    total = progress.get("section_total")
    percent = progress.get("percent")
    if not all(isinstance(value, int) for value in (completed, total, percent)):
        return [
            f"{path.name}: progress must contain integer section_completed, "
            "section_total, and percent"
        ]
    if completed < 0 or total < 0:
        errors.append(f"{path.name}: progress counts must be non-negative")
        return errors
    if total == 0:
        if completed != 0 or percent != 0:
            errors.append(f"{path.name}: progress with total 0 must be 0/0 (0%)")
        return errors
    if completed > total:
        errors.append(
            f"{path.name}: progress section_completed {completed} exceeds total {total}"
        )
    expected_percent = int(round(100 * completed / total))
    if percent != expected_percent:
        errors.append(
            f"{path.name}: progress percent {percent} does not match "
            f"{completed}/{total} ({expected_percent})"
        )
    return errors


def _validate_approval(approval: Any, path: Path) -> list[str]:
    if not isinstance(approval, dict):
        return [f"{path.name}: approval must be a mapping"]

    errors: list[str] = []
    state = approval.get("state")
    if state not in APPROVAL_STATES:
        errors.append(f"{path.name}: unknown approval state {state!r}")
    approver = approval.get("approver")
    if approver is not None and not _is_non_empty_string(approver):
        errors.append(f"{path.name}: approval.approver must be a non-empty string")
    approved_at = approval.get("approved_at")
    if approved_at is not None and not _is_non_empty_string(approved_at):
        errors.append(f"{path.name}: approval.approved_at must be a non-empty string")
    notes = approval.get("notes")
    if notes is not None and not isinstance(notes, str):
        errors.append(f"{path.name}: approval.notes must be a string or null")
    history = approval.get("history")
    if not isinstance(history, list):
        errors.append(f"{path.name}: approval.history must be a list")
    else:
        for index, item in enumerate(history):
            label = f"{path.name}: approval.history[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be a mapping")
                continue
            for key in ("state", "approver", "at"):
                if not _is_non_empty_string(item.get(key)):
                    errors.append(f"{label}.{key} must be a non-empty string")
            if item.get("state") not in APPROVAL_STATES:
                errors.append(f"{label}.state invalid: {item.get('state')!r}")
            item_notes = item.get("notes")
            if item_notes is not None and not isinstance(item_notes, str):
                errors.append(f"{label}.notes must be a string or null")
    if state == "approved" and not _is_non_empty_string(approved_at):
        errors.append(f"{path.name}: approved artifacts must set approval.approved_at")
    return errors


def _validate_file_role_list(value: Any, path: Path, field: str) -> list[str]:
    if not isinstance(value, list):
        return [f"{path.name}: {field} must be a list"]
    errors: list[str] = []
    for index, item in enumerate(value):
        label = f"{path.name}: {field}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be a mapping")
            continue
        for key in ("file", "role", "evidence"):
            if not _is_non_empty_string(item.get(key)):
                errors.append(f"{label}.{key} must be a non-empty string")
    return errors


def _validate_structure_map(data: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []

    project_root = data.get("project_root")
    if project_root is not None and not _is_non_empty_string(project_root):
        errors.append(f"{path.name}: project_root must be a non-empty string")

    file_count = data.get("file_count")
    if not isinstance(file_count, dict):
        errors.append(f"{path.name}: file_count must be a mapping")
    else:
        total = file_count.get("total")
        if not isinstance(total, int) or total < 0:
            errors.append(f"{path.name}: file_count.total must be a non-negative int")
        by_category = file_count.get("by_category")
        if not isinstance(by_category, dict):
            errors.append(f"{path.name}: file_count.by_category must be a mapping")
        else:
            for key, value in by_category.items():
                if not _is_non_empty_string(key) or not isinstance(value, int) or value < 0:
                    errors.append(
                        f"{path.name}: file_count.by_category must map strings to "
                        "non-negative ints"
                    )
                    break

    if not _is_string_list(data.get("directory_conventions", [])):
        errors.append(f"{path.name}: directory_conventions must be a list of strings")
    errors.extend(_validate_file_role_list(data.get("entry_points"), path, "entry_points"))
    errors.extend(_validate_file_role_list(data.get("config_files"), path, "config_files"))
    if not _is_string_list(data.get("ignored_patterns", [])):
        errors.append(f"{path.name}: ignored_patterns must be a list of strings")

    depth_mode = data.get("depth_mode")
    if depth_mode is not None and depth_mode not in ("lite", "heavy"):
        errors.append(f"{path.name}: depth_mode invalid: {depth_mode!r}")
    depth_evidence = data.get("depth_evidence")
    if depth_evidence is not None and not _is_non_empty_string(depth_evidence):
        errors.append(f"{path.name}: depth_evidence must be a non-empty string")

    if data.get("phase") in ("in_review", "approved"):
        if not _is_non_empty_string(project_root):
            errors.append(f"{path.name}: in_review structure-map must set project_root")
        if depth_mode is None:
            errors.append(f"{path.name}: in_review structure-map must set depth_mode")
        if not _is_non_empty_string(depth_evidence):
            errors.append(f"{path.name}: in_review structure-map must set depth_evidence")
    return errors


def _validate_tech_stack(data: dict[str, Any], path: Path) -> list[str]:
    technologies = data.get("technologies")
    if not isinstance(technologies, list):
        return [f"{path.name}: technologies must be a list"]

    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, tech in enumerate(technologies):
        label = f"{path.name}: technologies[{index}]"
        if not isinstance(tech, dict):
            errors.append(f"{label} must be a mapping")
            continue
        tech_id = tech.get("id")
        if not _is_non_empty_string(tech_id):
            errors.append(f"{label}.id must be a non-empty string")
        elif tech_id in seen_ids:
            errors.append(f"{label}.id duplicates {tech_id!r}")
        else:
            seen_ids.add(tech_id)
        if tech.get("category") not in TECH_CATEGORIES:
            errors.append(f"{label}.category invalid: {tech.get('category')!r}")
        for key in ("name", "evidence", "role"):
            if not _is_non_empty_string(tech.get(key)):
                errors.append(f"{label}.{key} must be a non-empty string")
        for key in ("version", "config_location"):
            value = tech.get(key)
            if value is not None and not _is_non_empty_string(value):
                errors.append(f"{label}.{key} must be a non-empty string or null")

    if data.get("phase") in ("in_review", "approved") and not technologies:
        errors.append(f"{path.name}: in_review tech-stack must contain technologies")
    return errors


def _validate_api_surface(value: Any, label: str) -> list[str]:
    if not isinstance(value, list):
        return [f"{label} must be a list"]
    errors: list[str] = []
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_label} must be a mapping")
            continue
        if not _is_non_empty_string(item.get("type")):
            errors.append(f"{item_label}.type must be a non-empty string")
        endpoint = item.get("endpoint")
        if endpoint is not None and not _is_non_empty_string(endpoint):
            errors.append(f"{item_label}.endpoint must be a non-empty string or null")
        methods = item.get("methods")
        if methods is not None and not _is_string_list(methods):
            errors.append(f"{item_label}.methods must be a list of strings")
    return errors


def _validate_components(data: dict[str, Any], path: Path) -> list[str]:
    components = data.get("components")
    if not isinstance(components, list):
        return [f"{path.name}: components must be a list"]

    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, component in enumerate(components):
        label = f"{path.name}: components[{index}]"
        if not isinstance(component, dict):
            errors.append(f"{label} must be a mapping")
            continue
        component_id = component.get("id")
        if not _is_non_empty_string(component_id):
            errors.append(f"{label}.id must be a non-empty string")
        elif component_id in seen_ids:
            errors.append(f"{label}.id duplicates {component_id!r}")
        else:
            seen_ids.add(component_id)
        for key in ("name", "path", "responsibility"):
            if not _is_non_empty_string(component.get(key)):
                errors.append(f"{label}.{key} must be a non-empty string")
        if component.get("type") not in COMPONENT_TYPES:
            errors.append(f"{label}.type invalid: {component.get('type')!r}")
        for key in ("dependencies_internal", "dependencies_external", "dependents", "patterns_detected"):
            value = component.get(key)
            if value is None:
                continue
            if not _is_string_list(value):
                errors.append(f"{label}.{key} must be a list of strings")
        if "api_surface" in component:
            errors.extend(_validate_api_surface(component.get("api_surface"), f"{label}.api_surface"))

    cycles = data.get("circular_dependencies")
    if not isinstance(cycles, list):
        errors.append(f"{path.name}: circular_dependencies must be a list")
    else:
        for index, cycle in enumerate(cycles):
            label = f"{path.name}: circular_dependencies[{index}]"
            if not isinstance(cycle, dict):
                errors.append(f"{label} must be a mapping")
                continue
            if not _is_string_list(cycle.get("cycle"), min_items=2):
                errors.append(f"{label}.cycle must be a non-empty list of strings")
            if not _is_non_empty_string(cycle.get("description")):
                errors.append(f"{label}.description must be a non-empty string")

    concerns = data.get("cross_cutting_concerns")
    if not isinstance(concerns, list):
        errors.append(f"{path.name}: cross_cutting_concerns must be a list")
    else:
        for index, concern in enumerate(concerns):
            label = f"{path.name}: cross_cutting_concerns[{index}]"
            if not isinstance(concern, dict):
                errors.append(f"{label} must be a mapping")
                continue
            for key in ("concern", "implementation"):
                if not _is_non_empty_string(concern.get(key)):
                    errors.append(f"{label}.{key} must be a non-empty string")
            if not _is_string_list(concern.get("components", [])):
                errors.append(f"{label}.components must be a list of strings")

    if data.get("phase") in ("in_review", "approved") and not components:
        errors.append(f"{path.name}: in_review components artifact must contain components")
    return errors


def _validate_architecture(data: dict[str, Any], path: Path) -> list[str]:
    errors: list[str] = []

    style = data.get("architecture_style")
    if style is not None and style not in ARCHITECTURE_STYLES:
        errors.append(f"{path.name}: architecture_style invalid: {style!r}")
    confidence = data.get("style_confidence")
    if confidence is not None and confidence not in STYLE_CONFIDENCES:
        errors.append(f"{path.name}: style_confidence invalid: {confidence!r}")
    style_evidence = data.get("style_evidence")
    if style_evidence is not None and not _is_non_empty_string(style_evidence):
        errors.append(f"{path.name}: style_evidence must be a non-empty string")

    for field, required_keys in (
        ("layer_structure", ("layer", "components", "responsibility")),
        ("communication_patterns", ("pattern", "evidence", "components")),
        ("data_stores", ("name", "type", "access_pattern", "components", "evidence")),
        ("cross_cutting_concerns", ("concern", "pattern", "evidence")),
    ):
        value = data.get(field)
        if not isinstance(value, list):
            errors.append(f"{path.name}: {field} must be a list")
            continue
        for index, item in enumerate(value):
            label = f"{path.name}: {field}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be a mapping")
                continue
            for key in required_keys:
                item_value = item.get(key)
                if key == "components":
                    if not _is_string_list(item_value):
                        errors.append(f"{label}.components must be a list of strings")
                elif not _is_non_empty_string(item_value):
                    errors.append(f"{label}.{key} must be a non-empty string")

    test_patterns = data.get("test_patterns")
    if not isinstance(test_patterns, dict):
        errors.append(f"{path.name}: test_patterns must be a mapping")
    else:
        unit_framework = test_patterns.get("unit_framework")
        if unit_framework is not None and not _is_non_empty_string(unit_framework):
            errors.append(
                f"{path.name}: test_patterns.unit_framework must be a string or null"
            )
        for key in ("integration_tests", "e2e_tests", "coverage_config"):
            if not isinstance(test_patterns.get(key), bool):
                errors.append(f"{path.name}: test_patterns.{key} must be a bool")
        organization = test_patterns.get("test_organization")
        if organization is not None and not _is_non_empty_string(organization):
            errors.append(
                f"{path.name}: test_patterns.test_organization must be a string or null"
            )

    build_patterns = data.get("build_deploy_patterns")
    if not isinstance(build_patterns, dict):
        errors.append(f"{path.name}: build_deploy_patterns must be a mapping")
    else:
        for key in ("build_tool", "container", "ci_cd", "iac", "deploy_target"):
            value = build_patterns.get(key)
            if value is not None and not _is_non_empty_string(value):
                errors.append(
                    f"{path.name}: build_deploy_patterns.{key} must be a string or null"
                )

    budget = data.get("token_budget_summary")
    if not isinstance(budget, dict):
        errors.append(f"{path.name}: token_budget_summary must be a mapping")
    else:
        target_budget = budget.get("target_budget")
        if not isinstance(target_budget, int) or target_budget <= 0:
            errors.append(
                f"{path.name}: token_budget_summary.target_budget must be a positive int"
            )
        actual = budget.get("actual_estimate")
        if actual is not None and (not isinstance(actual, int) or actual < 0):
            errors.append(
                f"{path.name}: token_budget_summary.actual_estimate must be an int or null"
            )
        if not _is_string_list(budget.get("compressions_applied", [])):
            errors.append(
                f"{path.name}: token_budget_summary.compressions_applied must be a list "
                "of strings"
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

    doc_rel = data.get("document_path")
    if doc_rel:
        if not _is_non_empty_string(doc_rel):
            errors.append(f"{path.name}: document_path must be a non-empty string")
        else:
            doc_path = path.parent / doc_rel
            if not doc_path.exists():
                errors.append(f"{path.name}: document_path missing: {doc_rel}")

    for field in ("artifact_id", "created_at", "updated_at"):
        value = data.get(field)
        if value is not None and not _is_non_empty_string(value):
            errors.append(f"{path.name}: {field} must be a non-empty string")

    for ref_field in ("upstream_refs", "downstream_refs"):
        refs = data.get(ref_field)
        if not _is_string_list(refs):
            errors.append(f"{path.name}: {ref_field} must be a list of strings")

    errors.extend(_validate_progress(data.get("progress"), path))
    errors.extend(_validate_approval(data.get("approval"), path))

    if section == "structure-map":
        errors.extend(_validate_structure_map(data, path))
    elif section == "tech-stack":
        errors.extend(_validate_tech_stack(data, path))
    elif section == "components":
        errors.extend(_validate_components(data, path))
    elif section == "architecture":
        errors.extend(_validate_architecture(data, path))

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


def _validate_cross_section_consistency(all_data: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    all_component_ids: set[str] = set()

    for data in all_data.values():
        if data.get("section") == "components":
            for component in data.get("components") or []:
                component_id = component.get("id")
                if _is_non_empty_string(component_id):
                    all_component_ids.add(component_id)

    for aid, data in all_data.items():
        if data.get("section") == "components":
            local_ids = {
                component.get("id")
                for component in data.get("components") or []
                if _is_non_empty_string(component.get("id"))
            }
            for component in data.get("components") or []:
                component_id = component.get("id", "?")
                for field in ("dependencies_internal", "dependents"):
                    for ref in component.get(field) or []:
                        if ref not in local_ids:
                            errors.append(
                                f"{aid}: component {component_id} references unknown "
                                f"{field[:-1]} {ref!r}"
                            )
            for cycle in data.get("circular_dependencies") or []:
                for ref in cycle.get("cycle") or []:
                    if ref not in local_ids:
                        errors.append(
                            f"{aid}: circular dependency references unknown component "
                            f"{ref!r}"
                        )

        if data.get("section") == "architecture" and all_component_ids:
            for field in ("layer_structure", "communication_patterns", "data_stores"):
                for item in data.get(field) or []:
                    for ref in item.get("components") or []:
                        if ref not in all_component_ids:
                            errors.append(
                                f"{aid}: {field} references unknown component {ref!r}"
                            )

    return errors


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
    meta_data["updated_at"] = meta_data["created_at"]

    errors = _validate_meta(meta_data, meta_path)
    if errors:
        for error in errors:
            sys.stderr.write(f"error: {error}\n")
        return 2

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
        _add_unique_ref(refs, args.upstream)
    if args.downstream:
        refs = data.setdefault("downstream_refs", [])
        _add_unique_ref(refs, args.downstream)
    save_meta(meta_path, data)

    # Maintain bidirectional integrity for artifact-to-artifact links only.
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


def cmd_link_defaults(args: argparse.Namespace) -> int:
    meta_path = find_meta_by_id(args.artifact_id)
    data = load_meta(meta_path)
    section = data.get("section")
    defaults = DEFAULT_DOWNSTREAM_BY_SECTION.get(section, ())
    refs = data.setdefault("downstream_refs", [])
    for downstream in defaults:
        _add_unique_ref(refs, downstream)
    save_meta(meta_path, data)
    print(
        json.dumps(
            {
                "artifact_id": args.artifact_id,
                "section": section,
                "downstream_refs": refs,
            },
            indent=2,
        )
    )
    return 0


def cmd_set_section(args: argparse.Namespace) -> int:
    meta_path = find_meta_by_id(args.artifact_id)
    data = load_meta(meta_path)
    section = data.get("section")

    payload = _load_structured_value(
        from_path=args.from_path,
        raw_value=args.value,
    )
    update = _extract_section_payload(section, payload)
    for field, value in update.items():
        _set_nested_value(data, field, value)

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
                "section": section,
                "updated_fields": sorted(update.keys()),
                "meta_path": str(meta_path),
            },
            indent=2,
        )
    )
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


def cmd_validate(args: argparse.Namespace) -> int:
    files = all_meta_files()
    if not files:
        print(f"artifacts directory: {artifacts_dir(create=False)}")
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
    errors.extend(_validate_cross_section_consistency(loaded))

    print(f"artifacts directory: {artifacts_dir(create=False)}")
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
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="artifact.py")
    p.add_argument(
        "--artifacts-dir",
        default=None,
        help=(
            "Override the artifacts directory. Defaults to HARNESS_ARTIFACTS_DIR "
            "or SKILL_DIR/out/<HARNESS_RUN_ID|SESSION_ID|standalone>."
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="create a new artifact from templates")
    sp.add_argument("--section", required=True, choices=SECTIONS)
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("set-section", help="replace the structured payload for a section")
    sp.add_argument("artifact_id")
    sp.add_argument("--from", dest="from_path", default=None)
    sp.add_argument("--value", default=None)
    sp.set_defaults(func=cmd_set_section)

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

    sp = sub.add_parser(
        "link-defaults",
        help="apply the documented downstream links for this section",
    )
    sp.add_argument("artifact_id")
    sp.set_defaults(func=cmd_link_defaults)

    sp = sub.add_parser("show", help="pretty-print an artifact's metadata")
    sp.add_argument("artifact_id")
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("list", help="list all artifacts in the project")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("validate", help="validate schema and traceability")
    sp.add_argument("artifact_id", nargs="?", default=None)
    sp.set_defaults(func=cmd_validate)

    return p


def main(argv: list[str] | None = None) -> int:
    global CLI_ARTIFACTS_DIR

    parser = build_parser()
    args = parser.parse_args(argv)
    CLI_ARTIFACTS_DIR = (
        Path(args.artifacts_dir).expanduser()
        if args.artifacts_dir
        else None
    )
    try:
        return args.func(args)
    except FileNotFoundError as e:
        sys.stderr.write(f"error: {e}\n")
        return 2
    except ValueError as e:
        sys.stderr.write(f"error: {e}\n")
        return 2
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"error: {e}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
