document.addEventListener('DOMContentLoaded', () => {
    const image = document.getElementById('map-image');
    let isDragging = false;
    let startX, startY, initialX, initialY;

    function startDrag(event) {
        if (event.button !== 0) return; // Apenas botão esquerdo inicia o arrasto
        isDragging = true;
        startX = event.clientX;
        startY = event.clientY;
        initialX = image.offsetLeft;
        initialY = image.offsetTop;
        image.style.cursor = 'grabbing';

        event.preventDefault(); // Impede interferência do botão direito
    }

    function drag(event) {
        if (!isDragging) return;
        const dx = event.clientX - startX;
        const dy = event.clientY - startY;
        image.style.position = 'absolute';
        image.style.left = `${initialX + dx}px`;
        image.style.top = `${initialY + dy}px`;
    }

    function endDrag(event) {
        if (event.button !== 0) return; // Apenas soltar o botão esquerdo para o arrasto
        isDragging = false;
        image.style.cursor = 'grab';
    }


    if (image) {
        image.addEventListener('mousedown', startDrag);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', endDrag);
    }
});
