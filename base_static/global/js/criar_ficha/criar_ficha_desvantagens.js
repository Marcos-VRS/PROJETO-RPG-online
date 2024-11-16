
document.addEventListener('DOMContentLoaded', function () {
    const btnAdicionarDesvantagem = document.getElementById('adicionar-desvantagem');
    const containerDesvantagens = document.getElementById('desvantagens-container');

    // Função para adicionar uma nova linha de inputs para as desvantagens
    function adicionarDesvantagem() {
        const novaDesvantagem = document.createElement('div');
        novaDesvantagem.classList.add('form-field', 'desvantagem-linha');

        novaDesvantagem.innerHTML = `
            <input type="text" name="desvantagens_nome[]" class="desvantagem-nome" placeholder="Nome da desvantagem" />
            <input type="number" name="desvantagens_valor[]" class="desvantagem-valor" placeholder="Valor da desvantagem" />
        `;

        containerDesvantagens.appendChild(novaDesvantagem);
    }

    // Adiciona um ouvinte de evento para o botão de adicionar desvantagem
    btnAdicionarDesvantagem.addEventListener('click', adicionarDesvantagem);
});
