from pathlib import Path
import json
from ..crawlers.shuttle_bus import ShuttleBusCrawler
from ..retrieval.rag_pipeline import HybridRetriever
from . import ensure_offline_db

OUT_DIR = Path('data/raw/shuttle_bus')


def _load_items(path: Path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as f:
        try:
            return json.load(f).get('items', [])
        except json.JSONDecodeError:
            return []


def _parse_type(q: str) -> str | None:
    if '노선' in q:
        return 'route'
    if '시간표' in q or '운행' in q or '시간' in q:
        return 'schedule'
    return None


def _has_update_request(q: str) -> bool:
    keywords = ['변동', '업데이트', '바뀐', '변경']
    return any(k in q for k in keywords)


def _search_fallback(question: str) -> str | None:
    retriever = HybridRetriever()
    docs = retriever.retrieve(question)
    return docs[0] if docs else None


def get_context(question: str) -> list[dict]:
    """Return shuttle bus info records as context."""
    ensure_offline_db()
    path = OUT_DIR / 'data.json'
    items = _load_items(path)

    if _has_update_request(question):
        prev_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in items}
        crawler = ShuttleBusCrawler(OUT_DIR)
        if crawler.run():
            new_items = _load_items(path)
            new_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in new_items}
            diff = [json.loads(s) for s in new_set - prev_set]
            return diff
        return []

    bus_type = _parse_type(question)

    def _filter(records: list[dict]) -> list[dict]:
        if bus_type:
            return [it for it in records if it.get('type') == bus_type]
        return records

    filtered = _filter(items)
    if not filtered:
        crawler = ShuttleBusCrawler(OUT_DIR)
        if crawler.run():
            items = _load_items(path)
            filtered = _filter(items)
    return filtered


def generate_answer(question: str) -> str:
    context = get_context(question)
    if not context:
        fb = _search_fallback(question)
        if fb:
            return fb
        return "요청하신 셔틀버스 정보를 찾지 못했습니다."
    sample = '; '.join(' '.join(it.get('row', [])) for it in context[:3])
    return f"셔틀버스 정보 예시: {sample} 등"
