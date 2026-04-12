from __future__ import annotations

import subprocess
from pathlib import Path


class FFmpegWhisperTranscriber:
    def __init__(self, config: dict, logger):
        self.config = config
        self.logger = logger
        self.ffmpeg_path = config["transcription"]["ffmpeg_path"]
        self.model_path = config["transcription"]["whisper_model_path"]

    def model_exists(self) -> bool:
        return Path(self.model_path).exists()

    def _ffmpeg_filter_quote_path(self, value: str) -> str:
        # FFmpeg filter args need quoting/escaping inside the filtergraph.
        # 1) normalize slashes
        # 2) escape backslashes and single quotes if present
        # 3) escape drive-letter colon
        # 4) wrap in single quotes so ":" inside the path is not treated as an option separator
        value = value.replace("\\", "/")
        value = value.replace("'", r"\'")
        value = value.replace(":", r"\:")
        return f"'{value}'"

    def transcribe(self, audio_path: str, output_txt_path: str) -> str:
        out_path = Path(output_txt_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        model = self._ffmpeg_filter_quote_path(self.model_path)
        destination = self._ffmpeg_filter_quote_path(str(out_path))

        af = (
            "aformat=sample_rates=16000:channel_layouts=mono,"
            f"whisper=model={model}:destination={destination}:format=text"
        )

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", audio_path,
            "-vn",
            "-af", af,
            "-f", "null",
            "-",
        ]

        self.logger.info("Running ffmpeg whisper transcription")
        cp = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )

        combined = (cp.stdout or "") + "\n" + (cp.stderr or "")
        if cp.returncode != 0:
            self.logger.warning("FFmpeg whisper failed:\n%s", combined)
            return ""

        if out_path.exists():
            transcript = out_path.read_text(encoding="utf-8", errors="ignore").strip()
            return transcript

        self.logger.warning("FFmpeg whisper completed but no transcript file was created")
        return ""