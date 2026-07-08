import subprocess
import sys

STEPS = [
    ("Duplicate Check", "scripts/importers/check_duplicates.py"),
    ("Quality Validator", "scripts/importers/product_quality_validator.py"),
]

print("=" * 70)
print("DAILY DEAL FINDER IMPORT PIPELINE")
print("=" * 70)

for name, script in STEPS:
    print(f"\n>>> {name}")
    result = subprocess.run([sys.executable, script])

    if result.returncode != 0:
        print(f"\nPipeline stopped: {name} failed.")
        sys.exit(result.returncode)

print("\n" + "=" * 70)
print("IMPORT PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 70)
