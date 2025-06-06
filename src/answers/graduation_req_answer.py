from pathlib import Path
import pandas as pd
import re
from difflib import SequenceMatcher

from ..crawlers.graduation_req import GraduationRequirementCrawler

OUT_DIR = Path('data/raw/graduation_req')


def _load_df() -> pd.DataFrame:
    path = OUT_DIR / 'data.csv'
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _parse_dept(q: str) -> str | None:
    m = re.search(r'([\w가-힣]+(?:학과|학부|대학원|대학))', q)
    return m.group(1) if m else None


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _has_update_request(q: str) -> bool:
    keywords = ['변동', '업데이트', '바뀐', '변경']
    return any(k in q for k in keywords)


def generate_answer(question: str) -> str:
    prev_df = _load_df()
    if _has_update_request(question):
        crawler = GraduationRequirementCrawler(OUT_DIR)
        try:
            crawler.run()
        except FileNotFoundError:
            return '졸업요건 원본 파일이 없습니다.'
        new_df = _load_df()
        if prev_df.empty and new_df.empty:
            return '졸업요건 데이터를 찾지 못했습니다.'
        if prev_df.equals(new_df):
            return '새로운 졸업요건 변경 사항이 없습니다.'
        diff_rows = len(new_df.drop_duplicates().merge(prev_df.drop_duplicates(), how='outer', indicator=True).query("_merge=='left_only'"))
        if diff_rows:
            return f'졸업요건 정보가 {diff_rows}건 업데이트되었습니다.'
        return '새로운 졸업요건 변경 사항이 없습니다.'

    dept = _parse_dept(question)
    df = prev_df
    if df.empty:
        crawler = GraduationRequirementCrawler(OUT_DIR)
        try:
            crawler.run()
        except FileNotFoundError:
            return '졸업요건 원본 파일이 없습니다.'
        df = _load_df()
    if dept and not df.empty:
        best_score = 0.0
        best_row = None
        for _, row in df.iterrows():
            for cell in row.astype(str):
                score = _similar(dept, str(cell))
                if score > best_score:
                    best_score = score
                    best_row = row
        if best_row is not None and best_score >= 0.5:
            sample = ' '.join(str(c) for c in best_row.dropna().astype(str).tolist()[:3])
            return f'{dept} 관련 졸업요건 정보: {sample} ...'
    return '요청하신 졸업요건 정보를 찾지 못했습니다.'
