document.addEventListener("DOMContentLoaded", function () {
    var miniatura = document.getElementById('miniatura_imagem');
    if (miniatura.src === "#") {
        miniatura.style.display = 'none';  // Esconde a imagem se não houver miniatura
    } else {
        miniatura.style.display = 'block';
    }
});
