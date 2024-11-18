document.addEventListener('DOMContentLoaded', function () {
    // Função para adicionar novo equipamento Melee
    function adicionarEquipamentoMelee() {
        const container = document.getElementById('equipamentos-melee-container');

        // Cria uma nova linha para os campos principais
        const novaLinha = document.createElement('div');
        novaLinha.classList.add('form-field', 'equipamento-linha');

        // Campos principais do equipamento Melee
        const campos = [
            { type: 'text', name: 'equipamentos_melee_nome[]', placeholder: 'Nome do equipamento Melee' },
            { type: 'text', name: 'equipamentos_melee_damage[]', placeholder: 'Damage' },
            { type: 'text', name: 'equipamentos_melee_reach[]', placeholder: 'Reach' },
            { type: 'text', name: 'equipamentos_melee_parry[]', placeholder: 'Parry' },
            { type: 'number', name: 'equipamentos_melee_cost[]', placeholder: 'Cost' },
            { type: 'number', name: 'equipamentos_melee_weight[]', placeholder: 'Weight' }
        ];

        // Criando inputs para os campos principais
        campos.forEach(campo => {
            const input = document.createElement('input');
            input.type = campo.type;
            input.name = campo.name;
            input.placeholder = campo.placeholder;
            input.classList.add('campo-curto'); // Adiciona a classe para os inputs menores
            input.style.marginRight = '4px'; // Espaçamento entre os inputs
            novaLinha.appendChild(input);
        });

        // Cria uma nova linha para o campo "Details"
        const linhaDetails = document.createElement('div');
        linhaDetails.classList.add('form-field', 'equipamento-linha');

        const textarea = document.createElement('textarea');
        textarea.name = 'equipamentos_melee_details[]';
        textarea.placeholder = 'Details';
        textarea.rows = 2;

        // Adiciona o campo "Details" à nova linha
        linhaDetails.appendChild(textarea);

        // Adicionando as linhas ao container
        container.appendChild(novaLinha);
        container.appendChild(linhaDetails);
    }

    // Event listener para o botão "Adicionar Melee"
    document.getElementById('adicionar-equipamento-melee').addEventListener('click', adicionarEquipamentoMelee);
});
