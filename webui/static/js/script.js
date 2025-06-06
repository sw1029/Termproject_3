document.addEventListener('DOMContentLoaded', () => {
  const socket = io();

  const chatWindow = document.getElementById('chat-window');
  const chatForm = document.getElementById('chat-form');
  const msgInput = document.getElementById('msg-input');

  function appendMessage(sender, text) {
    const div = document.createElement('div');
    div.classList.add('message', sender);
    div.innerText = text;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const msg = msgInput.value.trim();
    if (!msg) return;
    appendMessage('user', msg);
    socket.emit('user_message', { message: msg });
    msgInput.value = '';
  });

  socket.on('bot_message', (data) => {
    appendMessage('bot', data.message);
  });
});
