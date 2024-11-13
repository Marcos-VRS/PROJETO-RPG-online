document.addEventListener('DOMContentLoaded', () => {
    // Seleciona todos os links do menu
    document.querySelectorAll('.li-menu a').forEach(link => {
        link.addEventListener('click', function (event) {
            // Verifica se o link é o de logout
            if (this.href.includes('logout')) {
                // Oculta o menu antes de redirecionar
                document.querySelector('.menu-container').style.display = 'none';
            }

            event.preventDefault(); // Evita o carregamento normal

            const url = this.href; // Obtém a URL do link clicado

            // Faz a requisição AJAX para carregar o conteúdo
            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest' // Identifica como requisição AJAX
                }
            })
                .then(response => response.text()) // Converte para texto
                .then(html => {
                    document.querySelector('.main-content').innerHTML = html; // Insere na div
                })
                .catch(error => console.warn("Erro ao carregar conteúdo:", error));
        });
    });
});
