PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS channels (
    channel_id TEXT PRIMARY KEY,
    channel_name TEXT NOT NULL,
    is_enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL,
    title TEXT NOT NULL,
    video_url TEXT NOT NULL,
    publication_datetime TEXT NOT NULL,
    discovered_at TEXT NOT NULL,
    duration_seconds INTEGER,
    language_hint TEXT,
    is_short INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT,
    FOREIGN KEY (channel_id) REFERENCES channels(channel_id)
);

CREATE TABLE IF NOT EXISTS transcripts (
    transcript_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL UNIQUE,
    transcript_path TEXT,
    transcript_source TEXT NOT NULL,
    transcript_language TEXT,
    transcript_length_chars INTEGER,
    transcript_hash TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    first_attempt_at TEXT,
    last_attempt_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

CREATE TABLE IF NOT EXISTS summaries (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL UNIQUE,
    transcript_id INTEGER NOT NULL,
    summary_path TEXT,
    summary_language TEXT,
    model_name TEXT,
    prompt_version TEXT,
    summary_hash TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    first_attempt_at TEXT,
    last_attempt_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (video_id) REFERENCES videos(video_id),
    FOREIGN KEY (transcript_id) REFERENCES transcripts(transcript_id)
);

CREATE TABLE IF NOT EXISTS pdf_batches (
    batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_date TEXT NOT NULL,
    local_pdf_path TEXT,
    target_pdf_path TEXT,
    file_name TEXT,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    copied_at TEXT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS pdf_batch_items (
    batch_id INTEGER NOT NULL,
    video_id TEXT NOT NULL,
    summary_id INTEGER NOT NULL,
    included_at TEXT NOT NULL,
    PRIMARY KEY (batch_id, video_id),
    FOREIGN KEY (batch_id) REFERENCES pdf_batches(batch_id),
    FOREIGN KEY (video_id) REFERENCES videos(video_id),
    FOREIGN KEY (summary_id) REFERENCES summaries(summary_id)
);

CREATE TABLE IF NOT EXISTS app_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    time_window_start TEXT NOT NULL,
    time_window_end TEXT NOT NULL,
    total_candidates INTEGER NOT NULL DEFAULT 0,
    completed_items INTEGER NOT NULL DEFAULT 0,
    skipped_items INTEGER NOT NULL DEFAULT 0,
    failed_items INTEGER NOT NULL DEFAULT 0,
    interrupted_items INTEGER NOT NULL DEFAULT 0,
    remaining_items INTEGER NOT NULL DEFAULT 0,
    report_path TEXT,
    plot_path TEXT,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_videos_channel_id
ON videos(channel_id);

CREATE INDEX IF NOT EXISTS idx_videos_publication_datetime
ON videos(publication_datetime);

CREATE INDEX IF NOT EXISTS idx_transcripts_status
ON transcripts(status);

CREATE INDEX IF NOT EXISTS idx_summaries_status
ON summaries(status);

CREATE INDEX IF NOT EXISTS idx_app_runs_app_name_started_at
ON app_runs(app_name, started_at);

CREATE INDEX IF NOT EXISTS idx_pdf_batches_batch_date
ON pdf_batches(batch_date);