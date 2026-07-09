from datetime import datetime

def now_iso():
    return datetime.utcnow().isoformat() + "Z"

def make_pipeline_step(name, status, message="", details=None):
    return {
        "name": name,
        "status": status,
        "message": message,
        "details": details or {},
    }

def make_pipeline_report(started_at, steps, context=None):
    finished_at = now_iso()

    success = all(
        step.get("status") in ("success", "skipped")
        for step in steps
    )

    return {
        "started_at": started_at,
        "finished_at": finished_at,
        "success": success,
        "steps": steps,
        "context": context or {},
    }
