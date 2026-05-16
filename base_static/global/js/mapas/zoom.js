document.addEventListener('DOMContentLoaded', () => {
    const image = document.getElementById('map-image');
    if (!image) return;

    let scale = 1;
    const scaleFactor = 0.06;
    let animationFrameId = null;

    // Seletores de UI que devem rolar normalmente (sem zoom no mapa)
    // quando o cursor está sobre eles. closest() é resiliente a elementos
    // criados depois do DOMContentLoaded (menu-modal, .janela dinâmica, etc.).
    const UI_SELECTOR = [
        '.chat-container',
        '.chat-container-submit',
        '.janela',
        '.personagem-container',
        '.personagem-container-gm',
        '.player-side-nav',
        '.menu-modal',
        '.menu-modal-backdrop',
        '.players-bar',
        '.turn-controls',
    ].join(',');

    function zoom(event) {
        const t = event.target;
        if (t instanceof Element && t.closest(UI_SELECTOR)) {
            // Cursor está sobre UI scrollável — deixa o navegador rolar.
            // NÃO chama preventDefault, pra não bloquear o scroll natural.
            return;
        }

        event.preventDefault();

        const rect = image.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;
        const offsetX = (mouseX / rect.width) * 100;
        const offsetY = (mouseY / rect.height) * 100;

        if (event.deltaY < 0) {
            scale += scaleFactor;
        } else {
            scale -= scaleFactor;
            if (scale < 0.5) {
                scale = 0.5;
            }
        }

        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
        }
        animationFrameId = requestAnimationFrame(() => {
            image.style.transformOrigin = `${offsetX}% ${offsetY}%`;
            image.style.transform = `scale(${scale})`;
        });
    }

    image.style.transition = "transform 0.2s ease-out";
    document.addEventListener('wheel', zoom, { passive: false });
});
