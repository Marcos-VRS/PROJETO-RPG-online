// Mapa de status effects → emoji + label. Usado na mini da players-bar e
// (futuro) no token do mapa. Status que não estão no mapa caem num ponto
// genérico (●) com o próprio nome como title.
//
// Chaves alinhadas com os presets do GM Tool Box (ver TABLETOP_MAP_PLAN.md §6.1).
window.rd6StatusIcons = (function () {
    "use strict";

    var ICONS = {
        stunned:        { emoji: "💫", label: "Atordoado (defesas -4)" },
        knocked_down:   { emoji: "🔻", label: "Caído" },
        unconscious:    { emoji: "😵", label: "Inconsciente" },
        bleeding:       { emoji: "🩸", label: "Sangrando (HT/min)" },
        aiming:         { emoji: "🎯", label: "Mirando (+Acc)" },
        crippled_arm:   { emoji: "🦾", label: "Braço inutilizado" },
        crippled_leg:   { emoji: "🦿", label: "Perna inutilizada" },
        grappled:       { emoji: "🤝", label: "Agarrado (-4 DX)" },
        concentrating:  { emoji: "🧘", label: "Concentrando" },
        major_wound:    { emoji: "⚠️", label: "Ferida grave" },
        hostile:        { emoji: "😡", label: "Hostil" },
        prone:          { emoji: "🛌", label: "Deitado" },
        crouching:      { emoji: "🧎", label: "Agachado" },
        poisoned:       { emoji: "🤢", label: "Envenenado" },
        burning:        { emoji: "🔥", label: "Em chamas" },
        frozen:         { emoji: "🧊", label: "Congelado" },
        blessed:        { emoji: "✨", label: "Abençoado" },
        cursed:         { emoji: "💀", label: "Amaldiçoado" },
    };

    function get(key) {
        return ICONS[key] || { emoji: "●", label: key };
    }

    // Preenche os <span.player-mini-status-icon[data-status]> de um container
    function paintInto(container) {
        if (!container) return;
        container.querySelectorAll("[data-status]").forEach(function (el) {
            var info = get(el.dataset.status);
            el.textContent = info.emoji;
            if (!el.title) el.title = info.label;
        });
    }

    // Renderiza HTML de uma lista de status (pra minis criadas via JS)
    function html(statusList) {
        if (!statusList || !statusList.length) return "";
        return statusList.map(function (s) {
            var info = get(s);
            return '<span class="player-mini-status-icon" title="' +
                info.label.replace(/"/g, "&quot;") + '" data-status="' + s + '">' +
                info.emoji + '</span>';
        }).join("");
    }

    return { get: get, paintInto: paintInto, html: html, ICONS: ICONS };
})();
