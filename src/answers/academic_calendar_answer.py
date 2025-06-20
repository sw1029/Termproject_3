from pathlib import Path
import json
import re
from datetime import datetime, date
from ..crawlers.academic_calendar import AcademicCalendarCrawler
from ..retrieval.rag_pipeline import HybridRetriever
from . import ensure_offline_db
from src.utils.time_parser import TimeParser, is_holiday

OUT_DIR = Path('data/raw/academic_calendar')


def _load_items(path: Path):
    """Return list of events or ``None`` when JSON decoding fails."""
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as f:
        try:
            return json.load(f).get('items', [])
        except json.JSONDecodeError:
            # Invalid JSON indicates an outdated cache. Trigger a recrawl.
            return None


def _parse_year_month_day(q: str):
    parser = TimeParser(q)
    dt, status = parser.parse()
    if status == "failed":
        return None, None, None, status
    if status == "year":
        return dt.year, None, None, status
    if status == "month":
        return dt.year, dt.month, None, status
    return dt.year, dt.month, dt.day, status


def _has_update_request(q: str) -> bool:
    """Return True if question asks about updates or changes."""
    keywords = ["변동", "업데이트", "바뀐", "변경"]
    return any(k in q for k in keywords)


def _search_fallback(question: str) -> str | None:
    """Fallback to FAISS/BM25 search when regex parsing fails."""
    retriever = HybridRetriever()
    docs = retriever.retrieve(question)
    return docs[0] if docs else None


def get_context(question: str) -> tuple[list[dict], tuple[int|None,int|None,int|None], str]:
    """Return matching academic calendar events as context.

    If cached JSON data is missing or corrupted, the crawler will attempt
    to fetch and rebuild the cache before continuing.
    """
    ensure_offline_db()
    year, month, day, status = _parse_year_month_day(question)
    year = year or datetime.now().year
    path = OUT_DIR / str(year) / 'data.json'
    if not path.exists():
        crawler = AcademicCalendarCrawler(OUT_DIR, year)
        crawler.run()
    items = _load_items(path)
    if items is None or not items:
        crawler = AcademicCalendarCrawler(OUT_DIR, year)
        if crawler.run():
            items = _load_items(path) or []
        else:
            items = []

    if _has_update_request(question):
        prev_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in items}
        crawler = AcademicCalendarCrawler(OUT_DIR, year)
        if crawler.run():
            new_items = _load_items(path)
            new_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in new_items}
            diff = [json.loads(s) for s in new_set - prev_set]
            return diff, (year, month, day), "exact"
        return [], (year, month, day), "exact"

    def _filter(records: list[dict]) -> list[dict]:
        if month is None:
            return records
        matched = []
        for it in records:
            if str(month) in str(it.get('month', '')):
                if day is None or str(day) in str(it.get('date', '')):
                    matched.append(it)
        return matched

    matches = _filter(items)
    if not matches:
        crawler = AcademicCalendarCrawler(OUT_DIR, year)
        if crawler.run():
            items = _load_items(path)
            matches = _filter(items)
    return matches, (year, month, day), status


def generate_answer(question: str) -> str:
    context, (year, month, day), status = get_context(question)
    if month and day:
        dt = date(year, month, day)
        if is_holiday(dt):
            return f"{is_holiday(dt)}은 공휴일입니다."

    if not context:
        fb = _search_fallback(question)
        if fb:
            return fb
        return "학사일정 정보를 찾지 못했습니다."

    if status in ("year", "failed"):
        sample = ', '.join(f"{c.get('date')} {c.get('event')}" for c in context[:3])
        return f"학사일정 예시: {sample} 등"

    if status != "exact":
        if year and month and status == "month":
            dt = date(year, month, 1)
        elif year and status == "year":
            dt = date(year, 1, 1)
        else:
            dt = datetime.now().date()
        return f"{dt.strftime('%Y-%m-%d')} 일을 말씀하시는 게 맞을까요?"

    sample = ', '.join(f"{c.get('date')} {c.get('event')}" for c in context[:3])
    return f"학사일정 예시: {sample} 등"
