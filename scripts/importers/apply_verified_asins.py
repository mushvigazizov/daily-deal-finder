from __future__ import annotations

"""
Backward-compatible entry point for Amazon identity application.

This legacy command no longer applies ASIN values directly. All writes are
delegated to the locked identity application engine, which requires a valid
identity hash and identity_locked=true.
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from scripts.amazon.apply_locked_product_identities import main


if __name__ == "__main__":
    raise SystemExit(main())
