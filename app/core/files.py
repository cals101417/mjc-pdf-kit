"""Small file helpers: safe output names and human-readable sizes."""

from __future__ import annotations

from pathlib import Path


def unique_path(folder: Path, stem: str, suffix: str = ".pdf") -> Path:
    """Return folder/stem.pdf, or stem (2).pdf, stem (3).pdf... so nothing is overwritten."""
    folder = Path(folder)
    candidate = folder / f"{stem}{suffix}"
    n = 2
    while candidate.exists():
        candidate = folder / f"{stem} ({n}){suffix}"
        n += 1
    return candidate


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"
