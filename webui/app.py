from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import requests

API_URL = "http://localhost:8000"

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('user_message')
def handle_user_message(data):
    user_msg = data.get('message', '')
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
