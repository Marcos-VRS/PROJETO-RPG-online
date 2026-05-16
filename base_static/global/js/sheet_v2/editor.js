/* Ficha V2 editor:
   - Auto-cálculo de secundárias e custos quando atributos/mods mudam
   - Listas dinâmicas (vantagens/desvantagens/skills/equipment) JSON-backed
   - Picker de vantagens com autocomplete a partir do catálogo
*/
(function () {
    'use strict';

    const ATTR_COST = { st: 10, dx: 20, iq: 20, ht: 10 };
    const SEC_COST = { hp: 2, fp: 3, will: 5, per: 5, basic_speed: 20, basic_move: 5 };

    // Catálogos populados via API
    const CATALOGS = {
        advantages:   { loaded: false, list: [], url: '/v2/api/catalog/advantages/',    field: 'advantages' },
        disadvantages:{ loaded: false, list: [], url: '/v2/api/catalog/disadvantages/', field: 'disadvantages' },
        modifiers:    { loaded: false, list: [], url: '/v2/api/catalog/modifiers/',     field: 'modifiers'  },
        skills:       { loaded: false, list: [], url: '/v2/api/catalog/skills/',        field: 'skills'     },
    };
    // Aliases backward-compat
    let ADV_CATALOG = [];
    let ADV_CATALOG_LOADED = false;

    function $(id) { return document.getElementById(id); }
    function val(el) { return parseFloat(el.value || '0') || 0; }

    // ============== Cálculo ==============

    function computeSecondary(primary, mods) {
        const st = primary.st, dx = primary.dx, iq = primary.iq, ht = primary.ht;
        const hp = st + (mods.hp || 0);
        const fp = ht + (mods.fp || 0);
        const will = iq + (mods.will || 0);
        const per = iq + (mods.per || 0);
        const basicSpeed = (ht + dx) / 4 + (mods.basic_speed || 0);
        const basicMove = Math.floor(basicSpeed) + (mods.basic_move || 0);
        const dodge = Math.floor(basicSpeed) + 3;
        const basicLift = (st * st) / 5;
        return {
            hp, fp, will, per,
            basicSpeed: Math.round(basicSpeed * 100) / 100,
            basicMove, dodge,
            basicLift: Math.round(basicLift * 10) / 10,
            thrust: thrustForST(st),
            swing: swingForST(st),
        };
    }

    const DAMAGE_TABLE = {
        1:["1d-6","1d-5"],2:["1d-6","1d-5"],3:["1d-5","1d-4"],4:["1d-5","1d-4"],
        5:["1d-4","1d-3"],6:["1d-4","1d-3"],7:["1d-3","1d-2"],8:["1d-3","1d-2"],
        9:["1d-2","1d-1"],10:["1d-2","1d"],11:["1d-1","1d+1"],12:["1d-1","1d+2"],
        13:["1d","2d-1"],14:["1d","2d"],15:["1d+1","2d+1"],16:["1d+1","2d+2"],
        17:["1d+2","3d-1"],18:["1d+2","3d"],19:["2d-1","3d+1"],20:["2d-1","3d+2"],
        21:["2d","4d-1"],22:["2d","4d"],23:["2d+1","4d+1"],24:["2d+1","4d+2"],
        25:["2d+2","5d-1"],26:["2d+2","5d"],27:["3d-1","5d+1"],28:["3d-1","5d+1"],
        29:["3d","5d+2"],30:["3d","5d+2"]
    };
    function thrustForST(st) { const c = Math.max(1, Math.min(30, st)); return (DAMAGE_TABLE[c] || ["3d","5d+2"])[0]; }
    function swingForST(st)  { const c = Math.max(1, Math.min(30, st)); return (DAMAGE_TABLE[c] || ["3d","5d+2"])[1]; }

    function recalc() {
        const primary = {
            st: val($('attr-st')), dx: val($('attr-dx')),
            iq: val($('attr-iq')), ht: val($('attr-ht'))
        };
        const mods = {};
        document.querySelectorAll('.v2-sec-mod').forEach(inp => {
            const v = parseFloat(inp.value || '0');
            if (v !== 0) mods[inp.dataset.key] = v;
        });

        const sec = computeSecondary(primary, mods);
        $('sec-hp').textContent = sec.hp;
        $('sec-fp').textContent = sec.fp;
        $('sec-will').textContent = sec.will;
        $('sec-per').textContent = sec.per;
        $('sec-speed').textContent = sec.basicSpeed;
        $('sec-move').textContent = sec.basicMove;
        $('sec-dodge').textContent = sec.dodge;
        $('sec-bl').textContent = sec.basicLift;
        $('sec-thrust').textContent = sec.thrust;
        $('sec-swing').textContent = sec.swing;

        // Custos
        let attrCost = 0;
        for (const a of ['st','dx','iq','ht']) {
            attrCost += (primary[a] - 10) * ATTR_COST[a];
            const elCost = $('cost-' + a);
            if (elCost) elCost.textContent = (primary[a] - 10) * ATTR_COST[a];
        }
        let secCost = 0;
        for (const k in mods) {
            if (k === 'basic_speed') secCost += Math.round(mods[k] / 0.25) * 5;
            else if (SEC_COST[k]) secCost += Math.round(mods[k] * SEC_COST[k]);
        }

        const advCost = sumListCost('advantages-input', true);
        const disadCost = sumListCost('disadvantages-input', true);
        const skillCost = sumListCost('skills-input', false);

        $('adv-cost-display').textContent = advCost;
        $('disad-cost-display').textContent = disadCost;
        $('skill-cost-display').textContent = skillCost;

        const total = attrCost + secCost + advCost + disadCost + skillCost;
        const available = parseInt($('pt-available').textContent, 10) || 150;
        $('pt-spent').textContent = total;
        $('pt-remaining').textContent = '(' + (available - total) + ' restantes)';
    }

    function sumListCost(inputId, useComputed) {
        const el = $(inputId);
        if (!el) return 0;
        try {
            const list = JSON.parse(el.value || '[]');
            return list.reduce((acc, e) => {
                if (useComputed && typeof e.computed_cost === 'number') return acc + e.computed_cost;
                const c = (e.manual_cost !== null && e.manual_cost !== undefined) ? parseInt(e.manual_cost, 10) :
                          (e.custom_cost !== null && e.custom_cost !== undefined) ? parseInt(e.custom_cost, 10) :
                          (typeof e.computed_cost === 'number' ? e.computed_cost : 0);
                return acc + (c || 0);
            }, 0);
        } catch (_) { return 0; }
    }

    // ============== Catálogos (API) ==============

    function loadCatalog(kind) {
        const cat = CATALOGS[kind];
        if (!cat || cat.loaded) return Promise.resolve();
        return fetch(cat.url)
            .then(r => r.json())
            .then(data => {
                cat.list = data[kind] || [];
                cat.loaded = true;
                // mantém aliases para advantages (compat)
                if (kind === 'advantages') {
                    ADV_CATALOG = cat.list;
                    ADV_CATALOG_LOADED = true;
                }
            })
            .catch(err => console.warn(`Falha ao carregar catálogo (${kind}):`, err));
    }

    function findCatalogEntry(kind, key) {
        const cat = CATALOGS[kind];
        return cat ? cat.list.find(o => o.key === key) : null;
    }

    // ============== Render Picker Lists (Advantages, Disadvantages) ==============

    const PICKER_LIST_META = {
        advantages: {
            input: 'advantages-input',
            container: 'adv-list',
            placeholder: 'Search advantage...',
            manualPlaceholder: 'Advantage name (manual)',
        },
        disadvantages: {
            input: 'disadvantages-input',
            container: 'disad-list',
            placeholder: 'Search disadvantage...',
            manualPlaceholder: 'Disadvantage name (manual)',
        },
    };

    function renderAdvantages() { renderPickerList('advantages'); }
    function renderDisadvantages() { renderPickerList('disadvantages'); }

    function renderPickerList(kind) {
        const meta = PICKER_LIST_META[kind];
        const input = $(meta.input);
        const container = $(meta.container);
        let list;
        try { list = JSON.parse(input.value || '[]'); } catch (_) { list = []; }
        container.innerHTML = '';

        list.forEach((entry, idx) => {
            // Wrapper: contém a row principal + drawer de modifiers
            const wrap = document.createElement('div');
            wrap.className = 'v2-adv-row-wrap';

            const row = document.createElement('div');
            row.className = 'v2-list-row v2-adv-row';
            wrap.appendChild(row);

            const isManual = entry.is_manual === true;
            const supportsLevels = entry.supports_levels === true;
            if (!Array.isArray(entry.modifiers)) entry.modifiers = [];

            // Coluna 1: Picker (search + dropdown) OU input manual de nome
            const pickerWrap = document.createElement('div');
            pickerWrap.className = 'v2-picker-wrap';

            const nameInput = document.createElement('input');
            nameInput.type = 'text';
            nameInput.className = 'v2-picker-input';
            nameInput.placeholder = isManual ? meta.manualPlaceholder : meta.placeholder;
            nameInput.value = entry.label || '';
            nameInput.autocomplete = 'off';
            pickerWrap.appendChild(nameInput);

            const dropdown = document.createElement('div');
            dropdown.className = 'v2-picker-dropdown';
            dropdown.style.display = 'none';
            pickerWrap.appendChild(dropdown);

            row.appendChild(pickerWrap);

            // Coluna 2: Nível — sempre visível; vira "—" read-only se não suporta níveis
            const levelInput = document.createElement('input');
            levelInput.className = 'v2-level-input';
            row.appendChild(levelInput);

            function configureLevelInput(canLevels, currentLevel) {
                if (canLevels) {
                    levelInput.type = 'number';
                    levelInput.min = '1';
                    levelInput.readOnly = false;
                    levelInput.classList.remove('v2-level-disabled');
                    levelInput.value = currentLevel || 1;
                    levelInput.placeholder = '#';
                } else {
                    levelInput.type = 'text';
                    levelInput.readOnly = true;
                    levelInput.classList.add('v2-level-disabled');
                    levelInput.value = '—';
                }
            }
            configureLevelInput(supportsLevels, entry.level);

            // Coluna 3: Custo exibido (read-only quando catálogo; editável quando manual)
            const costInput = document.createElement('input');
            costInput.type = 'number';
            costInput.className = 'v2-cost-input';
            costInput.placeholder = 'Pts';
            costInput.value = entry.computed_cost !== undefined ? entry.computed_cost : '';
            costInput.readOnly = !isManual;
            costInput.title = isManual ? 'Custo manual (editável)' : 'Calculado a partir do catálogo';
            row.appendChild(costInput);

            // Coluna 4: Toggle manual
            const manualBtn = document.createElement('button');
            manualBtn.type = 'button';
            manualBtn.className = 'v2-manual-toggle';
            manualBtn.textContent = isManual ? '✏' : '📖';
            manualBtn.title = isManual ? 'Digitar manualmente (clique pra voltar ao catálogo)' : 'Catálogo (clique pra digitar manual)';
            row.appendChild(manualBtn);

            // Coluna 5: MOD (abre/fecha drawer)
            const modBtn = document.createElement('button');
            modBtn.type = 'button';
            modBtn.className = 'v2-mod-toggle';
            const modCount = (entry.modifiers || []).length;
            modBtn.textContent = modCount > 0 ? `MOD (${modCount})` : 'MOD';
            modBtn.title = 'Enhancements & Limitations';
            row.appendChild(modBtn);

            // Coluna 6: Notas
            const notesInput = document.createElement('input');
            notesInput.type = 'text';
            notesInput.className = 'v2-notes-input';
            notesInput.placeholder = 'Notes';
            notesInput.value = entry.notes || '';
            row.appendChild(notesInput);

            // Coluna 7: Remover
            const rm = document.createElement('button');
            rm.type = 'button';
            rm.className = 'v2-remove';
            rm.textContent = '×';
            row.appendChild(rm);

            // Drawer (abaixo da row, fechado por default)
            const drawer = document.createElement('div');
            drawer.className = 'v2-mods-drawer';
            drawer.style.display = entry.modifiers_open ? 'block' : 'none';
            wrap.appendChild(drawer);

            container.appendChild(wrap);

            // ============ Eventos ============

            function persist() {
                input.value = JSON.stringify(list);
                recalc();
            }

            // ============ Modifiers drawer ============

            function recomputeEntryCost() {
                // Recalcula custo base + soma modifiers
                let base;
                if (entry.is_manual) {
                    base = parseInt(entry.manual_cost, 10) || 0;
                } else {
                    const opt = findCatalogEntry(kind, entry.key);
                    if (!opt) {
                        entry.computed_cost = 0;
                        costInput.value = '';
                        return;
                    }
                    if (opt.cost_type === 'per_level') {
                        base = (opt.value || 0) * (entry.level || 1);
                    } else {
                        base = opt.value || 0;
                    }
                }
                const totalPct = sumModifierPct(entry.modifiers);
                const cappedPct = Math.max(totalPct, -80);
                const adjusted = base * (1 + cappedPct / 100);
                entry.computed_cost = adjusted >= 0 ? Math.ceil(adjusted) : Math.floor(adjusted);
                costInput.value = entry.computed_cost;
                // Atualiza display %
                const pctSpan = drawer.querySelector('.v2-mods-total-pct');
                if (pctSpan) pctSpan.textContent = (totalPct >= 0 ? '+' : '') + totalPct + '%' + (cappedPct !== totalPct ? ' (capped at -80%)' : '');
                // Atualiza counter no botão
                modBtn.textContent = entry.modifiers.length > 0 ? `MOD (${entry.modifiers.length})` : 'MOD';
            }

            function sumModifierPct(mods) {
                return (mods || []).reduce((acc, m) => {
                    if (m.is_manual) return acc + (parseInt(m.manual_percent, 10) || 0);
                    const pct = parseInt(m.percent, 10) || 0;
                    if (m.supports_levels) return acc + pct * (parseInt(m.level, 10) || 1);
                    return acc + pct;
                }, 0);
            }

            function renderDrawer() {
                drawer.innerHTML = '';
                const header = document.createElement('div');
                header.className = 'v2-mods-header';
                header.innerHTML = `Enhancements / Limitations &mdash; total <span class="v2-mods-total-pct">+0%</span>`;
                drawer.appendChild(header);

                const modsList = document.createElement('div');
                modsList.className = 'v2-mods-list';
                drawer.appendChild(modsList);

                entry.modifiers.forEach((mod, mIdx) => {
                    const mrow = document.createElement('div');
                    mrow.className = 'v2-mod-row';

                    // Picker
                    const modPicker = document.createElement('div');
                    modPicker.className = 'v2-picker-wrap v2-mod-picker-wrap';
                    const modName = document.createElement('input');
                    modName.type = 'text';
                    modName.className = 'v2-picker-input';
                    modName.placeholder = mod.is_manual ? 'Modifier name (manual)' : 'Search modifier...';
                    modName.value = mod.label || '';
                    modName.autocomplete = 'off';
                    modPicker.appendChild(modName);
                    const modDropdown = document.createElement('div');
                    modDropdown.className = 'v2-picker-dropdown';
                    modDropdown.style.display = 'none';
                    modPicker.appendChild(modDropdown);
                    mrow.appendChild(modPicker);

                    // Level (se per_level)
                    const modLevelInput = document.createElement('input');
                    modLevelInput.className = 'v2-mod-level-input v2-level-input';
                    mrow.appendChild(modLevelInput);
                    function configModLevel(canLevels, lvl) {
                        if (canLevels) {
                            modLevelInput.type = 'number';
                            modLevelInput.min = '1';
                            modLevelInput.readOnly = false;
                            modLevelInput.classList.remove('v2-level-disabled');
                            modLevelInput.value = lvl || 1;
                            modLevelInput.placeholder = '#';
                        } else {
                            modLevelInput.type = 'text';
                            modLevelInput.readOnly = true;
                            modLevelInput.classList.add('v2-level-disabled');
                            modLevelInput.value = '—';
                        }
                    }
                    configModLevel(mod.supports_levels, mod.level);

                    // Percent
                    const modPct = document.createElement('input');
                    modPct.type = 'number';
                    modPct.className = 'v2-mod-pct-input v2-cost-input';
                    modPct.value = mod.is_manual ? (mod.manual_percent ?? '') : (mod.percent ?? '');
                    modPct.readOnly = !mod.is_manual;
                    modPct.title = mod.is_manual ? 'Custom percent (editable)' : 'From catalog';
                    mrow.appendChild(modPct);

                    // Toggle manual
                    const modManualBtn = document.createElement('button');
                    modManualBtn.type = 'button';
                    modManualBtn.className = 'v2-manual-toggle';
                    modManualBtn.textContent = mod.is_manual ? '✏' : '📖';
                    modManualBtn.title = mod.is_manual ? 'Manual entry' : 'Catalog entry';
                    mrow.appendChild(modManualBtn);

                    // Remove
                    const modRm = document.createElement('button');
                    modRm.type = 'button';
                    modRm.className = 'v2-remove';
                    modRm.textContent = '×';
                    mrow.appendChild(modRm);

                    modsList.appendChild(mrow);

                    // === Eventos do modifier ===
                    function applyModCatalog(opt) {
                        mod.is_manual = false;
                        mod.key = opt.key;
                        mod.id = opt.id;
                        mod.label = opt.label;
                        mod.section = opt.section;
                        mod.percent = opt.percent;
                        mod.supports_levels = opt.supports_levels;
                        mod.kind = opt.kind;
                        mod.level = opt.supports_levels ? (mod.level || 1) : 1;
                        mod.manual_percent = null;
                        modName.value = opt.label;
                        modPct.value = opt.percent;
                        modPct.readOnly = true;
                        configModLevel(opt.supports_levels, mod.level);
                        modManualBtn.textContent = '📖';
                        // Para variáveis, força manual
                        if (opt.kind === 'variable') {
                            mod.is_manual = true;
                            modPct.readOnly = false;
                            modManualBtn.textContent = '✏';
                        }
                        modDropdown.style.display = 'none';
                        recomputeEntryCost();
                        persist();
                    }

                    function applyModManual() {
                        mod.is_manual = true;
                        mod.key = 'manual:' + (modName.value || '');
                        mod.id = mod.key;
                        mod.label = modName.value || '';
                        mod.supports_levels = false;
                        mod.kind = 'fixed';
                        mod.manual_percent = parseInt(modPct.value, 10) || 0;
                        mod.percent = mod.manual_percent;
                        configModLevel(false, 1);
                        modPct.readOnly = false;
                        modManualBtn.textContent = '✏';
                        modDropdown.style.display = 'none';
                        recomputeEntryCost();
                        persist();
                    }

                    function showModDropdown(filter) {
                        const cat = CATALOGS.modifiers;
                        if (!cat.loaded) {
                            modDropdown.innerHTML = '<div class="v2-dropdown-empty">Loading…</div>';
                            modDropdown.style.display = 'block';
                            return;
                        }
                        const q = (filter || '').toLowerCase().trim();
                        const matches = cat.list.filter(o => {
                            if (!q) return true;
                            return o.label.toLowerCase().includes(q) || o.id.toLowerCase().includes(q);
                        }).slice(0, 50);
                        modDropdown.innerHTML = '';
                        if (matches.length === 0) {
                            const empty = document.createElement('div');
                            empty.className = 'v2-dropdown-empty';
                            empty.textContent = 'No modifier found — click ✏ to enter manually.';
                            modDropdown.appendChild(empty);
                        } else {
                            matches.forEach(opt => {
                                const item = document.createElement('div');
                                item.className = 'v2-dropdown-item';
                                const sign = opt.percent >= 0 ? '+' : '';
                                const suffix = `${sign}${opt.percent}%` + (opt.supports_levels ? '/level' : '') + (opt.page_ref ? ' · p' + opt.page_ref : '');
                                item.innerHTML = `<span class="v2-dropdown-label">${escapeHtml(opt.label)}</span><span class="v2-dropdown-cost">${suffix}</span>`;
                                item.addEventListener('mousedown', (e) => { e.preventDefault(); applyModCatalog(opt); });
                                modDropdown.appendChild(item);
                            });
                        }
                        modDropdown.style.display = 'block';
                    }

                    modName.addEventListener('focus', () => { if (!mod.is_manual) showModDropdown(modName.value); });
                    modName.addEventListener('input', () => {
                        if (!mod.is_manual) {
                            showModDropdown(modName.value);
                        } else {
                            mod.label = modName.value;
                            mod.id = 'manual:' + mod.label;
                            mod.key = mod.id;
                            persist();
                        }
                    });
                    modName.addEventListener('blur', () => setTimeout(() => { modDropdown.style.display = 'none'; }, 150));

                    modLevelInput.addEventListener('input', () => {
                        mod.level = parseInt(modLevelInput.value, 10) || 1;
                        recomputeEntryCost();
                        persist();
                    });

                    modPct.addEventListener('input', () => {
                        if (mod.is_manual) {
                            const p = parseInt(modPct.value, 10) || 0;
                            mod.manual_percent = p;
                            mod.percent = p;
                            recomputeEntryCost();
                            persist();
                        }
                    });

                    modManualBtn.addEventListener('click', () => {
                        if (mod.is_manual) {
                            // back to catalog
                            mod.is_manual = false;
                            mod.manual_percent = null;
                            mod.label = '';
                            mod.key = '';
                            mod.id = '';
                            mod.percent = 0;
                            modName.value = '';
                            modPct.value = '';
                            modPct.readOnly = true;
                            configModLevel(false, 1);
                            modManualBtn.textContent = '📖';
                            modName.focus();
                        } else {
                            applyModManual();
                        }
                        recomputeEntryCost();
                        persist();
                    });

                    modRm.addEventListener('click', () => {
                        entry.modifiers.splice(mIdx, 1);
                        renderDrawer();
                        recomputeEntryCost();
                        persist();
                    });
                });

                const addBtn = document.createElement('button');
                addBtn.type = 'button';
                addBtn.className = 'v2-add-btn v2-mods-add';
                addBtn.textContent = '+ Add modifier';
                addBtn.addEventListener('click', () => {
                    entry.modifiers.push({
                        key: '', id: '', label: '',
                        percent: 0, supports_levels: false,
                        level: 1, is_manual: false, manual_percent: null,
                        section: '', kind: 'fixed',
                    });
                    renderDrawer();
                    recomputeEntryCost();
                    persist();
                    // Foco no campo recém-criado
                    const inputs = modsList.querySelectorAll('.v2-mod-row .v2-picker-input');
                    if (inputs.length) inputs[inputs.length - 1].focus();
                });
                drawer.appendChild(addBtn);

                recomputeEntryCost();
            }

            // Toggle drawer
            modBtn.addEventListener('click', () => {
                entry.modifiers_open = !entry.modifiers_open;
                drawer.style.display = entry.modifiers_open ? 'block' : 'none';
                if (entry.modifiers_open) renderDrawer();
                persist();
            });

            if (entry.modifiers_open) renderDrawer();

            function updateRowLabel(text) {
                nameInput.value = text;
            }

            function applyCatalogSelection(opt) {
                entry.is_manual = false;
                entry.key = opt.key;
                entry.id = opt.id;
                entry.label = opt.label;
                entry.variant_index = opt.variant_index;
                entry.supports_levels = opt.supports_levels;
                entry.manual_cost = null;
                // Custo
                if (opt.cost_type === 'per_level') {
                    const lvl = parseInt(levelInput.value, 10) || 1;
                    entry.level = lvl;
                    entry.computed_cost = opt.value * lvl;
                } else if (opt.cost_type === 'variable' || opt.cost_type === 'unknown') {
                    entry.level = 1;
                    entry.computed_cost = 0;
                    // forçar manual pra variável (precisa o user digitar)
                    entry.is_manual = true;
                } else {
                    entry.level = 1;
                    entry.computed_cost = opt.value;
                }
                // Atualiza UI sem re-render completo
                nameInput.value = opt.label;
                configureLevelInput(opt.supports_levels, entry.level);
                costInput.value = entry.computed_cost;
                costInput.readOnly = !entry.is_manual;
                manualBtn.textContent = entry.is_manual ? '✏' : '📖';
                dropdown.style.display = 'none';
                persist();
            }

            function applyManualMode() {
                entry.is_manual = true;
                entry.key = 'manual:' + (nameInput.value || '');
                entry.id = 'manual:' + (nameInput.value || '');
                entry.label = nameInput.value || '';
                entry.variant_index = undefined;
                entry.supports_levels = false;
                entry.level = 1;
                entry.manual_cost = parseInt(costInput.value, 10) || 0;
                entry.computed_cost = entry.manual_cost;
                configureLevelInput(false, 1);
                costInput.readOnly = false;
                manualBtn.textContent = '✏';
                dropdown.style.display = 'none';
                persist();
            }

            function showDropdown(filter) {
                const cat = CATALOGS[kind];
                if (!cat.loaded) {
                    dropdown.innerHTML = '<div class="v2-dropdown-empty">Loading catalog…</div>';
                    dropdown.style.display = 'block';
                    return;
                }
                const q = (filter || '').toLowerCase().trim();
                const matches = cat.list.filter(o => {
                    if (!q) return true;
                    return o.label.toLowerCase().includes(q) || o.id.toLowerCase().includes(q);
                }).slice(0, 50);

                dropdown.innerHTML = '';
                if (matches.length === 0) {
                    const empty = document.createElement('div');
                    empty.className = 'v2-dropdown-empty';
                    empty.textContent = 'Nenhuma vantagem encontrada — clique no ✏ para digitar manualmente.';
                    dropdown.appendChild(empty);
                } else {
                    matches.forEach(opt => {
                        const item = document.createElement('div');
                        item.className = 'v2-dropdown-item';
                        const costSuffix = opt.cost_type === 'per_level'
                            ? `${opt.value} pts/nível`
                            : opt.cost_type === 'variable'
                                ? 'custo variável'
                                : `${opt.value} pts`;
                        item.innerHTML = `<span class="v2-dropdown-label">${escapeHtml(opt.label)}</span><span class="v2-dropdown-cost">${costSuffix}${opt.page_ref ? ' · p' + opt.page_ref : ''}</span>`;
                        item.addEventListener('mousedown', (e) => {
                            // mousedown porque blur do input fecha o dropdown antes do click
                            e.preventDefault();
                            applyCatalogSelection(opt);
                        });
                        dropdown.appendChild(item);
                    });
                }
                dropdown.style.display = 'block';
            }

            // Foco no nameInput → mostra dropdown (se NÃO manual)
            nameInput.addEventListener('focus', () => {
                if (!entry.is_manual) showDropdown(nameInput.value);
            });
            nameInput.addEventListener('input', () => {
                if (!entry.is_manual) {
                    showDropdown(nameInput.value);
                } else {
                    entry.label = nameInput.value;
                    entry.id = 'manual:' + nameInput.value;
                    entry.key = entry.id;
                    persist();
                }
            });
            nameInput.addEventListener('blur', () => {
                // Atrasar pra permitir click no dropdown
                setTimeout(() => { dropdown.style.display = 'none'; }, 150);
            });

            // Level
            levelInput.addEventListener('input', () => {
                const lvl = parseInt(levelInput.value, 10) || 1;
                entry.level = lvl;
                if (!entry.is_manual) {
                    const opt = findCatalogEntry(kind, entry.key);
                    if (opt && opt.cost_type === 'per_level') {
                        entry.computed_cost = opt.value * lvl;
                        costInput.value = entry.computed_cost;
                    }
                }
                persist();
            });

            // Custo (só editável em manual)
            costInput.addEventListener('input', () => {
                if (entry.is_manual) {
                    const c = parseInt(costInput.value, 10) || 0;
                    entry.manual_cost = c;
                    entry.computed_cost = c;
                    persist();
                }
            });

            // Toggle manual
            manualBtn.addEventListener('click', () => {
                if (entry.is_manual) {
                    // Voltar para catálogo: limpa
                    entry.is_manual = false;
                    entry.manual_cost = null;
                    entry.id = '';
                    entry.key = '';
                    entry.label = '';
                    entry.computed_cost = 0;
                    entry.supports_levels = false;
                    nameInput.value = '';
                    costInput.value = '';
                    costInput.readOnly = true;
                    configureLevelInput(false, 1);
                    manualBtn.textContent = '📖';
                    nameInput.focus();
                    persist();
                } else {
                    applyManualMode();
                }
            });

            // Notas
            notesInput.addEventListener('input', () => {
                entry.notes = notesInput.value;
                persist();
            });

            // Remover
            rm.addEventListener('click', () => {
                list.splice(idx, 1);
                input.value = JSON.stringify(list);
                renderPickerList(kind);
                recalc();
            });
        });
    }

    function addPickerEntry(kind) {
        const meta = PICKER_LIST_META[kind];
        const input = $(meta.input);
        let list;
        try { list = JSON.parse(input.value || '[]'); } catch (_) { list = []; }
        list.push({
            key: '',
            id: '',
            label: '',
            level: 1,
            variant_index: undefined,
            is_manual: false,
            manual_cost: null,
            computed_cost: 0,
            supports_levels: false,
            notes: '',
        });
        input.value = JSON.stringify(list);
        renderPickerList(kind);
        recalc();
        // Foco no input recém-criado pra abrir dropdown
        const rows = document.querySelectorAll(`#${meta.container} .v2-picker-input`);
        if (rows.length) rows[rows.length - 1].focus();
    }

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, c => ({
            '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
        }[c]));
    }

    // ============== Render Skills (com picker próprio) ==============

    function computeSkillLevel(skillEntry, primary, secondary) {
        const attr = (skillEntry.attribute || '').toUpperCase();
        const diff = (skillEntry.difficulty || '').toUpperCase();
        const attrMap = {
            ST: primary.st, DX: primary.dx, IQ: primary.iq, HT: primary.ht,
            PER: secondary.per, WILL: secondary.will,
        };
        const baseAttr = attrMap[attr];
        if (baseAttr === undefined) return null;
        const offset = { EASY: 0, AVERAGE: -1, HARD: -2, 'VERY HARD': -3 }[diff];
        if (offset === undefined) return null;
        const pts = parseInt(skillEntry.points, 10) || 0;
        if (pts < 1) return null;
        // GURPS Skill Cost Table: 1pt = base; 2pt = +1; 4pt = +2; 8pt = +3;
        // depois +4 pts cada +1.
        let bonus;
        if (pts < 2) bonus = 0;
        else if (pts < 4) bonus = 1;
        else if (pts < 8) bonus = 2;
        else bonus = 3 + Math.floor((pts - 8) / 4);
        const mod = parseInt(skillEntry.mod, 10) || 0;
        return baseAttr + offset + bonus + mod;
    }

    function renderSkillsList() {
        const input = $('skills-input');
        const container = $('skill-list');
        let list;
        try { list = JSON.parse(input.value || '[]'); } catch (_) { list = []; }
        container.innerHTML = '';

        // Snapshot dos primários/secundários atuais pra cálculo
        const primary = {
            st: val($('attr-st')), dx: val($('attr-dx')),
            iq: val($('attr-iq')), ht: val($('attr-ht'))
        };
        const mods = {};
        document.querySelectorAll('.v2-sec-mod').forEach(inp => {
            const v = parseFloat(inp.value || '0');
            if (v !== 0) mods[inp.dataset.key] = v;
        });
        const secondary = computeSecondary(primary, mods);

        list.forEach((entry, idx) => {
            const row = document.createElement('div');
            row.className = 'v2-list-row v2-skill-row';

            const isManual = entry.is_manual === true;

            // 1: Skill picker
            const pickerWrap = document.createElement('div');
            pickerWrap.className = 'v2-picker-wrap';
            const nameInput = document.createElement('input');
            nameInput.type = 'text';
            nameInput.className = 'v2-picker-input';
            nameInput.placeholder = isManual ? 'Skill name (manual)' : 'Search skill...';
            nameInput.value = entry.label || '';
            nameInput.autocomplete = 'off';
            pickerWrap.appendChild(nameInput);
            const dropdown = document.createElement('div');
            dropdown.className = 'v2-picker-dropdown';
            dropdown.style.display = 'none';
            pickerWrap.appendChild(dropdown);
            row.appendChild(pickerWrap);

            // 2: Default (read-only do catálogo)
            const defaultDisplay = document.createElement('input');
            defaultDisplay.type = 'text';
            defaultDisplay.className = 'v2-skill-default';
            defaultDisplay.readOnly = !isManual;
            defaultDisplay.value = entry.default || '';
            defaultDisplay.placeholder = '—';
            defaultDisplay.title = 'Default (e.g. DX-5)';
            row.appendChild(defaultDisplay);

            // 3: Attr/Diff display (DX/A, IQ/H etc.)
            const attrDiffInput = document.createElement('input');
            attrDiffInput.type = 'text';
            attrDiffInput.className = 'v2-skill-attrdiff';
            attrDiffInput.readOnly = !isManual;
            const diffShort = ({EASY:'E', AVERAGE:'A', HARD:'H', 'VERY HARD':'VH'})[entry.difficulty] || '';
            attrDiffInput.value = entry.attribute && entry.difficulty ? `${entry.attribute}/${diffShort}` : '';
            attrDiffInput.placeholder = '—';
            row.appendChild(attrDiffInput);

            // 4: Points
            const pointsInput = document.createElement('input');
            pointsInput.type = 'number';
            pointsInput.className = 'v2-skill-points';
            pointsInput.min = '0';
            pointsInput.value = entry.points || 0;
            row.appendChild(pointsInput);

            // 5: MOD (somado direto ao NH; modifier situacional/permanente)
            const modInput = document.createElement('input');
            modInput.type = 'number';
            modInput.className = 'v2-skill-mod';
            modInput.value = entry.mod || 0;
            modInput.placeholder = '0';
            modInput.title = 'MOD — added to the final NH (e.g. +2 from talent, -3 darkness)';
            row.appendChild(modInput);

            // 6: Level (calculated)
            const levelDisplay = document.createElement('span');
            levelDisplay.className = 'v2-skill-level-display';
            const lvl = computeSkillLevel(entry, primary, secondary);
            levelDisplay.textContent = lvl !== null ? lvl : '—';
            row.appendChild(levelDisplay);

            // 6: Specialty
            const specialtyInput = document.createElement('input');
            specialtyInput.type = 'text';
            specialtyInput.className = 'v2-skill-specialty';
            specialtyInput.value = entry.specialty || '';
            specialtyInput.placeholder = entry.requires_specialty ? '*specialty required*' : 'optional';
            row.appendChild(specialtyInput);

            // 7: Mode toggle
            const manualBtn = document.createElement('button');
            manualBtn.type = 'button';
            manualBtn.className = 'v2-manual-toggle';
            manualBtn.textContent = isManual ? '✏' : '📖';
            manualBtn.title = isManual ? 'Manual entry' : 'Catalog entry';
            row.appendChild(manualBtn);

            // 8: Notes
            const notesInput = document.createElement('input');
            notesInput.type = 'text';
            notesInput.className = 'v2-notes-input';
            notesInput.placeholder = 'Notes';
            notesInput.value = entry.notes || '';
            row.appendChild(notesInput);

            // 9: Remove
            const rm = document.createElement('button');
            rm.type = 'button';
            rm.className = 'v2-remove';
            rm.textContent = '×';
            row.appendChild(rm);

            container.appendChild(row);

            // ============ Eventos ============

            function persist() {
                input.value = JSON.stringify(list);
                recalc();
            }

            function refreshLevelDisplay() {
                const newLvl = computeSkillLevel(entry, primary, secondary);
                levelDisplay.textContent = newLvl !== null ? newLvl : '—';
                entry.computed_level = newLvl;
            }

            function applyCatalogSelection(opt) {
                entry.is_manual = false;
                entry.key = opt.key;
                entry.id = opt.id;
                entry.label = opt.label;
                entry.attribute = opt.attribute;
                entry.difficulty = opt.difficulty;
                entry.default = opt.default || '';
                entry.requires_specialty = opt.requires_specialty;
                entry.tl_dependent = opt.tl_dependent;
                entry.page_ref = opt.page_ref;
                nameInput.value = opt.label;
                defaultDisplay.value = opt.default || '';
                defaultDisplay.readOnly = true;
                const ds = ({EASY:'E', AVERAGE:'A', HARD:'H', 'VERY HARD':'VH'})[opt.difficulty] || '';
                attrDiffInput.value = `${opt.attribute}/${ds}`;
                attrDiffInput.readOnly = true;
                specialtyInput.placeholder = opt.requires_specialty ? '*specialty required*' : 'optional';
                manualBtn.textContent = '📖';
                dropdown.style.display = 'none';
                refreshLevelDisplay();
                persist();
            }

            function applyManualMode() {
                entry.is_manual = true;
                entry.key = 'manual:' + (nameInput.value || '');
                entry.id = entry.key;
                entry.label = nameInput.value || '';
                defaultDisplay.readOnly = false;
                attrDiffInput.readOnly = false;
                manualBtn.textContent = '✏';
                dropdown.style.display = 'none';
                persist();
            }

            function showDropdown(filter) {
                const cat = CATALOGS.skills;
                if (!cat.loaded) {
                    dropdown.innerHTML = '<div class="v2-dropdown-empty">Loading catalog…</div>';
                    dropdown.style.display = 'block';
                    return;
                }
                const q = (filter || '').toLowerCase().trim();
                const matches = cat.list.filter(o => {
                    if (!q) return true;
                    return o.label.toLowerCase().includes(q) || o.id.toLowerCase().includes(q);
                }).slice(0, 50);
                dropdown.innerHTML = '';
                if (matches.length === 0) {
                    const empty = document.createElement('div');
                    empty.className = 'v2-dropdown-empty';
                    empty.textContent = 'No skill found — click ✏ to enter manually.';
                    dropdown.appendChild(empty);
                } else {
                    matches.forEach(opt => {
                        const item = document.createElement('div');
                        item.className = 'v2-dropdown-item';
                        const ds = ({EASY:'E', AVERAGE:'A', HARD:'H', 'VERY HARD':'VH'})[opt.difficulty] || '';
                        const suffix = `${opt.attribute}/${ds}` + (opt.tl_dependent ? '/TL' : '') + (opt.requires_specialty ? ' †' : '') + (opt.page_ref ? ' · p' + opt.page_ref : '');
                        item.innerHTML = `<span class="v2-dropdown-label">${escapeHtml(opt.label)}</span><span class="v2-dropdown-cost">${suffix}</span>`;
                        item.addEventListener('mousedown', (e) => { e.preventDefault(); applyCatalogSelection(opt); });
                        dropdown.appendChild(item);
                    });
                }
                dropdown.style.display = 'block';
            }

            nameInput.addEventListener('focus', () => { if (!entry.is_manual) showDropdown(nameInput.value); });
            nameInput.addEventListener('input', () => {
                if (!entry.is_manual) {
                    showDropdown(nameInput.value);
                } else {
                    entry.label = nameInput.value;
                    entry.id = 'manual:' + nameInput.value;
                    entry.key = entry.id;
                    persist();
                }
            });
            nameInput.addEventListener('blur', () => setTimeout(() => { dropdown.style.display = 'none'; }, 150));

            defaultDisplay.addEventListener('input', () => {
                if (entry.is_manual) { entry.default = defaultDisplay.value; persist(); }
            });

            attrDiffInput.addEventListener('input', () => {
                if (entry.is_manual) {
                    // Parse "DX/A" -> attribute, difficulty
                    const m = attrDiffInput.value.toUpperCase().match(/^(ST|DX|IQ|HT|PER|WILL)\/(E|A|H|VH)$/);
                    if (m) {
                        entry.attribute = m[1];
                        entry.difficulty = ({E:'EASY', A:'AVERAGE', H:'HARD', VH:'VERY HARD'})[m[2]];
                        refreshLevelDisplay();
                    }
                    persist();
                }
            });

            pointsInput.addEventListener('input', () => {
                entry.points = parseInt(pointsInput.value, 10) || 0;
                refreshLevelDisplay();
                persist();
            });

            modInput.addEventListener('input', () => {
                entry.mod = parseInt(modInput.value, 10) || 0;
                refreshLevelDisplay();
                persist();
            });

            specialtyInput.addEventListener('input', () => {
                entry.specialty = specialtyInput.value;
                persist();
            });

            notesInput.addEventListener('input', () => {
                entry.notes = notesInput.value;
                persist();
            });

            manualBtn.addEventListener('click', () => {
                if (entry.is_manual) {
                    // back to catalog
                    entry.is_manual = false;
                    entry.label = '';
                    entry.id = '';
                    entry.key = '';
                    entry.attribute = '';
                    entry.difficulty = '';
                    entry.default = '';
                    nameInput.value = '';
                    defaultDisplay.value = '';
                    defaultDisplay.readOnly = true;
                    attrDiffInput.value = '';
                    attrDiffInput.readOnly = true;
                    manualBtn.textContent = '📖';
                    refreshLevelDisplay();
                    nameInput.focus();
                    persist();
                } else {
                    applyManualMode();
                }
            });

            rm.addEventListener('click', () => {
                list.splice(idx, 1);
                input.value = JSON.stringify(list);
                renderSkillsList();
                recalc();
            });
        });
    }

    function addSkillEntry() {
        const input = $('skills-input');
        let list;
        try { list = JSON.parse(input.value || '[]'); } catch (_) { list = []; }
        list.push({
            key: '', id: '', label: '',
            attribute: '', difficulty: '',
            default: '', specialty: '',
            points: 1, is_manual: false,
            computed_level: null, notes: '',
            requires_specialty: false, tl_dependent: false,
        });
        input.value = JSON.stringify(list);
        renderSkillsList();
        recalc();
        const inputs = document.querySelectorAll('#skill-list .v2-picker-input');
        if (inputs.length) inputs[inputs.length - 1].focus();
    }

    // ============== Maneuver Cards (Attack Melee/Ranged + Defense) ==============

    const MANEUVER_META = {
        maneuvers_melee:   { input: 'maneuvers_melee-input',   container: 'man-melee-cards',   hasDamage: true,  label: 'Melee'   },
        maneuvers_ranged:  { input: 'maneuvers_ranged-input',  container: 'man-ranged-cards',  hasDamage: true,  label: 'Ranged'  },
        maneuvers_defense: { input: 'maneuvers_defense-input', container: 'man-defense-cards', hasDamage: false, label: 'Defense' },
    };

    function renderManeuverCards(kind) {
        const meta = MANEUVER_META[kind];
        if (!meta) return;
        const input = $(meta.input);
        const container = $(meta.container);
        let list;
        try { list = JSON.parse(input.value || '[]'); } catch (_) { list = []; }
        container.innerHTML = '';

        list.forEach((entry, idx) => {
            const card = document.createElement('div');
            card.className = 'v2-maneuver-card';

            // Header: nome + botão remover
            const header = document.createElement('div');
            header.className = 'v2-maneuver-header';

            const nameInput = document.createElement('input');
            nameInput.type = 'text';
            nameInput.className = 'v2-maneuver-name';
            nameInput.placeholder = 'Maneuver name';
            nameInput.maxLength = 60;
            nameInput.value = entry.name || '';
            header.appendChild(nameInput);

            const rm = document.createElement('button');
            rm.type = 'button';
            rm.className = 'v2-remove v2-maneuver-remove';
            rm.textContent = '×';
            rm.title = 'Remove maneuver';
            header.appendChild(rm);

            card.appendChild(header);

            // Stats row: Damage (se aplicável) + NH
            const stats = document.createElement('div');
            stats.className = 'v2-maneuver-stats';

            if (meta.hasDamage) {
                const dmgLabel = document.createElement('label');
                dmgLabel.textContent = 'Damage';
                stats.appendChild(dmgLabel);
                const dmgInput = document.createElement('input');
                dmgInput.type = 'text';
                dmgInput.className = 'v2-maneuver-damage';
                dmgInput.placeholder = 'e.g. 1d+2 cut';
                dmgInput.maxLength = 30;
                dmgInput.value = entry.damage || '';
                stats.appendChild(dmgInput);
                dmgInput.addEventListener('input', () => {
                    entry.damage = dmgInput.value;
                    persist();
                });
            }

            const nhLabel = document.createElement('label');
            nhLabel.textContent = 'NH';
            stats.appendChild(nhLabel);
            const nhInput = document.createElement('input');
            nhInput.type = 'text';
            nhInput.className = 'v2-maneuver-nh';
            nhInput.placeholder = 'e.g. 14';
            nhInput.maxLength = 12;
            nhInput.value = entry.nh || '';
            stats.appendChild(nhInput);

            card.appendChild(stats);

            // Details textarea
            const detailsLabel = document.createElement('label');
            detailsLabel.className = 'v2-maneuver-details-label';
            detailsLabel.textContent = 'Details';
            card.appendChild(detailsLabel);

            const detailsInput = document.createElement('textarea');
            detailsInput.className = 'v2-maneuver-details';
            detailsInput.placeholder = 'Damage type, range, modifiers, notes...';
            detailsInput.maxLength = 1000;
            detailsInput.rows = 2;
            detailsInput.value = entry.details || '';
            card.appendChild(detailsInput);

            container.appendChild(card);

            // === Events ===
            function persist() {
                input.value = JSON.stringify(list);
            }

            nameInput.addEventListener('input', () => { entry.name = nameInput.value; persist(); });
            nhInput.addEventListener('input', () => { entry.nh = nhInput.value; persist(); });
            detailsInput.addEventListener('input', () => { entry.details = detailsInput.value; persist(); });
            rm.addEventListener('click', () => {
                list.splice(idx, 1);
                input.value = JSON.stringify(list);
                renderManeuverCards(kind);
            });
        });
    }

    function addManeuverCard(kind) {
        const meta = MANEUVER_META[kind];
        if (!meta) return;
        const input = $(meta.input);
        let list;
        try { list = JSON.parse(input.value || '[]'); } catch (_) { list = []; }
        const newEntry = { name: '', nh: '', details: '' };
        if (meta.hasDamage) newEntry.damage = '';
        list.push(newEntry);
        input.value = JSON.stringify(list);
        renderManeuverCards(kind);
        // Foco no nome do novo card
        const inputs = $(meta.container).querySelectorAll('.v2-maneuver-name');
        if (inputs.length) inputs[inputs.length - 1].focus();
    }

    // ============== Listas genéricas (equip) ==============

    function listConfig(field) {
        const cfg = {
            equipment_melee: { container: 'eq-melee-list', input: 'equipment_melee-input',
                fields: [
                    { name: 'name', placeholder: 'Nome', type: 'text' },
                    { name: 'damage', placeholder: 'Dano', type: 'text' },
                    { name: 'reach', placeholder: 'Reach', type: 'text' },
                    { name: 'notes', placeholder: 'Notas', type: 'text' }
                ] },
            equipment_ranged: { container: 'eq-ranged-list', input: 'equipment_ranged-input',
                fields: [
                    { name: 'name', placeholder: 'Nome', type: 'text' },
                    { name: 'damage', placeholder: 'Dano', type: 'text' },
                    { name: 'range', placeholder: 'Range', type: 'text' },
                    { name: 'shots', placeholder: 'Shots', type: 'text' }
                ] },
            equipment_armor: { container: 'eq-armor-list', input: 'equipment_armor-input',
                fields: [
                    { name: 'name', placeholder: 'Nome', type: 'text' },
                    { name: 'dr', placeholder: 'DR', type: 'number' },
                    { name: 'location', placeholder: 'Local', type: 'text' },
                    { name: 'notes', placeholder: 'Notas', type: 'text' }
                ] },
            equipment_misc: { container: 'eq-misc-list', input: 'equipment_misc-input',
                fields: [
                    { name: 'name', placeholder: 'Nome', type: 'text' },
                    { name: 'qty', placeholder: 'Qtd', type: 'number', default: 1 },
                    { name: 'weight', placeholder: 'Peso (lbs)', type: 'number' },
                    { name: 'notes', placeholder: 'Notas', type: 'text' }
                ] },
        };
        return cfg[field];
    }

    function renderList(field) {
        const cfg = listConfig(field);
        if (!cfg) return;
        const container = $(cfg.container);
        const input = $(cfg.input);
        let list;
        try { list = JSON.parse(input.value || '[]'); } catch (_) { list = []; }
        container.innerHTML = '';

        list.forEach((entry, idx) => {
            const row = document.createElement('div');
            row.className = 'v2-list-row';

            cfg.fields.forEach(f => {
                const inp = document.createElement('input');
                inp.type = f.type;
                inp.placeholder = f.placeholder;
                inp.value = entry[f.name] !== undefined ? entry[f.name] : '';
                inp.addEventListener('input', () => {
                    const v = (f.type === 'number') ? (inp.value === '' ? null : parseFloat(inp.value)) : inp.value;
                    list[idx][f.name] = v;
                    input.value = JSON.stringify(list);
                    recalc();
                });
                row.appendChild(inp);
            });

            const rm = document.createElement('button');
            rm.type = 'button';
            rm.className = 'v2-remove';
            rm.textContent = '×';
            rm.addEventListener('click', () => {
                list.splice(idx, 1);
                input.value = JSON.stringify(list);
                renderList(field);
                recalc();
            });
            row.appendChild(rm);

            container.appendChild(row);
        });
    }

    function addEntry(field) {
        if (field === 'advantages' || field === 'disadvantages') { addPickerEntry(field); return; }
        if (field === 'skills') { addSkillEntry(); return; }
        if (field === 'maneuvers_melee' || field === 'maneuvers_ranged' || field === 'maneuvers_defense') {
            addManeuverCard(field);
            return;
        }
        const cfg = listConfig(field);
        if (!cfg) return;
        const input = $(cfg.input);
        let list;
        try { list = JSON.parse(input.value || '[]'); } catch (_) { list = []; }
        const newEntry = {};
        cfg.fields.forEach(f => { newEntry[f.name] = f.default !== undefined ? f.default : ''; });
        list.push(newEntry);
        input.value = JSON.stringify(list);
        renderList(field);
        recalc();
    }

    // ============== Init ==============

    document.addEventListener('DOMContentLoaded', () => {
        // Carrega catálogos em paralelo
        loadCatalog('advantages').then(() => renderAdvantages());
        loadCatalog('disadvantages').then(() => renderDisadvantages());
        loadCatalog('modifiers'); // usado nos drawers
        loadCatalog('skills').then(() => renderSkillsList());

        // Render listas
        renderAdvantages();
        renderDisadvantages();
        renderSkillsList();
        ['equipment_melee','equipment_ranged','equipment_armor','equipment_misc']
            .forEach(renderList);
        ['maneuvers_melee','maneuvers_ranged','maneuvers_defense']
            .forEach(renderManeuverCards);

        // Botões add
        document.querySelectorAll('.v2-add-btn').forEach(btn => {
            btn.addEventListener('click', () => addEntry(btn.dataset.target));
        });

        // Preview imediato da foto ao selecionar arquivo (antes de salvar)
        const photoInput = document.getElementById('photo-input');
        const photoPreview = document.getElementById('photo-preview');
        if (photoInput && photoPreview) {
            photoInput.addEventListener('change', () => {
                const file = photoInput.files && photoInput.files[0];
                if (!file) return;
                if (photoPreview.dataset.objurl) {
                    URL.revokeObjectURL(photoPreview.dataset.objurl);
                }
                const url = URL.createObjectURL(file);
                photoPreview.dataset.objurl = url;
                photoPreview.src = url;
                photoPreview.style.display = '';
            });
        }

        // Recalc on any attr/mod change — também re-renderiza skills (level muda)
        document.querySelectorAll('.v2-attr-input, .v2-sec-mod').forEach(inp => {
            inp.addEventListener('input', () => {
                recalc();
                renderSkillsList();
            });
        });

        recalc();
    });

})();
