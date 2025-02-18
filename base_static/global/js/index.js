document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.li-menu a').forEach(link => {
        // Se for o link "Fichas", não intercepta a requisição
        if (link.id === "fichas") {
            return;
        }

        link.addEventListener('click', function (event) {
            if (this.href.includes('logout')) {
                document.querySelector('.menu-container').style.display = 'none';
            }

            event.preventDefault();

            const url = this.href;

            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(response => response.text())
                .then(html => {
                    document.querySelector('.main-content').innerHTML = html;
                })
                .catch(error => console.warn("Erro ao carregar conteúdo:", error));
        });
    });
});
