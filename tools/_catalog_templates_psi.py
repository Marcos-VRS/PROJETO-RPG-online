"""templates.json + psionics.md + character_development.md."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "gurps" / "data"
DOCS = ROOT / "docs" / "gurps"

# === META-TRAITS (Characters p262-263) ===
META_TRAITS = [
    {"id":"automaton","name_en":"Automaton","cost":-85,"page":263,
     "components":["Hidebound","Incurious","Low Empathy","No Sense of Humor","Reprogrammable","Slave Mentality","Indomitable"],
     "notes":"Robôs simples, autônomos sem iniciativa."},
    {"id":"machine","name_en":"Machine","cost":25,"page":263,
     "components":["Doesn't Eat or Drink","Doesn't Sleep","Doesn't Breathe","Immunity to Metabolic Hazards","Injury Tolerance (No Blood, No Brain, No Vitals)","Unaging"],
     "notes":"Construto/máquina. Não tem necessidades biológicas."},
    {"id":"spirit","name_en":"Spirit","cost":261,"page":263,
     "components":["Doesn't Breathe","Doesn't Eat or Drink","Doesn't Sleep","Immunity to Metabolic Hazards","Insubstantiality (Always On, -50%)","Invisibility (with Switchable, +10%)","Unaging","Unkillable 2"],
     "notes":"Espíritos não-físicos."},
    {"id":"quadruped","name_en":"Quadruped","cost":-35,"page":263,
     "components":["Extra Legs (Four Legs, 5 pts)","Horizontal (-10)","No Fine Manipulators (-30 ST)"],
     "notes":"4 patas, andar horizontal."},
    {"id":"aquatic","name_en":"Aquatic","cost":-25,"page":145,
     "components":["Doesn't Breathe (Gills, -50%)","Restricted Diet (raras)","Vulnerability (depending on env)"],
     "notes":"Vive na água."},
    {"id":"ice_creature","name_en":"Ice Creature","cost":-5,"page":263,
     "components":["Doesn't Breathe (Oxygen Combustion, -50%)","Temperature Tolerance (cold)","Vulnerability (Fire)"],
     "notes":"Adaptado a frio extremo."},
]

# === CHARACTER TEMPLATES samples (Characters p259-260) ===
CHARACTER_TEMPLATES = [
    {"id":"soldier","name_en":"Soldier","cost_base":50,"type":"character",
     "page":259,
     "notes":"Template típico: ST 11, DX 12, IQ 10, HT 11, Combat Reflexes, Guns 12, Soldier 12, Tactics 11, etc."},
    {"id":"wizard","name_en":"Wizard","cost_base":75,"type":"character",
     "page":259,
     "notes":"IQ 12+, Magery 1+, Alchemy/Thaumatology, escolha de spells."},
    {"id":"thief","name_en":"Thief","cost_base":50,"type":"character",
     "page":259,
     "notes":"DX 12, Stealth, Lockpicking, Pickpocket, Climbing, Acrobatics."},
]

# === RACIAL TEMPLATES samples (Characters p261-262) ===
RACIAL_TEMPLATES = [
    {"id":"human","name_en":"Human","cost":0,"page":261,
     "notes":"Default. Base de comparação."},
    {"id":"dwarf","name_en":"Dwarf","cost":35,"page":261,
     "modifiers":["ST +1","HT +1","Hard to Kill 2","Resistant to Poison +3","Dependency (Mana, occasional, no -10)","Lifting ST +2"],
     "notes":"Robusto, baixo, longevo."},
    {"id":"elf","name_en":"Elf","cost":35,"page":261,
     "modifiers":["DX +1","Per +2","Magery 0","Acute Vision 2","Extended Lifespan 2","Unaging","Code of Honor"],
     "notes":"Ágil, sentidos, ligação mágica."},
    {"id":"halfling","name_en":"Halfling","cost":0,"page":261,
     "modifiers":["ST -2","Size Modifier -1","DX +1","Per +1","Silence 1"],
     "notes":"Pequenos, ágeis, furtivos."},
    {"id":"orc","name_en":"Orc","cost":-10,"page":261,
     "modifiers":["ST +1","HT +1","Bad Temper","Bully","Social Stigma (Savage)"],
     "notes":"Forte, agressivo, marginalizado socialmente."},
]


def write_templates_json():
    out = {
        "$schema_version": "1.0",
        "source": {"book":"GURPS 4e — Basic Set: Characters","chapter":7,"pages":"258-263"},
        "$progress": {"status":"core_samples","notes_pt":"Meta-traits completas; templates de personagem e raciais como samples — design custom por campanha."},
        "meta_traits": META_TRAITS,
        "character_templates": CHARACTER_TEMPLATES,
        "racial_templates": RACIAL_TEMPLATES,
    }
    (DATA / "templates.json").write_text(json.dumps(out, ensure_ascii=False, indent=2)+"\n", encoding='utf-8')


def write_psionics_md():
    md = '''# GURPS 4e — Psionics (resumo)

> **Fonte:** *Basic Set: Characters*, capítulo 6 (pp 254-257). Expansão completa em *GURPS Psionic Powers*.

Psionics em GURPS são habilidades sobrenaturais "mentais", construídas como **vantagens com modificador especial Telepathic, ESP, Psychokinesis, etc.** Cada categoria é um **psi power** que requer um Talent associado.

## Categorias padrão

| Power | Talent | Abilities | Limitation |
|---|---|---|---|
| **Antipsi** | Antipsi Talent | Cancel/neutralize outros psi | Psionic |
| **ESP** | ESP Talent | Clairsentience, Danger Sense, Precognition, Psychometry | ESP -10% |
| **Psychic Healing** | Psychic Healing Talent | Healing (Psychic Healing -10%) | Psychic Healing |
| **Psychokinesis (PK)** | PK Talent | Telekinesis, Temperature Control, etc. | Psychokinetic -10% |
| **Telepathy** | Telepathy Talent | Mind Control, Mind Reading, Mind Shield, Telesend, etc. | Telepathic -10% |
| **Teleportation** | Teleportation Talent | Warp, Jumper | Psionic Teleportation -10% |

## Mecânica

- Cada habilidade é uma vantagem normal (Telekinesis, Mind Reading, etc.) com a **limitation correspondente do power** (-10%).
- O **Talent** adiciona ao roll de skill psiônica (usado quando rolagem é necessária).
- **Psi Static** (advantage p78) cria "anti-psi": habilidades psi não funcionam contra alguém com Psi Static.
- **Neutralize** (advantage p71) cancela poderes psi temporariamente.

## Pside effects (efeitos colaterais)

Alguns usos psi causam efeitos secundários:
- Drain mental: -1 IQ por X minutos
- Backlash: dano de FP em falha crítica
- Burnout: indisponível por 1d horas

Detalhes específicos por habilidade.

## Aquisição em jogo

Você pode adquirir psi abilities pagando pontos normalmente em jogo (cap 9 Characters). Talent é pré-requisito comum. Em settings sem psi, GM define disponibilidade.

---

Esse arquivo é stub. Detalhes completos exigem o livro *Psionic Powers*. Para o app, basta saber que habilidades psi reaproveitam o sistema de vantagens com modifier.
'''
    (DOCS / "psionics.md").write_text(md, encoding='utf-8')


def write_char_development_md():
    md = '''# GURPS 4e — Character Development (resumo)

> **Fonte:** *Basic Set: Characters*, capítulo 9 (pp 290-296).

## Improvement Through Adventure

Após cada sessão/aventura, GM dá **earned character points** (CPs) aos jogadores. Use pra:
- Melhorar atributos (cost: 10/20/20/10 por ponto, mesmas regras da criação)
- Adicionar/melhorar advantages
- Aprender/melhorar skills (custo de tempo + pontos)
- Buy off disadvantages (custa pontos = valor original do disad)

Taxa típica: 1-5 pts por sessão dependendo de play time + bom roleplay + objetivos.

## Improvement Through Study

Skills crescem em jogo com:
- **Self-Teaching:** 200h por ponto investido (skill complexa: 400h)
- **Teacher:** 200h por ponto (encontrar professor — Talent helps)
- **Job:** trabalho relacionado conta como study time parcial

## Aging Rolls (p444)

Quando idade ultrapassa thresholds (default 50, 70, 90), faça **HT roll a cada 6 meses**:
- Falha = perde 1 atributo (random)
- Crítica = perde 2

Modifiers: *Longevity*, *Unaging*, *Fit*, *Very Fit* protegem.

## Body Modification / Mind Transfer / Supernatural Afflictions

Cirurgia, magia, etc. podem mudar template físico em jogo. Custo de pontos = diferença entre templates (pode ser positivo ou negativo).

## Death

Personagem chega a -5×HP = morte automática. Em settings com **Resurrection** ou **Extra Life**, regras especiais.

## Trait Lists (Apêndice)

Pp 297-306 listam todos os traits do livro alfabeticamente (Advantages, Disadvantages, Modifiers, Skills, Techniques, Spells). Útil pra consulta rápida.

---

Para o app, esta seção é meramente referencial. Pontos earned são tracking simples; expandir conforme necessário.
'''
    (DOCS / "character_development.md").write_text(md, encoding='utf-8')


if __name__ == "__main__":
    write_templates_json()
    write_psionics_md()
    write_char_development_md()
    print("escritos: templates.json + psionics.md + character_development.md")
