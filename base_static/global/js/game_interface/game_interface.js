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

// Fechar ao clicar fora de qualquer .janela ativa.
// Ignora cliques na própria janela e nos botões da side nav / barra antiga
// que abrem janelas (senão fecha imediatamente após abrir).
document.addEventListener('mousedown', function (event) {
    const ativa = document.querySelector('.janela.ativa');
    if (!ativa) return;
    const t = event.target;
    if (!(t instanceof Element)) return;
    // Clique dentro da janela aberta → não faz nada
    if (t.closest('.janela.ativa')) return;
    // Clique em algo que abre janela → deixa o handler dela cuidar
    if (t.closest('.player-side-icon, .menu-button, .menu-button-gm, [onclick*="abrirJanela"], [onclick*="abrirJanelaSecundario"]')) return;
    fecharJanela();
});


