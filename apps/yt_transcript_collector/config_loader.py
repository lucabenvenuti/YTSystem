from __future__ import annotations

from pathlib import Path
import yaml


def load_yaml(path: str | Path) -> dict:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def load_config(config_path: str | Path) -> dict:
    return load_yaml(config_path)


def load_channels(channels_path: str | Path) -> list[dict]:
    data = load_yaml(channels_path)
    return data.get("channels", [])