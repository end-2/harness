#!/usr/bin/env python3
"""Summary report script for the Sec skill.

Reads all sec meta.yaml files and prints a concise status report suitable
for injection into SKILL.md via the backtick command.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from typing import Any

try:
    from artifact import (
        SECTIONS,
        all_meta_files,
        artifacts_dir,
        load_meta,
    )
except ImportError:
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    from artifact import (
        SECTIONS,
        all_meta_files,
        artifacts_dir,
        load_meta,
    )


def _check_broken_refs(all_data: dict[str, dict[str, Any]]) -> list[str]:
    """Return list of broken reference descriptions."""
    broken: list[str] = []
    ids = set(all_data.keys())

    for aid, data in all_data.items():
        for ref in data.get("downstream_refs") or []:
            if ref.startswith("SEC-") and ref not in ids:
                broken.append(f"{aid} -> downstream {ref} (not found)")
            elif ref in ids:
                other = all_data[ref]
                if aid not in (other.get("upstream_refs") or []):
                    broken.append(f"{aid} -> downstream {ref} (no reciprocal upstream)")

        for ref in data.get("upstream_refs") or []:
            if ref.startswith("SEC-") and ref not in ids:
                broken.append(f"{aid} -> upstream {ref} (not found)")
            elif ref in ids:
                other = all_data[ref]
                if aid not in (other.get("downstream_refs") or []):
                    broken.append(f"{aid} -> upstream {ref} (no reciprocal downstream)")

        cross = data.get("cross_refs") or {}
        for ref_kind in ("threat_refs", "vuln_refs"):
            for ref in cross.get(ref_kind) or []:
                if ref.startswith("SEC-") and ref not in ids:
                    broken.append(f"{aid} -> {ref_kind}/{ref} (not found)")

    return broken


def _iter_critical_items(data: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (label, severity) pairs for nested critical findings."""
    section = data.get("section")
    critical: list[tuple[str, str]] = []

    if section == "threat-model":
        block = data.get("threat_model") or {}
        for threat in block.get("threats") or []:
            if str(threat.get("risk_level", "")).lower() == "critical":
                critical.append((threat.get("id", "?"), "critical"))
    elif section == "vulnerability-report":
        for vuln in data.get("vulnerability_report") or []:
            if str(vuln.get("severity", "")).lower() == "critical":
                critical.append((vuln.get("id", "?"), "critical"))
    elif section == "security-advisory":
        for advisory in data.get("security_advisory") or []:
            if str(advisory.get("priority", "")).lower() == "critical":
                critical.append((advisory.get("id", "?"), "critical"))
    elif section == "compliance-report":
        block = data.get("compliance_report") or {}
        for finding in block.get("findings") or []:
            status = str(finding.get("status", "")).lower()
            severity = str(finding.get("severity", "")).lower()
            if severity == "critical" or (
                severity == "" and status == "non_compliant"
            ):
                critical.append((finding.get("requirement_id", "?"), severity or status))

    return critical


def cmd_summary(_args: argparse.Namespace) -> int:
    """Print a concise status report of all sec artifacts."""
    files = all_meta_files()
    if not files:
        print("## Sec Skill Status")
        print()
        print("No artifacts found.")
        return 0

    all_data: dict[str, dict[str, Any]] = {}
    phase_counts: Counter[str] = Counter()
    approval_counts: Counter[str] = Counter()
    critical_unapproved: list[dict[str, Any]] = []
    compliance_artifacts: list[dict[str, Any]] = []

    for p in files:
        try:
            data = load_meta(p)
        except Exception:
            continue
        aid = data.get("artifact_id")
        if not isinstance(aid, str):
            continue
        all_data[aid] = data

        phase = data.get("phase", "unknown")
        approval = (data.get("approval") or {}).get("state", "unknown")
        phase_counts[phase] += 1
        approval_counts[approval] += 1

        if approval != "approved" and _iter_critical_items(data):
            critical_unapproved.append(data)

        # Collect compliance report artifacts
        if aid.startswith("SEC-CR-"):
            compliance_artifacts.append(data)

    # Header
    print("## Sec Skill Status")
    print()

    # Artifact listing
    print(f"### Artifacts ({len(all_data)})")
    print()
    if all_data:
        id_width = max(len(aid) for aid in all_data)
        sec_width = max(len(str(d.get("section", "?"))) for d in all_data.values())
        for aid, data in sorted(all_data.items()):
            phase = data.get("phase", "?")
            state = (data.get("approval") or {}).get("state", "?")
            section = data.get("section", "?")
            print(f"  {aid:<{id_width}}  {section:<{sec_width}}  phase={phase:<10}  approval={state}")
    print()

    # Phase totals
    print("### By Phase")
    print()
    for phase, count in sorted(phase_counts.items()):
        print(f"  {phase}: {count}")
    print()

    # Approval state totals
    print("### By Approval State")
    print()
    for state, count in sorted(approval_counts.items()):
        print(f"  {state}: {count}")
    print()

    # Unapproved critical findings
    if critical_unapproved:
        print("### Unapproved Critical Findings")
        print()
        for data in critical_unapproved:
            aid = data.get("artifact_id", "?")
            section = data.get("section", "?")
            critical_labels = ", ".join(
                f"{item_id}:{sev}" for item_id, sev in _iter_critical_items(data)
            )
            state = (data.get("approval") or {}).get("state", "?")
            print(f"  {aid}  section={section}  items={critical_labels}  approval={state}")
        print()

    # Compliance gap summary
    if compliance_artifacts:
        print("### Compliance Report Summary")
        print()
        for data in compliance_artifacts:
            aid = data.get("artifact_id", "?")
            phase = data.get("phase", "?")
            state = (data.get("approval") or {}).get("state", "?")
            block = data.get("compliance_report") or {}
            gaps = (
                block.get("gap_summary")
                or data.get("compliance_gaps")
                or data.get("gaps")
                or []
            )
            if isinstance(gaps, list):
                gap_info = f"  gaps={len(gaps)}" if gaps else ""
            else:
                gap_info = "  gaps=1" if str(gaps).strip() else ""
            print(f"  {aid}  phase={phase}  approval={state}{gap_info}")
        print()

    # Traceability integrity
    broken = _check_broken_refs(all_data)
    print("### Traceability Integrity")
    print()
    if broken:
        print(f"  Broken references ({len(broken)}):")
        for b in broken:
            print(f"    - {b}")
    else:
        print("  All references OK")
    print()

    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="report.py",
        description="Sec skill summary reporting",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("summary", help="print concise status report")
    sp.set_defaults(func=cmd_summary)

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
