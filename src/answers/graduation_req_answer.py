from pathlib import Path
from difflib import SequenceMatcher
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


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _find_best_dept(df: pd.DataFrame, query: str) -> str | None:
    """Return department name with highest similarity to ``query``."""
    best_score = 0.0
    best_dept = None
    for name in df["학과명"].dropna().unique():
        score = _similar(query, str(name))
        if score > best_score:
            best_score = score
            best_dept = name
    return best_dept if best_score >= 0.5 else None


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


def generate_answer(question: str) -> str:
    ensure_offline_db()
    year = _parse_year(question)
    dept_q = _parse_dept(question)
    if not dept_q:
        return "어떤 학과의 졸업요건이 궁금한지 다시 입력해주세요."

    target_year = year if year is not None else 2025
    df = _load_year_df(target_year)
    if df.empty:
        return "졸업요건 데이터를 찾지 못했습니다."

    best_dept = _find_best_dept(df, dept_q)
    if best_dept is None:
        return "과 이름을 다시 확인해주세요."

    major_df = df[df["학과명"] == best_dept]
    if major_df.empty:
        return "요청하신 졸업요건 정보를 찾지 못했습니다."

    table = (
        major_df[
            [
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
            ]
        ]
        .set_index("구분")
        .to_string()
    )

    return f"{target_year}학년도 {best_dept} 졸업요건\n{table}"
