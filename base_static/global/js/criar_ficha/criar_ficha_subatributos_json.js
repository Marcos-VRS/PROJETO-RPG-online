document.querySelector("form").addEventListener("submit", function (event) {
    // Prevenir o envio inicial
    event.preventDefault();

    // Capturar os valores dos campos subatributos
    const subatributos = {};
    const inputs = document.querySelectorAll("input[name^='subatributos']");

    inputs.forEach(input => {
        const key = input.name.match(/\[([^\]]+)\]/)[1]; // Extrai a chave dentro dos colchetes
        const value = input.value.trim(); // Obtém o valor e remove espaços
        subatributos[key] = value || null; // Se vazio, armazena como null
    });

    // Criar o JSON
    const jsonData = JSON.stringify(subatributos);

    // Adicionar o JSON a um campo oculto no formulário
    let jsonField = document.getElementById("id_sub_attributes");
    if (!jsonField) {
        jsonField = document.createElement("input");
        jsonField.type = "hidden";
        jsonField.name = "sub_attributes";
        jsonField.id = "id_sub_attributes";
        this.appendChild(jsonField);
    }

    jsonField.value = jsonData;

    // Enviar o formulário
    this.submit();
});
