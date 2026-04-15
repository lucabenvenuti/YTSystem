from __future__ import annotations

import shutil
from pathlib import Path


def copy_file_to_share(local_file_path: str, destination_share: str, verify: bool = True) -> str:
    src = Path(local_file_path)
    dst_dir = Path(destination_share)
    dst_dir.mkdir(parents=True, exist_ok=True)

    dst = dst_dir / src.name
    shutil.copy2(src, dst)

    if verify:
        if not dst.exists():
            raise RuntimeError(f"Copied file not found on destination share: {src.name}")
        if src.stat().st_size != dst.stat().st_size:
            raise RuntimeError(f"Copied file size does not match source file: {src.name}")

    return str(dst)


def copy_pdf_to_share(local_pdf_path: str, destination_share: str, verify: bool = True) -> str:
    return copy_file_to_share(local_pdf_path, destination_share, verify=verify)
