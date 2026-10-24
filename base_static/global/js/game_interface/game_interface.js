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

/* ============================================================
   JOURNAL — filtro por nome + lightbox (2026-08-09)
   ============================================================ */
function rd6FilterJournal(scope) {
    var input = document.getElementById('search-journal-' + scope);
    var root = document.getElementById('janela-journal-' + scope);
    if (!input || !root) return;
    var q = (input.value || '').toLowerCase().trim();
    root.querySelectorAll('.journal-card').forEach(function (card) {
        var n = card.getAttribute('data-nome') || '';
        card.style.display = (!q || n.indexOf(q) !== -1) ? '' : 'none';
    });
}

function rd6OpenLightbox(src, alt, text, title) {
    var lb = document.getElementById('journal-lightbox');
    if (!lb) return;
    var img = lb.querySelector('.jlb-img');
    if (img) { img.src = src; img.alt = alt || ''; }
    var titleEl = lb.querySelector('.jlb-title');
    var textEl = lb.querySelector('.jlb-text');
    if (titleEl) titleEl.textContent = title || '';
    if (textEl) textEl.textContent = text || '';
    var panel = lb.querySelector('.jlb-panel');
    var hasText = !!((title && title.trim()) || (text && text.trim()));
    if (panel) panel.hidden = !hasText;
    lb.classList.toggle('jlb-has-text', hasText);
    lb.classList.add('ativa');
}
function rd6CloseLightbox() {
    var lb = document.getElementById('journal-lightbox');
    if (lb) lb.classList.remove('ativa');
}

// DELEGAÇÃO: funciona mesmo quando os cards do journal são reconstruídos
// (rd6OpenJournal recarrega a lista). Clicar na miniatura expande a imagem
// numa janela grande, com o nome + descrição ao lado (se houver).
document.addEventListener('click', function (e) {
    if (!e.target || !e.target.closest) return;
    var thumb = e.target.closest('.journal-thumb');
    if (thumb) {
        var img = thumb.querySelector('img');
        if (!img) return;  // card "sem imagem" — nada a expandir
        e.stopPropagation();  // não fecha a modal do journal atrás
        var card = thumb.closest('.journal-card');
        var nameEl = card && card.querySelector('.journal-card-name');
        var descEl = card && card.querySelector('.journal-card-desc');
        rd6OpenLightbox(img.src, img.alt,
            descEl ? descEl.textContent : '',
            nameEl ? nameEl.textContent : '');
        return;
    }
    // Fecha ao clicar no fundo do lightbox ou no ×; clicar na imagem/texto não fecha.
    var lb = document.getElementById('journal-lightbox');
    if (lb && lb.classList.contains('ativa')) {
        if (e.target === lb || e.target.closest('.jlb-close')) {
            e.stopPropagation();
            rd6CloseLightbox();
        }
    }
});

// ESC fecha o lightbox PRIMEIRO (capture roda antes do ESC que fecha janelas).
document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var lb = document.getElementById('journal-lightbox');
    if (lb && lb.classList.contains('ativa')) {
        e.stopPropagation();
        rd6CloseLightbox();
    }
}, true);


