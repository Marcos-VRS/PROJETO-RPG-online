// Enter-como-Tab — APENAS nas telas de criar/editar ficha.
//
// Em campos de texto, pressionar Enter NÃO envia/salva o formulário —
// move o foco pro próximo campo, igual ao Tab. Regras:
//   - <textarea>: mantém o comportamento padrão (quebra de linha).
//   - Enter com Shift/Ctrl/Alt/Meta: ignorado (atalhos seguem normais).
//   - Handlers próprios que chamam preventDefault primeiro têm
//     prioridade — respeitamos via e.defaultPrevented.
//   - <button>/submit/checkbox/etc.: Enter mantém o comportamento nativo,
//     então dá pra "tabular" até o botão e enviar com Enter de propósito.
//
// Incluído só nas telas de ficha (criar/editar V1 e V2), NÃO no site
// inteiro. O guard idempotente evita anexar 2× se for incluído de novo.
(function () {
    "use strict";
    if (window.__rd6EnterAsTab) return;
    window.__rd6EnterAsTab = true;

    // Tipos de <input> onde NÃO movemos o foco (Enter segue nativo).
    var SKIP_TYPES = [
        "button", "submit", "reset", "image", "file",
        "checkbox", "radio", "range"
    ];

    function isEditableText(el) {
        if (!el || el.tagName !== "INPUT") return false;
        var t = (el.getAttribute("type") || "text").toLowerCase();
        return SKIP_TYPES.indexOf(t) === -1;
    }

    document.addEventListener("keydown", function (e) {
        if (e.key !== "Enter") return;
        if (e.shiftKey || e.ctrlKey || e.altKey || e.metaKey) return;
        if (e.isComposing) return;          // composição IME em andamento
        if (e.defaultPrevented) return;     // já tratado (chat, etc.)

        var target = e.target;
        if (!isEditableText(target)) return; // textarea/select/button: nativo

        // Bloqueia o submit implícito do formulário.
        e.preventDefault();

        // Próximo campo: dentro do mesmo form se houver, senão no documento.
        var scope = target.form || document;
        var list = scope.querySelectorAll("input, select, textarea, button");
        var idx = Array.prototype.indexOf.call(list, target);
        if (idx === -1) return;

        // Foca o próximo elemento que realmente aceite foco (pula ocultos/
        // desabilitados — o focus() não "pega" neles, então seguimos).
        for (var j = idx + 1; j < list.length; j++) {
            var el = list[j];
            if (el.disabled || el.type === "hidden" || el.tabIndex === -1) continue;
            el.focus();
            if (document.activeElement === el) {
                if (typeof el.select === "function") {
                    try { el.select(); } catch (_) {}
                }
                break;
            }
        }
    });
})();
