from flask import Flask, request, jsonify, render_template_string
import requests
from pathlib import Path
import json

app = Flask(__name__)
API_URL = "http://localhost:8000"
LOG_PATH = Path("outputs/chat_output.json")

def append_log(record: dict):
    """Append a chat record to ``chat_output.json`` using a JSON array."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    records = []
    if LOG_PATH.exists():
        text = LOG_PATH.read_text(encoding="utf-8").strip()
        if text:
            try:
                data = json.loads(text)
                records = data if isinstance(data, list) else [data]
            except json.JSONDecodeError:
                records = [json.loads(line) for line in text.splitlines() if line.strip()]
    records.append(record)
    with LOG_PATH.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

HTML = """
<!doctype html>
<title>Chatbot</title>
<h1>Chatbot Demo</h1>
<form method=post>
  <input name=question size=60 autofocus>
  <input type=submit value=Ask>
</form>
<pre>{{answer}}</pre>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    answer = ''
    if request.method == 'POST':
        q = request.form['question']
        resp = requests.post(f"{API_URL}/answer", json={'question': q}, timeout=10)
        if resp.ok:
            answer = resp.json().get('answer', '')
        else:
            answer = 'Error'
        append_log({"user": q, "model": answer})
    return render_template_string(HTML, answer=answer)


@app.route('/history', methods=['GET'])
def history():
    if not LOG_PATH.exists():
        return jsonify([])
    text = LOG_PATH.read_text(encoding="utf-8").strip()
    if not text:
        return jsonify([])
    try:
        items = json.loads(text)
        if not isinstance(items, list):
            items = [items]
    except json.JSONDecodeError:
        items = [json.loads(line) for line in text.splitlines() if line.strip()]
    return jsonify(items)

if __name__ == '__main__':
    app.run(debug=True)
