from pathlib import Path
import csv
import json
import re
from ..crawlers.notices import NoticeCrawler
from ..retrieval.rag_pipeline import HybridRetriever

OUT_DIR = Path('data/raw/notices')


def _load_rows() -> list[dict]:
    rows: list[dict] = []
    for path in OUT_DIR.glob('*.csv'):
        with path.open(encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows.extend(list(reader))
    return rows


def _parse_dept(q: str) -> str | None:
    m = re.search(r'([\w가-힣]+(?:학과|학부|대학원|대학))', q)
    return m.group(1) if m else None


def _has_update_request(q: str) -> bool:
    keywords = ['변동', '업데이트', '바뀐', '변경']
    return any(k in q for k in keywords)


def _search_fallback(question: str) -> str | None:
    retriever = HybridRetriever()
    docs = retriever.retrieve(question)
    return docs[0] if docs else None


def generate_answer(question: str) -> str:
    rows = _load_rows()

    if _has_update_request(question):
        prev_set = {json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows}
        crawler = NoticeCrawler(OUT_DIR)
        crawler.run()
        new_rows = _load_rows()
        new_set = {json.dumps(r, ensure_ascii=False, sort_keys=True) for r in new_rows}
        diff = [json.loads(s) for s in new_set - prev_set]
        if diff:
            sample = ', '.join(d['title'] for d in diff[:3])
            return f"새로운 공지가 업데이트되었습니다: {sample} 등"
        return "최근 공지사항 업데이트가 없습니다."

    dept = _parse_dept(question)

    def _filter(records: list[dict]) -> list[dict]:
        if not dept:
            return records
        return [r for r in records if dept in r.get('dept', '') or dept in r.get('college', '') or dept in r.get('title', '')]

    filtered = _filter(rows)
    if not filtered:
        crawler = NoticeCrawler(OUT_DIR)
        crawler.run()
        rows = _load_rows()
        filtered = _filter(rows)

    if filtered:
        sample = ', '.join(r['title'] for r in filtered[:3])
        prefix = dept if dept else '최근 공지'
        return f"{prefix} 목록: {sample} 등"

    fb = _search_fallback(question)
    if fb:
        return fb
    return "요청하신 공지사항을 찾지 못했습니다."
