document.addEventListener('DOMContentLoaded', function () {
    const containerVantagens = document.getElementById('vantagens-container');
    const totalVantagensLabel = document.getElementById('total_de_vantagens'); // Campo onde o total será exibido

    // Função para calcular o total de vantagens
    function calcularTotalVantagens() {
        let total = 0;

        // Seleciona todos os campos de vantagens_valor[]
        const camposValores = containerVantagens.querySelectorAll('input[name="vantagens_valor[]"]');

        camposValores.forEach(campo => {
            const valor = parseInt(campo.value) || 0; // Converte para inteiro, usa 0 se o campo estiver vazio
            total += valor;
        });

        totalVantagensLabel.textContent = total; // Atualiza o valor no campo
    }

    // Adiciona um evento de input nos campos de vantagens_valor[]
    containerVantagens.addEventListener('input', function (event) {
        if (event.target.name === 'vantagens_valor[]') {
            calcularTotalVantagens(); // Recalcula sempre que um valor for alterado
        }
    });

    // Faz o cálculo inicial quando a página é carregada
    calcularTotalVantagens();
});
