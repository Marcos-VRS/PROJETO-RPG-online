document.addEventListener('DOMContentLoaded', function () {
    // Captura os elementos de entrada para cada atributo
    const id_st = document.getElementById('id_st'); // Campo ST (resultado)
    const id_xp_st = document.getElementById('id_xp_st'); // Campo XP ST (entrada do usuário)
    const id_dx = document.getElementById('id_dx'); // Campo DX (resultado)
    const id_xp_dx = document.getElementById('id_xp_dx'); // Campo XP DX (entrada do usuário)
    const id_iq = document.getElementById('id_iq'); // Campo IQ (resultado)
    const id_xp_iq = document.getElementById('id_xp_iq'); // Campo XP IQ (entrada do usuário)
    const id_ht = document.getElementById('id_ht'); // Campo HT (resultado)
    const id_xp_ht = document.getElementById('id_xp_ht'); // Campo XP HT (entrada do usuário)

    // Função genérica para calcular o valor de um atributo
    function calcularAtributo(xpInput, atributoOutput, fatorXP) {
        // Obtém o valor do XP, garantindo que seja um número
        const xp = parseFloat(xpInput.value) || 0; // Assume 0 se o campo estiver vazio ou inválido

        // Calcula o valor do atributo com base no fatorXP e arredonda
        const novoValor = Math.floor(10 + xp / fatorXP);

        // Atualiza o campo do atributo com o novo valor
        atributoOutput.value = novoValor;
    }

    // Adiciona os eventos 'input' para cada campo de XP
    id_xp_st.addEventListener('input', () => calcularAtributo(id_xp_st, id_st, 10)); // ST: 10 XP por ponto
    id_xp_dx.addEventListener('input', () => calcularAtributo(id_xp_dx, id_dx, 20)); // DX: 20 XP por ponto
    id_xp_iq.addEventListener('input', () => calcularAtributo(id_xp_iq, id_iq, 20)); // IQ: 20 XP por ponto
    id_xp_ht.addEventListener('input', () => calcularAtributo(id_xp_ht, id_ht, 10)); // HT: 10 XP por ponto
});
