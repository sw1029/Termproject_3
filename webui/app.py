from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import requests
import json
from pathlib import Path

API_URL = "http://localhost:8000"

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

QUESTIONS_PATH = Path("outputs/web_questions.json")


def append_question(question: str):
    """Store ``question`` in ``web_questions.json`` as a JSON array."""
    QUESTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    items = []
    if QUESTIONS_PATH.exists():
        text = QUESTIONS_PATH.read_text(encoding="utf-8").strip()
        if text:
            try:
                data = json.loads(text)
                items = data if isinstance(data, list) else [data]
            except json.JSONDecodeError:
                items = [json.loads(line) for line in text.splitlines() if line.strip()]
    items.append({"question": question})
    with QUESTIONS_PATH.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('user_message')
def handle_user_message(data):
    user_msg = data.get('message', '')
    append_question(user_msg)
    try:
        resp = requests.post(f"{API_URL}/answer", json={"question": user_msg}, timeout=10)
        if resp.ok:
            bot_reply = resp.json().get('answer', '')
        else:
            bot_reply = 'Error'
    except Exception:
        bot_reply = 'Error'
    emit('bot_message', {'message': bot_reply})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
