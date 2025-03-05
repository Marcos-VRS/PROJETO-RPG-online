document.addEventListener("DOMContentLoaded", function () {
    window.rollAttribute = function (nh, attribute, name) {
        let bonus = document.getElementById(`bonus-${attribute}`)?.value || 0;
        let redutor = document.getElementById(`redutor-${attribute}`)?.value || 0;

        // Converte os valores para inteiros
        bonus = parseInt(bonus, 10) || 0;
        redutor = parseInt(redutor, 10) || 0;

        console.log(`Rolling attribute: ${attribute} with NH: ${nh}, bonus: ${bonus}, redutor: ${redutor}`);

        fetch(`/teste_atributos/${attribute}/${nh}/${bonus}/${redutor}/${encodeURIComponent(name)}/`)
            .then(response => response.json())
            .then(data => {
                let messageInput = document.getElementById("messageInput");
                let submitButton = document.getElementById("button-chat-submit");
                let form = submitButton.closest("form"); // Obtém o formulário mais próximo

                // Acessa a div com id 'owner-status'
                var hiddenDiv = document.getElementById("owner-status");

                // Obtém o valor do atributo 'data-is-owner'
                var isOwner = hiddenDiv.getAttribute("data-is-owner");

                console.log(isOwner);  // Isso vai imprimir "True" no console do navegador

                if (isOwner === "False") {
                    nomePersonagem = document.getElementById("personagem-nome").getAttribute("data-nome");
                    messageInput.value = `NOME:${nomePersonagem}\nTESTE:${data.atributo}\nNH: ${data.nh}(${data.nh_final})\nROLL: ${data.roll}\n${data.message}\n`;

                    console.log(nomePersonagem);
                } else {
                    // Preenche a mensagem
                    console.log(data.nome_personagem);

                    messageInput.value = `NOME:${decodeURIComponent(data.nome_personagem)}\nTESTE:${data.atributo}\nNH: ${data.nh}(${data.nh_final})\nROLL: ${data.roll}\n${data.message}\n`;
                }

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
