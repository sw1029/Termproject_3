from pathlib import Path
import json
from datetime import datetime
from ..crawlers.academic_calendar import AcademicCalendarCrawler

OUT_DIR = Path('data/raw/academic_calendar')


def _load_items(path: Path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as f:
        try:
            return json.load(f).get('items', [])
        except json.JSONDecodeError:
            return []


def generate_answer(question: str) -> str:
    prev_path = OUT_DIR / 'data.json'
    prev_items = _load_items(prev_path)
    crawler = AcademicCalendarCrawler(OUT_DIR)
    crawler.run()
    new_items = _load_items(prev_path)

    prev_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in prev_items}
    new_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in new_items}
    diff = [json.loads(s) for s in new_set - prev_set]

    if diff:
        events = ', '.join(f"{d['month']} {d['date']} {d['event']}" for d in diff[:3])
        return f"새로운 학사일정이 업데이트되었습니다: {events} 등"
    return "최근 학사일정 변동 사항이 없습니다."
