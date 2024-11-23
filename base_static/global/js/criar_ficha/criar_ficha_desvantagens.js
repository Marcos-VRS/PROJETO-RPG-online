
document.addEventListener('DOMContentLoaded', function () {
    const btnAdicionarDesvantagem = document.getElementById('adicionar-desvantagem');
    const containerDesvantagens = document.getElementById('desvantagens-container');

    // Função para adicionar uma nova linha de inputs para as desvantagens
    function adicionarDesvantagem() {
        const novaDesvantagem = document.createElement('div');
        novaDesvantagem.classList.add('form-field', 'desvantagem-linha');

        novaDesvantagem.innerHTML = `
            <input type="text" name="desvantagens_nome[]" class="campo-curto-vantagem medievalsharp-regular" placeholder="Nome da desvantagem" />
            <input type="text" name="desvantagens_valor[]"  class="campo-curto-valor-vantagem medievalsharp-regular" placeholder="Valor" />
        `;

        containerDesvantagens.appendChild(novaDesvantagem);
    }

    // Adiciona um ouvinte de evento para o botão de adicionar desvantagem
    btnAdicionarDesvantagem.addEventListener('click', adicionarDesvantagem);
});
