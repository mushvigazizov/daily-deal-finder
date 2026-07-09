from core.pipeline.context import make_pipeline_context
from core.pipeline.report import (
    now_iso,
    make_pipeline_step,
    make_pipeline_report,
)

def run_pipeline(mode="manual"):
    started_at = now_iso()
    context = make_pipeline_context(mode=mode)
    steps = []

    steps.append(
        make_pipeline_step(
            "pipeline",
            "success",
            "Pipeline runner initialized",
        )
    )

    return make_pipeline_report(started_at, steps, context)
