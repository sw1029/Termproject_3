from pathlib import Path
from datetime import datetime
import io
import re
import pdfplumber
import pandas as pd

from .base import BaseCrawler


class GraduationRequirementCrawler(BaseCrawler):
    """Parse graduation requirement PDFs located under ``data/pdf/``."""

    PDF_DIR = Path("data/pdf")

    def __init__(self, out_dir: Path, year: int | None = None):
        super().__init__(out_dir)
        self.year = year

    def _select_pdf(self) -> Path:
        if self.year is not None:
            return self.PDF_DIR / f"{self.year}.pdf"
        candidates = sorted(self.PDF_DIR.glob("*.pdf"))
        if not candidates:
            raise FileNotFoundError(str(self.PDF_DIR))
        return candidates[-1]

    def fetch(self) -> bytes:
        pdf_path = self._select_pdf()
        if not pdf_path.exists():
            raise FileNotFoundError(str(pdf_path))
        with open(pdf_path, "rb") as f:
            return f.read()

    def parse(self, raw: bytes | None):
        if raw is None:
            return pd.DataFrame()

        rows: list[list[str | None]] = []
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    rows.extend(table)
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        # try to infer year from selected file name
        if self.year is not None:
            yr = self.year
        else:
            match = re.search(r"(\d{4})", self._select_pdf().stem)
            yr = int(match.group(1)) if match else datetime.now().year
        df['year'] = yr
        return df

    def save(self, df: pd.DataFrame) -> None:  # type: ignore[override]
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
