#!/usr/bin/env python3
"""artifact — manage skill-agent output pairs (meta.json + body.md).

Every agent output lives under:
    runs/<run_id>/<skill>/<agent>[-NN]/{meta.json, body.md}

The CLI is the only supported way to mutate meta.json; agents edit body.md
directly via their normal file tools after calling `artifact path --body`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

SCHEMA_VERSION = 1

PROGRESS_VALUES = {
    "draft",
    "in_progress",
    "review",
    "approved",
    "rejected",
    "blocked",
}
VERDICT_VALUES = {"APPROVED", "CONDITIONAL", "REJECTED"}

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNS_ROOT = REPO_ROOT / "runs"
TEMPLATES_ROOT = REPO_ROOT / "templates"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or "run"


def new_run_id(title: str | None) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    slug = slugify(title) if title else "run"
    return f"{stamp}-{slug}"


def run_dir(run_id: str) -> Path:
    return RUNS_ROOT / run_id


def find_artifact_dir(run_id: str, artifact_id: str) -> Path:
    """Locate the directory holding meta.json for artifact_id inside run_id."""
    root = run_dir(run_id)
    if not root.is_dir():
        die(f"run not found: {run_id}")
    for meta_path in root.glob("*/*/meta.json"):
        try:
            with meta_path.open() as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("artifact_id") == artifact_id:
            return meta_path.parent
    die(f"artifact not found: {artifact_id} in run {run_id}")


def load_meta(meta_dir: Path) -> dict:
    with (meta_dir / "meta.json").open() as fh:
        return json.load(fh)


def save_meta(meta_dir: Path, meta: dict) -> None:
    meta["updated_at"] = now_iso()
    with (meta_dir / "meta.json").open("w") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def die(msg: str, code: int = 1) -> None:
    print(f"artifact: {msg}", file=sys.stderr)
    sys.exit(code)


# ----------------------------------------------------------------------------
# init
# ----------------------------------------------------------------------------


def next_artifact_slot(skill_dir: Path, agent: str) -> tuple[str, Path]:
    """Return (artifact_id, agent_dir) for the next available agent slot."""
    n = 1
    while True:
        suffix = "" if n == 1 else f"-{n}"
        candidate = skill_dir / f"{agent}{suffix}"
        if not candidate.exists():
            skill = skill_dir.name
            artifact_id = f"{skill}-{agent}-{n:02d}"
            return artifact_id, candidate
        n += 1


def render_template(template_path: Path, ctx: dict) -> str:
    text = template_path.read_text()
    for key, value in ctx.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def cmd_init(args: argparse.Namespace) -> None:
    skill = args.skill
    agent = args.agent
    title = args.title or f"{skill}/{agent}"
    run_id = args.run_id or new_run_id(title)
    template_key = args.template or f"{skill}/{agent}"
    template_path = TEMPLATES_ROOT / f"{template_key}.md"
    if not template_path.is_file():
        die(f"template not found: {template_path.relative_to(REPO_ROOT)}")

    skill_dir = run_dir(run_id) / skill
    skill_dir.mkdir(parents=True, exist_ok=True)
    artifact_id, agent_dir = next_artifact_slot(skill_dir, agent)
    agent_dir.mkdir()

    ctx = {
        "title": title,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "skill": skill,
        "agent": agent,
    }
    body_text = render_template(template_path, ctx)
    (agent_dir / "body.md").write_text(body_text)

    now = now_iso()
    meta = {
        "schema_version": SCHEMA_VERSION,
        "artifact_id": artifact_id,
        "run_id": run_id,
        "skill": skill,
        "agent": agent,
        "title": title,
        "template": template_key,
        "body_path": "body.md",
        "created_at": now,
        "updated_at": now,
        "progress": "draft",
        "approval": {
            "verdict": None,
            "approver": None,
            "approved_at": None,
            "notes": None,
        },
        "refs": {
            "re_refs": [],
            "upstream": [],
            "downstream": [],
        },
        "data": {},
    }
    with (agent_dir / "meta.json").open("w") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"run_id={run_id}")
    print(f"artifact_id={artifact_id}")
    print(f"dir={agent_dir}")


# ----------------------------------------------------------------------------
# path
# ----------------------------------------------------------------------------


def cmd_path(args: argparse.Namespace) -> None:
    meta_dir = find_artifact_dir(args.run_id, args.artifact_id)
    if args.body:
        print(meta_dir / "body.md")
    elif args.meta:
        print(meta_dir / "meta.json")
    else:
        print(meta_dir)


# ----------------------------------------------------------------------------
# get
# ----------------------------------------------------------------------------


def dotted_get(obj, path: str):
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            die(f"field not found: {path}")
    return cur


def cmd_get(args: argparse.Namespace) -> None:
    meta_dir = find_artifact_dir(args.run_id, args.artifact_id)
    meta = load_meta(meta_dir)
    if args.field:
        value = dotted_get(meta, args.field)
        if isinstance(value, (dict, list)):
            print(json.dumps(value, indent=2, ensure_ascii=False))
        elif value is None:
            print("")
        else:
            print(value)
    else:
        print(json.dumps(meta, indent=2, ensure_ascii=False))


# ----------------------------------------------------------------------------
# set
# ----------------------------------------------------------------------------


def cmd_set(args: argparse.Namespace) -> None:
    meta_dir = find_artifact_dir(args.run_id, args.artifact_id)
    meta = load_meta(meta_dir)

    if args.title is not None:
        meta["title"] = args.title

    if args.progress is not None:
        if args.progress not in PROGRESS_VALUES:
            die(f"invalid progress: {args.progress} (expected one of {sorted(PROGRESS_VALUES)})")
        meta["progress"] = args.progress

    if args.verdict is not None:
        if args.verdict not in VERDICT_VALUES:
            die(f"invalid verdict: {args.verdict} (expected one of {sorted(VERDICT_VALUES)})")
        meta["approval"]["verdict"] = args.verdict
        meta["approval"]["approved_at"] = now_iso()

    if args.approver is not None:
        meta["approval"]["approver"] = args.approver

    if args.notes is not None:
        meta["approval"]["notes"] = args.notes

    for ref in args.ref_re or []:
        if ref not in meta["refs"]["re_refs"]:
            meta["refs"]["re_refs"].append(ref)

    for ref in args.ref_upstream or []:
        if ref not in meta["refs"]["upstream"]:
            meta["refs"]["upstream"].append(ref)

    for ref in args.ref_downstream or []:
        if ref not in meta["refs"]["downstream"]:
            meta["refs"]["downstream"].append(ref)

    if args.data_file:
        patch_path = Path(args.data_file)
        if not patch_path.is_file():
            die(f"data file not found: {patch_path}")
        with patch_path.open() as fh:
            patch = json.load(fh)
        if not isinstance(patch, dict):
            die("data file must contain a JSON object at the top level")
        meta["data"].update(patch)

    save_meta(meta_dir, meta)
    print(f"updated {meta['artifact_id']}")


# ----------------------------------------------------------------------------
# list
# ----------------------------------------------------------------------------


def iter_meta(run_id: str | None):
    if run_id:
        roots = [run_dir(run_id)]
    else:
        roots = sorted(p for p in RUNS_ROOT.glob("*") if p.is_dir())
    for root in roots:
        if not root.is_dir():
            continue
        for meta_path in sorted(root.glob("*/*/meta.json")):
            try:
                with meta_path.open() as fh:
                    yield json.load(fh)
            except (OSError, json.JSONDecodeError):
                continue


def cmd_list(args: argparse.Namespace) -> None:
    rows = []
    for meta in iter_meta(args.run_id):
        if args.skill and meta.get("skill") != args.skill:
            continue
        if args.agent and meta.get("agent") != args.agent:
            continue
        if args.progress and meta.get("progress") != args.progress:
            continue
        if args.verdict and meta.get("approval", {}).get("verdict") != args.verdict:
            continue
        rows.append(meta)

    if not rows:
        return

    headers = ("ARTIFACT_ID", "SKILL", "AGENT", "PROGRESS", "VERDICT", "TITLE")
    widths = [len(h) for h in headers]
    data_rows = []
    for meta in rows:
        row = (
            meta.get("artifact_id", ""),
            meta.get("skill", ""),
            meta.get("agent", ""),
            meta.get("progress", ""),
            (meta.get("approval") or {}).get("verdict") or "-",
            meta.get("title", ""),
        )
        data_rows.append(row)
        widths = [max(w, len(str(c))) for w, c in zip(widths, row)]

    fmt = "  ".join("{:<" + str(w) + "}" for w in widths)
    print(fmt.format(*headers))
    for row in data_rows:
        print(fmt.format(*row))


# ----------------------------------------------------------------------------
# validate
# ----------------------------------------------------------------------------


REQUIRED_FIELDS = (
    "schema_version",
    "artifact_id",
    "run_id",
    "skill",
    "agent",
    "title",
    "template",
    "body_path",
    "created_at",
    "updated_at",
    "progress",
    "approval",
    "refs",
    "data",
)


def cmd_validate(args: argparse.Namespace) -> None:
    meta_dir = find_artifact_dir(args.run_id, args.artifact_id)
    meta = load_meta(meta_dir)
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in meta:
            errors.append(f"missing field: {field}")

    if meta.get("progress") not in PROGRESS_VALUES:
        errors.append(f"invalid progress: {meta.get('progress')}")

    verdict = (meta.get("approval") or {}).get("verdict")
    if verdict is not None and verdict not in VERDICT_VALUES:
        errors.append(f"invalid approval.verdict: {verdict}")

    body_path = meta_dir / meta.get("body_path", "body.md")
    if not body_path.is_file():
        errors.append(f"body file missing: {body_path}")

    template_key = meta.get("template", "")
    template_path = TEMPLATES_ROOT / f"{template_key}.md"
    if not template_path.is_file():
        errors.append(f"template missing: {template_path.relative_to(REPO_ROOT)}")

    if errors:
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        die(f"{meta.get('artifact_id')} invalid ({len(errors)} error(s))", code=2)

    print(f"ok {meta['artifact_id']}")


# ----------------------------------------------------------------------------
# argparse wiring
# ----------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="artifact", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="scaffold a new artifact")
    p_init.add_argument("--skill", required=True)
    p_init.add_argument("--agent", required=True)
    p_init.add_argument("--run-id")
    p_init.add_argument("--title")
    p_init.add_argument("--template")
    p_init.set_defaults(func=cmd_init)

    p_path = sub.add_parser("path", help="print artifact paths")
    p_path.add_argument("artifact_id")
    p_path.add_argument("--run-id", required=True)
    group = p_path.add_mutually_exclusive_group()
    group.add_argument("--body", action="store_true")
    group.add_argument("--meta", action="store_true")
    p_path.set_defaults(func=cmd_path)

    p_get = sub.add_parser("get", help="read meta.json (whole or a field)")
    p_get.add_argument("artifact_id")
    p_get.add_argument("--run-id", required=True)
    p_get.add_argument("--field", help="dotted path, e.g. approval.verdict")
    p_get.set_defaults(func=cmd_get)

    p_set = sub.add_parser("set", help="mutate meta.json fields")
    p_set.add_argument("artifact_id")
    p_set.add_argument("--run-id", required=True)
    p_set.add_argument("--title")
    p_set.add_argument("--progress", choices=sorted(PROGRESS_VALUES))
    p_set.add_argument("--verdict", choices=sorted(VERDICT_VALUES))
    p_set.add_argument("--approver")
    p_set.add_argument("--notes")
    p_set.add_argument("--ref-re", action="append", metavar="ID")
    p_set.add_argument("--ref-upstream", action="append", metavar="ID")
    p_set.add_argument("--ref-downstream", action="append", metavar="ID")
    p_set.add_argument("--data-file", metavar="PATH",
                       help="JSON object shallow-merged into data")
    p_set.set_defaults(func=cmd_set)

    p_list = sub.add_parser("list", help="list artifacts across runs")
    p_list.add_argument("--run-id")
    p_list.add_argument("--skill")
    p_list.add_argument("--agent")
    p_list.add_argument("--progress", choices=sorted(PROGRESS_VALUES))
    p_list.add_argument("--verdict", choices=sorted(VERDICT_VALUES))
    p_list.set_defaults(func=cmd_list)

    p_validate = sub.add_parser("validate", help="check an artifact's meta.json")
    p_validate.add_argument("artifact_id")
    p_validate.add_argument("--run-id", required=True)
    p_validate.set_defaults(func=cmd_validate)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
