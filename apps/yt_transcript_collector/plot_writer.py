from __future__ import annotations

from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt


def write_plot(plot_dir: str, app_name: str, stats: dict) -> str:
    Path(plot_dir).mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    out = Path(plot_dir) / f"{app_name}-{stamp}.png"

    labels = ["total", "completed", "skipped", "failed", "interrupted", "remaining"]
    values = [
        stats.get("total_candidates", 0),
        stats.get("completed_items", 0),
        stats.get("skipped_items", 0),
        stats.get("failed_items", 0),
        stats.get("interrupted_items", 0),
        stats.get("remaining_items", 0),
    ]

    plt.figure(figsize=(8, 5))
    plt.bar(labels, values)
    plt.title(f"{app_name} run status")
    plt.ylabel("count")
    plt.tight_layout()
    plt.savefig(out)
    plt.close()

    return str(out)