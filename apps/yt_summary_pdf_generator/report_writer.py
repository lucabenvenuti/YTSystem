from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime


def write_json_report(report_dir: str, app_name: str, payload: dict) -> str:
    Path(report_dir).mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    out = Path(report_dir) / f"{app_name}-{stamp}.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(out)