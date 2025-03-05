document.addEventListener('DOMContentLoaded', (event) => {
    const roomName = document.querySelector('.chat-container')?.dataset.roomName;
    const username = document.querySelector('.chat-container')?.dataset.username;

    if (!roomName || !username) {
        console.error('Erro: Dados necessários não encontrados.');
        return;
    }

    // Define chatSocket corretamente, verificando se já existe
    const chatSocket = window.chatSocket || new WebSocket(
        `${window.location.protocol === "https:" ? "wss://" : "ws://"}${window.location.host}/ws/chat/${roomName}/`
    );

    // Quando uma nova mensagem for recebida
    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        const messages = document.getElementById('messages');
        let formattedMessage = data.message
            .replace(/\n/g, '<br>');

        messages.innerHTML += `<li class="message-single-box  medievalsharp-mini"><strong class="username-chat">${data.username}:</strong class="content-message-chat"> ${formattedMessage}</li>`;
        messages.scrollTop = messages.scrollHeight;
    };

    chatSocket.onclose = function (e) {
        console.error('WebSocket fechado inesperadamente.');
    };

    function sendMessage(message) {
        const input = document.getElementById('messageInput');
        if (message.trim() !== "") {
            fetch('/save_message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    'message': message,
                    'campanha_id': roomName
                })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        input.value = '';
                    }
                });

            // Enviar a mensagem via WebSocket para atualização em tempo real
            chatSocket.send(JSON.stringify({
                'message': message,
                'username': username
            }));
        }
    }

    document.getElementById('messageInput')?.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(this.value);
        }
    });

    document.querySelector('form')?.addEventListener('submit', function (e) {
        e.preventDefault();
        sendMessage(document.getElementById('messageInput').value);
    });

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            document.cookie.split(';').forEach(cookie => {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                }
            });
        }
        return cookieValue;
    }
});
