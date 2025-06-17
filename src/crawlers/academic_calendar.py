from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from ..utils.config import settings

from .base import BaseCrawler

class AcademicCalendarCrawler(BaseCrawler):
    BASE_URL = 'https://plus.cnu.ac.kr/_prog/academic_calendar/'

    def __init__(self, out_dir: Path, year: int | None = None):
        self.year = year or datetime.now().year
        out_dir = Path(out_dir) / str(self.year)
        super().__init__(out_dir)

    def fetch(self) -> str:
        params = {
            'site_dvs_cd': 'kr',
            'menu_dvs_cd': '05020101',
            'year': str(self.year),
        }
        resp = requests.get(self.BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return resp.text

    def parse(self, raw: str):
        soup = BeautifulSoup(raw, 'html.parser')
        results = []
        for box in soup.select('div.calen_box'):
            month_kor = box.select_one('div.fl_month strong')
            if not month_kor:
                continue
            month_txt = month_kor.get_text(strip=True)
            for li in box.select('div.fr_list li'):
                date_text = li.select_one('strong').get_text(strip=True)
                desc = li.select_one('span.list').get_text(strip=True)
                results.append({'month': month_txt, 'date': date_text, 'event': desc})
        return results

if __name__ == '__main__':
    crawler = AcademicCalendarCrawler(settings.data_dir / 'raw/academic_calendar')
    crawler.run()
