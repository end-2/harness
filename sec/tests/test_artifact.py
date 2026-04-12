from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parents[2]
ARTIFACT_SCRIPT = ROOT_DIR / "sec" / "scripts" / "artifact.py"
APPROVAL_SCRIPT = ROOT_DIR / "sec" / "scripts" / "approval.py"
VALIDATE_SCRIPT = ROOT_DIR / "sec" / "scripts" / "validate.py"
EXAMPLE_LIGHT_META = (
    ROOT_DIR / "sec" / "references" / "examples" / "light" / "threat-model-output.meta.yaml"
)
EXAMPLE_HEAVY_META = (
    ROOT_DIR / "sec" / "references" / "examples" / "heavy" / "threat-model-output.meta.yaml"
)


_artifact_spec = importlib.util.spec_from_file_location("sec_artifact_module", ARTIFACT_SCRIPT)
assert _artifact_spec and _artifact_spec.loader
ARTIFACT_MODULE = importlib.util.module_from_spec(_artifact_spec)
_artifact_spec.loader.exec_module(ARTIFACT_MODULE)


class SecArtifactScriptTests(unittest.TestCase):
    def run_script(
        self,
        script: Path,
        *args: str,
        artifacts_dir: Path,
        expected_code: int,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HARNESS_ARTIFACTS_DIR"] = str(artifacts_dir)
        env["SESSION_ID"] = "sec-test-session"
        proc = subprocess.run(
            [sys.executable, str(script), *args],
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

    def test_validate_rejects_missing_threat_model_block_and_created_at(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            proc = self.run_script(
                ARTIFACT_SCRIPT,
                "init",
                "--section",
                "threat-model",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            payload = json.loads(proc.stdout)
            meta_path = Path(payload["meta_path"])
            data = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
            data.pop("created_at", None)
            data.pop("threat_model", None)
            meta_path.write_text(
                yaml.safe_dump(data, sort_keys=False),
                encoding="utf-8",
            )

            proc = self.run_script(
                ARTIFACT_SCRIPT,
                "validate",
                artifacts_dir=artifacts_dir,
                expected_code=1,
            )
            self.assertIn("missing field 'created_at'", proc.stdout)
            self.assertIn("missing section block 'threat_model'", proc.stdout)

    def test_validate_rejects_incoherent_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            self.run_script(
                ARTIFACT_SCRIPT,
                "init",
                "--section",
                "security-advisory",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            meta_path, data = self.load_meta(artifacts_dir, "SEC-SR-001")
            data["progress"] = {
                "section_completed": 4,
                "section_total": 2,
                "percent": 25,
            }
            meta_path.write_text(
                yaml.safe_dump(data, sort_keys=False),
                encoding="utf-8",
            )

            proc = self.run_script(
                ARTIFACT_SCRIPT,
                "validate",
                artifacts_dir=artifacts_dir,
                expected_code=1,
            )
            self.assertIn("progress.section_completed cannot exceed section_total", proc.stdout)
            self.assertIn("progress.percent must be 200, got 25", proc.stdout)

    def test_accept_risk_requires_compliance_override_for_compliance_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            self.run_script(
                ARTIFACT_SCRIPT,
                "init",
                "--section",
                "compliance-report",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            self.run_script(
                APPROVAL_SCRIPT,
                "request",
                "SEC-CR-001",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            proc = self.run_script(
                APPROVAL_SCRIPT,
                "accept-risk",
                "SEC-CR-001",
                "--approver",
                "alice.kim",
                "--rationale",
                "Accepted for MVP.",
                artifacts_dir=artifacts_dir,
                expected_code=2,
            )
            self.assertIn("requires --compliance-override", proc.stderr)

    def test_validate_wrapper_accepts_optional_subcommand(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            self.run_script(
                ARTIFACT_SCRIPT,
                "init",
                "--section",
                "vulnerability-report",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            self.run_script(
                VALIDATE_SCRIPT,
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            self.run_script(
                VALIDATE_SCRIPT,
                "validate",
                "SEC-VA-001",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )

    def test_approval_records_rationale_and_approved_phase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            artifacts_dir = Path(tmp_dir)
            self.run_script(
                ARTIFACT_SCRIPT,
                "init",
                "--section",
                "threat-model",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            self.run_script(
                APPROVAL_SCRIPT,
                "request",
                "SEC-TM-001",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )
            self.run_script(
                APPROVAL_SCRIPT,
                "approve",
                "SEC-TM-001",
                "--approver",
                "alice.kim",
                "--rationale",
                "Threat model is ready for downstream stages.",
                artifacts_dir=artifacts_dir,
                expected_code=0,
            )

            _meta_path, data = self.load_meta(artifacts_dir, "SEC-TM-001")
            self.assertEqual(data["phase"], "approved")
            self.assertEqual(data["approval"]["state"], "approved")
            self.assertEqual(
                data["approval"]["rationale"],
                "Threat model is ready for downstream stages.",
            )
            self.assertEqual(
                data["approval"]["history"][-1]["rationale"],
                "Threat model is ready for downstream stages.",
            )

    def test_reference_examples_match_validator_contract(self) -> None:
        for path in (EXAMPLE_LIGHT_META, EXAMPLE_HEAVY_META):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            errors: list[str] = []
            errors.extend(ARTIFACT_MODULE._validate_meta(data, path))
            errors.extend(ARTIFACT_MODULE._validate_progress(data, path))
            errors.extend(ARTIFACT_MODULE._validate_approval(data, path))
            self.assertEqual(
                errors,
                [],
                msg=f"{path.name} failed validation:\n" + "\n".join(errors),
            )


if __name__ == "__main__":
    unittest.main()
