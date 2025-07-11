from pathlib import Path
from thefuzz import process
import pandas as pd
import re

from ..crawlers.graduation_req import GraduationRequirementCrawler
from . import ensure_offline_db

OUT_DIR = Path("data/raw/graduation_req")


COLS = [
    "대학명",
    "학과명",
    "구분",
    "기초(필수)",
    "균형(인문학)",
    "균형(사회과학)",
    "균형(자연과학)",
    "균형(필수)",
    "소양(선택)",
    "소양(필수)",
    "교양 소계",
    "전공 기초",
    "전공 핵심",
    "전공 심화",
    "전공 소계",
    "일반 선택",
    "졸업 학점(총계)",
    "비고",
    "year",
]


def _parse_year(q: str) -> int | None:
    m = re.search(r"(20\d{2})", q)
    return int(m.group(1)) if m else None


def _parse_dept(q: str) -> str | None:
    m = re.search(r"([\w가-힣]+(?:학과|학부|대학원|대학))", q)
    return m.group(1) if m else None


def _find_best_dept(df: pd.DataFrame, query: str) -> list[str]:
    """Return up to three department names most similar to ``query``."""
    names = df["학과명"].dropna().unique().tolist()
    if not names:
        return []
    results = process.extract(query, names, limit=3)
    return [name for name, score in results if score >= 80]


def _load_year_df(year: int) -> pd.DataFrame:
    """Return cleaned DataFrame for the given year.

    The function first looks for a cached CSV file under ``OUT_DIR``. If the
    file is missing, the PDF for the requested year is parsed and the result is
    cached for future use.
    """
    csv_path = OUT_DIR / f"{year}.csv"
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            df = pd.DataFrame()
    else:
        crawler = GraduationRequirementCrawler(OUT_DIR, year=year)
        try:
            df = crawler.parse(crawler.fetch())
        except FileNotFoundError:
            return pd.DataFrame()
        if not df.empty:
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    if df.empty or len(df.columns) < len(COLS):
        return pd.DataFrame()

    df = df.iloc[3:].reset_index(drop=True)
    df.columns = COLS
    df["대학명"] = df["대학명"].ffill()
    df["학과명"] = df["학과명"].ffill()
    return df


def _has_update_request(q: str) -> bool:
    keywords = ["변동", "업데이트", "바뀐", "변경"]
    return any(k in q for k in keywords)


def _has_detail_request(q: str) -> bool:
    keywords = ["필수", "선택", "과목", "학점", "논문", "세부"]
    return any(k in q for k in keywords)


def _is_credit_request(q: str) -> bool:
    """Return True if the question specifically asks about required credits."""
    keywords = ["학점"]
    return any(k in q for k in keywords)


def get_context(question: str):
    """Return graduation requirement table rows matching the question."""
    ensure_offline_db()
    year = _parse_year(question)
    dept_q = _parse_dept(question)
    if not dept_q:
        return []

    target_year = year if year is not None else 2025
    df = _load_year_df(target_year)
    if df.empty:
        return []

    best_depts = _find_best_dept(df, dept_q)
    if not best_depts:
        return []

    major_df = df[df["학과명"].isin(best_depts)]
    return major_df.to_dict("records")


def generate_answer(question: str) -> str:
    context = get_context(question)
    if not _is_credit_request(question):
        return "졸업 필요 학점 외의 정보는 각 학과에 문의하시길 바랍니다."
    if not context:
        return "졸업요건 정보를 찾지 못했습니다."
    sample = context[0]
    dept = sample.get("학과명", "")
    year = sample.get("year", "")
    prefix = ""
    if _has_detail_request(question):
        prefix = "세부사항은 해당 학과 공지사항을 직접 확인하셔야 합니다.\n"
    return f"{prefix}{year}학년도 {dept} 졸업요건"
