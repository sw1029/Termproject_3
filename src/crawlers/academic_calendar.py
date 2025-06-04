from pathlib import Path
from .base import BaseCrawler

class AcademicCalendarCrawler(BaseCrawler):
    def fetch(self):
        # TODO: implement actual fetching logic
        return ''

    def parse(self, raw):
        # TODO: parse calendar HTML/PDF
        return []

if __name__ == '__main__':
    crawler = AcademicCalendarCrawler(Path('data/raw/academic_calendar'))
    crawler.run()
