from pathlib import Path
import csv
import json
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from importlib import util
import sys, types

def _load_notice_crawler():
    pkg = types.ModuleType("crawlers")
    base_dir = Path(__file__).resolve().parent.parent
    base_path = base_dir / "crawlers" / "base.py"
    notice_path = base_dir / "crawlers" / "notices.py"

    base_spec = util.spec_from_file_location("crawlers.base", base_path)
    base_mod = util.module_from_spec(base_spec)
    base_spec.loader.exec_module(base_mod)

    sys.modules.setdefault("crawlers", pkg)
    sys.modules["crawlers.base"] = base_mod

    spec = util.spec_from_file_location("crawlers.notices", notice_path)
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

def _has_update_request(q: str) -> bool:
    keywords = ['변동', '업데이트', '바뀐', '변경']
    return any(k in q for k in keywords)


def _is_specific_request(q: str) -> bool:
    patterns = [r'\d+일', '있는지', '여부', '있나요', '있습니까']
    return any(re.search(p, q) for p in patterns)


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
        names = [r.get('dept', '') for r in records]
        if not names:
            return []
        vec = TfidfVectorizer().fit_transform(names + [dept])
        sims = cosine_similarity(vec[-1], vec[:-1]).flatten()
        scored = [(s, records[i]) for i, s in enumerate(sims)]
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [r for _, r in scored[:3] if _ > 0.1]
        return top

    return _filter(rows)


def generate_answer(question: str) -> str:
    context = get_context(question)
    dept = _parse_dept(question) or ''
    prefix = f"{dept} 최신 공지사항입니다" if dept else "최신 공지사항입니다"
    head = ""
    if _is_specific_request(question):
        head = "죄송하지만 해당 정보는 직접 공지사항을 확인하셔야 합니다.\n"

    if context:
        titles = '\n'.join(f"- {r['title']}" for r in context[:3])
        return f"{head}{prefix}\n{titles}"

    fb = _search_fallback(question)
    if fb:
        return fb
    return f"{head}{prefix}\n공지사항을 찾지 못했습니다."
