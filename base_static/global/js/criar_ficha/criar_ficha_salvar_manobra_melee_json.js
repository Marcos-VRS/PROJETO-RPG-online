document.querySelector("form").addEventListener("submit", function (event) {
    // Prevenir o envio do formulário para capturar os dados primeiro
    event.preventDefault();

    // Capturar todas as manobras de ataque (tanto as estáticas quanto as dinâmicas)
    const manobrasMelee = [];

    // Selecionar todas as linhas de manobras, incluindo as dinâmicas
    const linhasManobras = document.querySelectorAll(".manobra-ataque-melee-id");

    linhasManobras.forEach(linha => {
        // Captura os dados de cada linha de manobra
        const nome = linha.querySelector("input[name='nome_manobra_melee[]']").value.trim();
        const damage = linha.querySelector("input[name='damage_manobra_melee[]']").value.trim();
        const nh = linha.querySelector("input[name='nh_manobra_melee[]']").value.trim();
        const detalhes = linha.querySelector("textarea[name='detalhes_manobra_melee[]']").value.trim();

        // Adicionar os dados da manobra ao array somente se pelo menos um campo estiver preenchido
        if (nome || damage || nh || detalhes) {
            manobrasMelee.push({ nome, damage, nh, detalhes });
        }
    });

    // Criar o JSON com as manobras
    const jsonData = JSON.stringify(manobrasMelee);

    // Exibir o JSON no console para depuração
    console.log("Manobras Melee JSON:", jsonData);

    // Adicionar o JSON ao campo oculto no formulário para envio
    let jsonField = document.getElementById("id_manobras_melee");
    if (!jsonField) {
        jsonField = document.createElement("input");
        jsonField.type = "hidden";
        jsonField.name = "maneuvers_melee"; // O nome do campo que será enviado
        jsonField.id = "id_manobras_melee";
        this.appendChild(jsonField);
    }

    jsonField.value = jsonData;

    // Exibir o valor do campo oculto no console antes de enviar
    console.log("Valor do campo oculto:", jsonField.value);

    // Enviar o formulário
    this.submit();
});
