from pathlib import Path
import io
import pdfplumber
import pandas as pd

from .base import BaseCrawler

class GraduationRequirementCrawler(BaseCrawler):
    PDF_FILE = Path('TODO_dir/graduate/pdf/2024.pdf')

    def fetch(self) -> bytes | None:
        if not self.PDF_FILE.exists():
            return None
        with open(self.PDF_FILE, 'rb') as f:
            return f.read()

    def parse(self, raw: bytes | None):
        if raw is None:
            return pd.DataFrame()
        rows = []
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    rows.extend(table)
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        return df

    def save(self, df: pd.DataFrame) -> None:  # type: ignore[override]
        from datetime import datetime

        self.out_dir.mkdir(parents=True, exist_ok=True)
        if df.empty:
            # create empty file to signal run but keep previous if exists
            path = self.out_dir / 'data.csv'
            if not path.exists():
                df.to_csv(path, index=False, encoding='utf-8-sig')
            return

        df['crawled_at'] = datetime.now().strftime('%Y-%m-%d')
        path = self.out_dir / 'data.csv'
        df.to_csv(path, index=False, encoding='utf-8-sig')

if __name__ == '__main__':
    crawler = GraduationRequirementCrawler(Path('data/raw/graduation_req'))
    crawler.run()
