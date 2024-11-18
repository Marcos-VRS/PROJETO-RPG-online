document.addEventListener('DOMContentLoaded', function () {
    // Função para adicionar novo equipamento Ranged
    function adicionarEquipamentoRanged() {
        const container = document.getElementById('equipamentos-ranged-container');
        const novaLinha = document.createElement('div');
        novaLinha.classList.add('form-field', 'equipamento-linha');

        // Campos do equipamento Ranged
        const campos = [
            { type: 'text', name: 'equipamentos_ranged_nome[]', placeholder: 'Nome da arma Ranged' },
            { type: 'text', name: 'equipamentos_ranged_damage[]', placeholder: 'Damage' },
            { type: 'text', name: 'equipamentos_ranged_acc[]', placeholder: 'Acc' },
            { type: 'text', name: 'equipamentos_ranged_range[]', placeholder: 'Range' },
            { type: 'number', name: 'equipamentos_ranged_weight[]', placeholder: 'Weight' },
            { type: 'text', name: 'equipamentos_ranged_rof[]', placeholder: 'Rof' },
            { type: 'text', name: 'equipamentos_ranged_shots[]', placeholder: 'Shots' },
            { type: 'text', name: 'equipamentos_ranged_bulk[]', placeholder: 'Bulk' },
            { type: 'text', name: 'equipamentos_ranged_rcl[]', placeholder: 'RCL' },
            { type: 'number', name: 'equipamentos_ranged_cost[]', placeholder: 'Cost' }
        ];

        // Criando inputs para os campos
        campos.forEach(campo => {
            const input = document.createElement('input');
            input.type = campo.type;
            input.name = campo.name;
            input.placeholder = campo.placeholder;
            input.classList.add('campo-curto'); // Adiciona a classe para os inputs menores
            novaLinha.appendChild(input);
        });

        // Adicionando a nova linha ao container
        container.appendChild(novaLinha);
    }

    // Event listener para o botão "Adicionar Ranged"
    document.getElementById('adicionar-equipamento-ranged').addEventListener('click', adicionarEquipamentoRanged);
});
