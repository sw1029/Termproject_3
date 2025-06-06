from pathlib import Path
import json
from datetime import datetime
from ..crawlers.meals import MealsCrawler

OUT_DIR = Path('data/raw/meals')


def _load_items(path: Path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as f:
        try:
            return json.load(f).get('items', [])
        except json.JSONDecodeError:
            return []


def generate_answer(question: str) -> str:
    date = datetime.now().strftime('%Y%m%d')
    path = OUT_DIR / f'{date}.json'
    prev_items = _load_items(path)
    crawler = MealsCrawler(OUT_DIR)
    crawler.run()
    new_items = _load_items(path)

    prev_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in prev_items}
    new_set = {json.dumps(it, ensure_ascii=False, sort_keys=True) for it in new_items}
    diff = [json.loads(s) for s in new_set - prev_set]

    if diff:
        sample = ', '.join(d.get('menu', '') for d in diff[:3])
        return f"오늘 식단이 업데이트되었습니다: {sample} 등"
    if new_items:
        sample = ', '.join(item.get('menu', '') for item in new_items[:3])
        return f"오늘 식단은 {sample} 등입니다."
    return "오늘은 식단 정보가 없습니다."
