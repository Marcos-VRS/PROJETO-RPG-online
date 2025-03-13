document.addEventListener('DOMContentLoaded', () => {
    const image = document.getElementById('map-image');
    const chatContainer = document.getElementById('chat-container-id'); // Obtém a div do chat
    const personagemContainer = document.querySelector('.personagem-container-gm') || document.querySelector('.personagem-container'); // Obtém a div do personagem
    const janelaElements = document.querySelectorAll('.janela'); // Todos os elementos com a classe "janela"


    console.log('Esse é o image:', image);
    console.log('Esse é o chatContainer:', chatContainer);
    console.log('Esse é o personagemContainer:', personagemContainer);
    console.log('Esses são os janelaElements:', janelaElements);
    let scale = 1;
    const scaleFactor = 0.06; // Zoom mais gradual
    let animationFrameId = null;
    let isMouseOverChat = false;
    let isMouseOverJanela = false;
    let isMouseOverPersonagem = false;

    // Detecta quando o mouse entra e sai do chat
    chatContainer.addEventListener('mouseenter', () => isMouseOverChat = true);
    chatContainer.addEventListener('mouseleave', () => isMouseOverChat = false);

    // Detecta quando o mouse entra e sai dos elementos com a classe "janela"
    janelaElements.forEach(janela => {
        janela.addEventListener('mouseenter', () => isMouseOverJanela = true);
        janela.addEventListener('mouseleave', () => isMouseOverJanela = false);
    });

    // Detecta quando o mouse entra e sai da div .personagem-container-gm
    personagemContainer.addEventListener('mouseenter', () => isMouseOverPersonagem = true);
    personagemContainer.addEventListener('mouseleave', () => isMouseOverPersonagem = false);

    function zoom(event) {
        // Impede o zoom se o mouse estiver sobre o chat, a div personagem-container-gm ou uma janela
        if (isMouseOverChat || isMouseOverJanela || isMouseOverPersonagem) return;

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
    document.addEventListener('wheel', zoom, { passive: false });
});
