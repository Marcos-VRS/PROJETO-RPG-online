document.addEventListener('DOMContentLoaded', function () {
    // Função para adicionar novo equipamento Ranged
    function adicionarEquipamentoRanged() {
        const container = document.getElementById('equipamentos-ranged-container');
        const novaLinha = document.createElement('div');
        novaLinha.classList.add('form-field', 'equipamento-linha');

        // Campos do equipamento Ranged
        const campos = [
            { type: 'text', name: 'equipamentos_ranged_nome[]', placeholder: 'Nome da arma Ranged', maxLength: 30, extraClasses: ['campo-curto-nome', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_ranged_damage[]', placeholder: 'Damage', maxLength: 12, extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_ranged_acc[]', placeholder: 'Acc', maxLength: 12, extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_ranged_range[]', placeholder: 'Range', maxLength: 12, extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_ranged_weight[]', placeholder: 'Weight', maxLength: 12, extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_ranged_rof[]', placeholder: 'Rof', maxLength: 12, extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_ranged_shots[]', placeholder: 'Shots', maxLength: 12, extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_ranged_bulk[]', placeholder: 'Bulk', maxLength: 12, extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_ranged_rcl[]', placeholder: 'RCL', maxLength: 12, extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_ranged_cost[]', placeholder: 'Cost', maxLength: 12, extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] }
        ];

        // Criando inputs para os campos
        campos.forEach(campo => {
            const input = document.createElement('input');
            input.type = campo.type;
            input.name = campo.name;
            input.maxLength = campo.maxLength; // Define o maxLength conforme especificado

            input.placeholder = campo.placeholder;
            input.classList.add('campo-curto'); // Adiciona a classe para os inputs menores
            novaLinha.appendChild(input);

            // Adiciona classes extras, se houver
            if (campo.extraClasses) {
                campo.extraClasses.forEach(classe => input.classList.add(classe));
            }
        });

        // Adicionando o campo textarea para "Details"
        const textarea = document.createElement('textarea');
        textarea.classList.add('campo-curto-equip', 'medievalsharp-mini');
        textarea.name = 'equipamentos_ranged_details[]'; // Corrigido: o nome deve ser 'equipamentos_ranged_details[]'
        textarea.placeholder = 'Details';
        textarea.rows = 2;
        textarea.maxLength = 200; // Define o maxLength conforme especificado
        novaLinha.appendChild(textarea);

        // Adicionando a nova linha ao container
        container.appendChild(novaLinha);

        // Adicionar um log para depuração e verificação da criação dos campos
        console.log('Nova linha criada:', novaLinha);
    }

    // Event listener para o botão "Adicionar Ranged"
    document.getElementById('adicionar-equipamento-ranged').addEventListener('click', adicionarEquipamentoRanged);
});
