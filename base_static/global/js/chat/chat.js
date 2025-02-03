document.addEventListener('DOMContentLoaded', (event) => {
    const roomName = document.querySelector('.chat-container').dataset.roomName;  // Certifique-se de que esta variável está sendo renderizada corretamente
    const username = document.querySelector('.chat-container').dataset.username;  // Nome do usuário

    // Verifica se a página está sendo acessada via HTTP ou HTTPS
    const wsProtocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    const chatSocket = new WebSocket(
        `${wsProtocol}${window.location.host}/ws/chat/${roomName}/`
    );

    // Quando uma nova mensagem for recebida
    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        const messages = document.getElementById('messages');
        messages.innerHTML += `<li><strong>${data.username}:</strong> ${data.message}</li>`;
        // Rolagem para o final da lista
        messages.scrollTop = messages.scrollHeight;
    };

    chatSocket.onclose = function (e) {
        console.error('WebSocket fechado inesperadamente.');
    };

    // Função para enviar uma mensagem
    document.querySelector('form').onsubmit = function (e) {
        e.preventDefault();
        const input = document.getElementById('messageInput');
        const message = input.value;
        if (message.trim() !== "") {
            // Envia a mensagem para salvar no banco de dados via AJAX
            fetch('/save_message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')  // para incluir o CSRF token
                },
                body: JSON.stringify({
                    'message': message,
                    'campanha_id': roomName
                })
            })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Limpar o campo após o envio
                        input.value = '';
                    }
                });

            // Enviar a mensagem via WebSocket para atualização em tempo real
            chatSocket.send(JSON.stringify({
                'message': message,
                'username': username
            }));
        }
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