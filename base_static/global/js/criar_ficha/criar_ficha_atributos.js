document.addEventListener('DOMContentLoaded', function () {
    // Captura os elementos de entrada
    const id_st = document.getElementById('id_st'); // Campo ST (resultado)
    const id_xp_st = document.getElementById('id_xp_st'); // Campo XP ST (entrada do usuário)
    const id_dx = document.getElementById('id_dx'); // Campo DX
    const id_xp_dx = document.getElementById('id_xp_dx'); // Campo XP DX
    const id_iq = document.getElementById('id_iq'); // Campo IQ
    const id_xp_iq = document.getElementById('id_xp_iq'); // Campo XP IQ
    const id_ht = document.getElementById('id_ht'); // Campo HT
    const id_xp_ht = document.getElementById('id_xp_ht'); // Campo XP HT

    // Função para calcular o valor de ST
    function calcularST() {
        const xp_st = parseFloat(id_xp_st.value) || 0; // Garantir que o valor seja 0 se inválido
        const novoST = Math.floor(10 + xp_st / 10); // Round down
        id_st.value = novoST;
    }

    // Função para calcular o valor de DX
    function calcularDX() {
        const xp_dx = parseFloat(id_xp_dx.value) || 0; // Garantir que o valor seja 0 se inválido
        const novoDX = Math.floor(10 + xp_dx / 20); // Round down
        id_dx.value = novoDX;
    }

    // Função para calcular o valor de IQ
    function calcularIQ() {
        const xp_iq = parseFloat(id_xp_iq.value) || 0; // Garantir que o valor seja 0 se inválido
        const novoIQ = Math.floor(10 + xp_iq / 20); // Round down
        id_iq.value = novoIQ;
    }

    // Função para calcular o valor de HT
    function calcularHT() {
        const xp_ht = parseFloat(id_xp_ht.value) || 0; // Garantir que o valor seja 0 se inválido
        const novoHT = Math.floor(10 + xp_ht / 10); // Round down
        id_ht.value = novoHT;
    }

    // Adiciona o evento 'input' em cada campo de XP
    id_xp_st.addEventListener('input', calcularST);
    id_xp_dx.addEventListener('input', calcularDX);
    id_xp_iq.addEventListener('input', calcularIQ);
    id_xp_ht.addEventListener('input', calcularHT);
});
