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

    bot_reply = "알 수 없는 오류가 발생했습니다."
    label = None

    try:
        resp = requests.post(
            f"{API_URL}/answer", json={"question": user_msg}, timeout=120
        )

        if resp.ok:
            data = resp.json()
            bot_reply = data.get("answer", "답변을 찾지 못했습니다.")
            label = data.get("label")
        else:
            status_code = resp.status_code
            try:
                error_data = resp.json().get("detail", {})
                code = error_data.get("code", "UNKNOWN_API_ERROR")
                message = error_data.get("message", resp.text)
                bot_reply = f"API 오류 (HTTP {status_code}, 코드: {code}): {message}"
            except json.JSONDecodeError:
                bot_reply = f"API 오류 (HTTP {status_code}): 서버로부터 유효하지 않은 응답을 받았습니다."

    except requests.exceptions.Timeout:
        bot_reply = "오류: 서버 응답 시간이 초과되었습니다 (120초). 백엔드 서버를 확인해주세요."
    except requests.exceptions.ConnectionError:
        bot_reply = "오류: 백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."
    except Exception as e:
        bot_reply = f"웹 UI에서 예상치 못한 오류가 발생했습니다: {e}"

    emit("bot_message", {"message": bot_reply, "label": label})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
