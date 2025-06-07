from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterable
import requests

class BaseCrawler(ABC):
    """Abstract base class for all crawlers."""

    def __init__(self, out_dir: Path):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def fetch(self) -> Any:
        """Retrieve raw data (HTML, CSV, etc.)"""

    @abstractmethod
    def parse(self, raw: Any) -> Iterable[dict]:
        """Parse raw data into structured records."""

    def save(self, items: Iterable[dict]) -> None:
        """Save items to ``data.json`` with crawl timestamp."""
        from datetime import datetime
        import json

        path = self.out_dir / 'data.json'
        payload = {
            'crawled_at': datetime.now().strftime('%Y-%m-%d'),
            'items': list(items),
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    def run(self) -> bool:
        """Fetch, parse and save records.

        Returns ``True`` when network calls succeed, ``False`` otherwise."""
        try:
            raw = self.fetch()
        except requests.RequestException:
            return False
        records = self.parse(raw)
        self.save(records)
        return True
