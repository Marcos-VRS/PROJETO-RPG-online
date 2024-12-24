document.querySelector("form").addEventListener("submit", function (event) {
    // Prevenir o envio inicial
    event.preventDefault();

    // Capturar os equipamentos Armor (tanto estáticos quanto dinâmicos)
    const equipamentosArmor = [];
    const armorLinhas = document.querySelectorAll("#equipamentos-armor-container .equipamento-linha");

    armorLinhas.forEach(linha => {
        const nome = linha.querySelector("input[name='equipamentos_armor_nome[]']").value.trim();
        const location = linha.querySelector("input[name='equipamentos_armor_location[]']").value.trim();
        const rd = linha.querySelector("input[name='equipamentos_armor_rd[]']").value.trim();
        const weight = linha.querySelector("input[name='equipamentos_armor_weight[]']").value.trim();
        const cost = linha.querySelector("input[name='equipamentos_armor_cost[]']").value.trim();

        // Adicionar o equipamento somente se pelo menos um campo for preenchido
        if (nome || location || rd || weight || cost) {
            equipamentosArmor.push({ nome, location, rd, weight, cost });
        }
    });

    // Criar o JSON
    const jsonData = JSON.stringify(equipamentosArmor);

    // Exibir o JSON no console para depuração
    console.log("Equipamentos Armor JSON:", jsonData);

    // Adicionar o JSON a um campo oculto no formulário
    let jsonField = document.getElementById("id_equipment_armor");
    if (!jsonField) {
        jsonField = document.createElement("input");
        jsonField.type = "hidden";
        jsonField.name = "equipment_armor";
        jsonField.id = "id_equipment_armor";
        this.appendChild(jsonField);
    }

    jsonField.value = jsonData;

    // Exibir no console o valor do campo oculto antes de enviar o formulário
    console.log("Valor do campo oculto:", jsonField.value);

    // Enviar o formulário
    this.submit();
});
