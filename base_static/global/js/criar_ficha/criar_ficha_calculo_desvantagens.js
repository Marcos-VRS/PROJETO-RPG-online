document.addEventListener('DOMContentLoaded', function () {
    const containerDesvantagens = document.getElementById('desvantagens-container');
    const totalDesvantagensLabel = document.getElementById('total_de_desvantagens'); // Campo onde o total será exibido

    // Função para calcular o total de pontos de desvantagens
    function calcularTotalDesvantagens() {
        let total = 0;

        // Seleciona todos os campos de desvantagens_valor[]
        const camposValores = containerDesvantagens.querySelectorAll('input[name="desvantagens_valor[]"]');

        camposValores.forEach(campo => {
            const valor = parseInt(campo.value) || 0; // Converte para inteiro, usa 0 se o campo estiver vazio
            total += valor;
        });

        totalDesvantagensLabel.textContent = total; // Atualiza o valor no campo
    }

    // Adiciona um evento de input nos campos de desvantagens_valor[]
    containerDesvantagens.addEventListener('input', function (event) {
        if (event.target.name === 'desvantagens_valor[]') {
            calcularTotalDesvantagens(); // Recalcula sempre que um valor for alterado
        }
    });

    // Faz o cálculo inicial quando a página é carregada
    calcularTotalDesvantagens();
});
