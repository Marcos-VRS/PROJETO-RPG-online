document.addEventListener('DOMContentLoaded', function () {
    const btnAdicionarVantagem = document.getElementById('adicionar-vantagem');
    const containerVantagens = document.getElementById('vantagens-container');

    // Função para adicionar uma nova linha de inputs para as vantagens
    function adicionarVantagem() {
        const novaVantagem = document.createElement('div');
        novaVantagem.classList.add('form-field', 'vantagem-linha');

        novaVantagem.innerHTML = `
            <input type="text" name="vantagens_nome[]" class="campo-curto-vantagem medievalsharp-regular" placeholder="Nome da vantagem" />
            <input type="number" name="vantagens_valor[]" class="campo-curto-valor-vantagem medievalsharp-regular" placeholder="Valor da vantagem" />
        `;

        containerVantagens.appendChild(novaVantagem);
    }

    // Adiciona um ouvinte de evento para o botão de adicionar vantagem
    btnAdicionarVantagem.addEventListener('click', adicionarVantagem);
});
