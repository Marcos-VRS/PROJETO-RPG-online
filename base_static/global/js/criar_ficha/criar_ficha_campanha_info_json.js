document.querySelector("form").addEventListener("submit", function (event) {
    //Prevenir o envio inicial
    event.preventDefault();

    //capturar os valores dos campos
    const playername = document.getElementById("player_name_id").textContent.trim();;
    const nomecampanha = document.getElementById("nome_campanha_id").textContent.trim();;
    const nomegm = document.getElementById("nome_gm_id").textContent.trim();;



    //Crirar o JSON
    const jsonData = JSON.stringify({
        player_name: playername,
        nome_campanha: nomecampanha,
        nome_gm: nomegm,
    })

    //Adicionar o JSON a um campo oculto no formulário 

    let jsonField = document.getElementById("id_info_campanha");
    if (!jsonField) {
        jsonField = document.createElement("input");
        jsonField.type = "hidden";
        jsonField.name = "info_campanha";
        jsonField.id = "id_info_campanha";
        this.appendChild(jsonField);
    }

    jsonField.value = jsonData;

    //Enviar o formulário
    this.submit();

})