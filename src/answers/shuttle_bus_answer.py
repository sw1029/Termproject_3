from pathlib import Path
import json
from ..crawlers.shuttle_bus import ShuttleBusCrawler
from ..retrieval.rag_pipeline import HybridRetriever

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


def generate_answer(question: str) -> str:
    path = OUT_DIR / 'data.json'
    items = _load_items(path)

    if _has_update_request(question):
        prev_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in items}
        crawler = ShuttleBusCrawler(OUT_DIR)
        if not crawler.run():
            return "네트워크 오류로 셔틀버스 정보를 가져오지 못했습니다."
        new_items = _load_items(path)
        new_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in new_items}
        diff = [json.loads(s) for s in new_set - prev_set]
        if diff:
            route_diff = [d for d in diff if d.get('type') == 'route']
            sched_diff = [d for d in diff if d.get('type') == 'schedule']
            parts = []
            if route_diff:
                sample = '; '.join(' '.join(r.get('row', [])) for r in route_diff[:3])
                parts.append(f"노선 {len(route_diff)}건({sample})")
            if sched_diff:
                sample = '; '.join(' '.join(r.get('row', [])) for r in sched_diff[:3])
                parts.append(f"시간표 {len(sched_diff)}건({sample})")
            msg = '; '.join(parts)
            return f"셔틀버스 정보가 업데이트되었습니다: {msg} 등"
        return "변경된 셔틀버스 정보가 없습니다."
    bus_type = _parse_type(question)

    def _filter(records: list[dict]) -> list[dict]:
        if bus_type:
            return [it for it in records if it.get('type') == bus_type]
        return records

    filtered = _filter(items)
    if not filtered:
        crawler = ShuttleBusCrawler(OUT_DIR)
        if not crawler.run():
            return "네트워크 오류로 셔틀버스 정보를 가져오지 못했습니다."
        items = _load_items(path)
        filtered = _filter(items)
    if filtered:
        sample = '; '.join(' '.join(it.get('row', [])) for it in filtered[:3])
        prefix = '셔틀버스'
        if bus_type == 'route':
            prefix += ' 노선'
        elif bus_type == 'schedule':
            prefix += ' 시간표'
        return f"{prefix}는 {sample} 등입니다."

    if items:
        return "셔틀버스 정보가 있지만 요청 조건과 일치하는 항목이 없습니다."
    fb = _search_fallback(question)
    if fb:
        return fb
    return "요청하신 셔틀버스 정보를 찾지 못했습니다."
