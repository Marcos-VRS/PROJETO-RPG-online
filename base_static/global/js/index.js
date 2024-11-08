document.addEventListener("DOMContentLoaded", function () {
    // Seleciona todos os links do menu
    const menuLinks = document.querySelectorAll(".menu-container ul li a");
    const mainContent = document.querySelector(".main-content");

    // Função para carregar o conteúdo de cada página
    function loadPage(url) {
        fetch(url)
            .then(response => response.text())
            .then(data => {
                mainContent.innerHTML = data;
            })
            .catch(error => {
                mainContent.innerHTML = "<p>Erro ao carregar a página.</p>";
                console.error("Erro ao carregar o conteúdo:", error);
            });
    }
})