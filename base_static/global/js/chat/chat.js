document.addEventListener('DOMContentLoaded', () => {
    const roomName = document.querySelector('.chat-container')?.dataset.roomName;
    const username = document.querySelector('.chat-container')?.dataset.username;

    if (!roomName || !username) {
        console.error('Erro: Dados necessários não encontrados.');
        return;
    }

    let chatSocket = null;
    let reconnectDelay = 3000; // 3 segundos entre tentativas

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

    function scrollToBottom() {
        const messages = document.getElementById('messages');
        setTimeout(() => {
            messages.scrollTop = messages.scrollHeight;
        }, 500);
    }

    function connectWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
        const wsUrl = `${protocol}${window.location.host}/ws/chat/${roomName}/`;

        chatSocket = new WebSocket(wsUrl);
        window.chatSocket = chatSocket;

        // Recebendo mensagens
        chatSocket.onmessage = function (e) {
            const data = JSON.parse(e.data);
            const messages = document.getElementById('messages');

            if (data.type === "pong") return; // Ignora respostas de ping

            let formattedMessage = data.message.replace(/\n/g, '<br>');

            let bgColorClass = "";
            if (formattedMessage.endsWith("<br>Acerto<br>")) {
                bgColorClass = "bg-green";
            } else if (formattedMessage.endsWith("<br>SUCESSO DECISIVO<br>")) {
                bgColorClass = "bg-orange";
            } else if (formattedMessage.endsWith("<br>SUCESSO<br>")) {
                bgColorClass = "bg-purple";
            } else if (formattedMessage.endsWith("<br>Falha<br>")) {
                bgColorClass = "bg-gray";
            } else if (formattedMessage.endsWith("<br>ERRO CRÍTICO<br>")) {
                bgColorClass = "bg-red";
            } else if (formattedMessage) {
                bgColorClass = "bg-blue";
            }

            messages.innerHTML += `<li class="message-single-box medievalsharp-mini ${bgColorClass}">
                <strong class="username-chat">${data.username}:</strong> <span class="content-message-chat">${formattedMessage}</span>
            </li><br>`;

            scrollToBottom();
            messages.lastElementChild.scrollIntoView({ behavior: 'smooth', block: 'end' });
        };

        // Erros de conexão
        chatSocket.onerror = function (error) {
            console.error('Erro no WebSocket:', error);
        };

        // Conexão fechada
        chatSocket.onclose = function (e) {
            console.warn('WebSocket desconectado. Tentando reconectar em 3 segundos...');
            setTimeout(connectWebSocket, reconnectDelay);
        };

        // Envio de ping a cada 30s
        setInterval(() => {
            if (chatSocket.readyState === WebSocket.OPEN) {
                chatSocket.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    }

    connectWebSocket();

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
            }).then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        input.value = '';
                    }
                });

            if (chatSocket.readyState === WebSocket.OPEN) {
                chatSocket.send(JSON.stringify({
                    'message': message,
                    'username': username
                }));
            } else {
                console.error('WebSocket não está conectado. Mensagem não enviada.');
            }
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

    scrollToBottom();
});
