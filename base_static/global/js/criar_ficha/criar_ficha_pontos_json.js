document.querySelector("form").addEventListener("submit", function (event) {
    //Prevenir o envio inicial
    event.preventDefault();

    //capturar os valores dos campos
    const pontosdacampanha = document.getElementById("pontos_da_campanha").textContent.trim();;
    const pontostotal = document.getElementById("total_de_pontos").textContent.trim();;
    const totalvantagens = document.getElementById("total_de_vantagens").textContent.trim();;
    const totaldesvantagens = document.getElementById("total_de_desvantagens").textContent.trim();;
    const totalpericias = document.getElementById("pontos_de_pericias").textContent.trim();;
    const totalatributos = document.getElementById("pontos_de_atributo").textContent.trim();;


    //Crirar o JSON
    const jsonData = JSON.stringify({
        pontos_da_campanha: pontosdacampanha,
        pontos_total: pontostotal,
        total_vantagens: totalvantagens,
        total_desvantagens: totaldesvantagens,
        total_pericias: totalpericias,
        total_atributos: totalatributos,
    })

    //Adicionar o JSON a um campo oculto no formulário 

    let jsonField = document.getElementById("id_pontos_soma");
    if (!jsonField) {
        jsonField = document.createElement("input");
        jsonField.type = "hidden";
        jsonField.name = "pontos_soma";
        jsonField.id = "id_pontos_soma";
        this.appendChild(jsonField);
    }

    jsonField.value = jsonData;

    //Enviar o formulário
    this.submit();

})