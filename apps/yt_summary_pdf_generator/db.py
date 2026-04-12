from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def open_db(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def initialize_schema_if_needed(conn: sqlite3.Connection, schema_path: str | Path) -> None:
    schema = Path(schema_path).read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()


def fetch_one_value(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> Any:
    row = conn.execute(sql, params).fetchone()
    if row is None:
        return None
    return row[0]


def insert_app_run(
    conn: sqlite3.Connection,
    app_name: str,
    started_at: str,
    time_window_start: str,
    time_window_end: str,
    status: str,
) -> int:
    sql = """
    INSERT INTO app_runs (
        app_name, started_at, time_window_start, time_window_end, status
    )
    VALUES (?, ?, ?, ?, ?)
    """
    cur = conn.execute(sql, (app_name, started_at, time_window_start, time_window_end, status))
    conn.commit()
    return int(cur.lastrowid)


def finalize_app_run(
    conn: sqlite3.Connection,
    run_id: int,
    status: str,
    completed_at: str,
    total_candidates: int,
    completed_items: int,
    skipped_items: int,
    failed_items: int,
    interrupted_items: int,
    remaining_items: int,
    report_path: str | None = None,
    plot_path: str | None = None,
    error_message: str | None = None,
) -> None:
    sql = """
    UPDATE app_runs
    SET status = ?,
        completed_at = ?,
        total_candidates = ?,
        completed_items = ?,
        skipped_items = ?,
        failed_items = ?,
        interrupted_items = ?,
        remaining_items = ?,
        report_path = ?,
        plot_path = ?,
        error_message = ?
    WHERE run_id = ?
    """
    conn.execute(
        sql,
        (
            status,
            completed_at,
            total_candidates,
            completed_items,
            skipped_items,
            failed_items,
            interrupted_items,
            remaining_items,
            report_path,
            plot_path,
            error_message,
            run_id,
        ),
    )
    conn.commit()


def select_eligible_unsummarized_transcripts(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    sql = """
    SELECT
        t.transcript_id,
        t.video_id,
        t.transcript_path,
        t.transcript_language,
        v.title,
        v.video_url,
        v.publication_datetime,
        c.channel_name
    FROM transcripts t
    JOIN videos v ON v.video_id = t.video_id
    JOIN channels c ON c.channel_id = v.channel_id
    LEFT JOIN summaries s
        ON s.video_id = t.video_id
        AND s.status = 'success'
    LEFT JOIN pdf_batch_items pbi
        ON pbi.video_id = t.video_id
    LEFT JOIN pdf_batches pb
        ON pb.batch_id = pbi.batch_id
        AND pb.status = 'success'
    WHERE t.status = 'success'
      AND t.transcript_path IS NOT NULL
      AND s.video_id IS NULL
      AND pb.batch_id IS NULL
    ORDER BY v.publication_datetime ASC
    """
    return list(conn.execute(sql).fetchall())


def mark_summary_in_progress(conn: sqlite3.Connection, video_id: str, transcript_id: int, now_iso: str) -> None:
    sql = """
    INSERT INTO summaries (
        video_id, transcript_id, status, first_attempt_at, last_attempt_at
    )
    VALUES (?, ?, 'in_progress', ?, ?)
    ON CONFLICT(video_id) DO UPDATE SET
        transcript_id = excluded.transcript_id,
        status = 'in_progress',
        last_attempt_at = excluded.last_attempt_at
    """
    conn.execute(sql, (video_id, transcript_id, now_iso, now_iso))
    conn.commit()


def mark_summary_success(
    conn: sqlite3.Connection,
    video_id: str,
    transcript_id: int,
    summary_path: str,
    summary_language: str | None,
    model_name: str,
    prompt_version: str,
    summary_hash: str,
    completed_at: str,
) -> int:
    sql = """
    INSERT INTO summaries (
        video_id, transcript_id, summary_path, summary_language,
        model_name, prompt_version, summary_hash,
        status, first_attempt_at, last_attempt_at, completed_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, 'success', ?, ?, ?)
    ON CONFLICT(video_id) DO UPDATE SET
        transcript_id = excluded.transcript_id,
        summary_path = excluded.summary_path,
        summary_language = excluded.summary_language,
        model_name = excluded.model_name,
        prompt_version = excluded.prompt_version,
        summary_hash = excluded.summary_hash,
        status = 'success',
        last_attempt_at = excluded.last_attempt_at,
        completed_at = excluded.completed_at
    """
    conn.execute(
        sql,
        (
            video_id,
            transcript_id,
            summary_path,
            summary_language,
            model_name,
            prompt_version,
            summary_hash,
            completed_at,
            completed_at,
            completed_at,
        ),
    )
    conn.commit()

    row = conn.execute("SELECT summary_id FROM summaries WHERE video_id = ?", (video_id,)).fetchone()
    return int(row["summary_id"])


def mark_summary_failed(conn: sqlite3.Connection, video_id: str, error_message: str, now_iso: str) -> None:
    sql = """
    UPDATE summaries
    SET status = 'failed',
        error_message = ?,
        last_attempt_at = ?
    WHERE video_id = ?
    """
    conn.execute(sql, (error_message, now_iso, video_id))
    conn.commit()


def insert_pdf_batch(conn: sqlite3.Connection, batch_date: str, started_at: str, status: str) -> int:
    sql = """
    INSERT INTO pdf_batches (
        batch_date, started_at, status
    )
    VALUES (?, ?, ?)
    """
    cur = conn.execute(sql, (batch_date, started_at, status))
    conn.commit()
    return int(cur.lastrowid)


def mark_pdf_batch_success(
    conn: sqlite3.Connection,
    batch_id: int,
    local_pdf_path: str,
    target_pdf_path: str | None,
    file_name: str,
    copied_at: str | None,
    completed_at: str,
) -> None:
    sql = """
    UPDATE pdf_batches
    SET local_pdf_path = ?,
        target_pdf_path = ?,
        file_name = ?,
        status = 'success',
        copied_at = ?,
        completed_at = ?
    WHERE batch_id = ?
    """
    conn.execute(sql, (local_pdf_path, target_pdf_path, file_name, copied_at, completed_at, batch_id))
    conn.commit()


def mark_pdf_batch_incomplete(conn: sqlite3.Connection, batch_id: int, completed_at: str, error_message: str | None = None) -> None:
    sql = """
    UPDATE pdf_batches
    SET status = 'incomplete',
        completed_at = ?,
        error_message = ?
    WHERE batch_id = ?
    """
    conn.execute(sql, (completed_at, error_message, batch_id))
    conn.commit()


def mark_pdf_batch_copy_failed(
    conn: sqlite3.Connection,
    batch_id: int,
    local_pdf_path: str,
    file_name: str,
    completed_at: str,
    error_message: str,
) -> None:
    sql = """
    UPDATE pdf_batches
    SET local_pdf_path = ?,
        file_name = ?,
        status = 'copy_failed',
        completed_at = ?,
        error_message = ?
    WHERE batch_id = ?
    """
    conn.execute(sql, (local_pdf_path, file_name, completed_at, error_message, batch_id))
    conn.commit()


def insert_pdf_batch_item(
    conn: sqlite3.Connection,
    batch_id: int,
    video_id: str,
    summary_id: int,
    included_at: str,
) -> None:
    sql = """
    INSERT OR IGNORE INTO pdf_batch_items (
        batch_id, video_id, summary_id, included_at
    )
    VALUES (?, ?, ?, ?)
    """
    conn.execute(sql, (batch_id, video_id, summary_id, included_at))
    conn.commit()