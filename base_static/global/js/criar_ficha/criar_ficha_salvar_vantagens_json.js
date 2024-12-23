document.querySelector("form").addEventListener("submit", function (event) {
    // Prevenir o envio inicial
    event.preventDefault();

    // Capturar as vantagens e seus modificadores
    const vantagens = [];
    const vantagemLinhas = document.querySelectorAll("#vantagens-container .vantagem-linha");

    vantagemLinhas.forEach(linha => {
        const nome = linha.querySelector("input[name='vantagens_nome[]']").value.trim();
        const valor = linha.querySelector("input[name='vantagens_valor[]']").value.trim();

        // Capturar os modificadores desta vantagem
        const modificadores = [];
        let proxElemento = linha.nextElementSibling;

        while (proxElemento && proxElemento.classList.contains("mod-container")) {
            const modTexto = proxElemento.querySelector("textarea[name='mod[]']").value.trim();
            if (modTexto) { // Inclui o modificador somente se não estiver vazio
                modificadores.push(modTexto);
            }
            proxElemento = proxElemento.nextElementSibling;
        }

        // Adicionar a vantagem somente se nome, valor ou modificadores existirem
        if (nome || valor || modificadores.length > 0) {
            vantagens.push({ nome, valor, modificadores });
        }
    });

    // Criar o JSON
    const jsonData = JSON.stringify(vantagens);

    // Adicionar o JSON a um campo oculto no formulário
    let jsonField = document.getElementById("id_vantagens");
    if (!jsonField) {
        jsonField = document.createElement("input");
        jsonField.type = "hidden";
        jsonField.name = "advantages";
        jsonField.id = "id_vantagens";
        this.appendChild(jsonField);
    }

    jsonField.value = jsonData;

    // Enviar o formulário
    this.submit();
});
