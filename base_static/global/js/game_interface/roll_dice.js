document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("botao-rolar-d6").addEventListener("click", function () {
        // Captura os valores dos inputs
        const quantidade = document.getElementById("quantidade-d6-id").value;
        let incremento = document.getElementById("incremento_d6_id").value || "0";

        // Substitui "+" por "%2B" para evitar problemas na URL (caso o usuário insira "+2")
        incremento = encodeURIComponent(incremento);

        // Constrói a URL corretamente
        const url = `/rolld6/${quantidade}/${incremento}/`;

        // Faz a requisição para o Django
        fetch(url)
            .then(response => response.json())
            .then(data => {
                let messageInput = document.getElementById("messageInput");
                let submitButton = document.getElementById("button-chat-submit");
                let form = submitButton.closest("form"); // Obtém o formulário mais próximo

                // Preenche a mensagem 
                messageInput.value = `Roll ${quantidade} + (${incremento}): Resultado = \n${data.resultado}`;

                // Aguarda um pequeno tempo para evitar conflitos e clica no botão de envio
                setTimeout(() => {
                    submitButton.click();
                }, 100);

                // Aguarda um tempo extra e reseta o formulário para permitir novos envios
                setTimeout(() => {
                    if (form) {
                        form.reset(); // Reseta os campos do formulário
                    } else {
                        messageInput.value = ""; // Caso não tenha formulário, limpa manualmente
                    }
                }, 500);
            })
            .catch(error => {
                console.error("Erro ao rolar os dados:", error);
            });
    });
});
