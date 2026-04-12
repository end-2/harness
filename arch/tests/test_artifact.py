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
SCRIPT_PATH = ROOT_DIR / "arch" / "scripts" / "artifact.py"


class ArchArtifactScriptTests(unittest.TestCase):
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

    def test_validate_rejects_empty_in_review_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            self.run_cmd(
                "init",
                "--section",
                "decisions",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            self.run_cmd(
                "set-phase",
                "ARCH-DEC-001",
                "in_review",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            proc = self.run_cmd(
                "validate",
                artifacts_dir=artifacts_dir,
                expected_code=1,
            )
            self.assertIn(
                "in_review decisions artifacts must contain at least one decision",
                proc.stdout,
            )

    def test_approve_rejects_review_unready_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            self.run_cmd(
                "init",
                "--section",
                "decisions",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            self.run_cmd(
                "set-phase",
                "ARCH-DEC-001",
                "in_review",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            proc = self.run_cmd(
                "approve",
                "ARCH-DEC-001",
                "--approver",
                "reviewer",
                artifacts_dir=artifacts_dir,
                expected_code=2,
            )
            self.assertIn("artifact is not review-ready", proc.stderr)

    def test_link_rejects_unknown_internal_arch_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            self.run_cmd(
                "init",
                "--section",
                "decisions",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            proc = self.run_cmd(
                "link",
                "ARCH-DEC-001",
                "--downstream",
                "ARCH-COMP-999",
                artifacts_dir=artifacts_dir,
                expected_code=2,
            )
            self.assertIn("points to a missing arch artifact", proc.stderr)

    def test_report_validate_rejects_invalid_review_contract(self) -> None:
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
                "ARCH-DEC-001",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            payload = json.loads(proc.stdout)
            report_path = Path(payload["path"])
            report_path.write_text(
                textwrap.dedent(
                    """\
                    ---
                    report_id: review-ARCH-DEC-001-20260412T000000Z
                    kind: review
                    skill: arch
                    stage: review
                    created_at: 2026-04-12T00:00:00Z
                    target_refs:
                      - ARCH-DEC-001
                    verdict: pass
                    summary: ok
                    proposed_meta_ops:
                      - cmd: set-phase
                        artifact_id: ARCH-DEC-001
                        phase: approved
                    items:
                      - id: 1
                        classification: totally_made_up
                        severity: high
                    ---

                    # review report (arch/review)

                    ## Summary
                    ok

                    ## Scenarios
                    | scenario | verdict | reason |
                    | --- | --- | --- |

                    ## Constraints
                    | constraint | satisfied by |
                    | --- | --- |

                    ## Traceability
                    none

                    ## Risks and open items
                    none
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
            self.assertIn("invalid classification", proc.stdout)
            self.assertIn("not allowed", proc.stdout)


if __name__ == "__main__":
    unittest.main()
