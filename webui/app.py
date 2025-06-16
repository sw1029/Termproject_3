from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json
from pathlib import Path

from src.realtime_model import (
    LLMClassifier,
    ANSWER_HANDLERS,
    retriever,
    generator,
)


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize chatbot components
classifier = LLMClassifier()

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
        label = classifier.predict(message)

        handler = ANSWER_HANDLERS.get(label)
        if handler:
            answer = handler(message)
            socketio.emit('stream_token', {'token': answer})
        else:
            docs = retriever.retrieve(message)
            for token in generator.generate(message, docs):
                socketio.emit('stream_token', {'token': token})

        socketio.emit('stream_end', {})

    except Exception as e:
        print(f"Error processing message: {e}")
        error_message = "죄송합니다, 답변을 처리하는 데 문제가 발생했습니다."
        socketio.emit('stream_token', {'token': error_message})
        socketio.emit('stream_end', {})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
