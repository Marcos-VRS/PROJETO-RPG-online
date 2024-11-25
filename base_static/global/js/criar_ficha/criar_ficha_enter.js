document.addEventListener("keydown", function (e) {
    const target = e.target; // Elemento que acionou o evento

    // Se a tecla pressionada não for "Enter", não faça nada
    if (e.key !== "Enter") {
        return;
    }

    // Comportamento no <input>
    if (target.tagName === "INPUT") {
        e.preventDefault(); // Evita o comportamento padrão do Enter
        const formElements = Array.from(document.querySelectorAll("input, textarea, select, button"));
        const currentIndex = formElements.indexOf(target);

        // Move para o próximo elemento focável, se existir
        if (currentIndex !== -1 && currentIndex < formElements.length - 1) {
            formElements[currentIndex + 1].focus();
        }
        return;
    }

    // Comportamento no <textarea>
    if (target.tagName === "TEXTAREA") {
        // Permite o comportamento padrão (quebra de linha)
        return;
    }

    // Comportamento em qualquer outro lugar
    e.preventDefault(); // Bloqueia o comportamento padrão do Enter
});
