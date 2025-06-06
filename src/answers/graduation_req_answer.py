from pathlib import Path
import json
from ..crawlers.graduation_req import GraduationRequirementCrawler

OUT_DIR = Path('data/raw/graduation_req')


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
    crawler = GraduationRequirementCrawler(OUT_DIR)
    crawler.run()
    new_items = _load_items(prev_path)

    prev_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in prev_items}
    new_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in new_items}
    diff = [json.loads(s) for s in new_set - prev_set]

    if diff:
        return f"졸업요건 정보가 {len(diff)}건 업데이트되었습니다."
    return "새로운 졸업요건 변경 사항이 없습니다."
