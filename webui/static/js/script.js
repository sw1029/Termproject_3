document.addEventListener('DOMContentLoaded', function () {
    const socket = io();
    const chatBox = document.getElementById('chat-window');
    const chatForm = document.getElementById('chat-form');
    const msgInput = document.getElementById('msg-input');

    function addMessage(sender, message, isStreaming = false) {
        const div = document.createElement('div');
        div.classList.add('message', sender);
        if (isStreaming) {
            div.id = 'streaming-message';
        }
        div.innerHTML = marked.parse(message);
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    chatForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const msg = msgInput.value.trim();
        if (!msg) return;
        socket.emit('send_message', { message: msg });
        addMessage('user', msg);
        addMessage('bot', '<div class="typing-indicator"></div>', true);
        msgInput.value = '';
    });

    socket.on('receive_message', function (data) {
        if (data.sender === 'user') {
            addMessage('user', data.message);
        } else {
            addMessage('bot', '<div class="typing-indicator"></div>', true);
        }
    });

    socket.on('stream_token', function (data) {
        const streaming = document.getElementById('streaming-message');
        if (streaming) {
            const indicator = streaming.querySelector('.typing-indicator');
            if (indicator) {
                indicator.remove();
            }
            const temp = document.createElement('div');
            temp.innerHTML = streaming.innerHTML;
            const current = temp.textContent || temp.innerText || '';
            streaming.innerHTML = marked.parse(current + data.token);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    });

    socket.on('stream_end', function () {
        const streaming = document.getElementById('streaming-message');
        if (streaming) {
            streaming.removeAttribute('id');
        }
    });
});
