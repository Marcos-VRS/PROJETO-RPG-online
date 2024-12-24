document.querySelector("form").addEventListener("submit", function (event) {
    // Prevenir o envio inicial
    event.preventDefault();

    // Capturar os equipamentos melee e seus detalhes
    const equipamentosMelee = [];
    const meleeLinhas = document.querySelectorAll("#equipamentos-melee-container .equipamento-linha");

    meleeLinhas.forEach(linha => {
        const nome = linha.querySelector("input[name='equipamentos_melee_nome[]']").value.trim();
        const damage = linha.querySelector("input[name='equipamentos_melee_damage[]']").value.trim();
        const reach = linha.querySelector("input[name='equipamentos_melee_reach[]']").value.trim();
        const parry = linha.querySelector("input[name='equipamentos_melee_parry[]']").value.trim();
        const cost = linha.querySelector("input[name='equipamentos_melee_cost[]']").value.trim();
        const weight = linha.querySelector("input[name='equipamentos_melee_weight[]']").value.trim();
        const details = linha.querySelector("textarea[name='equipamentos_melee_details[]']").value.trim();

        // Adicionar o equipamento somente se pelo menos um campo for preenchido
        if (nome || damage || reach || parry || cost || weight || details) {
            equipamentosMelee.push({ nome, damage, reach, parry, cost, weight, details });
        }
    });

    // Criar o JSON
    const jsonData = JSON.stringify(equipamentosMelee);

    // Adicionar o JSON a um campo oculto no formulário
    let jsonField = document.getElementById("id_equipment_melee");
    if (!jsonField) {
        jsonField = document.createElement("input");
        jsonField.type = "hidden";
        jsonField.name = "equipment_melee";
        jsonField.id = "id_equipment_melee";
        this.appendChild(jsonField);
    }

    jsonField.value = jsonData;

    // Enviar o formulário
    this.submit();
});
