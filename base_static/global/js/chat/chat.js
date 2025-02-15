document.addEventListener('DOMContentLoaded', (event) => {
    const roomName = document.querySelector('.chat-container').dataset.roomName;
    const username = document.querySelector('.chat-container').dataset.username;
    const chatSocket = new WebSocket(
        `${window.location.protocol === "https:" ? "wss://" : "ws://"}${window.location.host}/ws/chat/${roomName}/`
    );

    // Quando uma nova mensagem for recebida
    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        const messages = document.getElementById('messages');
        messages.innerHTML += `<li><strong>${data.username}:</strong> ${data.message}</li>`;
        messages.scrollTop = messages.scrollHeight;
    };

    chatSocket.onclose = function (e) {
        console.error('WebSocket fechado inesperadamente.');
    };

    // Função para enviar uma mensagem
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
                        input.value = '';  // Limpar o campo após o envio
                    }
                });

            // Enviar a mensagem via WebSocket para atualização em tempo real
            chatSocket.send(JSON.stringify({
                'message': message,
                'username': username
            }));
        }
    }

    // Captura do evento Enter no campo de input
    document.getElementById('messageInput').addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {  // Se pressionar Enter sem Shift (sem adicionar nova linha)
            e.preventDefault();  // Impede a ação padrão do Enter (como um "submit")
            const message = this.value;
            sendMessage(message);  // Envia a mensagem
        }
    });

    // Envia a mensagem ao clicar no botão
    document.querySelector('form').onsubmit = function (e) {
        e.preventDefault();  // Impede o envio do formulário padrão
        const input = document.getElementById('messageInput');
        const message = input.value;
        sendMessage(message);  // Envia a mensagem
    };

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
