document.addEventListener("keydown", function (e) {
    const target = e.target;

    // Verifica se o evento ocorreu em um textarea
    if (target.tagName === "TEXTAREA") {
        // Permite o comportamento padrão do Enter em <textarea>
        return;
    }

    // Impede o comportamento padrão do Enter fora de <textarea>
    if (e.key === "Enter") {
        e.preventDefault(); // Evita que o Enter funcione normalmente
    }
});
