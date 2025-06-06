document.addEventListener('DOMContentLoaded', () => {
  const socket = io();

  const chatWindow = document.getElementById('chat-window');
  const chatForm = document.getElementById('chat-form');
  const msgInput = document.getElementById('msg-input');

  let waitingDiv = null;

  function appendMessage(sender, text, label = null) {
    const div = document.createElement('div');
    div.classList.add('message', sender);
    if (label !== null) {
      div.classList.add(`label-${label}`);
    }
    div.innerText = text;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
    return div;
  }

  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const msg = msgInput.value.trim();
    if (!msg) return;
    appendMessage('user', msg);
    waitingDiv = appendMessage('bot', '정보를 확인하는 중...');
    socket.emit('user_message', { message: msg });
    msgInput.value = '';
  });

  socket.on('bot_message', (data) => {
    if (waitingDiv) {
      chatWindow.removeChild(waitingDiv);
      waitingDiv = null;
    }
    appendMessage('bot', data.message, data.label);
  });
});
