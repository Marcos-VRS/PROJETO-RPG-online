document.addEventListener("DOMContentLoaded", function () {
    window.rollAttribute = function (nh, attribute) {
        let bonus = document.getElementById(`bonus-${attribute}`)?.value || 0;
        let redutor = document.getElementById(`redutor-${attribute}`)?.value || 0;

        // Converte os valores para inteiros
        bonus = parseInt(bonus, 10);
        redutor = parseInt(redutor, 10);

        // Envia a string 'attribute' corretamente na URL
        fetch(`/teste_atributos/${attribute}/${nh}/${bonus}/${redutor}/`)
            .then(response => response.json())
            .then(data => {
                document.getElementById("resultado").innerText =
                    `Atributo: ${data.atributo}, Rolagem: ${data.roll}, Resultado: ${data.message}`;
            })
            .catch(error => console.error("Erro ao processar a rolagem:", error));
    };
});
