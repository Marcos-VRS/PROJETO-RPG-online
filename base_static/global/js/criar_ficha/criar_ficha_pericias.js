document.addEventListener('DOMContentLoaded', function () {
    const btnAdicionarPericia = document.getElementById('adicionar-pericia');
    const containerPericias = document.getElementById('pericias-container');

    // Função para calcular o NH
    function calcularNH(event) {
        const linha = event.target.closest('.pericia-linha');
        if (!linha) return; // Garante que estamos na linha correta

        const atributoBaseSelecionado = linha.querySelector('.pericia-atributo-base').value;
        const dificuldade = linha.querySelector('.pericia-dificuldade').value;
        const custo = parseInt(linha.querySelector('.pericia-custo').value) || 0;

        let atributoBaseValor = 0;
        switch (atributoBaseSelecionado) {
            case 'ST':
                atributoBaseValor = parseInt(document.querySelector('#id_st').value) || 0;
                break;
            case 'DX':
                atributoBaseValor = parseInt(document.querySelector('#id_dx').value) || 0;
                break;
            case 'IQ':
                atributoBaseValor = parseInt(document.querySelector('#id_iq').value) || 0;
                break;
            case 'HT':
                atributoBaseValor = parseInt(document.querySelector('#id_ht').value) || 0;
                break;
            case 'Will':
                atributoBaseValor = parseInt(document.querySelector('#subatributo_will').value) || 0;
                break;
            case 'Per':
                atributoBaseValor = parseInt(document.querySelector('#subatributo_perception').value) || 0;
                break;
            default:
                atributoBaseValor = 0;
                break;
        }

        let nhBase = 0;

        switch (dificuldade) {
            case 'Fácil':
                nhBase = atributoBaseValor;
                break;
            case 'Média':
                nhBase = atributoBaseValor - 1;
                break;
            case 'Difícil':
                nhBase = atributoBaseValor - 2;
                break;
            case 'Muito Difícil':
                nhBase = atributoBaseValor - 3;
                break;
            default:
                nhBase = 0;
                break;
        }

        let nhFinal = nhBase;

        if (custo >= 1) nhFinal += 0;
        if (custo >= 2) nhFinal += 1;
        if (custo >= 3) nhFinal += 0;
        if (custo >= 4) nhFinal += 1;
        if (custo >= 5) nhFinal += Math.floor((custo - 4) / 4);

        linha.querySelector('.pericia-nh').value = nhFinal;
    }

    // Delegação de evento para toda a container de perícias
    containerPericias.addEventListener('change', function (event) {
        if (event.target.matches('.pericia-atributo-base') || event.target.matches('.pericia-dificuldade') || event.target.matches('.pericia-custo')) {
            calcularNH(event);
        }
    });

    // Função para adicionar uma nova linha de inputs para as perícias
    function adicionarPericia() {
        const novaPericia = document.createElement('div');
        novaPericia.classList.add('form-field', 'pericia-linha');

        novaPericia.innerHTML = `
            <input type="text" name="pericias_nome[]" maxlength="30" class="pericia-nome campo-curto-nome medievalsharp-mini" placeholder="Nome da perícia" />
            <select name="pericias_atributo_base[]" class="pericia-atributo-base campo-curto-equip medievalsharp-mini">
                <option value="">Atributo Base</option>
                <option value="ST">ST</option>
                <option value="DX">DX</option>
                <option value="IQ">IQ</option>
                <option value="HT">HT</option>
                <option value="Will">Will</option>
                <option value="Per">Per</option>
            </select>
            <select name="pericias_dificuldade[]" class="pericia-dificuldade campo-curto-dif medievalsharp-mini">
                <option value="">Dificuldade</option>
                <option value="Fácil">Fácil</option>
                <option value="Média">Média</option>
                <option value="Difícil">Difícil</option>
                <option value="Muito Difícil">Muito Difícil</option>
            </select>
            <input type="number" name="pericias_custo[]"  min="1" class="pericia-custo campo-curto-equip medievalsharp-mini" placeholder="Custo" />
            <input type="number" name="pericias_nh[]" class="pericia-nh campo-curto-equip medievalsharp-mini" placeholder="NH" readonly />
        `;
        containerPericias.appendChild(novaPericia);
    }

    btnAdicionarPericia.addEventListener('click', adicionarPericia);
});
