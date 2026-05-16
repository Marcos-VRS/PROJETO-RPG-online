// Quickedit: adiciona/remove cards de maneuvers da ficha V2 a partir da tela
// de jogo, sem sair pra tela completa de edição.
(function () {
    "use strict";

    const LABEL = {
        "maneuvers_melee":   "Ataque Melee",
        "maneuvers_ranged":  "Ataque Ranged",
        "maneuvers_defense": "Defesa",
    };

    function getCSRF() {
        const m = document.cookie.match(/csrftoken=([^;]+)/);
        return m ? decodeURIComponent(m[1]) : "";
    }

    function getSheetId() {
        const janela = document.getElementById("janela-quickedit");
        return janela ? janela.dataset.sheetId : null;
    }

    async function postJSON(url, body) {
        const resp = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRF(),
            },
            body: JSON.stringify(body || {}),
        });
        if (!resp.ok) {
            const txt = await resp.text();
            throw new Error("HTTP " + resp.status + ": " + txt);
        }
        return resp.json();
    }

    // Estado do form: qual kind está sendo criado.
    let currentKind = null;

    function showForm(kind) {
        currentKind = kind;
        const form = document.getElementById("quickedit-form");
        const lbl = document.getElementById("qf-tipo-label");
        const damageWrap = document.getElementById("qf-damage-wrap");
        if (!form) return;
        lbl.textContent = LABEL[kind] || kind;
        // Defesa não tem campo Dano
        damageWrap.hidden = (kind === "maneuvers_defense");
        document.getElementById("qf-name").value = "";
        document.getElementById("qf-damage").value = "";
        document.getElementById("qf-nh").value = "10";
        form.hidden = false;
        document.getElementById("qf-name").focus();
    }

    function hideForm() {
        currentKind = null;
        const form = document.getElementById("quickedit-form");
        if (form) form.hidden = true;
    }

    async function confirmAdd() {
        const sheetId = getSheetId();
        if (!sheetId || !currentKind) return;
        const name = document.getElementById("qf-name").value.trim();
        if (!name) { alert("Nome é obrigatório."); return; }
        const nh = parseInt(document.getElementById("qf-nh").value, 10);
        const body = { name: name, nh: isNaN(nh) ? 10 : nh };
        if (currentKind !== "maneuvers_defense") {
            body.damage = document.getElementById("qf-damage").value.trim();
        }
        try {
            await postJSON(`/v2/api/Ficha/${sheetId}/quickadd/${currentKind}/`, body);
            window.location.reload();
        } catch (e) {
            alert("Erro ao adicionar: " + e.message);
        }
    }

    async function quickRemove(kind, index) {
        const sheetId = getSheetId();
        if (!sheetId) return;
        if (!confirm("Remover este card?")) return;
        try {
            await postJSON(`/v2/api/Ficha/${sheetId}/quickremove/${kind}/${index}/`, {});
            window.location.reload();
        } catch (e) {
            alert("Erro ao remover: " + e.message);
        }
    }

    document.addEventListener("click", function (ev) {
        const t = ev.target;
        if (!(t instanceof Element)) return;

        const addBtn = t.closest("[data-quick-add]");
        if (addBtn) {
            ev.preventDefault();
            showForm(addBtn.dataset.quickAdd);
            return;
        }
        const rmBtn = t.closest("[data-quick-remove]");
        if (rmBtn) {
            ev.preventDefault();
            const idx = parseInt(rmBtn.dataset.index, 10);
            quickRemove(rmBtn.dataset.quickRemove, idx);
            return;
        }
        if (t.id === "qf-confirm") {
            ev.preventDefault();
            confirmAdd();
            return;
        }
        if (t.id === "qf-cancel") {
            ev.preventDefault();
            hideForm();
            return;
        }
    });
})();
