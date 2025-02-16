document.addEventListener("DOMContentLoaded", function () {
    window.rollAttribute = function (nh, attribute) {
        let bonus = document.getElementById(`bonus-${attribute}`)?.value || 0;
        let redutor = document.getElementById(`redutor-${attribute}`)?.value || 0;

        // Converte os valores para inteiros
        bonus = parseInt(bonus, 10);
        redutor = parseInt(redutor, 10);

        console.log(`Rolling attribute: ${attribute} with NH: ${nh}, bonus: ${bonus}, redutor: ${redutor}`);

        fetch(`/teste_atributos/${attribute}/${nh}/${bonus}/${redutor}/`)
            .then(response => response.json())
            .then(data => {
                let messageInput = document.getElementById("messageInput");
                let submitButton = document.getElementById("button-chat-submit");
                let form = submitButton.closest("form"); // Obtém o formulário mais próximo

                // Preenche a mensagem
                messageInput.value = `TESTE: ${data.atributo}\nNH: ${data.nh}(${data.nh_final})\nROLL: ${data.roll}\n${data.message}`;

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
            .catch(error => console.error("Erro ao processar a rolagem:", error));
    };
});
