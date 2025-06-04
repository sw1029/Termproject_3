from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterable

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
        path = self.out_dir / 'data.json'
        import json
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(list(items), f, ensure_ascii=False, indent=2)

    def run(self) -> None:
        raw = self.fetch()
        records = self.parse(raw)
        self.save(records)
