document.addEventListener('DOMContentLoaded', function () {
    const messagesContainer = document.getElementById('chat-container-id');

    // Função para rolar para o fundo
    function scrollToBottom() {
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    // Rolar para o fundo assim que a página carregar
    setTimeout(scrollToBottom, 200);

    // Se estiver usando WebSockets, ou ouvindo eventos, você pode adicionar um ouvinte de evento
    const socket = new WebSocket('ws://127.0.0.1:8000/chat_socket/'); // Ajuste o URL para o WebSocket correto
    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        const message = data.message;

        // Aqui você pode adicionar a mensagem ao chat
        const newMessageElement = document.createElement('li');
        newMessageElement.innerHTML = `<strong>${message.user}:</strong> ${message.content} <em>(${message.timestamp})</em>`;
        messagesContainer.appendChild(newMessageElement);

        // Rolar para o fundo após adicionar a nova mensagem
        scrollToBottom();
    };

    // Caso as mensagens sejam enviadas via formulário (por exemplo, através de um AJAX)
    const form = document.querySelector('form');
    form.addEventListener('submit', function (event) {
        event.preventDefault();

        // Supondo que você tenha o código para enviar a mensagem aqui
        // (seja via AJAX ou outra implementação)

        // Após o envio, rolar para o fundo
        setTimeout(scrollToBottom, 100); // Aguarda um pouco para garantir que a mensagem foi adicionada
    });
});
