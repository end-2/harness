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
SCRIPT_PATH = ROOT_DIR / "qa" / "scripts" / "artifact.py"


class QaArtifactScriptTests(unittest.TestCase):
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

    def load_meta(self, artifacts_dir: Path, artifact_id: str) -> tuple[Path, dict]:
        path = artifacts_dir / f"{artifact_id}.meta.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return path, data

    def test_validate_rejects_missing_created_at_and_strategy_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            self.run_cmd(
                "init",
                "--section",
                "test-strategy",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            meta_path, data = self.load_meta(artifacts_dir, "QA-STRATEGY-001")
            data.pop("created_at", None)
            data.pop("test_strategy", None)
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
            self.assertIn("missing test_strategy block", proc.stdout)

    def test_validate_rejects_incoherent_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            self.run_cmd(
                "init",
                "--section",
                "test-strategy",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            meta_path, data = self.load_meta(artifacts_dir, "QA-STRATEGY-001")
            data["progress"] = {
                "section_completed": 99,
                "section_total": 1,
                "percent": 90,
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
            self.assertIn("section_completed 99 exceeds section_total 1", proc.stdout)
            self.assertIn("progress percent 90", proc.stdout)

    def test_set_block_updates_strategy_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            self.run_cmd(
                "init",
                "--section",
                "test-strategy",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            payload_path = artifacts_dir / "strategy-payload.yaml"
            payload_path.write_text(
                textwrap.dedent(
                    """\
                    test_strategy:
                      mode: light
                      scope:
                        in:
                          - re_id: FR-001
                            title: Login
                            priority: must
                            reason: core domain
                        out: []
                      pyramid:
                        - layer: unit
                          ratio: 0.7
                          rationale: simple service
                      nfr_test_plan: []
                      environment_matrix:
                        - environment: ci
                          purpose: full suite
                          notes: arch default
                          constraint_refs: []
                      test_double_strategy: []
                      quality_gate_criteria:
                        code_coverage_min: 0.8
                        requirements_coverage_must_min: 1.0
                        max_failed_tests: 0
                        nfr_metric_refs: []
                    """
                ),
                encoding="utf-8",
            )

            self.run_cmd(
                "set-block",
                "QA-STRATEGY-001",
                "--field",
                "test_strategy",
                "--from",
                str(payload_path),
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )

            _meta_path, data = self.load_meta(artifacts_dir, "QA-STRATEGY-001")
            self.assertEqual(data["test_strategy"]["mode"], "light")
            self.assertEqual(
                data["test_strategy"]["quality_gate_criteria"]["code_coverage_min"],
                0.8,
            )

    def test_set_block_updates_quality_gate_actuals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            self.run_cmd(
                "init",
                "--section",
                "quality-report",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            payload_path = artifacts_dir / "actuals.yaml"
            payload_path.write_text(
                textwrap.dedent(
                    """\
                    quality_gate:
                      actuals:
                        code_coverage: 0.84
                        requirements_coverage_must: 1.0
                        failed_tests: 0
                        nfr_results: []
                    """
                ),
                encoding="utf-8",
            )

            self.run_cmd(
                "set-block",
                "QA-REPORT-001",
                "--field",
                "quality_gate.actuals",
                "--from",
                str(payload_path),
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )

            _meta_path, data = self.load_meta(artifacts_dir, "QA-REPORT-001")
            self.assertEqual(data["quality_gate"]["actuals"]["code_coverage"], 0.84)

    def test_report_validate_rejects_final_na_verdict_and_invalid_review_shapes(
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
                    skill: qa
                    stage: review
                    created_at: 2026-04-12T00:00:00Z
                    target_refs: []
                    verdict: n/a
                    summary: invalid
                    proposed_meta_ops:
                      - op: write-quality-report-actuals
                        artifact_id: QA-REPORT-001
                    items:
                      - re_id: FR-001
                        priority: must
                        gap_type: made_up_gap
                        description: bad shape
                        suggested_fix: fix it
                        auto_fixable: true
                    ---

                    Body
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
            self.assertIn("verdict 'n/a' is only allowed", proc.stdout)
            self.assertIn("invalid gap_type", proc.stdout)
            self.assertIn("is not allowed for stage 'review'", proc.stdout)


if __name__ == "__main__":
    unittest.main()
