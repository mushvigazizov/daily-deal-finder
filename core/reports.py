import json
from datetime import datetime
from pathlib import Path
from core.paths import REPORTS_DIR

def write_report(kind, data):
    out_dir = REPORTS_DIR / kind
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_file = out_dir / f"{stamp}.json"

    out_file.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"REPORT {out_file.relative_to(Path.cwd())}")
    return out_file
