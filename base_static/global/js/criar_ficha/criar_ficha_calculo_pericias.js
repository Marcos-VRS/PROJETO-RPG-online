document.addEventListener('DOMContentLoaded', function () {
    const containerPericias = document.getElementById('pericias-container');
    const totalPericiasLabel = document.getElementById('pontos_de_pericias'); // Campo onde o total será exibido

    // Função para calcular o total de pontos de perícias
    function calcularTotalPericias() {
        let total = 0;

        // Seleciona todos os campos de pericias_custo[]
        const camposCustos = containerPericias.querySelectorAll('input[name="pericias_custo[]"]');

        camposCustos.forEach(campo => {
            const valor = parseInt(campo.value) || 0; // Converte para inteiro, usa 0 se o campo estiver vazio
            total += valor;
        });

        totalPericiasLabel.textContent = total; // Atualiza o valor no campo
    }

    // Adiciona um evento de input nos campos de pericias_custo[]
    containerPericias.addEventListener('input', function (event) {
        if (event.target.name === 'pericias_custo[]') {
            calcularTotalPericias(); // Recalcula sempre que um valor for alterado
        }
    });

    // Faz o cálculo inicial quando a página é carregada
    calcularTotalPericias();
});
