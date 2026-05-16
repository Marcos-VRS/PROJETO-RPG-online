"""Append batch de vantagens G-final + H-M no advantages.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "gurps" / "data" / "advantages.json"

NEW_ENTRIES = [
    # ===== G (final, pp 58) =====
    {
        "id": "growth",
        "name_en": "Growth",
        "name_pt": "Crescimento",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "per_level", "value": 10},
        "description_pt": "Cada nível aumenta Size Modifier em +1. Altura via tabela SM (p19). +1 SM/segundo. Equipamento não muda de tamanho. Precisa comprar ST suficiente (5×altura em jds); pode usar Size limitation. Pode romper paredes se thrust damage > DR. Modifier: Maximum Size Only +0%.",
        "page_ref": 58,
        "detail_level": "full"
    },
    {
        "id": "gunslinger",
        "name_en": "Gunslinger",
        "name_pt": "Atirador de Elite",
        "type": "physical",
        "origin": "mundane",
        "cost": {"type": "fixed", "value": 25},
        "description_pt": "Tiros precisos sem Aim. Funciona com Beam Weapons, Gunner, Guns, Liquid Projector (NÃO em armas muscle-powered). One-handed RoF 1-3: ganha Acc full sem Aim; two-handed ou automático: ½ Acc (round up). Com Aim, ganha tudo + scopes/brace. Cinematic — GM pode proibir em realista.",
        "page_ref": 58,
        "detail_level": "full"
    },

    # ===== H (pp 58-60) =====
    {
        "id": "hard_to_kill",
        "name_en": "Hard to Kill",
        "name_pt": "Difícil de Matar",
        "type": "physical",
        "origin": "mundane",
        "cost": {"type": "per_level", "value": 2},
        "description_pt": "+1/nível em HT rolls de sobrevivência a -HP ou pior, e em HT rolls de morte instantânea (cardíaca, veneno). Se o bônus salvar, colapsa parecendo morto mas acorda no tempo normal (Recovering from Unconsciousness, p423). Diagnosis revela verdade. Realista: GM pode limitar a 1-2 níveis.",
        "page_ref": 58,
        "detail_level": "full"
    },
    {
        "id": "hard_to_subdue",
        "name_en": "Hard to Subdue",
        "name_pt": "Difícil de Subjugar",
        "type": "physical",
        "origin": "mundane",
        "cost": {"type": "per_level", "value": 2},
        "description_pt": "+1/nível em HT rolls para evitar unconsciousness (ferimento, drogas, ultra-tech) e resistir poderes sobrenaturais que causam unconsciousness. Realista: GM pode limitar a 1-2.",
        "page_ref": 59,
        "detail_level": "full"
    },
    {
        "id": "healing",
        "name_en": "Healing",
        "name_pt": "Cura",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "fixed", "value": 30},
        "description_pt": "Cura outros via contato físico. 1 seg concentração + IQ roll (-2 se subject inconsciente). Heal Injuries: 1 FP por 2 HP curados (round up); falha = 1d FP; crítica = +1d dano no subject. Sangramento para com 1 HP. Curar membro paralisado: IQ-6, cura todos HP da lesão (1 tentativa por curador). Não restaura membros perdidos nem ressuscita. Cure Disease: IQ com modificador (+1 cold até -15 AIDS); FP = 2× penalty. Penalty cumulativo -3 por cura sucessiva no mesmo subject. Enhancements: Faith Healing +20%, Xenohealing +20% a +100%. Limitations: Disease Only -40%, Injuries Only -20%, Own Race Only -20%, Psychic Healing -10%.",
        "page_ref": 59,
        "detail_level": "full"
    },
    {
        "id": "hermaphromorph",
        "name_en": "Hermaphromorph",
        "name_pt": "Hermafromorfo",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 5},
        "description_pt": "Alterna entre formas neutra, masculina e feminina funcionais. 10 seg. Comuns: Preparation Required, Takes Extra Time, Takes Recharge.",
        "page_ref": 59,
        "detail_level": "full"
    },
    {
        "id": "high_manual_dexterity",
        "name_en": "High Manual Dexterity",
        "name_pt": "Alta Destreza Manual",
        "type": "physical",
        "origin": "mundane",
        "cost": {"type": "per_level", "value": 5, "level_label": "máx 4 níveis"},
        "description_pt": "+1/nível em DX para tarefas delicadas. Aplica em DX-based: Artist, Jeweler, Knot-Tying, Leatherworking, Lockpicking, Pickpocket, Sewing, Sleight of Hand, Surgery + Machinist/Mechanic em trabalho fino. NÃO afeta combate nem tarefas IQ-based.",
        "page_ref": 59,
        "detail_level": "full"
    },
    {
        "id": "high_pain_threshold",
        "name_en": "High Pain Threshold",
        "name_pt": "Alto Limiar de Dor",
        "type": "physical",
        "origin": "mundane",
        "cost": {"type": "fixed", "value": 10},
        "description_pt": "Nunca sofre shock penalty quando ferido. +3 em HT rolls contra knockdown/stunning, +3 para resistir tortura física. GM pode permitir Will+3 em outras situações. Incluído em Supernatural Durability (incompatível).",
        "page_ref": 59,
        "detail_level": "full"
    },
    {
        "id": "higher_purpose",
        "name_en": "Higher Purpose",
        "name_pt": "Propósito Maior",
        "type": "mental",
        "origin": "mundane",
        "cost": {"type": "fixed", "value": 5},
        "description_pt": "Conduzido a exceder limites num pursuit específico (declarado como Code of Honor: 'Defender mulheres', 'Matar demônios'). +1 em todos rolls relacionados ao pursuit. Desvio = perde bônus + GM pode penalizar. Deve ser específico, com risco/inconveniência genuínos. GM aprova.",
        "page_ref": 59,
        "detail_level": "full"
    },
    {
        "id": "hyperspectral_vision",
        "name_en": "Hyperspectral Vision",
        "name_pt": "Visão Hiperespectral",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 25},
        "description_pt": "Visão integrada IR + visível + UV. Visão noturna quase perfeita; em escuridão total funciona como Infravision. +3 em Vision rolls, Forensics, Observation, Search, Tracking. Incompatível com Infravision e Ultravision (substitui ambos). Modifiers cinematic: Extended Low-Band +30% (radio/radar), Extended High-Band +30% (X-ray/gamma).",
        "page_ref": 60,
        "detail_level": "full"
    },

    # ===== I (pp 60-64) =====
    {
        "id": "illuminated",
        "name_en": "Illuminated",
        "name_pt": "Iluminado",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "fixed", "value": 15},
        "description_pt": "'Iluminatus' no sentido original — sabe das conspirações intuitivamente. Reconhece outros Illuminati à vista (infalível). Em rolls de Current Affairs/Hidden Lore/Intelligence Analysis para distinguir coincidência de conspiração, rola contra o maior de IQ ou skill. Percebe e fala com seres sobrenaturais ligados a conspirações Iluminadas; +3 reaction deles. Outros Illuminati também identificam você. Setting místico/fantástico.",
        "page_ref": 60,
        "detail_level": "full"
    },
    {
        "id": "improved_g_tolerance",
        "name_en": "Improved G-Tolerance",
        "name_pt": "Tolerância G Aprimorada",
        "type": "physical",
        "origin": "exotic",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 5,  "name_pt": "0.3G de incremento"},
                {"value": 10, "name_pt": "0.5G de incremento"},
                {"value": 15, "name_pt": "1G de incremento"},
                {"value": 20, "name_pt": "5G de incremento"},
                {"value": 25, "name_pt": "10G de incremento"}
            ]
        },
        "description_pt": "Funciona sob ampla gama de gravidades. Default humano sofre penalty a cada 0.2G. Maior incremento = menos penalty. Humanos normais limitados a 10 pts (1G).",
        "page_ref": 60,
        "detail_level": "full"
    },
    {
        "id": "indomitable",
        "name_en": "Indomitable",
        "name_pt": "Indomável",
        "type": "mental",
        "origin": "mundane",
        "cost": {"type": "fixed", "value": 15},
        "description_pt": "Impossível de ser influenciado por palavras/ações ordinárias. Skills de Influence falham automaticamente, exceto contra quem tem Empathy (ou Animal Empathy/Plant Empathy/Spirit Empathy conforme natureza). Frequentemente acompanha Unfazeable.",
        "page_ref": 60,
        "detail_level": "full"
    },
    {
        "id": "infravision",
        "name_en": "Infravision",
        "name_pt": "Infravisão",
        "type": "physical",
        "origin": "exotic",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 0,  "name_pt": "Só Infravision sempre (limitações permanentes)"},
                {"value": 10, "name_pt": "Pode alternar com visão normal"}
            ]
        },
        "description_pt": "Vê IR (calor). Combate sem penalty em escuridão absoluta contra alvos quentes. +2 em Vision rolls contra alvos quentes; +3 em Tracking via trilha de calor (até 1h). Não distingue cores. -4 para distinguir objetos de tamanho/forma similar. -4 Vision para ler por calor refletido. Pode ser ofuscado por flashes IR.",
        "page_ref": 60,
        "detail_level": "full"
    },
    {
        "id": "injury_tolerance",
        "name_en": "Injury Tolerance",
        "name_pt": "Tolerância a Ferimentos",
        "type": "physical",
        "origin": "exotic",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 100, "name_pt": "Diffuse — corpo fluido/enxame/energia; imune a crippling; reduz dano físico drasticamente. Inclui No Blood, No Brain, No Vitals."},
                {"value": 40,  "name_pt": "Homogenous — sem órgãos internos vulneráveis. Reduz piercing/impaling. Inclui No Brain, No Vitals."},
                {"value": 5,   "name_pt": "No Blood — sem fluido vital; não sangra; imune a toxinas hematogênicas"},
                {"value": 5,   "name_pt": "No Brain — cérebro distribuído; sem extra damage por crânio/face"},
                {"value": 5,   "name_pt": "No Eyes — sem olhos; imune a blinding attacks"},
                {"value": 7,   "name_pt": "No Head — sem cabeça; inclui No Brain. Sem skull/face hit locations."},
                {"value": 5,   "name_pt": "No Neck — sem pescoço; imune a decapitação, estrangulamento"},
                {"value": 5,   "name_pt": "No Vitals — sem órgãos vitais; vitals/groin tratados como torso"},
                {"value": 20,  "name_pt": "Unliving — corpo não-vivo (máquinas, mortos-vivos corporais); reduz piercing/impaling"}
            ]
        },
        "description_pt": "Diffuse/Homogenous/Unliving são mutuamente incompatíveis. Diversas formas podem ser combinadas. Ver p380 para detalhes sobre injury para targets unliving/homogenous/diffuse.",
        "page_ref": 60,
        "detail_level": "full"
    },
    {
        "id": "innate_attack",
        "name_en": "Innate Attack",
        "name_pt": "Ataque Inato",
        "type": "physical",
        "origin": "exotic",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 5,  "name_pt": "Burning (burn) — 5 pts/dado; igniza fogos"},
                {"value": 10, "name_pt": "Corrosion (cor) — 10 pts/dado; reduz DR alvo em 1 a cada 5 pts dano"},
                {"value": 5,  "name_pt": "Crushing (cr) — 5 pts/dado; knockback; mais eficaz em blunt trauma"},
                {"value": 7,  "name_pt": "Cutting (cut) — 7 pts/dado; ×1.5 dano penetrante; knockback"},
                {"value": 10, "name_pt": "Fatigue (fat) — 10 pts/dado; reduz FP não HP; não afeta máquinas"},
                {"value": 8,  "name_pt": "Impaling (imp) — 8 pts/dado; ×2 dano em carne; pode mirar vitais/olhos"},
                {"value": 3,  "name_pt": "Small Piercing (pi-) — 3 pts/dado; ½ dano em carne"},
                {"value": 5,  "name_pt": "Piercing (pi) — 5 pts/dado; rifle/pistol padrão"},
                {"value": 6,  "name_pt": "Large Piercing (pi+) — 6 pts/dado; ×1.5 em carne"},
                {"value": 8,  "name_pt": "Huge Piercing (pi++) — 8 pts/dado; ×2 em carne"},
                {"value": 4,  "name_pt": "Toxic (tox) — 4 pts/dado; dano celular; não afeta máquinas"}
            ]
        },
        "description_pt": "Ataque natural built-in. Default: ranged, 1/2D 10, Max 100, Acc 3, RoF 1, Recoil 1, Shots N/A. Inflige 1d/nível. Modificadores p101-116 permitem criar quase qualquer ataque. Partial dice: ±1 dano = ±0.3 dado, 1pt = 0.25 dado. Alternative Attacks: ataques múltiplos como mesmo ability — full price no mais caro, 1/5 nos outros (não simultâneos).",
        "page_ref": 61,
        "detail_level": "full"
    },
    {
        "id": "insubstantiality",
        "name_en": "Insubstantiality",
        "name_pt": "Insubstancialidade",
        "type": "physical",
        "origin": "supernatural",
        "cost": {"type": "fixed", "value": 80},
        "description_pt": "Intangível, passa por sólidos. Gravidade não afeta — move-se em qualquer direção a Move full, silenciosamente. Percebe e fala com mundo tangível mas não pega objetos. Ataques físicos/energia mútuos não funcionam. Psi e magia funcionam mas a -3. Não pode materializar dentro de sólido. Atravessar sólido = suffocation como nadar. Enhancements: Affect Substantial +100%, Can Carry Objects +10% a +100%, Partial Change +20%/+100%. Limitations: Always On -50%, Usually On -40%.",
        "page_ref": 62,
        "detail_level": "full"
    },
    {
        "id": "intuition",
        "name_en": "Intuition",
        "name_pt": "Intuição",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "fixed", "value": 15},
        "description_pt": "Diante de alternativas sem lógica clara, pede pra usar Intuition. GM rola IQ secretamente: bônus = boas escolhas, penalty = más. Sucesso → guia para boa; crítico → melhor; falha → nada; falha crítica → guia para má. 1 roll por pergunta. GM nunca permite curto-circuitar aventura.",
        "page_ref": 63,
        "detail_level": "full"
    },
    {
        "id": "invisibility",
        "name_en": "Invisibility",
        "name_pt": "Invisibilidade",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 40},
        "description_pt": "Sempre on (sem enhancement). Ainda faz barulho, pegadas, cheiro; equipamento permanece visível. Sem carregar nada: +9 em Stealth quando ser visto importa. Remote viewing paranormal segue não vendo. Default: invisível a UM tipo de visão. Tipos: eletromagnético (visão normal/IR/UV/radar), sonar, magnetic, etc. Invisível a EM = sem sombra, sem reflexo. Enhancements: Affects Machines +50%, Can Carry Objects +10/+100%, Extended +20%/tipo, Switchable +10%, Usually On +5%. Limitations: Machines Only -50%, Substantial Only -10%, Visible Reflection -10%, Visible Shadow -10%.",
        "page_ref": 63,
        "detail_level": "full"
    },

    # ===== J (pp 64) =====
    {
        "id": "jumper",
        "name_en": "Jumper",
        "name_pt": "Saltador (Tempo/Mundos)",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "fixed", "value": 100, "note": "Jumper(Time) e Jumper(World) compram separados"},
        "description_pt": "Viaja no tempo OU entre mundos paralelos pela vontade. Visualizar destino + 10 seg concentração + IQ roll (-1/seg omitido, max -10 sem prep; 14+ sempre falha). Sucesso → destino. Falha crítica → destino errado escolhido pelo GM. Aparece no mesmo local. Sem 'safe location' a até 100 jds → falha conhecida. Custa ≥1 FP. Carrega até Basic Lift. Múltiplos Jumpers em contato podem 'pegar carona'. Enhancements: Extra Carrying Capacity +10/+20/+30/+50%, New Worlds +50%, Omni-Jump +10%, Tracking +20%, Tunnel +40%, Warp Jump +10%. Limitations: Cannot Escort -10%, Cannot Follow -20%, Drift -15%, Limited Jump -10%, Maximum Range (GM), Naked -30%, Stunning -10%.",
        "page_ref": 64,
        "detail_level": "full"
    },

    # ===== L (pp 65-66) =====
    {
        "id": "language_talent",
        "name_en": "Language Talent",
        "name_pt": "Talento Linguístico",
        "type": "mental",
        "origin": "mundane",
        "cost": {"type": "fixed", "value": 10},
        "description_pt": "Ao aprender idioma acima de None, automaticamente sobe um nível: 2 pts por Accented, 4 pts por Native (vs 4/6 normais). Ver Language (p23).",
        "page_ref": 65,
        "detail_level": "full"
    },
    {
        "id": "legal_enforcement_powers",
        "name_en": "Legal Enforcement Powers",
        "name_pt": "Poderes Legais de Aplicação",
        "type": "social",
        "origin": "mundane",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 5,  "name_pt": "Local — prender suspeitos, busca com mandado, talvez porte oculto. Ex: policial moderno, bobby vitoriano."},
                {"value": 10, "name_pt": "Nacional/internacional OU sem respeito a civil rights OU investigação coberta OU matar com impunidade. Ex: FBI, Royal Guard medieval."},
                {"value": 15, "name_pt": "Três ou mais do nível anterior. Ex: Gestapo, KGB, Stasi."}
            ]
        },
        "description_pt": "Quase sempre exige Duty. Pode exigir Reputation. Inclui Police Rank 0 — compre mais Rank para hierarquia.",
        "page_ref": 65,
        "detail_level": "full"
    },
    {
        "id": "legal_immunity",
        "name_en": "Legal Immunity",
        "name_pt": "Imunidade Legal",
        "type": "social",
        "origin": "mundane",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 5,  "name_pt": "Sujeito a regras paralelas tão estritas. Ex: abade medieval, observador UN."},
                {"value": 10, "name_pt": "Regras paralelas menos estritas. Ex: Bardic Immunity."},
                {"value": 15, "name_pt": "Quase qualquer coisa se não fere quem concedeu. Ex: duque medieval."},
                {"value": 20, "name_pt": "Diplomatic Immunity — ignora leis estrangeiras; só persona non grata."}
            ]
        },
        "description_pt": "+5 pts opcional: 'diplomatic pouch' (objetos invioláveis). Bardic Immunity exige 1+ pt em Performance/Poetry/Singing. Diplomatic geralmente requer Administrative Rank + Duty.",
        "page_ref": 65,
        "detail_level": "full"
    },
    {
        "id": "less_sleep",
        "name_en": "Less Sleep",
        "name_pt": "Menos Sono",
        "type": "physical",
        "origin": "mundane",
        "cost": {"type": "per_level", "value": 2, "level_label": "máx 4 níveis"},
        "description_pt": "Humano default precisa 8h sono. Cada nível reduz em 1h (até 4h em level 4).",
        "page_ref": 65,
        "detail_level": "full"
    },
    {
        "id": "lifting_st",
        "name_en": "Lifting ST",
        "name_pt": "ST de Levantamento",
        "type": "physical",
        "origin": "mundane",
        "cost": {"type": "per_level", "value": 3, "level_label": "por +1 Lifting ST"},
        "description_pt": "ST extra para carregar/levantar/empurrar/puxar. Adiciona ao ST normal para Basic Lift e força de pressão lenta (grapple/choke). NÃO afeta HP, throwing distance, dano em melee ou thrown. Se ST normal tem Size limitation, aplica em Lifting ST também (mas No Fine Manipulators não dá desconto).",
        "page_ref": 65,
        "detail_level": "full"
    },
    {
        "id": "lightning_calculator",
        "name_en": "Lightning Calculator",
        "name_pt": "Calculadora Mental",
        "type": "mental",
        "origin": "mundane",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 2, "name_pt": "Lightning Calculator — aritmética instantânea; jogador pode usar calculadora real a qualquer momento"},
                {"value": 5, "name_pt": "Intuitive Mathematician — astrogation, engenharia, equações diferenciais sem computador"}
            ]
        },
        "description_pt": "Math em segundos. Verdadeiros gênios pegam ambos níveis + Mathematical Ability (Talent).",
        "page_ref": 66,
        "detail_level": "full"
    },
    {
        "id": "longevity",
        "name_en": "Longevity",
        "name_pt": "Longevidade",
        "type": "physical",
        "origin": "mundane",
        "cost": {"type": "fixed", "value": 2},
        "description_pt": "Falha aging rolls (p444) só em 17 ou 18 (ou só 18 se HT modificado ≥17).",
        "page_ref": 66,
        "detail_level": "full"
    },
    {
        "id": "luck",
        "name_en": "Luck",
        "name_pt": "Sorte",
        "type": "mental",
        "origin": "supernatural",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 15, "name_pt": "Luck — re-rola um die roll ruim 2× e pega melhor, 1×/hora de jogo"},
                {"value": 30, "name_pt": "Extraordinary Luck — mesmo mas 1×/30min"},
                {"value": 60, "name_pt": "Ridiculous Luck — mesmo mas 1×/10min"}
            ]
        },
        "description_pt": "Declara IMEDIATAMENTE após roll (outras rolagens depois = tarde demais). Se GM rolando em segredo, avisa antes e GM rola 3× pegando melhor. Aplica em seus success/damage/reaction rolls ou eventos que afetam você/party. Em ataque contra você, força atacante rolar 3× pegando pior. Não compartilha. Wait real time entre usos. Limitations: Active -40%, Aspected -20%, Defensive -20%.",
        "page_ref": 66,
        "detail_level": "full"
    },

    # ===== M (pp 66-70) =====
    {
        "id": "magery",
        "name_en": "Magery",
        "name_pt": "Aptidão Mágica",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "tiered", "tiers": [{"level": 0, "value": 5}, {"level": "1+", "value": "10 pts/nível adicional"}]},
        "description_pt": "Magery 0 (5 pts): consciência mágica básica, pré-req para aprender magia. Sense roll ao ver/tocar item mágico. 1+: Soma Magery ao IQ para aprender spells; +Magery em Per para sense magic items; +Magery em IQ para Thaumatology. Reduz tempo de aprendizado em -10%/nível (mín 60%). Spells poderosos exigem Magery mínima como pré-req. Magery 3 é padrão para 'fantasy clássica'. Limitations: Dance -40%, Dark-Aspected -50%, Day-Aspected -40%, Night-Aspected -40%, Musical -50%, Song -40%, One College Only -40%, Solitary -40%.",
        "page_ref": 66,
        "detail_level": "full"
    },
    {
        "id": "magic_resistance",
        "name_en": "Magic Resistance",
        "name_pt": "Resistência Mágica",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "per_level", "value": 2},
        "description_pt": "Subtrai nível do skill do conjurador, soma ao seu roll de resistência. Aplica em magic elixirs (HT + Magic Resistance). NÃO pode 'desligar' — bloqueia até magia amiga. Só afeta spells lançados diretamente em você (não Missile spells, magic weapons, info spells). Não afeta outros poderes sobrenaturais (milagres, psi, espíritos). Incompatível com Magery (qualquer nível impede cast). Enhancement Improved +150% (permite Magery + Magic Resistance).",
        "page_ref": 67,
        "detail_level": "full"
    },
    {
        "id": "mana_damper",
        "name_en": "Mana Damper",
        "name_pt": "Amortecedor de Mana",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "per_level", "value": 10, "level_label": "máx 3 níveis"},
        "description_pt": "Cada nível reduz mana local em 1 step (apenas para você e itens carregados). Wizards têm dificuldade de afetar você diretamente. Nunca pode cast spells nem ter Magery. Enhancements: Area Effect +50%/nível, Switchable +100%.",
        "page_ref": 67,
        "detail_level": "full"
    },
    {
        "id": "mana_enhancer",
        "name_en": "Mana Enhancer",
        "name_pt": "Amplificador de Mana",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "per_level", "value": 50, "level_label": "máx 2 níveis"},
        "description_pt": "Cada nível aumenta mana local em 1 step (só você e carregados). Não dá power de cast (precisa Magery), mas em mana 'high+' pode cast vários spells sem Magery. Incompatível com Magic Resistance. Mages detectam via IQ+Magery roll. Enhancements: Area Effect +50%/nível, Switchable +100%.",
        "page_ref": 68,
        "detail_level": "full"
    },
    {
        "id": "medium",
        "name_en": "Medium",
        "name_pt": "Médium",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "fixed", "value": 10},
        "description_pt": "Percebe e fala com espíritos (especialmente mortos). Não vê visualmente mas sabe quando próximo. Pode falar (mesma língua). Pode invocar (sem garantia de resposta). NÃO dá reaction bonus nem controle.",
        "page_ref": 68,
        "detail_level": "full"
    },
    {
        "id": "metabolism_control",
        "name_en": "Metabolism Control",
        "name_pt": "Controle Metabólico",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "per_level", "value": 5},
        "description_pt": "Controla funções involuntárias (pulso, fluxo sanguíneo, digestão, respiração). +1/nível em HT rolls beneficiados, incluindo bleeding e recovery de disease/poison. Pode entrar em transe de morte aparente — Diagnosis vs HT+Metabolism Control para detectar. Cada nível reduz O₂ necessário em 10% (lvl 10 = não respira) e dobra tempo sem comida/água. Incompatível com Machine meta-trait. Limitation Hibernation -60% (só transe + entra hibernação involuntária em condições extremas).",
        "page_ref": 68,
        "detail_level": "full"
    },
    {
        "id": "microscopic_vision",
        "name_en": "Microscopic Vision",
        "name_pt": "Visão Microscópica",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "per_level", "value": 5},
        "description_pt": "Cada nível ×10 ampliação: lvl 1 = 10× (perícia forense), lvl 3 = 1000× (microscópio óptico), lvl 5 = 100k× (eletrônico, vê vírus), lvl 6 = 1M× (estrutura atômica). Só para objetos a ≤1 pé.",
        "page_ref": 68,
        "detail_level": "full"
    },
    {
        "id": "mimicry",
        "name_en": "Mimicry",
        "name_pt": "Mímica Sonora",
        "type": "mental",
        "origin": "mundane",
        "cost": {"type": "fixed", "value": 10},
        "description_pt": "Duplica som simples (alarme, tiro) após 1 seg + IQ roll. Imita vozes após ≥10 seg + IQ roll. NÃO dá poder de stun/deafen nem cast verbal de magia.",
        "page_ref": 68,
        "detail_level": "full"
    },
    {
        "id": "mind_control",
        "name_en": "Mind Control",
        "name_pt": "Controle Mental",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "fixed", "value": 50},
        "description_pt": "Domina mentalmente alvo visto/tocado. 1 seg concentração + Quick Contest: seu IQ vs Will alvo. Modifiers: range penalties; -1/escravo já controlado; +2 (1 min concentração) ou +4 (1 hora). Vitória → vítima vira Reprogrammable até liberar. Controle dura enquanto Concentra; depois ainda 1 min/ponto de margem. Forçar contra princípios = novo Quick Contest. Falha crítica = perde todos sob controle. Enhancements: Conditioning +50%, No Memory +10%. Limitations: Conditioning Only -50%, Puppet -40%, Telepathic -10%.",
        "page_ref": 68,
        "detail_level": "full"
    },
    {
        "id": "mind_probe",
        "name_en": "Mind Probe",
        "name_pt": "Sondagem Mental",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "fixed", "value": 20},
        "description_pt": "Força alvo responder uma pergunta específica (resposta em sentença breve). Pré-requisito: tocar OU ter Mind Reading bem-sucedido. Precisam compartilhar língua. 1 seg + Quick Contest: IQ (ou Interrogation maior) vs Will. Vitória = arranca resposta crida pelo alvo. Penalty cumulativo -2 por repetição na mesma pergunta/hora. Falha crítica = 24h sem probe. Modifiers iguais aos de Mind Reading.",
        "page_ref": 69,
        "detail_level": "full"
    },
    {
        "id": "mind_reading",
        "name_en": "Mind Reading",
        "name_pt": "Leitura Mental",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "fixed", "value": 30},
        "description_pt": "Escuta pensamentos de superfície. Vê ou toca alvo. 1 seg + Quick Contest: IQ vs Will (com range penalties). Vitória = ouve fala/subvocalização/pensamento ativo em velocidade de fala. Sem língua comum ou não-sapiente = só sentimentos/imagens/intent. Mantém indefinidamente sem reconcentrar. Trocar alvo = parar + Quick Contest com novo. Múltiplos simultâneos = Compartmentalized Mind. Falha crítica = 24h sem leitura nesse alvo. Comum: Sense-Based limitation (Touch, Hearing). Enhancements: Cybernetic +50%, Sensory +20%, Universal +50%. Limitations: Cybernetic Only -50%, Racial -20%, Sensory Only -20%, Telecommunication -20%, Telepathic -10%.",
        "page_ref": 69,
        "detail_level": "full"
    },
    {
        "id": "mind_shield",
        "name_en": "Mind Shield",
        "name_pt": "Escudo Mental",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "per_level", "value": 4},
        "description_pt": "Avisa e defende contra ataques mentais. Soma nível ao IQ/Will contra Telepathic-limited advantages e Communication/Empathy/Mind Control spells. Bloqueia localização mental (Quick Contest Will+Mind Shield). Pode baixar voluntariamente (free action no início do turno). Protege durante sono/inconsciência (a menos que tenha sido baixado conscientemente antes). Limitations: Cybernetic -50% (vs computer attacks, requer Digital Mind), Telepathic -10%.",
        "page_ref": 70,
        "detail_level": "full"
    },
    {
        "id": "mindlink",
        "name_en": "Mindlink",
        "name_pt": "Vínculo Mental",
        "type": "mental",
        "origin": "supernatural",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 5,  "name_pt": "1 pessoa"},
                {"value": 10, "name_pt": "2-9 pessoas"},
                {"value": 20, "name_pt": "10-99 pessoas"},
                {"value": 30, "name_pt": "100-999 pessoas"}
            ]
        },
        "description_pt": "Rapport telepático permanente com alguém (gêmeo, amor, hive member). Sucesso automático em Telesend e Mind Reading (se alvo não resiste ou tem Slave Mentality). Não funciona a mais de 0.1 ano-luz nem entre dimensões. +10 pts por aumento decuplo no número (1k = 40, 10k = 50…).",
        "page_ref": 70,
        "detail_level": "full"
    },
]


def main():
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    existing_ids = {e["id"] for e in data["entries"]}
    added = 0
    skipped = []
    for entry in NEW_ENTRIES:
        if entry["id"] in existing_ids:
            skipped.append(entry["id"])
            continue
        data["entries"].append(entry)
        existing_ids.add(entry["id"])
        added += 1

    data["$progress"] = {
        "status": "partial",
        "batch": "A-M (até Mindlink p70)",
        "entries_in_file": len(data["entries"]),
        "total_estimated_in_book": 155,
        "next_letters": "N-R",
        "notes_pt": "Catálogo incremental. Cobre A até M. Detail_level=full com modificadores principais resumidos. Para detalhes completos de cada modifier, ver livro pp 102-116 (gerais) ou páginas específicas.",
    }
    TARGET.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"adicionadas: {added}, puladas: {skipped}")
    print(f"total no arquivo: {len(data['entries'])} / ~155")


if __name__ == "__main__":
    main()
