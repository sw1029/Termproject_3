from pathlib import Path
import json
from ..crawlers.notices import NoticeCrawler

OUT_DIR = Path('data/raw/notices')


def generate_answer(question: str) -> str:
    before_files = {p.name for p in OUT_DIR.glob('*.csv')}
    crawler = NoticeCrawler(OUT_DIR)
    crawler.run()
    after_files = {p.name for p in OUT_DIR.glob('*.csv')}
    new_files = after_files - before_files

    if new_files:
        sample = ', '.join(list(new_files)[:3])
        return f"새로운 공지 파일이 생성되었습니다: {sample} 등"
    return "최근 공지사항 업데이트가 없습니다."
