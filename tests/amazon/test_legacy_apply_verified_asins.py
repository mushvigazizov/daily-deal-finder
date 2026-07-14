import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = (
    PROJECT_ROOT
    / "scripts"
    / "importers"
    / "apply_verified_asins.py"
)


class TestLegacyApplyVerifiedAsins(unittest.TestCase):
    def test_legacy_entry_point_uses_safe_locked_engine(self):
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

        self.assertEqual(result.returncode, 0)
        self.assertIn(
            "APPLY LOCKED AMAZON PRODUCT IDENTITIES",
            result.stdout,
        )
        self.assertIn(
            "Write mode        : DRY RUN",
            result.stdout,
        )
        self.assertIn(
            "Products file was not changed.",
            result.stdout,
        )


if __name__ == "__main__":
    unittest.main()
