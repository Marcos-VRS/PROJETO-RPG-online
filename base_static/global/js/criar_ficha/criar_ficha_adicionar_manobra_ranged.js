document.addEventListener("DOMContentLoaded", function () {
    const botaoAdicionarRanged = document.getElementById("botao4");
    const containerRanged = document.querySelector(".ficha-box-ranged");

    // Adicionar nova manobra ao clicar no botão 4
    botaoAdicionarRanged.addEventListener("click", function () {
        // Clonar a estrutura da manobra existente
        const novaManobra = document.createElement("div");
        novaManobra.classList.add("ficha-box-manobra-ataque");

        // Adiciona o conteúdo da nova manobra
        novaManobra.innerHTML = `
            <div class="manobra-ataque-ranged-id">
                <div class="col-manobra">
                    <label for="nome_manobra_Ranged_id" class="label-nome-manobra medievalsharp-mini">Nome da
                        manobra</label>
                    <input class="campo-curto-nome medievalsharp-mini" name="nome_manobra_Ranged[]" placeholder="Nome da manobra" type="text" />
                </div>
                <div>
                    <label for="manobra_damage_Ranged_id" class="medievalsharp-mini">Dano:</label>
                    <input class="campo-curto-equip medievalsharp-mini" name="damage_manobra_Ranged[]" placeholder="Damage" type="text">
                    <label for="manobra_nh_Ranged_id" class="medievalsharp-mini">NH:</label>
                    <input class="campo-curto-equip medievalsharp-mini" name="nh_manobra_Ranged[]" placeholder="NH" type="text">
                </div>
                <div>
                    <label for="manobra_Ranged_detalhe_id" class="label-nome-detalhes medievalsharp-mini">Detalhes:</label>
                    <textarea class="campo-curto-detalhes-manobra medievalsharp-mini"
                        placeholder="Detalhes como tipo de dano, alcance, modificadores, e características do ataque"
                        name="detalhes_manobra_Ranged[]"></textarea>
                    <div class="posicao-botao-remover">
                        <span class="botao-remover"></span>
                    </div>
                </div>
            </div>
        `;

        // Adiciona a nova manobra ao container principal
        containerRanged.appendChild(novaManobra);
    });

    // Remover a manobra ao clicar no botão 5
    containerRanged.addEventListener("click", function (e) {
        if (e.target.classList.contains("botao-remover")) {
            const manobraParaRemover = e.target.closest(".ficha-box-manobra-ataque");
            if (manobraParaRemover) {
                manobraParaRemover.remove();
            }
        }
    });
});
