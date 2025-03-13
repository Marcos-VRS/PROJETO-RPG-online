document.addEventListener("DOMContentLoaded", function () {
    const botaoAdicionarDefesa = document.getElementById("botao6");
    const containerDefesa = document.querySelector(".ficha-box-defesa");

    // Adicionar nova manobra de defesa ao clicar no botão 6
    botaoAdicionarDefesa.addEventListener("click", function () {
        // Cria uma nova div com a mesma estrutura da manobra de defesa
        const novaDefesa = document.createElement("div");
        novaDefesa.classList.add("ficha-box-manobra-defesa");

        // Define o conteúdo HTML da nova manobra de defesa
        novaDefesa.innerHTML = `
            <div class="manobra-defesa-id">
                <div class="col-manobra">
                    <label for="nome_manobra_defesa_id" class="label-nome-manobra medievalsharp-mini">Nome da
                        manobra</label>
                    <input class="campo-curto-nome medievalsharp-mini" name="nome_manobra_defesa[]" placeholder="Nome da manobra" maxlength="30" type="text" />
                </div>
                <div>
                    <label for="manobra_nh_defesa_id" class="medievalsharp-mini">NH:</label>
                    <input class="campo-curto-equip medievalsharp-mini" name="nh_manobra_defesa[]" placeholder="NH" maxlength="12" type="text">
                </div>
                <div>
                    <label for="manobra_defesa_detalhe_id" class="label-nome-detalhes medievalsharp-mini">Detalhes:</label>
                    <textarea class="campo-curto-detalhes-manobra medievalsharp-mini"
                        placeholder="Detalhes como tipo de dano, alcance, modificadores, e características do ataque"
                        name="detalhes_manobra_defesa[]" maxlength="1000"></textarea>
                    <div class="posicao-botao-remover">
                        <span class="botao-remover"></span>
                    </div>
                </div>
            </div>
        `;

        // Adiciona a nova manobra de defesa ao container principal
        containerDefesa.appendChild(novaDefesa);
    });

    // Remover a manobra de defesa ao clicar no botão 7
    containerDefesa.addEventListener("click", function (e) {
        if (e.target.classList.contains("botao-remover")) {
            const defesaParaRemover = e.target.closest(".ficha-box-manobra-defesa");
            if (defesaParaRemover) {
                defesaParaRemover.remove();
            }
        }
    });
});
