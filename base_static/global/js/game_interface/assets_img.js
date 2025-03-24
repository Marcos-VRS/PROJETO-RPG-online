document.addEventListener("DOMContentLoaded", function () {
    var assets = document.querySelectorAll(".ficha-parte-box-journal .asset-line img"); // Seleciona todas as imagens dentro da ficha

    assets.forEach(function (img) {
        if (!img.src || img.src === "#" || img.complete === false) {
            img.style.display = 'none';  // Esconde a imagem se não houver uma válida
        } else {
            img.style.display = 'block';
        }
    });
});
