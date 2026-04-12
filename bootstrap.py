import os

FOLDERS = [
    "data/transcripts",
    "data/summaries",
    "data/audio_cache",
    "data/pdf",
    "data/reports/collector",
    "data/reports/summary",
    "data/plots/collector",
    "data/plots/summary",
    "data/logs/collector",
    "data/logs/summary",
    "temp",
    "db"
]

def create_folders():
    for folder in FOLDERS:
        os.makedirs(folder, exist_ok=True)
        print(f"[OK] {folder}")

if __name__ == "__main__":
    create_folders()