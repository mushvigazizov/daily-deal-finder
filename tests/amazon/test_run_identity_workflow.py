import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = (
    PROJECT_ROOT
    / "scripts"
    / "amazon"
    / "run_identity_workflow.py"
)


class TestRunIdentityWorkflow(unittest.TestCase):
    def test_dry_run_workflow_completes(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stdout + result.stderr,
        )
        self.assertIn(
            "AMAZON PRODUCT IDENTITY WORKFLOW",
            result.stdout,
        )
        self.assertIn(
            "SAFE DRY RUN PASSED",
            result.stdout,
        )
        self.assertIn(
            "Write phase skipped",
            result.stdout,
        )
        self.assertIn(
            "STEP 5 — LOCKED IDENTITY GUARD",
            result.stdout,
        )
        self.assertIn(
            "Result : IDENTITY GUARD PASSED",
            result.stdout,
        )
        self.assertIn(
            "STEP 6 — FINAL PRODUCT IDENTITY AUDIT",
            result.stdout,
        )

    def test_write_flag_is_supported_safely(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--write",
            ],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=result.stdout + result.stderr,
        )
        self.assertIn(
            "SAFE WRITE WORKFLOW PASSED",
            result.stdout,
        )
        self.assertIn(
            "Locked identities :",
            result.stdout,
        )
        self.assertIn(
            "Result : SAFE WRITE WORKFLOW PASSED",
            result.stdout,
        )
        self.assertIn(
            "STEP 5 — LOCKED IDENTITY GUARD",
            result.stdout,
        )
        self.assertIn(
            "Result : IDENTITY GUARD PASSED",
            result.stdout,
        )
        self.assertIn(
            "STEP 6 — FINAL PRODUCT IDENTITY AUDIT",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
