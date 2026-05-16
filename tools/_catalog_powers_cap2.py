"""Adiciona new advantages + new modifiers do livro Powers cap 2."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADV = ROOT / "gurps" / "data" / "advantages.json"
MOD = ROOT / "gurps" / "data" / "modifiers.json"

# ============= NEW ADVANTAGES do Powers cap 2 (pp 92-100) =============
POWERS_ADVANTAGES = [
    {
        "id": "control",
        "name_en": "Control",
        "name_pt": "Controle (Elemento)",
        "type": "physical",
        "origin": "supernatural",
        "source_book": "GURPS Powers",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 20, "name_pt": "Common — Earth, Fire, Gravity, Light, Metal, Plastic, Sound, Water, Wood"},
                {"value": 15, "name_pt": "Occasional — Ceramics, Ferrous Metals, Ice, Steam, Stone"},
                {"value": 10, "name_pt": "Rare — Brick, Iron, Paper, Rubber"}
            ],
            "level_label": "por nível"
        },
        "description_pt": "Molda e move uma categoria de matéria/energia/força (seu 'elemento'). Sólidos: até 10×(nível²) lbs num objeto contínuo. Gases/energia: raio = nível em jds. Tocar (sólido/líquido) ou estar dentro da área (gás/energia) + IQ roll. Quick Contest se outro Control opera. Defensiva: pode shapear barreiras. Ofensiva: move perigo do elemento sobre foe. Não cria o elemento (precisa Create).",
        "page_ref": 92,
        "detail_level": "full"
    },
    {
        "id": "create",
        "name_en": "Create",
        "name_pt": "Criar (Elemento)",
        "type": "physical",
        "origin": "supernatural",
        "source_book": "GURPS Powers",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 40, "name_pt": "Large Category — Solid, Liquid, Gas, Organic, Inorganic, EM Waves, Physical Waves"},
                {"value": 20, "name_pt": "Medium Category — Acid, Biochemicals, Drugs, Earth, Metal"},
                {"value": 10, "name_pt": "Small Category — substância específica"}
            ],
            "level_label": "por nível"
        },
        "description_pt": "Cria elemento do nada via Concentrate + IQ roll. Sólido/líquido em mãos, gás/energia ao redor. Custa 2 FP por tentativa. Falha crítica = aparece de modo inconveniente. Nível define quantidade. Modifiers: Permanent (+300%), Subtle (+50%), Reduced Range (-20%).",
        "page_ref": 92,
        "detail_level": "full"
    },
    {
        "id": "illusion",
        "name_en": "Illusion",
        "name_pt": "Ilusão",
        "type": "mental",
        "origin": "supernatural",
        "source_book": "GURPS Powers",
        "cost": {"type": "fixed", "value": 25},
        "description_pt": "Cria construções de luz/som em raio 2 jds. Sem massa/substância. Concentrate maneuver. Quick Contest IQ vs Per dos observadores. Vitória = vê real; senão nota falha. Para causar Fright Check, exige Artist (Illusion) Quick Contest vs IQ/Per. Modifiers: Adjustable +20%, Independent +40%, Mobile +40%/nv, Reduced Fatigue Cost, Targeting +20%, etc.",
        "page_ref": 95,
        "detail_level": "full"
    },
    {
        "id": "leech",
        "name_en": "Leech",
        "name_pt": "Drenagem (Vampire)",
        "type": "physical",
        "origin": "supernatural",
        "source_book": "GURPS Powers",
        "cost": {"type": "variable", "formula": "25 pts level 1 + 4 pts/nível adicional"},
        "description_pt": "Drena vida via contato (grapple/pin). Cada nível: 1 HP/seg drenado. Cura 1 HP por 3 HP roubados (não passa max). Drain termina se solta/morre. Variantes: Leech (Mechanical) afeta máquinas. Pontos convertem em dados conforme Modifying Dice (p269 Basic). Modifiers: Accelerated Healing +25%/lvl, Affects Self +0% (heals you), Steal FP +50% etc.",
        "page_ref": 96,
        "detail_level": "full"
    },
    {
        "id": "neutralize_powers",
        "name_en": "Neutralize (Powers variant)",
        "name_pt": "Neutralizar (Poderes — variant)",
        "type": "mental",
        "origin": "supernatural",
        "source_book": "GURPS Powers",
        "cost": {"type": "fixed", "value": 50},
        "description_pt": "Versão do Neutralize do Basic Set adaptada pra Powers: pode neutralizar TODOS poderes de um source (magia, psi, super, etc.) — não só psi. Veja entry 'neutralize' do Basic Set p71 e Static p98 do Powers. Talent: Antipsi Talent ou equivalente.",
        "page_ref": 97,
        "detail_level": "full"
    },
    {
        "id": "static",
        "name_en": "Static",
        "name_pt": "Estática (anti-poderes)",
        "type": "physical",
        "origin": "supernatural",
        "source_book": "GURPS Powers",
        "cost": {"type": "fixed", "value": 30},
        "description_pt": "Bloqueia poderes de UM source específico de afetá-lo (ou equipamento que carrega). Compre separado por source. Magic, Psi, super-powers, etc. Não nega poderes que afetam ambiente ao redor (telekinético pode levantar pedra sobre você). Bloqueia friendly e hostile igualmente. Não pode possuir abilities/Talent desse source. Enhancements: Area Effect +50%/nv, Discriminatory +100%, Switchable +10%. Limitations: Resistible -50%.",
        "page_ref": 97,
        "detail_level": "full"
    },
]

# ============= NEW ENHANCEMENTS do Powers cap 2 (pp 109-111) =============
POWERS_ENHANCEMENTS = [
    {"id":"erosive","name_en":"Erosive","name_pt":"Erosivo","cost":"+10%","applies_to":["Innate Attack","attack"],"source_book":"GURPS Powers","description_pt":"Cada acerto bem-sucedido remove 1 ponto de DR (cumulativo) da armadura/cobertura atingida, mesmo se não penetrar. DR perdida não regenera; conserto exige reparos físicos.","page_ref":109},
    {"id":"force_field","name_en":"Force Field","name_pt":"Campo de Força","cost":"+20%","applies_to":["DR"],"source_book":"GURPS Powers","description_pt":"Já existe para DR no Basic Set (p47). Reforço aqui: força protetora projetada cobrindo corpo + carregados. Reduz dano antes de armor DR.","page_ref":109},
    {"id":"game_time","name_en":"Game Time","cost":"+0%","name_pt":"Tempo de Jogo","applies_to":["Extended Duration"],"source_book":"GURPS Powers","description_pt":"Variante Extended Duration: usa tempo real fora do jogo (sessões). Não afeta cost.","page_ref":109},
    {"id":"independent","name_en":"Independent","name_pt":"Independente","cost":"+40%","applies_to":["attack with duration","Affliction","Innate Attack"],"source_book":"GURPS Powers","description_pt":"Habilidade continua funcionando independente de concentração depois de ativada. Pode usar outras abilities enquanto esta opera.","page_ref":110},
    {"id":"long_range","name_en":"Long-Range","name_pt":"Longo Alcance","cost":"+50%/nível","applies_to":["ranged","Telecommunication"],"source_book":"GURPS Powers","description_pt":"Cada nível usa próxima coluna da Long-Distance Modifiers table (p241 Magic) em vez da Size/Speed/Range table. Permite alcance enorme (km, planetário).","page_ref":110},
    {"id":"reflexive","name_en":"Reflexive","name_pt":"Reflexivo","cost":"+40%","applies_to":["any"],"source_book":"GURPS Powers","description_pt":"Ativa automaticamente quando relevante; não exige ação. Comum em defesas (Damage Resistance, Magic Resistance), poderes de aviso (Danger Sense), e habilidades passivas.","page_ref":110},
    {"id":"reliable_enh","name_en":"Reliable","name_pt":"Confiável","cost":"+5%/+1, max +10","applies_to":["abilities with skill rolls (Warp, etc.)"],"source_book":"GURPS Powers","description_pt":"+1/nível ao IQ roll de ativação. Já no Basic Set para Warp p98.","page_ref":110},
    {"id":"ricochet","name_en":"Ricochet","name_pt":"Ricochete","cost":"+10%","applies_to":["ranged Innate Attack"],"source_book":"GURPS Powers","description_pt":"Pode ricochetear de superfície dura (parede, chão) pra acertar alvo atrás de cover. Skill -2 por ricochete.","page_ref":110},
    {"id":"switchable","name_en":"Switchable","name_pt":"Alternável","cost":"+10%","applies_to":["Always On abilities"],"source_book":"GURPS Powers","description_pt":"Ability normalmente Always On pode ser desligada à vontade. Action-free no início do turno.","page_ref":110},
    {"id":"world_spanning","name_en":"World-Spanning","name_pt":"Inter-Mundos","cost":"+50%","applies_to":["range-based abilities","Mindlink","Telecommunication"],"source_book":"GURPS Powers","description_pt":"Funciona entre planos/dimensões/timelines paralelas. Default abilities ranged não atravessam barreiras dimensionais.","page_ref":111},
]

# ============= NEW LIMITATIONS do Powers cap 2 (pp 112-114) =============
POWERS_LIMITATIONS = [
    {"id":"all_out","name_en":"All-Out","name_pt":"Tudo-ou-Nada","cost":"-25%","applies_to":["any"],"source_book":"GURPS Powers","description_pt":"Usar a habilidade impede defesas ativas até início do próximo turno. Sem Dodge/Parry/Block enquanto cooldown.","page_ref":112},
    {"id":"aspected","name_en":"Aspected","name_pt":"Aspectado","cost":"-20%","applies_to":["any"],"source_book":"GURPS Powers","description_pt":"Funciona só em circunstâncias temáticas específicas (somente de noite, somente em batalha, etc.). Mais restrito que Accessibility.","page_ref":112},
    {"id":"blockable","name_en":"Blockable","name_pt":"Bloqueável","cost":"-5%","applies_to":["any with line-of-sight"],"source_book":"GURPS Powers","description_pt":"Material comum mas específico bloqueia (chumbo bloqueia X-ray vision; espelho bloqueia gaze; etc.).","page_ref":112},
    {"id":"fickle","name_en":"Fickle","name_pt":"Volúvel","cost":"-20%","applies_to":["any"],"source_book":"GURPS Powers","description_pt":"Roll 3d cada vez que ativa: 17-18 falha (independente de outros rolls). Power 'desliga' sozinho às vezes.","page_ref":112},
    {"id":"insubstantial_only","name_en":"Insubstantial Only","name_pt":"Só Insubstancial","cost":"-30%","applies_to":["abilities"],"source_book":"GURPS Powers","description_pt":"Só funciona quando você está insubstancial (Insubstantiality, Spirit meta-trait). Útil para spirit powers.","page_ref":113},
    {"id":"greater_than_one_month","name_en":"Greater than One Month","name_pt":"Mais de Um Mês","cost":"-30%","applies_to":["Extended Duration"],"source_book":"GURPS Powers","description_pt":"Variante para Extended Duration acima de 1 mês — efeitos podem ser desfeitos via tratamento longo.","page_ref":113},
    {"id":"minimum_range","name_en":"Minimum Range","name_pt":"Alcance Mínimo","cost":"-5%","applies_to":["ranged"],"source_book":"GURPS Powers","description_pt":"Não pode usar abaixo de range mínimo (5 jds típico). Em close combat, ability inútil.","page_ref":113},
    {"id":"requires_concentrate_ready","name_en":"Requires Concentrate or Ready","name_pt":"Requer Concentrate/Ready","cost":"-15%","applies_to":["abilities normally instant"],"source_book":"GURPS Powers","description_pt":"Reflexive abilities precisam Concentrate/Ready maneuver para ativar — não funcionam reflexivamente.","page_ref":113},
    {"id":"short_range","name_en":"Short-Range","name_pt":"Curto Alcance","cost":"-10%/nível","applies_to":["ranged"],"source_book":"GURPS Powers","description_pt":"Range reduzido drasticamente. Cada nível usa coluna anterior da Long-Distance table. Oposto de Long-Range.","page_ref":113},
    {"id":"visible","name_en":"Visible","name_pt":"Visível","cost":"-10%","applies_to":["abilities normally invisible"],"source_book":"GURPS Powers","description_pt":"Manifestação visível óbvia (mão fantasma, luz brilhante, ondas distorcidas). Compromete stealth e secrecy.","page_ref":114},
]


def main():
    # Append advantages
    adv = json.loads(ADV.read_text(encoding='utf-8'))
    existing_adv_ids = {e["id"] for e in adv["entries"]}
    added_adv = 0
    for e in POWERS_ADVANTAGES:
        if e["id"] in existing_adv_ids:
            # Já existia (control e neutralize talvez); ainda assim, marca source
            for ex in adv["entries"]:
                if ex["id"] == e["id"]:
                    ex.setdefault("source_book", e.get("source_book", "GURPS Basic Set: Characters"))
                    break
        else:
            adv["entries"].append(e)
            existing_adv_ids.add(e["id"])
            added_adv += 1
    adv.setdefault("$expansion", {})["GURPS Powers Cap 2"] = {
        "advantages_added": added_adv,
        "completion_date": "2026-05-16"
    }
    ADV.write_text(json.dumps(adv, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
    print(f"advantages.json: +{added_adv} entries (total {len(adv['entries'])})")

    # Append enhancements + limitations
    mods = json.loads(MOD.read_text(encoding='utf-8'))
    existing_enh = {e["id"] for e in mods["enhancements"]}
    existing_lim = {e["id"] for e in mods["limitations"]}
    enh_added = 0
    for e in POWERS_ENHANCEMENTS:
        if e["id"] not in existing_enh:
            mods["enhancements"].append(e)
            existing_enh.add(e["id"])
            enh_added += 1
    lim_added = 0
    for e in POWERS_LIMITATIONS:
        if e["id"] not in existing_lim:
            mods["limitations"].append(e)
            existing_lim.add(e["id"])
            lim_added += 1
    mods.setdefault("$expansion", {})["GURPS Powers Cap 2"] = {
        "enhancements_added": enh_added, "limitations_added": lim_added,
        "completion_date": "2026-05-16",
    }
    MOD.write_text(json.dumps(mods, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
    print(f"modifiers.json: +{enh_added} enhancements, +{lim_added} limitations (totals: {len(mods['enhancements'])} enh, {len(mods['limitations'])} lim)")


if __name__ == "__main__":
    main()
