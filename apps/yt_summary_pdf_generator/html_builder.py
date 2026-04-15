from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path


def _safe_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _published_display(value: str) -> str:
    raw = _safe_text(value)
    if not raw:
        return ""

    try:
        dt = datetime.fromisoformat(raw)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return raw


def _summary_char_count(item: dict) -> int:
    return len(_safe_text(item.get("summary_text")))


def _markdown_to_html(summary_text: str) -> str:
    parts: list[str] = []
    in_list = False

    for raw_line in summary_text.splitlines():
        line = raw_line.strip()

        if not line:
            if in_list:
                parts.append("</ul>")
                in_list = False
            continue

        if line.startswith("# "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h2>{escape(line[2:].strip())}</h2>")
            continue

        if line.startswith("## "):
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f"<h3>{escape(line[3:].strip())}</h3>")
            continue

        if line.startswith("- "):
            if not in_list:
                parts.append("<ul>")
                in_list = True
            parts.append(f"<li>{escape(line[2:].strip())}</li>")
            continue

        if in_list:
            parts.append("</ul>")
            in_list = False

        parts.append(f"<p>{escape(line)}</p>")

    if in_list:
        parts.append("</ul>")

    return "\n".join(parts)


def build_html(output_path: str, batch_items: list[dict], document_title: str) -> str:
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    toc_items: list[str] = []
    summary_sections: list[str] = []

    for idx, item in enumerate(batch_items, start=1):
        title = _safe_text(item.get("title")) or f"Summary {idx}"
        channel_name = _safe_text(item.get("channel_name"))
        publication_datetime = _published_display(_safe_text(item.get("publication_datetime")))
        video_url = _safe_text(item.get("video_url"))
        summary_text = _safe_text(item.get("summary_text"))
        summary_chars = _summary_char_count(item)
        anchor = f"summary-{idx}"

        toc_items.append(
            f'<li><a href="#{anchor}">{escape(title)}</a><div class="toc-meta">{escape(channel_name)} | {escape(publication_datetime)} | {summary_chars} chars</div></li>'
        )

        video_link = f'<a href="{escape(video_url)}" target="_blank" rel="noreferrer">{escape(video_url)}</a>' if video_url else ''
        summary_sections.append(
            f'''<section id="{anchor}" class="summary-card">
<h2>{escape(title)}</h2>
<div class="meta-grid">
<div><strong>Channel</strong><span>{escape(channel_name)}</span></div>
<div><strong>Published</strong><span>{escape(publication_datetime)}</span></div>
<div><strong>Summary chars</strong><span>{summary_chars}</span></div>
<div><strong>Video</strong><span>{video_link}</span></div>
</div>
<div class="summary-body">
{_markdown_to_html(summary_text)}
</div>
</section>'''
        )

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(document_title)}</title>
<style>
:root {{
  --bg: #f6f1e8;
  --panel: #fffdf8;
  --ink: #1f2933;
  --muted: #6b7280;
  --accent: #99582a;
  --accent-soft: #f3e9dc;
  --border: #dcc5a8;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: Georgia, "Times New Roman", serif; background: linear-gradient(180deg, #efe7da 0%, var(--bg) 45%, #f9f6ef 100%); color: var(--ink); line-height: 1.6; }}
a {{ color: #0b63b6; }}
.container {{ max-width: 1080px; margin: 0 auto; padding: 32px 20px 56px; }}
.hero {{ background: var(--panel); border: 1px solid var(--border); border-radius: 18px; padding: 28px; box-shadow: 0 18px 50px rgba(91, 62, 36, 0.08); }}
.hero h1 {{ margin: 0 0 10px; font-size: clamp(2rem, 4vw, 3.2rem); line-height: 1.1; }}
.hero p {{ margin: 0; color: var(--muted); }}
.index-card {{ margin-top: 22px; background: rgba(255, 253, 248, 0.95); border: 1px solid var(--border); border-radius: 18px; padding: 22px; }}
.index-card h2 {{ margin-top: 0; }}
.toc {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 14px; }}
.toc li {{ padding-bottom: 14px; border-bottom: 1px solid #eadbc8; }}
.toc li:last-child {{ border-bottom: 0; padding-bottom: 0; }}
.toc-meta {{ color: var(--muted); font-size: 0.95rem; margin-top: 3px; }}
.summary-list {{ display: grid; gap: 20px; margin-top: 24px; }}
.summary-card {{ background: var(--panel); border: 1px solid var(--border); border-radius: 18px; padding: 24px; box-shadow: 0 14px 34px rgba(91, 62, 36, 0.07); scroll-margin-top: 24px; }}
.summary-card h2 {{ margin-top: 0; font-size: clamp(1.4rem, 2.5vw, 2rem); line-height: 1.2; }}
.meta-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 18px; padding: 14px; background: var(--accent-soft); border-radius: 12px; }}
.meta-grid div {{ display: grid; gap: 2px; }}
.meta-grid strong {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--accent); }}
.summary-body h2, .summary-body h3 {{ margin-top: 1.4em; margin-bottom: 0.4em; }}
.summary-body p {{ margin: 0 0 0.9em; }}
.summary-body ul {{ margin: 0 0 1em 1.2em; padding: 0; }}
@media (max-width: 700px) {{
  .container {{ padding: 18px 14px 40px; }}
  .hero, .index-card, .summary-card {{ padding: 18px; border-radius: 14px; }}
}}
</style>
</head>
<body>
<div class="container">
<header class="hero">
<h1>{escape(document_title)}</h1>
<p>Generated: {escape(generated_at)}</p>
</header>
<nav class="index-card">
<h2>Index</h2>
<ol class="toc">
{''.join(toc_items)}
</ol>
</nav>
<main class="summary-list">
{''.join(summary_sections)}
</main>
</div>
</body>
</html>
'''

    out_path.write_text(html, encoding='utf-8')
    return str(out_path)
