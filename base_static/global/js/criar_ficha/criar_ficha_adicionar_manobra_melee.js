document.addEventListener("DOMContentLoaded", function () {
    const botaoAdicionarManobra = document.getElementById("botao2");
    const containerManobras = document.querySelector(".ficha-box-melee");

    // Adicionar nova manobra ao clicar no botão 2
    botaoAdicionarManobra.addEventListener("click", function () {
        // Cria uma nova div com a mesma estrutura da manobra
        const novaManobra = document.createElement("div");
        novaManobra.classList.add("ficha-box-manobra-ataque");

        novaManobra.innerHTML = `
            <div>
                <div class="col-manobra">
                    <label for="nome_manobra_melee_id" class="label-nome-manobra medievalsharp-mini">Nome da
                        manobra</label>
                    <input class="campo-curto-nome medievalsharp-mini" name="nome_manobra_melee[]" placeholder="Nome da manobra" type="text" />
                </div>
                <div>
                    <label for="manobra_damage_melee_id" class="medievalsharp-mini">Dano:</label>
                    <input class="campo-curto-equip medievalsharp-mini" name="damage_manobra_melee[]" placeholder="Damage" type="text">
                    <label for="manobra_nh_melee_id" class="medievalsharp-mini">NH:</label>
                    <input class="campo-curto-equip medievalsharp-mini" name="nh_manobra_melee[]" placeholder="NH" type="text">
                </div>
                <div>
                    <label for="manobra_melee_detalhe_id" class="label-nome-detalhes medievalsharp-mini">Detalhes:</label>
                    <textarea class="campo-curto-detalhes-manobra medievalsharp-mini"
                        placeholder="Detalhes como tipo de dano, alcance, modificadores, e características do ataque"
                        name="detalhes_manobra_melee[]"></textarea>
                    <div class="posicao-botao-remover">
                        <span class="botao-remover"></span>
                    </div>
                </div>
            </div>
        `;

        // Adiciona a nova manobra ao container principal
        containerManobras.appendChild(novaManobra);
    });

    // Remover a manobra ao clicar no botão 3
    containerManobras.addEventListener("click", function (e) {
        if (e.target.classList.contains("botao-remover")) {
            const manobraParaRemover = e.target.closest(".ficha-box-manobra-ataque");
            if (manobraParaRemover) {
                manobraParaRemover.remove();
            }
        }
    });
});