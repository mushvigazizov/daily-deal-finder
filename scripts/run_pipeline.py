import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.pipeline.runner import run_pipeline

def main():
    print("=" * 70)
    print("DAILY DEAL FINDER PIPELINE")
    print("=" * 70)

    report = run_pipeline()

    for step in report["steps"]:
        icon = "[OK]" if step["status"] == "success" else "[SKIP]" if step["status"] == "skipped" else "[FAIL]"
        print(f"{icon} {step['name']} - {step['message']}")

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETED" if report["success"] else "PIPELINE FAILED")
    print("=" * 70)

    print(json.dumps(report, indent=2))

    return 0 if report["success"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
