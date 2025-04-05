document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("search-campanha");
    const campanhas = document.querySelectorAll(".item-lista");

    input.addEventListener("input", function () {
        const filtro = input.value.toLowerCase();

        campanhas.forEach(campanha => {
            const titulo = campanha.querySelector(".personagem-nome").textContent.toLowerCase();

            if (titulo.includes(filtro)) {
                campanha.style.display = ""; // Mostra o item
            } else {
                campanha.style.display = "none"; // Esconde completamente
            }
        });
    });
});
