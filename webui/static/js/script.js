document.addEventListener('DOMContentLoaded', function () {
    const chatBox = document.getElementById('chat-window');
    const chatForm = document.getElementById('chat-form');
    const msgInput = document.getElementById('msg-input');

    function addMessage(sender, message) {
        const div = document.createElement('div');
        div.classList.add('message', sender);
        div.textContent = message;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    async function submitQuestion() {
        const question = msgInput.value.trim();
        if (!question) return;

        addMessage('user', question);
        msgInput.value = '';

        const res = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        const data = await res.json();
        if (data.question_id) {
            addMessage('bot', '답변을 분류 중입니다...');
            pollForAnswer(data.question_id);
        }
    }

    function pollForAnswer(id) {
        const interval = setInterval(async () => {
            const resp = await fetch(`/check_answer/${id}`);
            const data = await resp.json();
            if (data.status === 'completed') {
                clearInterval(interval);
                addMessage('bot', data.response);
            }
        }, 3000);
    }

    chatForm.addEventListener('submit', function (e) {
        e.preventDefault();
        submitQuestion();
    });
});
