from __future__ import annotations

import re
from pathlib import Path


TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def vtt_to_text(path: str | Path) -> str:
    raw = Path(path).read_text(encoding="utf-8", errors="ignore")
    lines: list[str] = []

    for line in raw.splitlines():
        t = line.strip()
        if not t:
            continue
        if t == "WEBVTT":
            continue
        if "-->" in t:
            continue
        if t.isdigit():
            continue

        t = TAG_RE.sub("", t)
        if t:
            lines.append(t)

    text = " ".join(lines)
    text = SPACE_RE.sub(" ", text).strip()
    return text