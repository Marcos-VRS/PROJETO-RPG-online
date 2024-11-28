document.querySelector("form").addEventListener("submit", function (event) {
    // Prevenir o envio inicial
    event.preventDefault();

    // Capturar os valores dos campos
    const st = document.getElementById("id_st").value;
    const xpst = document.getElementById("id_xp_st").value;
    const stbonus = document.getElementById("id_st_bonus").value;

    const dx = document.getElementById("id_dx").value;
    const xpdx = document.getElementById("id_xp_dx").value;
    const dxbonus = document.getElementById("id_dx_bonus").value;

    const iq = document.getElementById("id_iq").value;
    const xpiq = document.getElementById("id_xp_iq").value;
    const iqbonus = document.getElementById("id_iq_bonus").value;

    const ht = document.getElementById("id_ht").value;
    const xpht = document.getElementById("id_xp_ht").value;
    const htbonus = document.getElementById("id_ht_bonus").value;


    // Criar o JSON
    const jsonData = JSON.stringify({
        ST: st,
        XP_ST: xpst,
        ST_Bonus: stbonus,
        DX: dx,
        XP_DX: xpdx,
        DX_Bonus: dxbonus,
        IQ: iq,
        XP_IQ: xpiq,
        IQ_Bonus: iqbonus,
        HT: ht,
        XP_HT: xpht,
        HT_Bonus: htbonus,
    });

    // Adicionar o JSON a um campo oculto no formulário
    let jsonField = document.getElementById("id_atributos");
    if (!jsonField) {
        jsonField = document.createElement("input");
        jsonField.type = "hidden";
        jsonField.name = "atributos";
        jsonField.id = "id_atributos";
        this.appendChild(jsonField);
    }
    jsonField.value = jsonData;

    // Enviar o formulário
    this.submit();
});
