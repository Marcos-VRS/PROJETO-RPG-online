document.querySelector("form").addEventListener("submit", function (event) {
    // Prevenir o envio inicial
    event.preventDefault();

    // Capturar os nomes e valores das desvantagens
    const desvantagens = [];
    const desvantagemLinhas = document.querySelectorAll("#desvantagens-container .desvantagem-linha");

    desvantagemLinhas.forEach(linha => {
        const nome = linha.querySelector("input[name='desvantagens_nome[]']").value.trim();
        const valor = linha.querySelector("input[name='desvantagens_valor[]']").value.trim();
        if (nome || valor) { // Inclui apenas se pelo menos um campo não estiver vazio
            desvantagens.push({ nome, valor });
        }
    });

    // Criar o JSON
    const jsonData = JSON.stringify(desvantagens);

    // Adicionar o JSON a um campo oculto no formulário
    let jsonField = document.getElementById("id_desvantagens");
    if (!jsonField) {
        jsonField = document.createElement("input");
        jsonField.type = "hidden";
        jsonField.name = "disadvantages";
        jsonField.id = "id_desvantagens";
        this.appendChild(jsonField);
    }

    jsonField.value = jsonData;

    // Enviar o formulário
    this.submit();
});
