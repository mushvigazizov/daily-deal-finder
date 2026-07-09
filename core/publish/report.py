from datetime import datetime

def now_iso():
    return datetime.utcnow().isoformat() + "Z"

def make_step(name, status, message="", details=None):
    return {
        "name": name,
        "status": status,
        "message": message,
        "details": details or {},
    }

def make_publish_report(started_at, steps):
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
    }
