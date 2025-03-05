document.addEventListener('DOMContentLoaded', () => {
    const image = document.getElementById('map-image');
    let scale = 1;
    const scaleFactor = 0.1;

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

        // Aplica o zoom mantendo o ponto do mouse como referência
        image.style.transformOrigin = `${offsetX}% ${offsetY}%`;
        image.style.transform = `scale(${scale})`;
    }

    // Ouvinte de evento global para o zoom (independente da posição do mouse)
    document.addEventListener('wheel', zoom);
});
