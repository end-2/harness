from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT_DIR / "impl" / "scripts" / "artifact.py"


class ImplArtifactScriptTests(unittest.TestCase):
    def run_cmd(
        self,
        *args: str,
        artifacts_dir: Path,
        expected_code: int,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HARNESS_ARTIFACTS_DIR"] = str(artifacts_dir)
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            cwd=ROOT_DIR,
            env=env,
            text=True,
            capture_output=True,
        )
        self.assertEqual(
            proc.returncode,
            expected_code,
            msg=f"stdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}",
        )
        return proc

    def test_validate_rejects_missing_created_at_and_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            self.run_cmd(
                "init",
                "--section",
                "implementation-map",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )

            meta_path = artifacts_dir / "IMPL-MAP-001.meta.yaml"
            lines = meta_path.read_text(encoding="utf-8").splitlines()
            mutated = [
                line
                for line in lines
                if not line.startswith("created_at: ")
                and line.strip() != "implementation_map: []"
            ]
            meta_path.write_text("\n".join(mutated) + "\n", encoding="utf-8")

            proc = self.run_cmd(
                "validate",
                artifacts_dir=artifacts_dir,
                expected_code=1,
            )
            self.assertIn("missing field 'created_at'", proc.stdout)
            self.assertIn("implementation_map must be a list", proc.stdout)

    def test_validate_rejects_incoherent_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            self.run_cmd(
                "init",
                "--section",
                "implementation-map",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )

            meta_path = artifacts_dir / "IMPL-MAP-001.meta.yaml"
            text = meta_path.read_text(encoding="utf-8")
            text = text.replace("section_total: 0", "section_total: -1", 1)
            text = text.replace("percent: 0", "percent: 999", 1)
            meta_path.write_text(text, encoding="utf-8")

            proc = self.run_cmd(
                "validate",
                artifacts_dir=artifacts_dir,
                expected_code=1,
            )
            self.assertIn("progress.section_total must be >= 0", proc.stdout)
            self.assertIn("progress.percent must be 0, got 999", proc.stdout)

    def test_validate_rejects_unknown_artifact_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            self.run_cmd(
                "init",
                "--section",
                "implementation-map",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )

            proc = self.run_cmd(
                "validate",
                "IMPL-MAP-999",
                artifacts_dir=artifacts_dir,
                expected_code=2,
            )
            self.assertIn("No artifact found with id 'IMPL-MAP-999'", proc.stderr)

    def test_report_validate_rejects_incomplete_review_item_and_disallowed_op(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            proc = self.run_cmd(
                "report",
                "path",
                "--kind",
                "review",
                "--stage",
                "review",
                "--target",
                "IMPL-MAP-001",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            payload = json.loads(proc.stdout)
            report_path = Path(payload["path"])
            report_path.write_text(
                textwrap.dedent(
                    f"""\
                    ---
                    report_id: {payload["report_id"]}
                    kind: review
                    skill: impl
                    stage: review
                    created_at: 2026-04-12T00:00:00Z
                    target_refs:
                      - IMPL-MAP-001
                    verdict: at_risk
                    summary: review found issues
                    proposed_meta_ops:
                      - cmd: set-phase
                        artifact_id: IMPL-MAP-001
                        phase: approved
                    items:
                      - id: 1
                        classification: clean_code
                        severity: med
                    ---

                    # review report (impl/review)

                    ## Summary
                    review found issues

                    ## Auto-fixable issues (route to refactor)
                    missing details
                    """
                ),
                encoding="utf-8",
            )

            proc = self.run_cmd(
                "report",
                "validate",
                str(report_path),
                artifacts_dir=artifacts_dir,
                expected_code=1,
            )
            self.assertIn("items[1] missing location", proc.stdout)
            self.assertIn("items[1] missing message", proc.stdout)
            self.assertIn("items[1] missing suggested_fix", proc.stdout)
            self.assertIn("command 'set-phase' is not allowed", proc.stdout)


if __name__ == "__main__":
    unittest.main()
