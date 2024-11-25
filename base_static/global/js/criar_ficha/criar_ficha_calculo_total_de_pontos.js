document.addEventListener('DOMContentLoaded', function () {
    const totalVantagensLabel = document.getElementById('total_de_vantagens');
    const totalDesvantagensLabel = document.getElementById('total_de_desvantagens');
    const totalAtributosLabel = document.getElementById('pontos_de_atributo');
    const totalPericiasLabel = document.getElementById('pontos_de_pericias');
    const totalPontosLabel = document.getElementById('total_de_pontos'); // Campo onde o total geral será exibido

    // Função para calcular o total de pontos gerais
    function calcularTotalPontos() {
        const totalVantagens = parseInt(totalVantagensLabel.textContent) || 0;
        const totalDesvantagens = parseInt(totalDesvantagensLabel.textContent) || 0;
        const totalAtributos = parseInt(totalAtributosLabel.textContent) || 0;
        const totalPericias = parseInt(totalPericiasLabel.textContent) || 0;

        const total = totalVantagens + totalDesvantagens + totalAtributos + totalPericias;
        totalPontosLabel.textContent = total; // Atualiza o total de pontos
    }

    // Observa mudanças nos subtotais e recalcula o total geral
    function adicionarObservadores() {
        [totalVantagensLabel, totalDesvantagensLabel, totalAtributosLabel, totalPericiasLabel].forEach(label => {
            const observer = new MutationObserver(calcularTotalPontos);
            observer.observe(label, { characterData: true, childList: true });
        });
    }

    // Inicializa os cálculos e observadores
    calcularTotalPontos();
    adicionarObservadores();
});
