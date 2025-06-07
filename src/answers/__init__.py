from __future__ import annotations

from datetime import datetime
from pathlib import Path

from importlib import import_module


def ensure_offline_db(days: int = 7) -> None:
    """Run offline crawler when ``data/raw`` is empty."""
    root = Path("data/raw")
    if not root.exists() or not any(root.iterdir()):
        year = datetime.now().year
        build_offline_db = import_module("src.offline_crawl").build_offline_db
        build_offline_db(year - 1, year, days)
