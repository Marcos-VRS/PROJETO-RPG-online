document.addEventListener('DOMContentLoaded', function () {
    const formulario = document.querySelector('form'); // Selecione seu formulário

    formulario.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' || event.key === 'NumpadEnter') {
            event.preventDefault(); // Previne o envio do formulário
        }
    });
});
