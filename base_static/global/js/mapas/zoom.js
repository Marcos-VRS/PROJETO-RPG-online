document.addEventListener('DOMContentLoaded', (event) => {
    const image = document.getElementById('map-image');
    let scale = 1;
    const scaleFactor = 0.1;
    let isDragging = false;
    let startX, startY, initialX, initialY;

    function zoom(event) {
        event.preventDefault();

        if (event.deltaY < 0) {
            // Zoom in
            scale += scaleFactor;
        } else {
            // Zoom out
            scale -= scaleFactor;
            if (scale < 1) {
                scale = 1;
            }
        }

        image.style.transform = `scale(${scale})`;
    }

    function startDrag(event) {
        if (event.button === 0) { // Verifica se o botão esquerdo do mouse está pressionado
            isDragging = true;
            startX = event.clientX;
            startY = event.clientY;
            initialX = image.offsetLeft;
            initialY = image.offsetTop;
            image.style.cursor = 'grabbing'; // Muda o cursor para indicar que está arrastando
        }
    }

    function drag(event) {
        if (isDragging) {
            const dx = event.clientX - startX;
            const dy = event.clientY - startY;
            image.style.left = `${initialX + dx}px`;
            image.style.top = `${initialY + dy}px`;
        }
    }

    function endDrag() {
        isDragging = false;
        image.style.cursor = 'grab'; // Muda o cursor de volta para indicar que pode arrastar
    }

    if (image) {
        image.addEventListener('wheel', zoom);
        image.addEventListener('mousedown', startDrag);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', endDrag);
    }
});