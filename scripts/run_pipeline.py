#!/usr/bin/env python3

import subprocess
import sys
import time
from datetime import datetime
from reporting.report_engine import write_report

STEPS = [
    ("Duplicate Check", "scripts/importers/check_duplicates.py"),
    ("AI Content Generator", "scripts/importers/generate_ai_content.py"),
    ("Product Quality Validator", "scripts/importers/product_quality_validator.py"),
    ("Amazon Link Audit", "scripts/reports/amazon_link_audit.py"),
    ("Project Health Check", "scripts/project_health_check.py"),
    ("Generate Premium UI", "scripts/generate_premium_ui.py"),
]


def run_step(name, script):
    print("\n" + "=" * 70)
    print(f"RUNNING: {name}")
    print("=" * 70)

    start = time.time()
    result = subprocess.run([sys.executable, script])
    duration = round(time.time() - start, 2)

    status = "PASS" if result.returncode == 0 else "FAIL"

    return {
        "name": name,
        "script": script,
        "status": status,
        "duration": duration,
        "returncode": result.returncode,
    }


def print_report(results, started_at, finished_at):
    total_duration = round((finished_at - started_at).total_seconds(), 2)
    failed = [r for r in results if r["status"] == "FAIL"]

    print("\n" + "=" * 70)
    print("DAILY DEAL FINDER - PIPELINE REPORT")
    print("=" * 70)
    print(f"Started : {started_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Finished: {finished_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration: {total_duration}s")
    print("-" * 70)

    for r in results:
        icon = "✅" if r["status"] == "PASS" else "❌"
        print(f"{icon} {r['name']:<30} {r['status']:<5} {r['duration']}s")

    print("-" * 70)
    print(f"Steps   : {len(results)}")
    print(f"Passed  : {len(results) - len(failed)}")
    print(f"Failed  : {len(failed)}")

    if failed:
        print("\nFAILED STEPS")
        for r in failed:
            print(f"- {r['name']} ({r['script']})")
        print("\n❌ PIPELINE FAILED")
    else:
        print("\n🎉 PIPELINE FINISHED SUCCESSFULLY")


def write_pipeline_report(results, started_at, finished_at):
    report_data = {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 2),
        "steps": results,
        "passed": sum(r["status"] == "PASS" for r in results),
        "failed": sum(r["status"] == "FAIL" for r in results),
    }

    write_report("pipeline", report_data)


def main():
    started_at = datetime.now()
    results = []

    print("=" * 70)
    print("DAILY DEAL FINDER PRODUCTION PIPELINE")
    print("=" * 70)

    for name, script in STEPS:
        result = run_step(name, script)
        results.append(result)

        if result["returncode"] != 0:
            break

    finished_at = datetime.now()
    print_report(results, started_at, finished_at)
    write_pipeline_report(results, started_at, finished_at)

    if any(r["status"] == "FAIL" for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
