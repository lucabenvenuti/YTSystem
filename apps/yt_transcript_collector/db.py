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


def get_last_successful_run_end(conn: sqlite3.Connection, app_name: str) -> str | None:
    sql = """
    SELECT completed_at
    FROM app_runs
    WHERE app_name = ?
      AND status IN ('success', 'partial_success')
      AND completed_items > 0
      AND completed_at IS NOT NULL
    ORDER BY completed_at DESC
    LIMIT 1
    """
    return fetch_one_value(conn, sql, (app_name,))
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


def upsert_channel(conn: sqlite3.Connection, channel_id: str, channel_name: str, now_iso: str, is_enabled: int = 1) -> None:
    sql = """
    INSERT INTO channels (channel_id, channel_name, is_enabled, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(channel_id) DO UPDATE SET
        channel_name = excluded.channel_name,
        is_enabled = excluded.is_enabled,
        updated_at = excluded.updated_at
    """
    conn.execute(sql, (channel_id, channel_name, is_enabled, now_iso, now_iso))
    conn.commit()


def upsert_video(
    conn: sqlite3.Connection,
    video_id: str,
    channel_id: str,
    title: str,
    video_url: str,
    publication_datetime: str,
    discovered_at: str,
    duration_seconds: int | None = None,
    language_hint: str | None = None,
    is_short: int = 0,
    metadata_json: str | None = None,
) -> None:
    sql = """
    INSERT INTO videos (
        video_id, channel_id, title, video_url, publication_datetime, discovered_at,
        duration_seconds, language_hint, is_short, metadata_json
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(video_id) DO UPDATE SET
        channel_id = excluded.channel_id,
        title = excluded.title,
        video_url = excluded.video_url,
        publication_datetime = excluded.publication_datetime,
        discovered_at = excluded.discovered_at,
        duration_seconds = excluded.duration_seconds,
        language_hint = excluded.language_hint,
        is_short = excluded.is_short,
        metadata_json = excluded.metadata_json
    """
    conn.execute(
        sql,
        (
            video_id,
            channel_id,
            title,
            video_url,
            publication_datetime,
            discovered_at,
            duration_seconds,
            language_hint,
            is_short,
            metadata_json,
        ),
    )
    conn.commit()


def transcript_success_exists(conn: sqlite3.Connection, video_id: str) -> bool:
    sql = """
    SELECT 1
    FROM transcripts
    WHERE video_id = ?
      AND status = 'success'
    LIMIT 1
    """
    row = conn.execute(sql, (video_id,)).fetchone()
    return row is not None


def mark_transcript_in_progress(conn: sqlite3.Connection, video_id: str, now_iso: str) -> None:
    sql = """
    INSERT INTO transcripts (
        video_id, transcript_source, status, first_attempt_at, last_attempt_at
    )
    VALUES (?, 'pending', 'in_progress', ?, ?)
    ON CONFLICT(video_id) DO UPDATE SET
        status = 'in_progress',
        last_attempt_at = excluded.last_attempt_at
    """
    conn.execute(sql, (video_id, now_iso, now_iso))
    conn.commit()


def mark_transcript_success(
    conn: sqlite3.Connection,
    video_id: str,
    transcript_path: str,
    transcript_source: str,
    transcript_language: str | None,
    transcript_length_chars: int,
    transcript_hash: str | None,
    completed_at: str,
) -> None:
    sql = """
    UPDATE transcripts
    SET transcript_path = ?,
        transcript_source = ?,
        transcript_language = ?,
        transcript_length_chars = ?,
        transcript_hash = ?,
        status = 'success',
        completed_at = ?,
        last_attempt_at = ?
    WHERE video_id = ?
    """
    conn.execute(
        sql,
        (
            transcript_path,
            transcript_source,
            transcript_language,
            transcript_length_chars,
            transcript_hash,
            completed_at,
            completed_at,
            video_id,
        ),
    )
    conn.commit()


def mark_transcript_failed(conn: sqlite3.Connection, video_id: str, error_message: str, now_iso: str) -> None:
    sql = """
    UPDATE transcripts
    SET status = 'failed',
        error_message = ?,
        last_attempt_at = ?
    WHERE video_id = ?
    """
    conn.execute(sql, (error_message, now_iso, video_id))
    conn.commit()