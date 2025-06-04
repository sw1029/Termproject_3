from pathlib import Path
from .base import BaseCrawler

class NoticeCrawler(BaseCrawler):
    def fetch(self):
        return ''

    def parse(self, raw):
        return []

if __name__ == '__main__':
    crawler = NoticeCrawler(Path('data/raw/notices'))
    crawler.run()
