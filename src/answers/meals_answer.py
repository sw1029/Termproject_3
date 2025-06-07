from pathlib import Path
import json
import re
from datetime import datetime
from importlib import util
import sys, types

def _load_meals_crawler():
    """Dynamically load ``MealsCrawler`` without importing other crawlers."""
    pkg = types.ModuleType('crawlers')
    base_spec = util.spec_from_file_location('crawlers.base', 'src/crawlers/base.py')
    base_mod = util.module_from_spec(base_spec)
    base_spec.loader.exec_module(base_mod)
    sys.modules.setdefault('crawlers', pkg)
    sys.modules['crawlers.base'] = base_mod
    spec = util.spec_from_file_location('crawlers.meals', 'src/crawlers/meals.py')
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.MealsCrawler
from ..retrieval.rag_pipeline import HybridRetriever
from . import ensure_offline_db


def _is_weekend(date_str: str) -> bool:
    dt = datetime.strptime(date_str, "%Y%m%d")
    return dt.weekday() >= 5

OUT_DIR = Path('data/raw/meals')


def _load_items(path: Path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as f:
        try:
            return json.load(f).get('items', [])
        except json.JSONDecodeError:
            return []


def _parse_date(question: str) -> str:
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", question)
    if not m:
        m = re.search(r"(\d{1,2})월(\d{1,2})일", question)
    if m:
        now = datetime.now()
        year = now.year
        month, day = int(m.group(1)), int(m.group(2))
        return f"{year}{month:02d}{day:02d}"
    return datetime.now().strftime('%Y%m%d')


def _parse_meal(question: str):
    if '조식' in question or '아침' in question:
        return '조식'
    if '중식' in question or '점심' in question:
        return '중식'
    if '석식' in question or '저녁' in question:
        return '석식'
    return None


def _parse_cafeteria(question: str):
    m = re.search(r"(\d)\s*학생회관", question)
    if m:
        return int(m.group(1))
    return None


def _has_update_request(q: str) -> bool:
    keywords = ["변동", "업데이트", "바뀐", "변경"]
    return any(k in q for k in keywords)


def _search_fallback(question: str) -> str | None:
    """Fallback to FAISS/BM25 search when regex parsing fails."""
    retriever = HybridRetriever()
    docs = retriever.retrieve(question)
    return docs[0] if docs else None


def generate_answer(question: str) -> str:
    ensure_offline_db()
    date = _parse_date(question)
    path = OUT_DIR / f'{date}.json'
    items = _load_items(path)

    if _is_weekend(date):
        return "주말에는 운영하지 않습니다."

    if _has_update_request(question):
        prev_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in items}
        MealsCrawler = _load_meals_crawler()
        crawler = MealsCrawler(OUT_DIR, date)
        if not crawler.run():
            return "네트워크 오류로 식단 정보를 가져오지 못했습니다."
        new_items = _load_items(path)
        new_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in new_items}
        diff = [json.loads(s) for s in new_set - prev_set]
        if diff:
            sample = ', '.join(d.get('menu', '') for d in diff[:3])
            return f"식단이 업데이트되었습니다: {sample} 등"
        return "최근 식단 변동 사항이 없습니다."

    cafeteria = _parse_cafeteria(question)
    meal_type = _parse_meal(question)

    def _filter(records: list[dict]) -> list[dict]:
        filtered = records
        if cafeteria is not None:
            filtered = [it for it in filtered if it.get('cafeteria') == cafeteria]
        if meal_type is not None:
            filtered = [it for it in filtered if it.get('meal') == meal_type]
        return filtered

    filtered = _filter(items)
    if not filtered or all(it.get('menu') == '운영안함' for it in filtered):
        MealsCrawler = _load_meals_crawler()
        crawler = MealsCrawler(OUT_DIR, date)
        if not crawler.run():
            return "네트워크 오류로 식단 정보를 가져오지 못했습니다."
        items = _load_items(path)
        filtered = _filter(items)
        if not filtered or all(it.get('menu') == '운영안함' for it in filtered):
            # fallback to previous year if future menu is unavailable
            prev_year = str(int(date[:4]) - 1) + date[4:]
            path_prev = OUT_DIR / f'{prev_year}.json'
            MealsCrawler = _load_meals_crawler()
            crawler = MealsCrawler(OUT_DIR, prev_year)
            if crawler.run():
                items = _load_items(path_prev)
                filtered = _filter(items)

    if filtered:
        menus = ', '.join(it.get('menu', '') for it in filtered[:3])
        date_txt = datetime.strptime(date, '%Y%m%d').strftime('%m월 %d일')
        prefix = f"{date_txt}"
        if cafeteria is not None:
            prefix += f" {cafeteria}학생회관"
        if meal_type:
            prefix += f" {meal_type}"
        return f"{prefix} 식단은 {menus} 등입니다."

    if items:
        if all(it.get('menu') == '주말' for it in items):
            return "주말에는 운영하지 않습니다."
        sample = ', '.join(it.get('menu', '') for it in items[:3])
        return f"식단은 {sample} 등입니다."
    fb = _search_fallback(question)
    if fb:
        return fb
    return "식단 정보가 없습니다."
