#!/usr/bin/env python3
"""Dedicated approval workflow script for the Sec skill.

Provides subcommands for requesting, approving, rejecting, and accepting risk
on security artifacts. All actions are recorded to the approval.history audit
trail with session_id tracking.
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any

# Re-use IO helpers from the sec artifact module
try:
    from artifact import (
        APPROVAL_STATES,
        APPROVAL_TRANSITIONS,
        find_meta_by_id,
        load_meta,
        now_iso,
        save_meta,
    )
except ImportError:
    # Support running from a different working directory
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    from artifact import (
        APPROVAL_STATES,
        APPROVAL_TRANSITIONS,
        find_meta_by_id,
        load_meta,
        now_iso,
        save_meta,
    )


def _session_id() -> str | None:
    """Return the current CLAUDE_SESSION_ID from the environment, or None."""
    return os.environ.get("CLAUDE_SESSION_ID")


def _append_history(
    approval: dict[str, Any],
    *,
    state: str,
    approver: str | None,
    rationale: str | None,
) -> None:
    """Append an entry to approval.history with timestamp and session_id."""
    history = approval.setdefault("history", [])
    history.append(
        {
            "state": state,
            "approver": approver,
            "rationale": rationale,
            "at": now_iso(),
            "session_id": _session_id(),
        }
    )


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_request(args: argparse.Namespace) -> int:
    """Set approval state to pending and phase to in_review."""
    meta_path = find_meta_by_id(args.id)
    data = load_meta(meta_path)
    approval = data.setdefault("approval", {"state": "pending", "history": []})
    current = approval.get("state", "pending")

    # Allow transition to pending from any state that permits it, or if already pending
    if current != "pending" and "pending" not in APPROVAL_TRANSITIONS.get(current, set()):
        sys.stderr.write(
            f"error: cannot request review from state {current!r}\n"
        )
        return 2

    approval["state"] = "pending"
    data["phase"] = "in_review"
    _append_history(approval, state="pending", approver=None, rationale="Review requested")
    save_meta(meta_path, data)
    print(f"{args.id}: approval -> pending, phase -> in_review")
    return 0


def cmd_approve(args: argparse.Namespace) -> int:
    """Approve the artifact with required rationale."""
    meta_path = find_meta_by_id(args.id)
    data = load_meta(meta_path)
    approval = data.setdefault("approval", {"state": "pending", "history": []})
    current = approval.get("state", "pending")

    if "approved" not in APPROVAL_TRANSITIONS.get(current, set()) and current != "approved":
        sys.stderr.write(
            f"error: cannot approve from state {current!r}\n"
        )
        return 2

    if data.get("phase") != "in_review":
        sys.stderr.write(
            "error: artifact must be in_review before it can be approved\n"
        )
        return 2

    ts = now_iso()
    approval["state"] = "approved"
    approval["approver"] = args.approver
    approval["approved_at"] = ts
    approval["notes"] = args.rationale
    data["phase"] = "approved"
    _append_history(approval, state="approved", approver=args.approver, rationale=args.rationale)
    save_meta(meta_path, data)
    print(f"{args.id}: approved by {args.approver}")
    return 0


def cmd_reject(args: argparse.Namespace) -> int:
    """Reject the artifact with required rationale."""
    meta_path = find_meta_by_id(args.id)
    data = load_meta(meta_path)
    approval = data.setdefault("approval", {"state": "pending", "history": []})
    current = approval.get("state", "pending")

    if "rejected" not in APPROVAL_TRANSITIONS.get(current, set()) and current != "rejected":
        sys.stderr.write(
            f"error: cannot reject from state {current!r}\n"
        )
        return 2

    approval["state"] = "rejected"
    approval["approver"] = args.approver
    approval["notes"] = args.rationale
    data["phase"] = "revising"
    _append_history(approval, state="rejected", approver=args.approver, rationale=args.rationale)
    save_meta(meta_path, data)
    print(f"{args.id}: rejected by {args.approver}, phase -> revising")
    return 0


def cmd_accept_risk(args: argparse.Namespace) -> int:
    """Record risk acceptance as an audit trail entry.

    This is the critical audit case — used when a user accepts a security risk.
    The approval state is set to conditionally_approved and the rationale
    documents the accepted risk.
    """
    meta_path = find_meta_by_id(args.id)
    data = load_meta(meta_path)
    approval = data.setdefault("approval", {"state": "pending", "history": []})
    current = approval.get("state", "pending")

    if (
        "conditionally_approved" not in APPROVAL_TRANSITIONS.get(current, set())
        and current != "conditionally_approved"
    ):
        sys.stderr.write(
            f"error: cannot accept-risk from state {current!r}\n"
        )
        return 2

    approval["state"] = "conditionally_approved"
    approval["approver"] = args.approver
    approval["notes"] = args.rationale
    approval["risk_accepted"] = True
    approval["risk_accepted_at"] = now_iso()
    _append_history(
        approval,
        state="conditionally_approved",
        approver=args.approver,
        rationale=f"[RISK ACCEPTED] {args.rationale}",
    )
    save_meta(meta_path, data)
    print(f"{args.id}: risk accepted by {args.approver} (conditionally_approved)")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="approval.py",
        description="Sec skill approval workflow manager",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("request", help="request review (set pending / in_review)")
    sp.add_argument("id", help="artifact id (e.g. SEC-TM-001)")
    sp.set_defaults(func=cmd_request)

    sp = sub.add_parser("approve", help="approve with rationale")
    sp.add_argument("id", help="artifact id")
    sp.add_argument("--approver", required=True, help="name of the approver")
    sp.add_argument("--rationale", required=True, help="approval rationale")
    sp.set_defaults(func=cmd_approve)

    sp = sub.add_parser("reject", help="reject with rationale")
    sp.add_argument("id", help="artifact id")
    sp.add_argument("--approver", required=True, help="name of the rejector")
    sp.add_argument("--rationale", required=True, help="rejection rationale")
    sp.set_defaults(func=cmd_reject)

    sp = sub.add_parser("accept-risk", help="accept a security risk (audit trail)")
    sp.add_argument("id", help="artifact id")
    sp.add_argument("--approver", required=True, help="name of person accepting the risk")
    sp.add_argument("--rationale", required=True, help="risk acceptance rationale")
    sp.set_defaults(func=cmd_accept_risk)

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
