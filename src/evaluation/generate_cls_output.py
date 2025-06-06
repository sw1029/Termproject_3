import json
from pathlib import Path

LABELS = {
    0: "졸업요건",
    1: "학교 공지사항",
    2: "학사일정",
    3: "식단 안내",
    4: "통학/ 셔틀 버스",
}


def append_json(path: Path, data: dict):
    """Append ``data`` to ``path`` storing items as a JSON array."""
    path.parent.mkdir(parents=True, exist_ok=True)
    records = []
    if path.exists():
        text = path.read_text(encoding="utf-8").strip()
        if text:
            try:
                obj = json.loads(text)
                records = obj if isinstance(obj, list) else [obj]
            except json.JSONDecodeError:
                records = [json.loads(line) for line in text.splitlines() if line.strip()]
    records.append(data)
    with path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def load_json_lines(path: Path):
    """Load JSON objects from ``path`` accepting either array or JSONL."""
    with path.open(encoding="utf-8") as f:
        text = f.read().strip()
        if not text:
            return []
        try:
            obj = json.loads(text)
            if isinstance(obj, list):
                return obj
            return [obj]
        except json.JSONDecodeError:
            return [json.loads(line) for line in text.splitlines() if line.strip()]


def main():
    input_path = Path("data/test_cls.json")
    output_path = Path("outputs/cls_output.json")
    if not input_path.exists():
        return
    for item in load_json_lines(input_path):
        q = item.get("user") or item.get("question")
        # placeholder classifier always returns label 0
        label = 0
        append_json(output_path, {"question": q, "label": label})


if __name__ == "__main__":
    main()

