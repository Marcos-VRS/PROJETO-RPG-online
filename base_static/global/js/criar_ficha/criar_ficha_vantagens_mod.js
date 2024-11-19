document.addEventListener('DOMContentLoaded', function () {
    const containerVantagens = document.getElementById('vantagens-container');

    // Função para adicionar uma caixa de texto de modificador abaixo do nome
    function adicionarModificador(event) {
        if (event.target.classList.contains('btn-adicionar-modificador')) {
            const parentLinha = event.target.closest('.vantagem-linha');

            // Verifica se já existe uma área de modificadores
            if (!parentLinha.querySelector('.modificadores-container')) {
                const modificadoresContainer = document.createElement('div');
                modificadoresContainer.classList.add('modificadores-container');

                modificadoresContainer.innerHTML = `
                    <input type="text" name="modificadores[]" class="campo-curto-modificador medievalsharp-regular" placeholder="Modificador" />
                `;

                parentLinha.appendChild(modificadoresContainer);
            }
        }
    }

    // Adiciona um ouvinte de evento ao container para delegar o clique no botão
    containerVantagens.addEventListener('click', adicionarModificador);
});
