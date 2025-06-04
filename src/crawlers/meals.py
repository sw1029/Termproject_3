from pathlib import Path
from .base import BaseCrawler

class MealsCrawler(BaseCrawler):
    def fetch(self):
        return ''

    def parse(self, raw):
        return []

if __name__ == '__main__':
    crawler = MealsCrawler(Path('data/raw/meals'))
    crawler.run()
