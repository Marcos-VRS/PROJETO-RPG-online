document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById('search-journal');

    searchInput.addEventListener("input", function () {
        const input = searchInput.value.toLowerCase();
        const itens = document.querySelectorAll('.item-lista-journal');

        itens.forEach(item => {
            const texto = item.textContent.toLowerCase();

            if (texto.includes(input)) {
                item.style.display = "";
            } else {
                item.style.display = "none";
            }
        });
    });
});
