from pathlib import Path
from .base import BaseCrawler

class GraduationRequirementCrawler(BaseCrawler):
    def fetch(self):
        return ''

    def parse(self, raw):
        return []

if __name__ == '__main__':
    crawler = GraduationRequirementCrawler(Path('data/raw/graduation_req'))
    crawler.run()
