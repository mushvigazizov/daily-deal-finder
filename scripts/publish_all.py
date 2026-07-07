import argparse
import subprocess
import sys
import time
from pathlib import Path

from scripts.reporting.report_engine import write_report

ROOT = Path(__file__).resolve().parents[1]

def run(cmd):
    print("RUN:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print("FAILED:", " ".join(cmd))
        sys.exit(result.returncode)

def main():
    started = time.time()

    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=1)
    args = parser.parse_args()

    run(["python3", "-m", "scripts.publish_product", "--all", "--limit", str(args.limit)])
    run(["python3", "-m", "scripts.content_engine"])
    run(["python3", "scripts/quality_validator.py"])

    duration = round(time.time() - started, 2)

    write_report("publish", {
        "status": "success",
        "workflow": "publish_all",
        "limit": args.limit,
        "duration_seconds": duration,
        "message": "Publish workflow completed successfully"
    })

    print("")
    print("✅ MASTER WORKFLOW COMPLETE")
    print("If commit was created, push from host:")
    print("git push origin main")

if __name__ == "__main__":
    main()
