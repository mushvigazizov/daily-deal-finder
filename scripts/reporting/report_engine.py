import json
from datetime import datetime, timezone
from pathlib import Path

REPORT_ROOT = Path("reports")

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def write_report(module: str, data: dict) -> Path:
    folder = REPORT_ROOT / module
    folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    path = folder / f"{timestamp}.json"

    report = {
        "module": module,
        "created_at": utc_now(),
        **data,
    }

    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"REPORT {path}")
    return path
