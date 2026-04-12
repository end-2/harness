#!/usr/bin/env python3
"""Standalone validation wrapper for the Sec skill.

Supports both forms:
  - validate.py
  - validate.py SEC-TM-001
  - validate.py validate
  - validate.py validate SEC-TM-001
"""
from __future__ import annotations

import argparse
import sys

try:
    from artifact import cmd_validate
except ImportError:
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    from artifact import cmd_validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate.py",
        description="Sec skill artifact validation",
    )
    parser.add_argument(
        "id",
        nargs="?",
        default=None,
        help="artifact id to validate (omit for all)",
    )
    return parser


def _normalize_argv(argv: list[str]) -> list[str]:
    if argv and argv[0] == "validate":
        return argv[1:]
    return argv


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(_normalize_argv(raw))
    try:
        return cmd_validate(argparse.Namespace(artifact_id=args.id))
    except FileNotFoundError as e:
        sys.stderr.write(f"error: {e}\n")
        return 2
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"error: {e}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
