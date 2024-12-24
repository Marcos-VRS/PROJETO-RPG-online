document.querySelector("form").addEventListener("submit", function (event) {
    // Prevenir o envio inicial
    event.preventDefault();

    // Capturar os equipamentos Ranged e seus detalhes
    const equipamentosRanged = [];
    const rangedLinhas = document.querySelectorAll("#equipamentos-ranged-container .equipamento-linha");

    rangedLinhas.forEach(linha => {
        const nome = linha.querySelector("input[name='equipamentos_ranged_nome[]']").value.trim();
        const damage = linha.querySelector("input[name='equipamentos_ranged_damage[]']").value.trim();
        const acc = linha.querySelector("input[name='equipamentos_ranged_acc[]']").value.trim();
        const range = linha.querySelector("input[name='equipamentos_ranged_range[]']").value.trim();
        const weight = linha.querySelector("input[name='equipamentos_ranged_weight[]']").value.trim();
        const rof = linha.querySelector("input[name='equipamentos_ranged_rof[]']").value.trim();
        const shots = linha.querySelector("input[name='equipamentos_ranged_shots[]']").value.trim();
        const bulk = linha.querySelector("input[name='equipamentos_ranged_bulk[]']").value.trim();
        const rcl = linha.querySelector("input[name='equipamentos_ranged_rcl[]']").value.trim();
        const cost = linha.querySelector("input[name='equipamentos_ranged_cost[]']").value.trim();
        const details = linha.querySelector("textarea[name='equipamentos_ranged_details[]']").value.trim();

        // Adicionar o equipamento somente se pelo menos um campo for preenchido
        if (nome || damage || acc || range || weight || rof || shots || bulk || rcl || cost || details) {
            equipamentosRanged.push({ nome, damage, acc, range, weight, rof, shots, bulk, rcl, cost, details });
        }
    });

    // Criar o JSON
    const jsonData = JSON.stringify(equipamentosRanged);

    // Exibir o JSON no console para depuração
    console.log("Equipamentos Ranged JSON:", jsonData);

    // Adicionar o JSON a um campo oculto no formulário
    let jsonField = document.getElementById("id_equipment_ranged");
    if (!jsonField) {
        jsonField = document.createElement("input");
        jsonField.type = "hidden";
        jsonField.name = "equipment_ranged";
        jsonField.id = "id_equipment_ranged";
        this.appendChild(jsonField);
    }

    jsonField.value = jsonData;

    // Exibir no console o valor do campo oculto antes de enviar o formulário
    console.log("Valor do campo oculto:", jsonField.value);

    // Enviar o formulário
    this.submit();
});
