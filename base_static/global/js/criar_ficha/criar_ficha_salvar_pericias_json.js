document.querySelector("form").addEventListener("submit", function (event) {
    // Prevenir o envio inicial
    event.preventDefault();

    // Capturar os valores das perícias
    const pericias = [];
    const periciaLinhas = document.querySelectorAll("#pericias-container .pericia-linha");

    periciaLinhas.forEach(linha => {
        const nome = linha.querySelector("input[name='pericias_nome[]']").value.trim();
        const atributoBase = linha.querySelector("select[name='pericias_atributo_base[]']").value;
        const dificuldade = linha.querySelector("select[name='pericias_dificuldade[]']").value;
        const custo = linha.querySelector("input[name='pericias_custo[]']").value;
        const nh = linha.querySelector("input[name='pericias_nh[]']").value;

        if (nome || atributoBase || dificuldade || custo || nh) { // Verifica se pelo menos um campo foi preenchido
            pericias.push({
                nome,
                atributoBase,
                dificuldade,
                custo: custo ? parseInt(custo) : null, // Converte para número, se existir
                nh: nh ? parseInt(nh) : null           // Converte para número, se existir
            });
        }
    });

    // Criar o JSON
    const jsonData = JSON.stringify(pericias);

    // Adicionar o JSON a um campo oculto no formulário
    let jsonField = document.getElementById("id_pericias");
    if (!jsonField) {
        jsonField = document.createElement("input");
        jsonField.type = "hidden";
        jsonField.name = "skills";
        jsonField.id = "id_pericias";
        this.appendChild(jsonField);
    }

    jsonField.value = jsonData;

    // Enviar o formulário
    this.submit();
});