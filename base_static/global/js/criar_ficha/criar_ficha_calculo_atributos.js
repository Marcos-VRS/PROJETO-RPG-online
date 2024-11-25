document.addEventListener('DOMContentLoaded', () => {
    // IDs dos campos de pontos gastos nos atributos
    const idsPontosGastos = ['id_xp_st', 'id_xp_dx', 'id_xp_iq', 'id_xp_ht'];

    // Campo para exibir o total de pontos de atributo
    const totalPontosAtributo = document.getElementById('pontos_de_atributo');

    // Função para calcular os pontos de atributo
    function calcularPontosDeAtributo() {
        let total = 0;

        idsPontosGastos.forEach(id => {
            const campo = document.getElementById(id);
            if (campo) {
                const valor = parseInt(campo.value) || 0; // Converte para número ou usa 0 como padrão
                total += valor;
            }
        });

        // Atualiza o campo "pontos_de_atributo" com o total calculado
        if (totalPontosAtributo) {
            totalPontosAtributo.textContent = total;
        }
    }

    // Adiciona um evento "input" para recalcular ao alterar qualquer campo de pontos gastos
    idsPontosGastos.forEach(id => {
        const campo = document.getElementById(id);
        if (campo) {
            campo.addEventListener('input', calcularPontosDeAtributo);
        }
    });

    // Calcula o valor inicial ao carregar a página
    calcularPontosDeAtributo();
});
