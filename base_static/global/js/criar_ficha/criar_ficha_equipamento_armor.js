document.addEventListener('DOMContentLoaded', function () {
    // Função para adicionar novo equipamento Armor
    function adicionarEquipamentoArmor() {
        const container = document.getElementById('equipamentos-armor-container');
        const novaLinha = document.createElement('div');
        novaLinha.classList.add('form-field', 'equipamento-linha');

        // Campos do equipamento Armor
        const campos = [
            { type: 'text', name: 'equipamentos_armor_nome[]', placeholder: 'Nome da armadura', extraClasses: ['campo-curto-nome', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_armor_location[]', placeholder: 'Location', extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_armor_rd[]', placeholder: 'RD', extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_armor_weight[]', placeholder: 'Weight', extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
            { type: 'text', name: 'equipamentos_armor_cost[]', placeholder: 'Cost', extraClasses: ['campo-curto-equip', 'medievalsharp-mini'] },
        ];

        // Criando inputs para os campos
        campos.forEach(campo => {
            const input = document.createElement('input');
            input.type = campo.type;
            input.name = campo.name;
            input.placeholder = campo.placeholder;
            input.classList.add('campo-curto'); // Adiciona a classe padrão para os inputs menores


            // Adiciona classes extras, se houver
            if (campo.extraClasses) {
                campo.extraClasses.forEach(classe => input.classList.add(classe));
            }

            novaLinha.appendChild(input);
        });

        // Adicionando a nova linha ao container
        container.appendChild(novaLinha);
    }

    // Event listener para o botão "Adicionar Armor"
    document.getElementById('adicionar-equipamento-armor').addEventListener('click', adicionarEquipamentoArmor);
});
