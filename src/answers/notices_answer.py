from pathlib import Path
import csv
import json
import re
from difflib import SequenceMatcher

from importlib import util
import sys, types

def _load_notice_crawler():
    pkg = types.ModuleType('crawlers')
    base_spec = util.spec_from_file_location('crawlers.base', 'src/crawlers/base.py')
    base_mod = util.module_from_spec(base_spec)
    base_spec.loader.exec_module(base_mod)
    sys.modules.setdefault('crawlers', pkg)
    sys.modules['crawlers.base'] = base_mod
    spec = util.spec_from_file_location('crawlers.notices', 'src/crawlers/notices.py')
    mod = util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.NoticeCrawler
from ..retrieval.rag_pipeline import HybridRetriever
from . import ensure_offline_db

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


def _similar(a: str, b: str) -> float:
    """Return a similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def _has_update_request(q: str) -> bool:
    keywords = ['변동', '업데이트', '바뀐', '변경']
    return any(k in q for k in keywords)


def _search_fallback(question: str) -> str | None:
    retriever = HybridRetriever()
    docs = retriever.retrieve(question)
    return docs[0] if docs else None


def get_context(question: str) -> list[dict]:
    """Return notice rows related to the question."""
    ensure_offline_db()
    prev_rows = _load_rows()
    NoticeCrawler = _load_notice_crawler()
    crawler = NoticeCrawler(OUT_DIR)
    crawler.run()
    rows = _load_rows()

    if _has_update_request(question):
        prev_set = {json.dumps(r, ensure_ascii=False, sort_keys=True) for r in prev_rows}
        new_set = {json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows}
        diff = [json.loads(s) for s in new_set - prev_set]
        return diff

    dept = _parse_dept(question)

    def _filter(records: list[dict]) -> list[dict]:
        if not dept:
            return records
        scored: list[tuple[float, dict]] = []
        for r in records:
            candidates = [r.get('dept', ''), r.get('college', ''), r.get('title', '')]
            score = max(_similar(dept, c) for c in candidates)
            if score >= 0.5:
                scored.append((score, r))
        if not scored:
            return []
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored]

    return _filter(rows)


def generate_answer(question: str) -> str:
    context = get_context(question)
    if context:
        sample = ', '.join(r['title'] for r in context[:3])
        return f"공지 예시: {sample} 등"
    fb = _search_fallback(question)
    if fb:
        return fb
    return "요청하신 공지사항을 찾지 못했습니다."
