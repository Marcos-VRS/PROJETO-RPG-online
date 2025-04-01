function abrirJanela(tipo) {
    // Esconde todas as janelas antes de abrir uma nova
    document.querySelectorAll('.janela').forEach(j => j.classList.remove('ativa'));

    let janela = document.getElementById(`janela-${tipo}`);

    if (janela) {
        janela.classList.add('ativa');
        console.log(`Janela ${tipo} aberta`);
    } else {
        console.error(`Erro: Elemento #janela-${tipo} não encontrado!`);
    }
}

// Função para fechar qualquer janela aberta
function fecharJanela() {
    document.querySelectorAll('.janela').forEach(j => j.classList.remove('ativa'));
}

// Fechar ao pressionar a tecla ESC
document.addEventListener('keydown', function (event) {
    if (event.key === "Escape") {
        fecharJanela();
    }
});
