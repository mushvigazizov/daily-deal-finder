import subprocess
import sys

from core.pipeline.context import make_pipeline_context
from core.pipeline.report import (
    now_iso,
    make_pipeline_step,
    make_pipeline_report,
)

PIPELINE_STEPS = [
    ("duplicate_check", "Duplicate Check", ["scripts/importers/check_duplicates.py"]),
    ("ai_content", "AI Content Generator", ["-m", "scripts.importers.generate_ai_content"]),
    ("quality_validator", "Quality Validator", ["scripts/importers/product_quality_validator.py"]),
]

def run_command(command):
    return subprocess.run(
        [sys.executable, *command],
        capture_output=True,
        text=True,
    )

def run_pipeline(mode="manual"):
    started_at = now_iso()
    context = make_pipeline_context(mode=mode)
    steps = []

    for step_key, step_name, command in PIPELINE_STEPS:
        result = run_command(command)

        status = "success" if result.returncode == 0 else "failed"

        steps.append(
            make_pipeline_step(
                step_key,
                status,
                step_name,
                {
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
            )
        )

        if status != "success":
            context["errors"].append(step_key)
            return make_pipeline_report(started_at, steps, context)

    return make_pipeline_report(started_at, steps, context)
