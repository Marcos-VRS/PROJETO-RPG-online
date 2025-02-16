document.addEventListener('DOMContentLoaded', function () {
    const messagesContainer = document.getElementById('chat-container-id');

    // Função para rolar o chat para a mensagem mais nova
    function scrollToBottom() {
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }

    // Garantir que o scroll seja feito após um pequeno delay ao carregar a página
    setTimeout(scrollToBottom, 200); // 200ms de delay para garantir que as mensagens foram renderizadas

    // Observar mudanças no contêiner de mensagens
    const observer = new MutationObserver(scrollToBottom);
    observer.observe(messagesContainer, { childList: true });

    // Garantir que o scroll seja feito após uma nova mensagem ser enviada
    const form = document.querySelector('form');
    form.addEventListener('submit', function () {
        setTimeout(scrollToBottom, 100); // 100ms de delay para garantir que a mensagem foi adicionada
    });
});