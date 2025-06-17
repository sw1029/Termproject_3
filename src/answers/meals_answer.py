from pathlib import Path
import json
import re
from datetime import datetime, timedelta
from importlib import util
import sys, types

from src.utils.logger import get_logger
from src.utils.time_parser import TimeParser, is_holiday
from src.utils.config import settings

logger = get_logger(__name__)

def _load_meals_crawler():
    """Dynamically load ``MealsCrawler`` without importing other crawlers."""
    # Use fully qualified package names so that relative imports inside the
    # crawler modules work correctly when loaded dynamically.
    pkg = types.ModuleType("src.crawlers")
    base_dir = Path(__file__).resolve().parent.parent
    base_path = base_dir / "crawlers" / "base.py"
    meals_path = base_dir / "crawlers" / "meals.py"

    base_spec = util.spec_from_file_location("src.crawlers.base", base_path)
    base_mod = util.module_from_spec(base_spec)
    base_spec.loader.exec_module(base_mod)

    sys.modules.setdefault("src.crawlers", pkg)
    sys.modules["src.crawlers.base"] = base_mod

    spec = util.spec_from_file_location("src.crawlers.meals", meals_path)
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.MealsCrawler
from ..retrieval.rag_pipeline import HybridRetriever
from . import ensure_offline_db


def _is_weekend(date_str: str) -> bool:
    dt = datetime.strptime(date_str, "%Y%m%d")
    return dt.weekday() >= 5

OUT_DIR = settings.data_dir / 'raw/meals'


def _load_items(path: Path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as f:
        try:
            return json.load(f).get('items', [])
        except json.JSONDecodeError:
            return []


def _parse_date(question: str) -> tuple[str, bool]:
    parser = TimeParser(question)
    dt, status = parser.parse()
    return dt.strftime("%Y%m%d"), status == "exact"


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


def get_context(question: str) -> tuple[list[dict], str, bool]:
    """Return filtered meal records as context, parsed date string and accuracy."""
    ensure_offline_db()
    date, exact = _parse_date(question)
    path = OUT_DIR / f"{date}.json"
    prev_items = _load_items(path)

    if not path.exists():
        logger.info("'%s' 날짜의 식단 정보가 로컬에 없어 새로 수집합니다.", date)
        MealsCrawler = _load_meals_crawler()
        crawler = MealsCrawler(OUT_DIR, date)
        crawler.run()
    else:
        logger.info("'%s' 날짜의 로컬 식단 정보를 사용합니다.", date)

    items = _load_items(path)

    if _is_weekend(date):
        return [{"message": "주말에는 운영하지 않습니다."}]

    if _has_update_request(question):
        prev_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in prev_items}
        new_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in items}
        diff = [json.loads(s) for s in new_set - prev_set]
        return diff

    cafeteria = _parse_cafeteria(question)
    meal_type = _parse_meal(question)

    def _filter(records: list[dict]) -> list[dict]:
        filtered = records
        if cafeteria is not None:
            filtered = [it for it in filtered if it.get("cafeteria") == cafeteria]
        if meal_type is not None:
            filtered = [it for it in filtered if it.get("meal") == meal_type]
        return filtered

    filtered = _filter(items)
    if not filtered or all(it.get("menu") == "운영안함" for it in filtered):
        prev_year = str(int(date[:4]) - 1) + date[4:]
        path_prev = OUT_DIR / f"{prev_year}.json"
        if not path_prev.exists():
            MealsCrawler = _load_meals_crawler()
            crawler = MealsCrawler(OUT_DIR, prev_year)
            crawler.run()
        items = _load_items(path_prev)
        filtered = _filter(items)
    return filtered, date, exact


def generate_answer(question: str) -> str:
    context, date, exact = get_context(question)
    if is_holiday(datetime.strptime(date, "%Y%m%d").date()):
        holiday = is_holiday(datetime.strptime(date, "%Y%m%d").date())
        return f"{holiday}은 공휴일입니다."

    if not context:
        fb = _search_fallback(question)
        if fb:
            return fb
        return "식단 정보가 없습니다."

    if not exact:
        dt = datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d")
        return f"{dt} 일을 말씀하시는 게 맞을까요?"

    menus = ', '.join(it.get('menu', '') for it in context[:3])
    return f"찾은 식단 정보: {menus} 등"
