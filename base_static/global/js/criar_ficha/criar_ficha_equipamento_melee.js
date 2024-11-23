document.addEventListener('DOMContentLoaded', function () {
    // Função para adicionar novo equipamento Melee
    function adicionarEquipamentoMelee() {
        const container = document.getElementById('equipamentos-melee-container');

        // Cria uma nova linha para todos os campos
        const novaLinha = document.createElement('div');
        novaLinha.classList.add('form-field', 'equipamento-linha');

        // Campos principais do equipamento Melee
        const campos = [
            { type: 'text', name: 'equipamentos_melee_nome[]', placeholder: 'Nome do equipamento Melee', extraClasses: ['campo-curto-nome', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_melee_damage[]', placeholder: 'Damage', extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_melee_reach[]', placeholder: 'Reach', extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_melee_parry[]', placeholder: 'Parry', extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'number', name: 'equipamentos_melee_cost[]', placeholder: 'Cost', extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'number', name: 'equipamentos_melee_weight[]', placeholder: 'Weight', extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] }
        ];

        // Criando inputs para os campos principais
        campos.forEach(campo => {
            const input = document.createElement('input');
            input.type = campo.type;
            input.name = campo.name;
            input.placeholder = campo.placeholder;
            input.classList.add('campo-curto'); // Adiciona a classe para os inputs menores
            novaLinha.appendChild(input);
            // Adiciona classes extras, se houver
            if (campo.extraClasses) {
                campo.extraClasses.forEach(classe => input.classList.add(classe));
            }
        });

        // Criação do campo "Details" (textarea)
        const textarea = document.createElement('textarea');
        textarea.name = 'equipamentos_melee_details[]';
        textarea.placeholder = 'Details';
        textarea.rows = 2;
        textarea.className = 'campo-curto-equip medievalsharp-mini';

        // Adiciona o campo "Details" à mesma linha
        novaLinha.appendChild(textarea);

        // Adiciona a nova linha ao container
        container.appendChild(novaLinha);
    }

    // Event listener para o botão "Adicionar Melee"
    document.getElementById('adicionar-equipamento-melee').addEventListener('click', adicionarEquipamentoMelee);
});
