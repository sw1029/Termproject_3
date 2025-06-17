from pathlib import Path
import requests
from bs4 import BeautifulSoup

from ..utils.config import settings

from .base import BaseCrawler

class ShuttleBusCrawler(BaseCrawler):
    URL = 'https://plus.cnu.ac.kr/html/kr/sub05/sub05_050403.html'

    def fetch(self) -> str:
        resp = requests.get(self.URL, timeout=10)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or 'utf-8'
        return resp.text

    def parse(self, raw: str):
        soup = BeautifulSoup(raw, 'html.parser')
        tables = soup.select('table.content_table')
        results = []
        if tables:
            schedule = tables[0]
            for row in schedule.select('tbody tr'):
                cells = [c.get_text(' ', strip=True) for c in row.find_all('td')]
                if cells:
                    results.append({'type': 'schedule', 'row': cells})
        if len(tables) > 1:
            routes = tables[1]
            for row in routes.select('tbody tr'):
                cells = [c.get_text(' ', strip=True) for c in row.find_all(['th', 'td'])]
                if cells:
                    results.append({'type': 'route', 'row': cells})
        return results

if __name__ == '__main__':
    crawler = ShuttleBusCrawler(settings.data_dir / 'raw/shuttle_bus')
    crawler.run()
