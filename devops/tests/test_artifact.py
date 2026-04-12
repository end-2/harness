from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT_DIR / "devops" / "scripts" / "artifact.py"


class DevopsArtifactScriptTests(unittest.TestCase):
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

    def test_validate_rejects_unknown_artifact_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            proc = self.run_cmd(
                "validate",
                "DEVOPS-PL-999",
                artifacts_dir=artifacts_dir,
                expected_code=2,
            )
            self.assertIn("No artifact found with id 'DEVOPS-PL-999'", proc.stderr)

    def test_validate_rejects_missing_created_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            proc = self.run_cmd(
                "init",
                "--section",
                "pipeline",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            payload = json.loads(proc.stdout)
            meta_path = Path(payload["meta_path"])
            data = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
            data.pop("created_at", None)
            meta_path.write_text(
                yaml.safe_dump(data, sort_keys=False),
                encoding="utf-8",
            )

            proc = self.run_cmd(
                "validate",
                artifacts_dir=artifacts_dir,
                expected_code=1,
            )
            self.assertIn("missing field 'created_at'", proc.stdout)

    def test_validate_rejects_incoherent_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            proc = self.run_cmd(
                "init",
                "--section",
                "pipeline",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            payload = json.loads(proc.stdout)
            meta_path = Path(payload["meta_path"])
            data = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
            data["progress"] = {
                "section_completed": 9,
                "section_total": 3,
                "percent": 42,
            }
            meta_path.write_text(
                yaml.safe_dump(data, sort_keys=False),
                encoding="utf-8",
            )

            proc = self.run_cmd(
                "validate",
                artifacts_dir=artifacts_dir,
                expected_code=1,
            )
            self.assertIn("progress.section_completed cannot exceed section_total", proc.stdout)
            self.assertIn("progress.percent must be 300, got 42", proc.stdout)

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
                "--scope",
                "all",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            payload = json.loads(proc.stdout)
            report_path = Path(payload["path"])
            report_path.write_text(
                textwrap.dedent(
                    """\
                    ---
                    report_id: review-all-20260412T000000Z
                    kind: review
                    skill: devops
                    stage: review
                    created_at: 2026-04-12T00:00:00Z
                    target_refs:
                      - DEVOPS-OBS-001
                    verdict: pass
                    summary: review completed
                    proposed_meta_ops:
                      - cmd: set-phase
                        artifact_id: DEVOPS-OBS-001
                        phase: in_review
                    items:
                      - id: 1
                        classification: definitely_not_allowed
                        severity: high
                        message: bad classification
                    ---

                    # review report (devops/review)

                    body
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
            self.assertIn("command 'set-phase' is not allowed", proc.stdout)

    def test_report_validate_accepts_well_formed_monitor_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            proc = self.run_cmd(
                "report",
                "path",
                "--kind",
                "monitor",
                "--stage",
                "monitor",
                "--target",
                "DEVOPS-OBS-001",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            payload = json.loads(proc.stdout)
            report_path = Path(payload["path"])
            report_path.write_text(
                textwrap.dedent(
                    """\
                    ---
                    report_id: monitor-DEVOPS-OBS-001-20260412T000000Z
                    kind: monitor
                    skill: devops
                    stage: monitor
                    created_at: 2026-04-12T00:00:00Z
                    target_refs:
                      - DEVOPS-OBS-001
                    verdict: pass
                    summary: generated monitor draft
                    proposed_meta_ops:
                      - cmd: set-progress
                        artifact_id: DEVOPS-OBS-001
                        completed: 3
                        total: 4
                    items:
                      - id: 1
                        classification: content_draft
                        severity: info
                        message: generated alert rules
                    ---

                    # monitor report (devops/monitor)

                    body
                    """
                ),
                encoding="utf-8",
            )

            self.run_cmd(
                "report",
                "validate",
                str(report_path),
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )


if __name__ == "__main__":
    unittest.main()
