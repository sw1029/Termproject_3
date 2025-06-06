from pathlib import Path
import json
import re
from datetime import datetime
from ..crawlers.academic_calendar import AcademicCalendarCrawler
from ..retrieval.rag_pipeline import HybridRetriever

OUT_DIR = Path('data/raw/academic_calendar')


def _load_items(path: Path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as f:
        try:
            return json.load(f).get('items', [])
        except json.JSONDecodeError:
            return []


def _parse_month_day(q: str):
    """Extract month and day from question if present."""
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", q)
    if not m:
        m = re.search(r"(\d{1,2})월(\d{1,2})일", q)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d{1,2})\s*월", q)
    if m:
        return int(m.group(1)), None
    return None, None


def _has_update_request(q: str) -> bool:
    """Return True if question asks about updates or changes."""
    keywords = ["변동", "업데이트", "바뀐", "변경"]
    return any(k in q for k in keywords)


def _search_fallback(question: str) -> str | None:
    """Fallback to FAISS/BM25 search when regex parsing fails."""
    retriever = HybridRetriever()
    docs = retriever.retrieve(question)
    return docs[0] if docs else None


def generate_answer(question: str) -> str:
    path = OUT_DIR / 'data.json'
    items = _load_items(path)

    if _has_update_request(question):
        prev_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in items}
        crawler = AcademicCalendarCrawler(OUT_DIR)
        crawler.run()
        new_items = _load_items(path)
        new_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in new_items}
        diff = [json.loads(s) for s in new_set - prev_set]
        if diff:
            events = ', '.join(f"{d['month']} {d['date']} {d['event']}" for d in diff[:3])
            return f"새로운 학사일정이 업데이트되었습니다: {events} 등"
        return "최근 학사일정 변동 사항이 없습니다."

    month, day = _parse_month_day(question)

    def _filter(records: list[dict]) -> list[str]:
        if month is None:
            return []
        matched = []
        for it in records:
            if str(month) in str(it.get('month', '')):
                if day is None or str(day) in str(it.get('date', '')):
                    matched.append(f"{it['date']} {it['event']}")
        return matched

    matches = _filter(items)
    if not matches:
        crawler = AcademicCalendarCrawler(OUT_DIR)
        crawler.run()
        items = _load_items(path)
        matches = _filter(items)

    if matches:
        pre = f"{month}월"
        if day is not None:
            pre += f" {day}일"
        sample = ', '.join(matches[:3])
        return f"{pre} 학사일정은 {sample} 등입니다."

    fb = _search_fallback(question)
    if fb:
        return fb
    return f"{month}월 {day or ''} 학사일정 정보가 없습니다.".strip()
