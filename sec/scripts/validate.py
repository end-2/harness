#!/usr/bin/env python3
"""Standalone validation script for the Sec skill.

Validates schema, traceability, and cross-references for sec artifacts.
"""
from __future__ import annotations

import argparse
import sys
from typing import Any

try:
    from artifact import (
        APPROVAL_STATES,
        PHASES,
        REQUIRED_META_FIELDS,
        SECTIONS,
        all_meta_files,
        artifacts_dir,
        load_meta,
    )
except ImportError:
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    from artifact import (
        APPROVAL_STATES,
        PHASES,
        REQUIRED_META_FIELDS,
        SECTIONS,
        all_meta_files,
        artifacts_dir,
        load_meta,
    )

# Valid cross-skill reference prefixes
CROSS_SKILL_PREFIXES = ("ARCH-", "IMPL-", "RE-", "SEC-")


def _validate_schema(data: dict[str, Any], filename: str) -> list[str]:
    """Check required fields, valid phase, valid section, valid approval state."""
    errors: list[str] = []
    for field in REQUIRED_META_FIELDS:
        if field not in data:
            errors.append(f"{filename}: missing required field {field!r}")

    phase = data.get("phase")
    if phase not in PHASES:
        errors.append(f"{filename}: unknown phase {phase!r}")

    section = data.get("section")
    if section not in SECTIONS:
        errors.append(f"{filename}: unknown section {section!r}")

    approval = data.get("approval") or {}
    state = approval.get("state")
    if state and state not in APPROVAL_STATES:
        errors.append(f"{filename}: unknown approval state {state!r}")

    return errors


def _validate_document_path(data: dict[str, Any], meta_path: Any, filename: str) -> list[str]:
    """Check that document_path exists on disk."""
    errors: list[str] = []
    doc_rel = data.get("document_path")
    if doc_rel:
        doc_path = meta_path.parent / doc_rel
        if not doc_path.exists():
            errors.append(f"{filename}: document_path missing: {doc_rel}")
    else:
        errors.append(f"{filename}: document_path is empty or unset")
    return errors


def _validate_traceability(all_data: dict[str, dict[str, Any]]) -> list[str]:
    """Check upstream/downstream reciprocity and cross_refs validity."""
    errors: list[str] = []
    ids = set(all_data.keys())

    for aid, data in all_data.items():
        # upstream/downstream reciprocity
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

        # cross_refs validation (threat_refs, vuln_refs)
        cross = data.get("cross_refs") or {}
        for ref_kind in ("threat_refs", "vuln_refs"):
            for ref in cross.get(ref_kind) or []:
                # If it is a local sec ref, check it exists
                if ref.startswith("SEC-") and ref not in ids:
                    errors.append(
                        f"{aid}: cross_ref {ref!r} in {ref_kind} not found among sec artifacts"
                    )
                # Validate cross-skill ref format
                if not any(ref.startswith(p) for p in CROSS_SKILL_PREFIXES):
                    errors.append(
                        f"{aid}: cross_ref {ref!r} in {ref_kind} has invalid prefix "
                        f"(expected one of {CROSS_SKILL_PREFIXES})"
                    )

    return errors


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate schema + traceability for one or all sec artifacts."""
    files = all_meta_files()
    if not files:
        print("(no artifacts yet -- nothing to validate)")
        return 0

    loaded: dict[str, dict[str, Any]] = {}
    errors: list[str] = []

    for p in files:
        try:
            data = load_meta(p)
        except Exception as e:
            errors.append(f"{p.name}: unreadable ({e})")
            continue

        aid = data.get("artifact_id")
        if args.id and aid != args.id:
            continue

        errors.extend(_validate_schema(data, p.name))
        errors.extend(_validate_document_path(data, p, p.name))

        if isinstance(aid, str):
            loaded[aid] = data

    if args.id and not loaded:
        sys.stderr.write(f"error: artifact {args.id!r} not found\n")
        return 2

    errors.extend(_validate_traceability(loaded))

    print(f"artifacts directory: {artifacts_dir()}")
    print(f"artifacts validated: {len(loaded)}")
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

    print("\nOK - all validations passed")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="validate.py",
        description="Sec skill artifact validation",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("validate", help="validate schema + traceability")
    sp.add_argument(
        "id",
        nargs="?",
        default=None,
        help="artifact id to validate (omit for all)",
    )
    sp.set_defaults(func=cmd_validate)

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
