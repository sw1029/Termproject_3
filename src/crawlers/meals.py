from pathlib import Path
from datetime import datetime
import requests
from lxml import html

from .base import BaseCrawler

class MealsCrawler(BaseCrawler):
    BASE_URL = 'https://mobileadmin.cnu.ac.kr/food/index.jsp'

    def __init__(self, out_dir: Path, date: str | None = None):
        super().__init__(out_dir)
        self.date = date or datetime.now().strftime('%Y%m%d')

    def fetch(self) -> str:
        d = datetime.strptime(self.date, '%Y%m%d').strftime('%Y.%m.%d')
        params = {
            'searchYmd': d,
            'searchLang': 'OCL04.10',
            'searchView': 'cafeteria',
            'searchCafeteria': 'OCL03.02',
            'Language_gb': 'OCL04.10#tmp',
        }
        resp = requests.get(self.BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.text

    def parse(self, raw: str):
        tree = html.fromstring(raw)
        table = tree.xpath("//table[contains(@class,'menu-tbl')]")
        if not table:
            return []
        table = table[0]
        rows = table.xpath('./tbody/tr')
        mapping = [
            ('조식', '직원'), ('조식', '학생'),
            ('중식', '직원'), ('중식', '학생'),
            ('석식', '직원'), ('석식', '학생'),
        ]
        results = []
        for idx, row in enumerate(rows):
            meal, who = mapping[idx] if idx < len(mapping) else (None, None)
            tds = row.xpath('./td')
            first_cls = tds[0].get('class', '')
            offset = 2 if 'building' in first_cls else 1
            for caf_idx, cell in enumerate(tds[offset:], start=1):
                menu = cell.text_content().strip()
                results.append({
                    'meal': meal,
                    'who': who,
                    'cafeteria': caf_idx + 1,
                    'menu': menu or '운영안함'
                })
        return results

if __name__ == '__main__':
    crawler = MealsCrawler(Path('data/raw/meals'))
    crawler.run()
