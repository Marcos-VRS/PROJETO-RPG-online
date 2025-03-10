function filtrarPersonagens() {
    let input = document.getElementById('search-personagem').value.toLowerCase();
    console.log(input);
    let personagens = document.querySelectorAll('.menu-button-gm');
    console.log(personagens);

    personagens.forEach(botao => {
        let nomePersonagem = botao.textContent.trim().toLocaleLowerCase(); // Remove espaços extras antes e depois
        console.log(`[${nomePersonagem}]`); // Exibe os nomes entre colchetes para ver os espaços

        if (nomePersonagem.includes(input)) {
            botao.style.visibility = "visible"; // Apenas esconde visualmente
            botao.style.position = "static"; // Mantém a posição original
        } else {
            botao.style.visibility = "hidden"; // Torna invisível sem alterar o layout
            botao.style.position = "absolute"; // Remove o botão visualmente sem ocupar espaço
        }
    });
}
