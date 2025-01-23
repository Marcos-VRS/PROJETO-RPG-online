const roomName = JSON.parse(document.getElementById('room-name').textContent);
const chatSocket = new WebSocket(
    `ws://${window.location.host}/ws/chat/${roomName}/`
);

chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    document.querySelector('#chat-log').innerHTML += `<p><b>${data.username}:</b> ${data.message}</p>`;
};

chatSocket.onclose = function (e) {
    console.error('Chat socket closed unexpectedly');
};

document.querySelector('#chat-message-submit').onclick = function (e) {
    const messageInput = document.querySelector('#chat-message-input');
    const message = messageInput.value;

    chatSocket.send(JSON.stringify({
        'message': message,
        'username': 'Anonymous' // Troque pelo nome real do usuário
    }));
    messageInput.value = '';
};