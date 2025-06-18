from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import uuid
from datetime import datetime
from pathlib import Path
import os
import sys

# Ensure the project root is on the Python path so that ``src`` can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.answers import (
    academic_calendar_answer,
    shuttle_bus_answer,
    graduation_req_answer,
    meals_answer,
    notices_answer,
)

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Directory paths
QUESTION_DIR = Path('question')
ANSWER_DIR = Path('answer')
PROCESSED_DIR = QUESTION_DIR / 'processed'

# Create directories if they do not exist
QUESTION_DIR.mkdir(exist_ok=True)
ANSWER_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

# Path for storing question/answer history
OUTPUTS_DIR = Path('outputs')
QA_JSON_PATH = OUTPUTS_DIR / 'chat_output.json'

# Map labels to rule-based answer generators
ANSWER_HANDLERS = {
    0: graduation_req_answer.generate_answer,
    1: notices_answer.generate_answer,
    2: academic_calendar_answer.generate_answer,
    3: meals_answer.generate_answer,
    4: shuttle_bus_answer.generate_answer,
}

def get_rule_based_response(label: int, question_text: str) -> str:
    handler = ANSWER_HANDLERS.get(label)
    if handler:
        return handler(question_text)
    return '적절한 답변을 찾지 못했습니다.'


def append_qa(question: str, answer: str) -> None:
    """Append a question/answer pair to ``chat_output.json``."""
    OUTPUTS_DIR.mkdir(exist_ok=True)
    records = []
    if QA_JSON_PATH.exists():
        try:
            with QA_JSON_PATH.open('r', encoding='utf-8') as f:
                records = json.load(f)
                if not isinstance(records, list):
                    records = [records]
        except json.JSONDecodeError:
            with QA_JSON_PATH.open('r', encoding='utf-8') as f:
                records = [json.loads(line) for line in f if line.strip()]

    records.append({
        'question': question,
        'answer': answer,
        'timestamp': datetime.now().isoformat(),
    })

    with QA_JSON_PATH.open('w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question_text = data.get('question')
    if not question_text:
        return jsonify({'error': 'Question is missing'}), 400

    question_id = f"q_{datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:4]}"
    payload = {
        'question_id': question_id,
        'text': question_text,
        'timestamp': datetime.now().isoformat()
    }
    file_path = QUESTION_DIR / f"{question_id}.json"
    with file_path.open('w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)

    return jsonify({'status': 'pending', 'question_id': question_id})

@app.route('/check_answer/<question_id>', methods=['GET'])
def check_answer(question_id):
    answer_id = question_id.replace('q_', 'a_')
    answer_file = ANSWER_DIR / f"{answer_id}.json"
    if not answer_file.exists():
        return jsonify({'status': 'pending'})

    # Load existing classification result
    with answer_file.open('r+', encoding='utf-8') as f:
        answer_data = json.load(f)
        label = int(answer_data.get('label', -1))
        original_question = answer_data.get('original_question', '')

        # Generate answer only once and persist it
        if 'response' not in answer_data:
            response = get_rule_based_response(label, original_question)
            answer_data['response'] = response
            answer_data['answered_at'] = datetime.now().isoformat()
            f.seek(0)
            json.dump(answer_data, f, ensure_ascii=False, indent=4)
            f.truncate()
            append_qa(original_question, response)
        else:
            response = answer_data['response']

    return jsonify({'status': 'completed', 'label': label, 'response': response})

# WebSocket handlers
@socketio.on('ask_question')
def handle_ask_question(data):
    """Receive a question via WebSocket and start waiting for an answer."""
    question_text = data.get('question')
    if not question_text:
        emit('error', {'message': 'Question is missing'})
        return

    question_id = f"q_{datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:4]}"
    payload = {
        'question_id': question_id,
        'text': question_text,
        'timestamp': datetime.now().isoformat(),
    }
    file_path = QUESTION_DIR / f"{question_id}.json"
    with file_path.open('w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=4)

    emit('question_received', {'question_id': question_id})
    socketio.start_background_task(wait_for_answer, question_id, request.sid)


def wait_for_answer(question_id: str, sid: str) -> None:
    """Wait for the classifier to produce an answer file and emit it."""
    answer_id = question_id.replace('q_', 'a_')
    answer_file = ANSWER_DIR / f"{answer_id}.json"
    while not answer_file.exists():
        socketio.sleep(3)

    with answer_file.open('r+', encoding='utf-8') as f:
        answer_data = json.load(f)
        label = int(answer_data.get('label', -1))
        original_question = answer_data.get('original_question', '')

        if 'response' not in answer_data:
            response = get_rule_based_response(label, original_question)
            answer_data['response'] = response
            answer_data['answered_at'] = datetime.now().isoformat()
            f.seek(0)
            json.dump(answer_data, f, ensure_ascii=False, indent=4)
            f.truncate()
            append_qa(original_question, response)
        else:
            response = answer_data['response']

    socketio.emit(
        'answer_response',
        {'label': label, 'response': response, 'question_id': question_id},
        to=sid,
    )

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
