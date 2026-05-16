// GM clica num mini da players-bar → popover pra ajustar HP/FP atuais.
// POST pra /character/<id>/vitals/ ; o backend faz broadcast WS e todos os
// clientes atualizam a barra em tempo real (incluindo o próprio GM).
(function () {
    "use strict";

    function getCSRF() {
        const m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : "";
    }

    const editor = document.getElementById("vitals-editor");
    if (!editor) return; // template renderizou só pra GM; player não tem popover

    let currentCharId = null;

    function openFor(mini) {
        currentCharId = mini.dataset.characterId;
        const nameEl = document.getElementById("vitals-editor-name");
        nameEl.textContent = mini.dataset.characterName || mini.title || "";
        document.getElementById("vitals-hp-atual").value = mini.dataset.hpAtual || "0";
        document.getElementById("vitals-hp-max").textContent = mini.dataset.hpMax || "0";
        document.getElementById("vitals-fp-atual").value = mini.dataset.fpAtual || "0";
        document.getElementById("vitals-fp-max").textContent = mini.dataset.fpMax || "0";

        // Posiciona logo abaixo do mini
        const rect = mini.getBoundingClientRect();
        editor.hidden = false;
        editor.style.left = Math.max(8, rect.left) + "px";
        editor.style.top = (rect.bottom + 6) + "px";
    }

    function close() {
        editor.hidden = true;
        currentCharId = null;
    }

    async function postVitals(body) {
        if (!currentCharId) return;
        try {
            const resp = await fetch(`/character/${currentCharId}/vitals/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCSRF(),
                },
                body: JSON.stringify(body),
            });
            if (!resp.ok) {
                const txt = await resp.text();
                console.error("Erro ajuste vitals:", resp.status, txt);
                return;
            }
            // Resposta tem o estado já normalizado; reescreve inputs caso
            // tenha clamp (ex: HP > max ⇒ vira max).
            const data = await resp.json();
            document.getElementById("vitals-hp-atual").value = data.hp_atual;
            document.getElementById("vitals-fp-atual").value = data.fp_atual;
        } catch (e) {
            console.error("Network erro vitals:", e);
        }
    }

    function applyDelta(stat, amount) {
        const input = document.getElementById(`vitals-${stat}-atual`);
        const cur = parseInt(input.value, 10) || 0;
        // HP pode ir negativo (até -10×max, backend clampa); FP min 0
        const next = stat === "hp" ? (cur + amount) : Math.max(0, cur + amount);
        input.value = next;
        postVitals({ [`${stat}_atual`]: next });
    }

    function applyAbsolute(stat) {
        const input = document.getElementById(`vitals-${stat}-atual`);
        const v = parseInt(input.value, 10);
        if (isNaN(v)) return;
        if (stat === "fp" && v < 0) return; // FP não pode negativo
        postVitals({ [`${stat}_atual`]: v });
    }

    // Click no mini abre o editor
    document.addEventListener("click", function (ev) {
        const t = ev.target;
        if (!(t instanceof Element)) return;

        // Clique nos botões -/+ do editor
        const deltaBtn = t.closest("[data-vitals-delta]");
        if (deltaBtn) {
            ev.preventDefault();
            const stat = deltaBtn.dataset.vitalsDelta; // 'hp' ou 'fp'
            const amount = parseInt(deltaBtn.dataset.amount, 10) || 0;
            applyDelta(stat, amount);
            return;
        }

        // Clique num mini abre o editor
        const mini = t.closest(".player-mini");
        if (mini) {
            ev.preventDefault();
            ev.stopPropagation();
            openFor(mini);
            return;
        }

        // Click fora do editor (e não numa mini): fecha
        if (!editor.hidden && !t.closest("#vitals-editor")) {
            close();
        }
    });

    // Enter / blur no input absoluto = aplica
    ["vitals-hp-atual", "vitals-fp-atual"].forEach(function (id) {
        const inp = document.getElementById(id);
        if (!inp) return;
        const stat = id.includes("hp") ? "hp" : "fp";
        inp.addEventListener("change", function () { applyAbsolute(stat); });
        inp.addEventListener("keydown", function (ev) {
            if (ev.key === "Enter") { ev.preventDefault(); applyAbsolute(stat); }
            if (ev.key === "Escape") { close(); }
        });
    });

    // ESC fecha
    document.addEventListener("keydown", function (ev) {
        if (ev.key === "Escape" && !editor.hidden) close();
    });
})();
