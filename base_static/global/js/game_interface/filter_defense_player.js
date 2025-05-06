function filtrarDefesa() {
    let input = document.getElementById('search-defense').value.toLowerCase(); // Obtém o texto digitado e converte para minúsculas
    let assets = document.querySelectorAll('.ficha-parte-box-defesa'); // Seleciona todos os assets


    console.log(input, assets); // Adiciona log para verificar os assets selecionados

    assets.forEach(asset => {
        let nomeAsset = asset.querySelector('.medievalsharp-large').textContent.trim().toLowerCase(); // Obtém o nome do asset

        if (nomeAsset.includes(input)) {
            asset.style.visibility = "visible"; // Mantém visível
            asset.style.position = "static"; // Mantém a posição
        } else {
            asset.style.visibility = "hidden"; // Esconde sem remover completamente
            asset.style.position = "absolute"; // Remove do fluxo visual
        }
    });
}
