document.addEventListener('DOMContentLoaded', function () {
    // Captura os elementos de entrada
    const id_st = document.getElementById('id_st'); // Campo ST (resultado)
    const id_xp_st = document.getElementById('id_xp_st'); // Campo XP ST (entrada do usuário)
    const id_st_bonus = document.getElementById('id_st_bonus'); // Campo  ST bonus (entrada do usuário)
    const id_dx = document.getElementById('id_dx'); // Campo DX (resultado)
    const id_xp_dx = document.getElementById('id_xp_dx'); // Campo XP DX (entrada do usuário)
    const id_dx_bonus = document.getElementById('id_dx_bonus'); // Campo bonus DX (entrada do usuário)
    const id_iq = document.getElementById('id_iq'); // Campo IQ (resultado)
    const id_xp_iq = document.getElementById('id_xp_iq'); // Campo XP IQ (entrada do usuário)
    const id_iq_bonus = document.getElementById('id_iq_bonus'); // Campo bonus IQ (entrada do usuário)
    const id_ht = document.getElementById('id_ht'); // Campo HT (resultado)
    const id_xp_ht = document.getElementById('id_xp_ht'); // Campo XP HT (entrada do usuário)
    const id_ht_bonus = document.getElementById('id_ht_bonus'); // Campo bonus HT (entrada do usuário)

    // Inicializa os valores dos campos XP e Bônus com 0
    function inicializarCampos() {



        // Calcula os valores iniciais dos atributos
        calcularST();
        calcularDX();
        calcularIQ();
        calcularHT();
    }

    // Função para calcular o valor de ST
    function calcularST() {
        const xp_st = parseFloat(id_xp_st.value) || 0; // Garantir que o valor seja 0 se inválido
        const bonus_st = parseFloat(id_st_bonus.value) || 0;
        const novoST = Math.floor(10 + xp_st / 10) + bonus_st; // Round down
        id_st.value = novoST;
    }

    // Função para calcular o valor de DX
    function calcularDX() {
        const xp_dx = parseFloat(id_xp_dx.value) || 0; // Garantir que o valor seja 0 se inválido
        const bonus_dx = parseFloat(id_dx_bonus.value) || 0;
        const novoDX = Math.floor(10 + xp_dx / 20) + bonus_dx; // Round down
        id_dx.value = novoDX;
    }

    // Função para calcular o valor de IQ
    function calcularIQ() {
        const xp_iq = parseFloat(id_xp_iq.value) || 0; // Garantir que o valor seja 0 se inválido
        const bonus_iq = parseFloat(id_iq_bonus.value) || 0;
        const novoIQ = Math.floor(10 + xp_iq / 20) + bonus_iq; // Round down
        id_iq.value = novoIQ;
    }

    // Função para calcular o valor de HT
    function calcularHT() {
        const xp_ht = parseFloat(id_xp_ht.value) || 0; // Garantir que o valor seja 0 se inválido
        const bonus_ht = parseFloat(id_ht_bonus.value) || 0;
        const novoHT = Math.floor(10 + xp_ht / 10) + bonus_ht; // Round down
        id_ht.value = novoHT;
    }

    // Adiciona o evento 'input' em cada campo de XP
    id_xp_st.addEventListener('input', calcularST);
    id_st_bonus.addEventListener('input', calcularST);
    id_xp_dx.addEventListener('input', calcularDX);
    id_dx_bonus.addEventListener('input', calcularDX);
    id_xp_iq.addEventListener('input', calcularIQ);
    id_iq_bonus.addEventListener('input', calcularIQ);
    id_xp_ht.addEventListener('input', calcularHT);
    id_ht_bonus.addEventListener('input', calcularHT);

    // Inicializa os valores ao carregar a página
    inicializarCampos();
});
