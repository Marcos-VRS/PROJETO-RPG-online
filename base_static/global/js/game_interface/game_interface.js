function abrirJanela(tipo) {
    // Esconde todas as janelas antes de abrir uma nova
    document.querySelectorAll('.janela').forEach(j => j.classList.remove('ativa'));

    // Exibe a janela correta
    document.getElementById(`janela-${tipo}`).classList.add('ativa');
}

function abrirJanelaSecundario(tipo) {
    // Esconde todas as janelas antes de abrir uma nova
    document.querySelectorAll('.janela').forEach(j => j.classList.remove('ativa'));

    // Exibe a janela correta
    document.getElementById(`janela-${tipo}`).classList.add('ativa');
}

// Função para fechar qualquer janela aberta
function fecharJanela() {
    document.querySelectorAll('.janela').forEach(j => j.classList.remove('ativa'));
}

// Função para fechar qualquer janela aberta
function fecharJanelaSecundario() {
    document.querySelectorAll('.janela').forEach(j => j.classList.remove('ativa'));
}

// Fechar ao pressionar a tecla ESC
document.addEventListener('keydown', function (event) {
    if (event.key === "Escape") {
        fecharJanela();
    }
});


