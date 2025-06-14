from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import requests
import json
from pathlib import Path

FASTAPI_URL = "http://127.0.0.1:8000/answer"

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

@socketio.on('send_message')
def handle_send_message(data):
    message = data['message']
    append_question(message)
    print(f'Received message: {message}')
    emit('receive_message', {'sender': 'user', 'message': message})

    emit('receive_message', {'sender': 'bot', 'message': ''}, broadcast=True)

    try:
        response = requests.post(FASTAPI_URL, json={'question': message}, stream=True)
        response.raise_for_status()

        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                socketio.emit('stream_token', {'token': chunk})

        socketio.emit('stream_end', {})

    except requests.exceptions.RequestException as e:
        print(f"Error calling FastAPI: {e}")
        error_message = "죄송합니다, 답변을 생성하는 데 문제가 발생했습니다."
        socketio.emit('stream_token', {'token': error_message})
        socketio.emit('stream_end', {})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
