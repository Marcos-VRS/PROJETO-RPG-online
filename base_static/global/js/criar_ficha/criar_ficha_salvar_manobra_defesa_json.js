document.querySelector("form").addEventListener("submit", function (event) {
    // Prevenir o envio do formulário para capturar os dados primeiro
    event.preventDefault();

    // Capturar todas as manobras de ataque (tanto as estáticas quanto as dinâmicas)
    const manobrasDefesa = [];

    // Selecionar todas as linhas de manobras, incluindo as dinâmicas
    const linhasManobras = document.querySelectorAll(".manobra-defesa-id");

    linhasManobras.forEach(linha => {
        // Captura os dados de cada linha de manobra
        const nome = linha.querySelector("input[name='nome_manobra_defesa[]']").value.trim();
        const nh = linha.querySelector("input[name='nh_manobra_defesa[]']").value.trim();
        const detalhes = linha.querySelector("textarea[name='detalhes_manobra_defesa[]']").value.trim();

        // Adicionar os dados da manobra ao array somente se pelo menos um campo estiver preenchido
        if (nome || nh || detalhes) {
            manobrasDefesa.push({ nome, nh, detalhes });
        }
    });

    // Criar o JSON com as manobras
    const jsonData = JSON.stringify(manobrasDefesa);

    // Exibir o JSON no console para depuração
    console.log("Manobras Defense JSON:", jsonData);

    // Adicionar o JSON ao campo oculto no formulário para envio
    let jsonField = document.getElementById("id_manobras_defesa");
    if (!jsonField) {
        jsonField = document.createElement("input");
        jsonField.type = "hidden";
        jsonField.name = "maneuvers_defense"; // O nome do campo que será enviado
        jsonField.id = "id_manobras_defense";
        this.appendChild(jsonField);
    }

    jsonField.value = jsonData;

    // Exibir o valor do campo oculto no console antes de enviar
    console.log("Valor do campo oculto:", jsonField.value);

    // Enviar o formulário
    this.submit();
});
