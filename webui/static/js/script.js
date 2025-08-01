document.addEventListener('DOMContentLoaded', function () {
    const socket = io();
    const chatBox = document.getElementById('chat-window');
    const chatForm = document.getElementById('chat-form');
    const msgInput = document.getElementById('msg-input');

    function addMessage(sender, message) {
        const div = document.createElement('div');
        div.classList.add('message', sender);
        div.innerHTML = message;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function submitQuestion() {
        const question = msgInput.value;
        if (!question) return;

        addMessage('user', question);
        msgInput.value = '';

        socket.emit('ask_question', { question });
        addMessage('bot', '답변을 분류 중입니다...');
        console.log('보낸 질문:', question);
    }

    socket.on('answer_response', function (data) {
    addMessage('bot', data.response);
    if (data.script) {
        eval(data.script);
    }
});

    chatForm.addEventListener('submit', function (e) {
        e.preventDefault();
        submitQuestion();
    });
});
