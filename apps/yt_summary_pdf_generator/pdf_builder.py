from __future__ import annotations

from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


def _wrap_text(text: str, font_name: str, font_size: int, max_width: float) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = ""

    for word in words:
        candidate = word if not current else f"{current} {word}"
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def _safe_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _summary_char_count(item: dict) -> int:
    return len(_safe_text(item.get("summary_text")))


def _published_display(value: str) -> str:
    raw = _safe_text(value)
    if not raw:
        return ""

    try:
        dt = datetime.fromisoformat(raw)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return raw


def build_pdf(output_path: str, batch_items: list[dict], document_title: str) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    left = 18 * mm
    right = width - 18 * mm
    top = height - 18 * mm
    bottom = 16 * mm
    max_width = right - left

    title_font = "Helvetica-Bold"
    body_font = "Helvetica"
    link_font = "Helvetica"

    page_anchor_names: list[str] = []

    # ------------------------------------------------------------------
    # First pass: reserve one page per summary and remember destination page
    # Cover/index page is page 1, summary pages start at page 2
    # ------------------------------------------------------------------
    for idx, _item in enumerate(batch_items, start=1):
        page_anchor_names.append(f"summary_{idx}")

    # ------------------------------------------------------------------
    # Cover / index page
    # ------------------------------------------------------------------
    c.setTitle(document_title)

    y = top

    c.setFont(title_font, 18)
    c.drawString(left, y, document_title)
    y -= 10 * mm

    c.setFont(body_font, 10)
    c.drawString(left, y, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 8 * mm

    c.setFont(title_font, 12)
    c.drawString(left, y, "Index")
    y -= 7 * mm

    c.setStrokeColor(colors.black)
    c.line(left, y, right, y)
    y -= 5 * mm

    for idx, item in enumerate(batch_items, start=1):
        title = _safe_text(item.get("title"))
        channel_name = _safe_text(item.get("channel_name"))
        published = _published_display(_safe_text(item.get("publication_datetime")))
        summary_chars = _summary_char_count(item)
        page_number = idx + 1
        anchor_name = page_anchor_names[idx - 1]

        bullet = u"\u2022"

        first_line = f"{bullet} {title}"
        second_line = (
            f"  Channel: {channel_name} | Published: {published} | "
            f"Summary chars: {summary_chars} | Page: {page_number}"
        )

        title_lines = _wrap_text(first_line, link_font, 10, max_width)
        meta_lines = _wrap_text(second_line, body_font, 9, max_width - 4 * mm)

        needed_height = (len(title_lines) * 5.5 + len(meta_lines) * 5.0 + 3.5) * mm

        if y - needed_height < bottom:
            c.showPage()
            y = top
            c.setFont(title_font, 12)
            c.drawString(left, y, "Index (continued)")
            y -= 7 * mm
            c.line(left, y, right, y)
            y -= 5 * mm

        link_rect_top = y + 1.5 * mm

        c.setFont(link_font, 10)
        current_y = y
        for line in title_lines:
            c.setFillColor(colors.blue)
            c.drawString(left, current_y, line)
            current_y -= 5.5 * mm

        c.setFillColor(colors.black)
        c.setFont(body_font, 9)
        for line in meta_lines:
            c.drawString(left + 4 * mm, current_y, line)
            current_y -= 5.0 * mm

        link_rect_bottom = current_y + 2.5 * mm
        c.linkAbsolute(
            "",
            anchor_name,
            Rect=(left, link_rect_bottom, right, link_rect_top),
            thickness=0,
        )

        y = current_y - 1.0 * mm

    c.showPage()

    # ------------------------------------------------------------------
    # Summary pages
    # ------------------------------------------------------------------
    for idx, item in enumerate(batch_items, start=1):
        anchor_name = page_anchor_names[idx - 1]
        c.bookmarkPage(anchor_name)
        c.addOutlineEntry(_safe_text(item.get("title")) or f"Summary {idx}", anchor_name, level=0, closed=False)

        y = top

        title = _safe_text(item.get("title"))
        channel_name = _safe_text(item.get("channel_name"))
        publication_datetime = _published_display(_safe_text(item.get("publication_datetime")))
        video_url = _safe_text(item.get("video_url"))
        summary_text = _safe_text(item.get("summary_text"))
        summary_chars = _summary_char_count(item)

        c.setFont(title_font, 14)
        for line in _wrap_text(title, title_font, 14, max_width):
            c.drawString(left, y, line)
            y -= 6.5 * mm

        y -= 1 * mm

        c.setFont(body_font, 10)
        meta_lines = [
            f"Channel: {channel_name}",
            f"Published: {publication_datetime}",
            f"Summary chars: {summary_chars}",
            f"URL: {video_url}",
        ]

        for line in meta_lines:
            wrapped = _wrap_text(line, body_font, 10, max_width)
            for wrapped_line in wrapped:
                if y < bottom + 15 * mm:
                    c.showPage()
                    y = top
                    c.setFont(body_font, 10)
                c.drawString(left, y, wrapped_line)
                y -= 5.2 * mm

        y -= 2 * mm

        for para in summary_text.splitlines():
            para = para.strip()

            if not para:
                y -= 3.5 * mm
                continue

            if para.startswith("# "):
                if y < bottom + 18 * mm:
                    c.showPage()
                    y = top
                c.setFont(title_font, 13)
                c.drawString(left, y, para[2:].strip())
                y -= 6.5 * mm
                c.setFont(body_font, 10)
                continue

            if para.startswith("## "):
                if y < bottom + 16 * mm:
                    c.showPage()
                    y = top
                c.setFont(title_font, 11)
                c.drawString(left, y, para[3:].strip())
                y -= 5.8 * mm
                c.setFont(body_font, 10)
                continue

            if para.startswith("- "):
                wrapped = _wrap_text(para, body_font, 10, max_width - 5 * mm)
                for i, line in enumerate(wrapped):
                    if y < bottom + 10 * mm:
                        c.showPage()
                        y = top
                        c.setFont(body_font, 10)
                    prefix = u"\u2022 " if i == 0 else "  "
                    c.drawString(left + 2 * mm, y, prefix + line)
                    y -= 5.0 * mm
                continue

            wrapped = _wrap_text(para, body_font, 10, max_width)
            for line in wrapped:
                if y < bottom + 10 * mm:
                    c.showPage()
                    y = top
                    c.setFont(body_font, 10)
                c.drawString(left, y, line)
                y -= 5.0 * mm

        c.showPage()

    c.save()
    return output_path