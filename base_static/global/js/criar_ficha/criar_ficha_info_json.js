document.querySelector("form").addEventListener("submit", function (event) {
    // Prevenir o envio inicial
    event.preventDefault();

    // Capturar os valores dos campos
    const aparencia = document.getElementById("id_aparencia").value;
    const idade = document.getElementById("id_idade").value;

    // Criar o JSON
    const jsonData = JSON.stringify({ aparencia: aparencia, idade: idade });

    // Adicionar o JSON a um campo oculto no formulário
    let jsonField = document.getElementById("id_aparencia_idade");
    if (!jsonField) {
        jsonField = document.createElement("input");
        jsonField.type = "hidden";
        jsonField.name = "aparencia_idade";
        jsonField.id = "id_aparencia_idade";
        this.appendChild(jsonField);
    }
    jsonField.value = jsonData;

    // Enviar o formulário
    this.submit();
});
