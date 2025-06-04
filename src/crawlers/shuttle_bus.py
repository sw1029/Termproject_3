from pathlib import Path
from .base import BaseCrawler

class ShuttleBusCrawler(BaseCrawler):
    def fetch(self):
        return ''

    def parse(self, raw):
        return []

if __name__ == '__main__':
    crawler = ShuttleBusCrawler(Path('data/raw/shuttle_bus'))
    crawler.run()
