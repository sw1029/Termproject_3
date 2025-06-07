from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..offline_crawl import build_offline_db


def ensure_offline_db(days: int = 7) -> None:
    """Run offline crawler when ``data/raw`` is empty."""
    root = Path("data/raw")
    # treat a directory with only ``.gitkeep`` as empty
    def _has_files(path: Path) -> bool:
        for p in path.rglob("*"):
            if p.is_file() and p.name != ".gitkeep":
                return True
        return False

    if not root.exists() or not _has_files(root):
        year = datetime.now().year
        build_offline_db(year - 1, year, days)
