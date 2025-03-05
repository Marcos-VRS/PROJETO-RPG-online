document.addEventListener('DOMContentLoaded', () => {
    const image = document.getElementById('map-image');
    let scale = 1;
    const scaleFactor = 0.06; // Zoom mais gradual
    let animationFrameId = null;

    function zoom(event) {
        event.preventDefault();

        // Obtém as coordenadas do mouse em relação à imagem
        const rect = image.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;

        // Obtém as coordenadas relativas ao centro da imagem
        const offsetX = (mouseX / rect.width) * 100;
        const offsetY = (mouseY / rect.height) * 100;

        // Define o novo scale (mantendo limites)
        if (event.deltaY < 0) {
            scale += scaleFactor; // Zoom in
        } else {
            scale -= scaleFactor; // Zoom out
            if (scale < 0.5) {
                scale = 0.5; // Permite zoom até 50% do tamanho original
            }
        }

        // Garante que a animação não seja executada várias vezes ao mesmo tempo
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
        }

        animationFrameId = requestAnimationFrame(() => {
            image.style.transformOrigin = `${offsetX}% ${offsetY}%`;
            image.style.transform = `scale(${scale})`;
        });
    }

    // Adiciona transição suave no CSS
    image.style.transition = "transform 0.2s ease-out";

    // Ouvinte de evento global para o zoom (independente da posição do mouse)
    document.addEventListener('wheel', zoom);
});
