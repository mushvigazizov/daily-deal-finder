import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from core.ai_image.pipeline import ImagePipeline


def main():
    print("=" * 70)
    print("AI IMAGE GENERATOR")
    print("=" * 70)

    pipeline = ImagePipeline(platform="website")
    results = pipeline.run_batch()
    report = pipeline.generate_report(results)

    print(json.dumps(report, indent=2))

    if report["complete"] == report["total"]:
        print("AI IMAGE GENERATION COMPLETED")
        return 0

    print("AI IMAGE GENERATION PARTIALLY FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
