from flask import Flask, request, jsonify, render_template_string
import requests
from pathlib import Path
import json

app = Flask(__name__)
API_URL = "http://localhost:8000"
LOG_PATH = Path("outputs/chat_output.json")

def append_log(record: dict):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False)
        f.write("\n")

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
    items = [json.loads(line) for line in LOG_PATH.read_text().splitlines() if line]
    return jsonify(items)

if __name__ == '__main__':
    app.run(debug=True)
