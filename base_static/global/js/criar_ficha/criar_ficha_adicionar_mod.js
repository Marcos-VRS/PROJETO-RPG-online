document.addEventListener("DOMContentLoaded", function () {
    const containerVantagens = document.getElementById("vantagens-container");

    containerVantagens.addEventListener("click", function (e) {
        const botao = e.target;

        // Verifica se o botão clicado é um "botao-adicionar"
        if (botao.classList.contains("botao-adicionar")) {
            const linhaAtual = botao.parentNode; // Linha do botão clicado

            // Verifica o estado do botão
            if (!botao.classList.contains("remover")) {
                // Estado para "adicionar": cria o campo "Mod"
                const modLinha = document.createElement("div");
                modLinha.classList.add("form-field", "mod-container"); // Classe para estilizar

                // Cria o label do campo "Mod"
                const labelMod = document.createElement("label");
                labelMod.textContent = "Mod:";
                labelMod.style.marginRight = "0.5rem";

                // Cria o textarea do campo "Mod"
                const textareaMod = document.createElement("textarea");
                textareaMod.name = "mod[]"; // Para agrupar como array no formulário
                textareaMod.placeholder = "Adicione modificações";
                textareaMod.style.width = "43.5%"; // Ajusta para ocupar toda a largura disponível
                textareaMod.style.resize = "vertical"; // Permite redimensionar verticalmente
                textareaMod.style.height = "3rem"; // Define uma altura inicial
                textareaMod.style.borderRadius = "0.2rem";
                textareaMod.style.marginBottom = "2rem";
                textareaMod.className = "medievalsharp-mini";

                // Adiciona o label e o textarea na nova linha
                modLinha.appendChild(labelMod);
                modLinha.appendChild(textareaMod);

                // Insere a nova linha abaixo do "Nome da vantagem"
                linhaAtual.parentNode.insertBefore(modLinha, linhaAtual.nextSibling);

                // Alterna o botão para estado "remover"
                botao.classList.add("remover");
                botao.style.backgroundColor = "red";
            } else {
                // Estado para "remover": remove o campo "Mod"
                const modLinha = linhaAtual.nextSibling;
                if (modLinha && modLinha.classList.contains("mod-container")) {
                    modLinha.remove();
                }

                // Alterna o botão de volta para estado "adicionar"
                botao.classList.remove("remover");
                botao.style.backgroundColor = "green";
                botao.textContent = ""; // Volta ao estado do símbolo "+"
            }
        }
    });
});
