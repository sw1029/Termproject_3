from datetime import datetime, timedelta
from pathlib import Path

from .crawlers.academic_calendar import AcademicCalendarCrawler
from .crawlers.meals import MealsCrawler
from .crawlers.shuttle_bus import ShuttleBusCrawler
from .crawlers.graduation_req import GraduationRequirementCrawler
from .crawlers.notices import NoticeCrawler


def build_offline_db(year_start: int, year_end: int, days: int) -> None:
    """Crawl a range of data to populate local cache."""
    for year in range(year_start, year_end + 1):
        AcademicCalendarCrawler(Path("data/raw/academic_calendar"), year).run()
        GraduationRequirementCrawler(Path("data/raw/graduation_req"), year).run()

    for d in range(days):
        date = (datetime.now() - timedelta(days=d)).strftime("%Y%m%d")
        MealsCrawler(Path("data/raw/meals"), date).run()

    NoticeCrawler(Path("data/raw/notices")).run()
    ShuttleBusCrawler(Path("data/raw/shuttle_bus")).run()


if __name__ == "__main__":
    build_offline_db(datetime.now().year - 1, datetime.now().year, 7)

