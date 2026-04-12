from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime


INVALID_CHARS_RE = re.compile(r'[\\/:*?"<>|]+')
MULTISPACE_RE = re.compile(r"\s+")
MULTIDASH_RE = re.compile(r"-{2,}")


def sanitize_windows_filename(value: str, max_len: int = 140) -> str:
    value = INVALID_CHARS_RE.sub("_", value)
    value = MULTISPACE_RE.sub(" ", value).strip(" .")
    value = value.replace(" ", "-")
    value = MULTIDASH_RE.sub("-", value)
    if not value:
        value = "untitled"
    return value[:max_len]


def build_transcript_filename(publication_dt: datetime, title: str, extension: str = ".txt") -> str:
    ts = publication_dt.strftime("%Y-%m-%d-%H-%M")
    safe_title = sanitize_windows_filename(title)
    return f"{ts}-{safe_title}{extension}"


def build_summary_filename_from_transcript(transcript_path: str | Path) -> str:
    p = Path(transcript_path)
    return f"{p.stem}.md"


def build_pdf_filename(now: datetime, extension: str = ".pdf") -> str:
    return now.strftime("%Y-%m-%d-%H-%M") + extension