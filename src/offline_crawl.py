from datetime import datetime, timedelta
from pathlib import Path

from .utils.config import settings

from .crawlers.academic_calendar import AcademicCalendarCrawler
from .crawlers.meals import MealsCrawler
from .crawlers.shuttle_bus import ShuttleBusCrawler
from .crawlers.graduation_req import GraduationRequirementCrawler
from .crawlers.notices import NoticeCrawler


def build_offline_db(year_start: int, year_end: int, days: int) -> None:
    """Crawl a range of data to populate local cache."""
    data_root = settings.data_dir / "raw"

    for year in range(year_start, year_end + 1):
        AcademicCalendarCrawler(data_root / "academic_calendar", year).run()
        GraduationRequirementCrawler(data_root / "graduation_req", year).run()

    for d in range(days):
        date = (datetime.now() - timedelta(days=d)).strftime("%Y%m%d")
        MealsCrawler(data_root / "meals", date).run()

    NoticeCrawler(data_root / "notices").run()
    ShuttleBusCrawler(data_root / "shuttle_bus").run()


if __name__ == "__main__":
    build_offline_db(datetime.now().year - 1, datetime.now().year, 7)

