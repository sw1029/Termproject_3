import json
from pathlib import Path

LABELS = {
    0: "졸업요건",
    1: "학교 공지사항",
    2: "학사일정",
    3: "식단 안내",
    4: "통학/ 셔틀 버스",
}


def append_jsonl(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        f.write("\n")


def load_json_lines(path: Path):
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    input_path = Path("data/test_cls.json")
    output_path = Path("outputs/cls_output.json")
    if not input_path.exists():
        return
    for item in load_json_lines(input_path):
        q = item.get("user") or item.get("question")
        # placeholder classifier always returns label 0
        label = 0
        append_jsonl(output_path, {"question": q, "label": label})


if __name__ == "__main__":
    main()

