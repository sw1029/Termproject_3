import json
from pathlib import Path
import requests

API_URL = "http://localhost:8000"


def append_jsonl(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        f.write("\n")


def load_json_lines(path: Path):
    with path.open(encoding="utf-8") as f:
        text = f.read().strip()
        if not text:
            return []
        try:
            # try JSON array
            obj = json.loads(text)
            if isinstance(obj, list):
                return obj
            return [obj]
        except json.JSONDecodeError:
            return [json.loads(line) for line in text.splitlines() if line.strip()]


def run_dataset(input_path: Path, output_path: Path):
    if not input_path.exists():
        return
    for item in load_json_lines(input_path):
        q = item.get("user") or item.get("question")
        if not q:
            continue
        try:
            resp = requests.post(f"{API_URL}/answer", json={"question": q}, timeout=15)
            ans = resp.json().get("answer", "") if resp.ok else ""
        except Exception:
            ans = ""
        append_jsonl(output_path, {"user": q, "model": ans})


def main():
    run_dataset(Path("data/test_chat.json"), Path("outputs/chat_output.json"))
    run_dataset(Path("data/test_realtime.json"), Path("outputs/realtime_output.json"))


if __name__ == "__main__":
    main()
