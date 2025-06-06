from pathlib import Path
import io
import pdfplumber

from .base import BaseCrawler

class GraduationRequirementCrawler(BaseCrawler):
    PDF_FILE = Path('TODO_dir/graduate/pdf/2024.pdf')

    def fetch(self) -> bytes:
        with open(self.PDF_FILE, 'rb') as f:
            return f.read()

    def parse(self, raw: bytes):
        rows = []
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    for row in table:
                        rows.append({'row': row})
        return rows

if __name__ == '__main__':
    crawler = GraduationRequirementCrawler(Path('data/raw/graduation_req'))
    crawler.run()
