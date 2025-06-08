from datetime import datetime
from .offline_crawl import build_offline_db


def init_db(days: int = 7) -> None:
    """Populate local data cache by running the offline crawler."""
    year = datetime.now().year
    build_offline_db(year - 1, year, days)


if __name__ == "__main__":
    init_db()
