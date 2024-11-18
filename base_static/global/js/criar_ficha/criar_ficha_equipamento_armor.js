document.addEventListener('DOMContentLoaded', function () {
    // Função para adicionar novo equipamento Armor
    function adicionarEquipamentoArmor() {
        const container = document.getElementById('equipamentos-armor-container');
        const novaLinha = document.createElement('div');
        novaLinha.classList.add('form-field', 'equipamento-linha');

        // Campos do equipamento Armor
        const campos = [
            { type: 'text', name: 'equipamentos_armor_nome[]', placeholder: 'Nome da armadura' },
            { type: 'text', name: 'equipamentos_armor_location[]', placeholder: 'Location' },
            { type: 'number', name: 'equipamentos_armor_rd[]', placeholder: 'RD' },
            { type: 'number', name: 'equipamentos_armor_cost[]', placeholder: 'Cost' },
            { type: 'number', name: 'equipamentos_armor_weight[]', placeholder: 'Weight' }
        ];

        // Criando inputs para os campos
        campos.forEach(campo => {
            const input = document.createElement('input');
            input.type = campo.type;
            input.name = campo.name;
            input.placeholder = campo.placeholder;
            input.classList.add('campo-curto'); // Adiciona a classe para os inputs menores
            input.style.marginRight = '4px'; // Espaçamento entre os inputs

            novaLinha.appendChild(input);
        });

        // Adicionando a nova linha ao container
        container.appendChild(novaLinha);
    }

    // Event listener para o botão "Adicionar Armor"
    document.getElementById('adicionar-equipamento-armor').addEventListener('click', adicionarEquipamentoArmor);
});
