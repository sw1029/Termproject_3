from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
# CORS 설정이 필요하면 cors_allowed_origins="*"
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('user_message')
def handle_user_message(data):
    user_msg = data.get('message')
    # TODO: 실제 챗봇 로직을 여기에 연동
    bot_reply = f"Echo: {user_msg}"
    emit('bot_message', {'message': bot_reply})

if __name__ == '__main__':
    # eventlet 또는 gevent 중 설치된 것으로 실행
    socketio.run(app, host='0.0.0.0', port=5000)
