#!/usr/bin/env python3

import subprocess
import sys

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

    result = subprocess.run([sys.executable, script])

    if result.returncode != 0:
        print(f"\n❌ FAILED: {name}")
        sys.exit(result.returncode)

    print(f"✅ COMPLETED: {name}")


def main():
    print("=" * 70)
    print("DAILY DEAL FINDER PRODUCTION PIPELINE")
    print("=" * 70)

    for name, script in STEPS:
        run_step(name, script)

    print("\n" + "=" * 70)
    print("🎉 PIPELINE FINISHED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()
