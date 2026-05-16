"""Append batch de vantagens N-S no advantages.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "gurps" / "data" / "advantages.json"

NEW_ENTRIES = [
    # ===== N (pp 71) =====
    {"id":"modular_abilities","name_en":"Modular Abilities","name_pt":"Habilidades Modulares","type":"mental","origin":"exotic",
     "cost":{"type":"variable","formula":"base_per_slot + N×pts_per_pt; varia por tipo"},
     "description_pt":"Pool de pontos realocáveis em skills/spells/vantagens mentais sob condições. Slots: Computer Brain (6+4 pts/pt), Chip Slots (5+3), Super-Memorization (5+3), Cosmic Power (10/pt, slot único, qualquer config). Enhancements: Physical +50%/+100%. Limitations: Spells Only -20%, Virtual -50%.","page_ref":71,"detail_level":"full"},
    {"id":"neutralize","name_en":"Neutralize","name_pt":"Neutralizar","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":50},
     "description_pt":"Cancela poderes psi de UM alvo. Atacante (touch + Attack maneuver) + Quick Contest Will. Vitória → todos psionic powers do alvo neutralizados por (margem) minutos. NÃO afeta Talents. 1 uso por alvo até recuperar. Falha crítica = 1d horas crippled. Enhancement: Power Theft +200% (rouba poderes). Limitation: One Power -50%.","page_ref":71,"detail_level":"full"},
    {"id":"nictitating_membrane","name_en":"Nictitating Membrane","name_pt":"Membrana Nictante","type":"physical","origin":"exotic",
     "cost":{"type":"per_level","value":1},
     "description_pt":"Pálpebra transparente. Vê normalmente subaquático; protege olhos de areia/irritantes. Cada nível: DR 1 nos olhos + +1 em HT rolls relacionados a dano nos olhos.","page_ref":71,"detail_level":"full"},
    {"id":"night_vision","name_en":"Night Vision","name_pt":"Visão Noturna","type":"physical","origin":"exotic",
     "cost":{"type":"per_level","value":1,"level_label":"máx 9 níveis"},
     "description_pt":"Cada nível ignora -1 de penalty por escuridão (combate e visão) — DESDE que haja alguma luz. Não funciona em escuridão total (-10 fixo; precisa Dark Vision).","page_ref":71,"detail_level":"full"},

    # ===== O (pp 72) =====
    {"id":"obscure","name_en":"Obscure","name_pt":"Obscurecer","type":"physical","origin":"exotic",
     "cost":{"type":"per_level","value":2},
     "description_pt":"Bloqueia UM sentido em raio 2 jds em torno de você. Especifica sentido (Vision, Hearing, Radar, Detect específico). -1/nível para detectar no raio; 10 níveis = bloqueio total. Bordas detectáveis em +1/nível. Enhancements: Defensive +50%, Extended +20%/sentido, Ranged +50%, Stealthy +100% (silencioso). Limitation: Always On -50%.","page_ref":72,"detail_level":"full"},
    {"id":"oracle","name_en":"Oracle","name_pt":"Oráculo","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":15},
     "description_pt":"Sensível a presságios. 1×/dia checa omens (≥1 hora). GM rola 2× em segredo: Discovery (Sense roll) + Interpretation (IQ roll). Crítico em Discovery = +5 em Interpretation. Crítico em Interpretation = info específica. Falha crítica = GM mente. Diferente de Precognition (que não exige interpretação).","page_ref":72,"detail_level":"full"},

    # ===== P (pp 72-78) =====
    {"id":"parabolic_hearing","name_en":"Parabolic Hearing","name_pt":"Audição Parabólica","type":"physical","origin":"exotic",
     "cost":{"type":"per_level","value":4},
     "description_pt":"'Zoom' auditivo em som/área específica, filtra ruído de fundo. Cada nível dobra distância de audição clara (ver Hearing p358).","page_ref":72,"detail_level":"full"},
    {"id":"patrons","name_en":"Patrons","name_pt":"Patronos","type":"social","origin":"mundane",
     "cost":{"type":"options","choices":[
         {"value":10,"name_pt":"Indivíduo 150% PCs OU organização 1k× wealth (ex: dep. polícia pequeno)"},
         {"value":15,"name_pt":"Indivíduo 2× PCs OU org 10k× wealth (ex: deus menor, bilionário)"},
         {"value":20,"name_pt":"Ultra-poderoso indivíduo OU org 100k× wealth (super, deus maior, cidade grande)"},
         {"value":25,"name_pt":"Org extremamente poderosa (1M× wealth: corporação grande, nação pequena)"},
         {"value":30,"name_pt":"Governo nacional/multinacional OU verdadeiro deus pessoal"}
     ]},
     "description_pt":"NPC ou organização que serve de mentor/empregador/protetor. Custo × frequency multiplier. Deus exige Special Abilities enhancement. PC pode contatar 1×/aventura. Em party-shared, todos pagam full. Enhancements: Equipment +50%/+100%, Highly Accessible +50%, Special Abilities +50%/+100%. Limitations: Minimal Intervention -50%, Secret -50%, Unwilling -50%.","page_ref":72,"detail_level":"full"},
    {"id":"payload","name_en":"Payload","name_pt":"Capacidade de Carga","type":"physical","origin":"mundane",
     "cost":{"type":"per_level","value":1},
     "description_pt":"Carrega cargo/ocupantes DENTRO do corpo. Cada nível = Basic Lift/10 lbs. internos. Cargo: 20 lbs ~ 1 ft³. Occupants: humano ~200 lbs (×10 se cabin). >5 níveis sem Injury Tolerance(Homogenous)/Machine = GM approves. Limitation Exposed -50% (motos).","page_ref":74,"detail_level":"full"},
    {"id":"penetrating_vision","name_en":"Penetrating Vision","name_pt":"Visão Penetrante","type":"physical","origin":"exotic",
     "cost":{"type":"per_level","value":10},
     "description_pt":"'X-ray vision'. Cada nível enxerga até 6\" de matéria normal. Funciona com outras vision advantages. Limitations: Blockable -10 a -30%, Specific -40 a -80%.","page_ref":74,"detail_level":"full"},
    {"id":"perfect_balance","name_en":"Perfect Balance","name_pt":"Equilíbrio Perfeito","type":"physical","origin":"mundane",
     "cost":{"type":"fixed","value":15},
     "description_pt":"Equilíbrio em qualquer superfície estreita (corda, beira, galho) sem die roll. +6 em rolls de equilíbrio em superfícies escorregadias. Em combate: +4 em DX/skills para se manter em pé / evitar knockdown. +1 em Acrobatics, Climbing, Piloting.","page_ref":74,"detail_level":"full"},
    {"id":"peripheral_vision","name_en":"Peripheral Vision","name_pt":"Visão Periférica","type":"physical","origin":"exotic",
     "cost":{"type":"fixed","value":15},
     "description_pt":"Arco visual 240° (180° frontal + 30° cada lado). Em battle map: ataques melee nos hexes laterais (-Wild Swing se mão oposta). Defesas em side hex sem penalty; defesa contra ataques pelas costas só -2. +3 contra Shadowing/ambush. GM rola Vision pra perigos atrás. Limitation Easy to Hit -20% (olhos em hastes/vulneráveis).","page_ref":74,"detail_level":"full"},
    {"id":"permeation","name_en":"Permeation","name_pt":"Permeação","type":"physical","origin":"exotic",
     "cost":{"type":"options","choices":[
         {"value":40,"name_pt":"Very Common (terra, metal, pedra, madeira)"},
         {"value":20,"name_pt":"Common (concreto, plástico, aço)"},
         {"value":10,"name_pt":"Occasional (vidro, gelo, areia, alumínio)"},
         {"value":5,"name_pt":"Rare (osso, carne, papel)"}
     ]},
     "description_pt":"Atravessa material sólido específico. Não abre passagem — 'derrete' nele. Precisa Penetrating Vision pra navegar. Ainda precisa respirar (limita a holding breath). Gravidade afeta. Vulnerável a ataques no interior. Enhancements: Can Carry Objects +10/+100%, Tunnel +40%.","page_ref":75,"detail_level":"full"},
    {"id":"plant_empathy","name_en":"Plant Empathy","name_pt":"Empatia com Plantas","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":5},
     "description_pt":"Rapport com plantas. GM rola IQ ao encontrar planta — sucesso = sente saúde + natureza (natural/sobrenatural). Funciona como Empathy com plantas sapientes. Permite Influence skills em plantas sapientes. Acompanha Green Thumb (Talent), Sense of Duty (Plants), ou Vow.","page_ref":75,"detail_level":"full"},
    {"id":"possession","name_en":"Possession","name_pt":"Possessão","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":100},
     "description_pt":"Move consciência entre corpos. Toca + 1 seg concentração + Quick Contest IQ vs Will (alvo wary = +5). Vitória = toma corpo, suprime personalidade do alvo (acorda em 1d seg sem memória). Ganha ST/DX/HT/secundários e vantagens físicas do host; mantém IQ/Per/Will/mentais. Skills mantêm relative level. Memória limitada (IQ -1/h desde takeover). Enhancements: Telecontrol +50%, Assimilation +10%, Chronic +20%, Mind Swap +10%. Limitations: Digital -40%, Magical -10%, Mindlink Required -40%, No Memory Access -10%, Parasitic -60%, Puppet Only -30%, Spiritual -20%, Telepathic -10% (mutuamente exclusivas).","page_ref":75,"detail_level":"full"},
    {"id":"power_investiture","name_en":"Power Investiture","name_pt":"Investidura de Poder","type":"mental","origin":"supernatural",
     "cost":{"type":"per_level","value":10},
     "description_pt":"Divindade empoderou para cast spells clericais. +Nível em IQ para aprender spells daquela divindade. Lista fixa de spells; sem pré-requisitos (canaliza vontade divina, não estuda magia). Limitação intrínseca: Pact (não aplique de novo). Pode ter Magery + Power Investiture mas não se sobrepõem. Setting: priestos como divinely-inspired wizards.","page_ref":77,"detail_level":"full"},
    {"id":"precognition","name_en":"Precognition","name_pt":"Precognição","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":25},
     "description_pt":"Visões de futuro (incontroláveis). Só info que seu 'futuro you' aprenderia e importaria. Vision vívida pode exigir Fright Check. Uso deliberado: 10 min + 2 FP + IQ-8. Tipicamente até ~1 semana futuro. Inclui Danger Sense (não pegue ambos). Limitations: Can't See Own Death -60%, ESP -10%, One Event -40%.","page_ref":77,"detail_level":"full"},
    {"id":"pressure_support","name_en":"Pressure Support","name_pt":"Suporte a Pressão","type":"physical","origin":"exotic",
     "cost":{"type":"options","choices":[
         {"value":5,"name_pt":"PS 1 — até 10× pressão nativa (humano: shelf continental)"},
         {"value":10,"name_pt":"PS 2 — até 100× (humano: oceanos exceto trincheiras)"},
         {"value":15,"name_pt":"PS 3 — imune a alta pressão"}
     ]},
     "description_pt":"Pressão interna constante vs externa. NÃO protege contra crushing/explosions (localizadas/transientes). Frequentemente acompanha Sealed mas não requer.","page_ref":77,"detail_level":"full"},
    {"id":"protected_sense","name_en":"Protected Sense","name_pt":"Sentido Protegido","type":"physical","origin":"exotic",
     "cost":{"type":"per_level","value":5,"level_label":"por sentido"},
     "description_pt":"Sentido ranged adapta a sobrecarga em ≤2 seg. Sem dano permanente por overload. +5 contra dano temporário e Sense-Based attacks daquele sentido. Tipos: Protected Vision, Hearing, Taste/Smell — GM pode permitir outros.","page_ref":78,"detail_level":"full"},
    {"id":"psi_static","name_en":"Psi Static","name_pt":"Estática Psiônica","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":30},
     "description_pt":"'Null' psi. Habilidades psi não afetam você nem que carrega. Telekinético arremessa rocha sim, mas não te levita. Enhancements: Area Effect +50%/nível, Switchable +100%. Limitation: Resistible -50% (Quick Contest de Will).","page_ref":78,"detail_level":"full"},
    {"id":"psychometry","name_en":"Psychometry","name_pt":"Psicometria","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":20},
     "description_pt":"Sente história de objeto/local. Toca + 1 seg + IQ roll (penalty por idade: same day 0, 10d -1, 100d -2, 3y -3, 30y -4, 300y -5…). Sucesso = sensações de eventos carregados. Crítico = visão real. Falha crítica = 24h sem leitura. Limitation ESP -10%.","page_ref":78,"detail_level":"full"},
    {"id":"puppet","name_en":"Puppet","name_pt":"Marionete","type":"mental","origin":"supernatural",
     "cost":{"type":"options","choices":[
         {"value":5,"name_pt":"Um Puppet"},
         {"value":10,"name_pt":"Grupo inteiro de Allies como Puppets"}
     ]},
     "description_pt":"Pré-req: Possession + Ally ou Dependent. Puppet não resiste sua Possession (auto-success). Puppet sempre IQ 0, ou Involuntary Duty, ou Reprogrammable. Custo só do Puppet — Ally/Dependent separado. Comum: Minion enhancement ou Unwilling limitation.","page_ref":78,"detail_level":"full"},

    # ===== R (pp 78-81) =====
    {"id":"racial_memory","name_en":"Racial Memory","name_pt":"Memória Racial","type":"mental","origin":"supernatural",
     "cost":{"type":"options","choices":[
         {"value":15,"name_pt":"Passive — déjà vu via IQ secret em situações ancestrais"},
         {"value":40,"name_pt":"Active — consulta deliberada (1 turno concentração, GM define se ancestrais sabiam, IQ roll)"}
     ]},
     "description_pt":"Acessa memórias de ancestrais genéticos (ou gerações anteriores de software para Digital Minds).","page_ref":78,"detail_level":"full"},
    {"id":"radiation_tolerance","name_en":"Radiation Tolerance","name_pt":"Tolerância à Radiação","type":"physical","origin":"exotic",
     "cost":{"type":"options","choices":[
         {"value":5,"name_pt":"Divisor 2"},{"value":10,"name_pt":"Divisor 5"},{"value":15,"name_pt":"Divisor 10"},
         {"value":20,"name_pt":"Divisor 20"},{"value":25,"name_pt":"Divisor 50"},{"value":30,"name_pt":"Divisor 100"},
         {"value":35,"name_pt":"Divisor 200"},{"value":40,"name_pt":"Divisor 500"},{"value":45,"name_pt":"Divisor 1000"}
     ]},
     "description_pt":"Divide dose efetiva de radiação (após PF de armadura) pelo divisor.","page_ref":79,"detail_level":"full"},
    {"id":"rapid_healing","name_en":"Rapid Healing","name_pt":"Cura Rápida","type":"physical","origin":"mundane",
     "cost":{"type":"options","choices":[
         {"value":5,"name_pt":"Rapid Healing — +5 em HT effective ao recuperar HP (pré-req HT 10+)"},
         {"value":15,"name_pt":"Very Rapid Healing — mesma + sucesso = 2 HP em vez de 1 (pré-req HT 12+)"}
     ]},
     "description_pt":"Não acelera recuperação de stunning/knockout (use Recovery).","page_ref":79,"detail_level":"full"},
    {"id":"rapier_wit","name_en":"Rapier Wit","name_pt":"Sagacidade Mordaz","type":"mental","origin":"mundane",
     "cost":{"type":"fixed","value":5},
     "description_pt":"Stuna oponentes com repartee. Free action. Quick Contest: Public Speaking vs Will. Modifiers: -2 se Clueless/No Sense of Humor; -1/oponente após 1º se atacando grupo; Unfazeable = imune. Vitória = mental stun. Crítico = +1 HP dano por acidente. Falha crítica = enraivece oponente.","page_ref":79,"detail_level":"full"},
    {"id":"reawakened","name_en":"Reawakened","name_pt":"Redespertado","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":10},
     "description_pt":"'Lembra' skills/spells/techniques de vidas passadas. Compra normalmente; advantage só justifica como aprendeu sem professor. Só em settings com reincarnação.","page_ref":80,"detail_level":"full"},
    {"id":"recovery","name_en":"Recovery","name_pt":"Recuperação","type":"physical","origin":"exotic",
     "cost":{"type":"fixed","value":10},
     "description_pt":"Recupera de unconsciousness 60× mais rápido. Horas → minutos, minutos → segundos. Coma de mês = 12h.","page_ref":80,"detail_level":"full"},
    {"id":"reduced_consumption","name_en":"Reduced Consumption","name_pt":"Consumo Reduzido","type":"physical","origin":"mundane",
     "cost":{"type":"per_level","value":2,"level_label":"4 níveis"},
     "description_pt":"Lvl 1: 2/3 normal (2 refeições/dia). Lvl 2: 1/3 (1/dia). Lvl 3: 1×/semana (~5%). Lvl 4: 1×/mês (~1%). Limitations: Cast-Iron Stomach -50%, Food Only -50%, Water Only -50%.","page_ref":80,"detail_level":"full"},
    {"id":"regeneration","name_en":"Regeneration","name_pt":"Regeneração","type":"physical","origin":"exotic",
     "cost":{"type":"options","choices":[
         {"value":10,"name_pt":"Slow — 1 HP/12h"},
         {"value":25,"name_pt":"Regular — 1 HP/h"},
         {"value":50,"name_pt":"Fast — 1 HP/min"},
         {"value":100,"name_pt":"Very Fast — 1 HP/seg"},
         {"value":150,"name_pt":"Extreme — 10 HP/seg"}
     ]},
     "description_pt":"Inclui Rapid Healing sem custo. Não compatível com Slow Healing/Unhealing. Enhancement: Heals Radiation +40% (10×/HP). Limitation: Radiation Only -60% (só rads, não HP).","page_ref":80,"detail_level":"full"},
    {"id":"regrowth","name_en":"Regrowth","name_pt":"Reconstituição","type":"physical","origin":"exotic",
     "cost":{"type":"fixed","value":40},
     "description_pt":"Regrowth de membros: orelha/dedo em 1d semanas; mão/pé em 1d+1 meses; olho/braço/perna em 2d+2 meses. Com Regeneration: tempo = tempo para curar full HP. Limitation Minor -50% (só pequenos: orelhas, dedos).","page_ref":80,"detail_level":"full"},
    {"id":"resistant","name_en":"Resistant","name_pt":"Resistente","type":"physical","origin":"mundane",
     "cost":{"type":"variable","formula":"base × resist_mult; base por raridade, mult por nível"},
     "description_pt":"+bonus em HT para resistir noxious itens (disease, poison, env. syndromes). Base: Very Common (Metabolic Hazards) 30, Common (Poison/Sickness) 15, Occasional (Disease/Ingested Poison) 10, Rare (Acceleration/Altitude/Bends/Sea/Space Sickness) 5. Multiplicador: Immunity ×1, +8 ×½, +3 ×⅓. Mental Resistance: substitui HT por IQ/Will (Psionics é Very Common).","page_ref":80,"detail_level":"full"},

    # ===== S (pp 81-84) =====
    {"id":"scanning_sense","name_en":"Scanning Sense","name_pt":"Sentido de Varredura","type":"physical","origin":"exotic",
     "cost":{"type":"options","choices":[
         {"value":20,"name_pt":"Radar (2000 jds, só grandes, não water)"},
         {"value":20,"name_pt":"Imaging Radar (200 jds, vê pequenos/forma)"},
         {"value":20,"name_pt":"Ladar (200 jds, alta resolução, sem fumaça/sólido)"},
         {"value":40,"name_pt":"Para-Radar (200 jds, qualquer ambiente, indetectável)"},
         {"value":20,"name_pt":"Sonar (2000 jds underwater, 20 jds × atm em ar)"}
     ]},
     "description_pt":"Emite + recebe energia, monta 'picture' (tamanho/forma, sem cor). Sem light needed. Ativo: outros sensores te detectam até 2× range. Pode desligar. Arco 120°. Enhancements: Extended Arc +75/+125%, LPI +10%, Multi-Mode +50%, Penetrating +50%, Targeting +20%. Limitation: Targeting Only -40%.","page_ref":81,"detail_level":"full"},
    {"id":"sealed","name_en":"Sealed","name_pt":"Selado","type":"physical","origin":"exotic",
     "cost":{"type":"fixed","value":15},
     "description_pt":"Impermeável a gás/líquido. Waterproof + imune a agentes corrosivos/tóxicos por contato. Aparato respiratório externo protegido. NÃO pressuriza (precisa Pressure Support) nem dispensa respiração (precisa Doesn't Breathe).","page_ref":82,"detail_level":"full"},
    {"id":"security_clearance","name_en":"Security Clearance","name_pt":"Credencial de Segurança","type":"social","origin":"mundane",
     "cost":{"type":"options","choices":[
         {"value":5,"name_pt":"Acesso 'need to know' a faixa estreita (piloto de bombardeiro)"},
         {"value":10,"name_pt":"Acesso livre a faixa estreita OU 'need to know' a faixa ampla"},
         {"value":75,"name_pt":"Acesso livre a faixa ampla (agente secreto cinematic)"}
     ]},
     "description_pt":"Halve costs para org de importância menor. Exige background check; GM pode proibir para chars com passado suspeito (Debt, Secret, Paranoia, Sadism).","page_ref":82,"detail_level":"full"},
    {"id":"see_invisible","name_en":"See Invisible","name_pt":"Ver o Invisível","type":"physical","origin":"exotic",
     "cost":{"type":"fixed","value":15,"note":"comprar separado por tipo de invisibilidade"},
     "description_pt":"Vê objetos/indivíduos normalmente invisíveis. Um tipo de invisibilidade por compra.","page_ref":83,"detail_level":"full"},
    {"id":"sensitive_touch","name_en":"Sensitive Touch","name_pt":"Toque Sensível","type":"physical","origin":"exotic",
     "cost":{"type":"fixed","value":10},
     "description_pt":"Pontas dos dedos hipersensíveis: calor residual em cadeira, vibração no chão. +4 em qualquer tarefa que usa tato (além de Acute Touch). Ex: Forensics comparando tecidos, Search procurando objetos pequenos.","page_ref":83,"detail_level":"full"},
    {"id":"serendipity","name_en":"Serendipity","name_pt":"Serendipidade","type":"mental","origin":"supernatural",
     "cost":{"type":"per_level","value":15},
     "description_pt":"1 coincidência plausível favorável por sessão por nível. GM decide os detalhes. Você pode sugerir, mas GM tem palavra final. Coincidência implausível pode 'gastar' várias.","page_ref":83,"detail_level":"full"},
    {"id":"shadow_form","name_en":"Shadow Form","name_pt":"Forma de Sombra","type":"physical","origin":"supernatural",
     "cost":{"type":"fixed","value":50},
     "description_pt":"Vira sombra 2D. Desliza por paredes/chão, atravessa frestas. Sobe paredes/tetos a ½ Move. Físico → ½ dano; energia → normal; LUZ → 1.5× dano. Magia/psi normal. Não atravessa 3D space (só slide). Sem ataques/ações físicas. Sem switch = -20 disadvantage. Enhancement: Can Carry Objects +10/+100%.","page_ref":83,"detail_level":"full"},
    {"id":"alternate_form","name_en":"Alternate Form","name_pt":"Forma Alternativa","type":"physical","origin":"exotic",
     "cost":{"type":"variable","formula":"15 + 0.9 × (cost(form) - cost(native_form))"},
     "description_pt":"Substitui Shapeshifting parcial. Switch on/off entre formas. Forma desenhada como racial template. 10 seg pra mudar. Fatigue/injury carregam entre formas (escalam). 1 forma: 15 pts (se ≤ nativa) ou 15 + 90% da diferença. Formas adicionais: 15 pts cada, ou full se for a mais cara. Especifique influência externa que força reversão (Dispel Magic, exorcism, etc.).","page_ref":83,"detail_level":"full"},
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
        "batch": "A-S (até Alternate Form p83)",
        "entries_in_file": len(data["entries"]),
        "total_estimated_in_book": 155,
        "next_letters": "S-final (Signature Gear→Striker) + T-Z + outliers (Talents p89, Perks p100)",
        "notes_pt": "Cobre A-S parcial. Faltam: Signature Gear, Silence, Single-Minded, Slippery, Speak With Animals/Fish/Plants, Special Rapport, Speed-Reading, Spirit Empathy, Status, Striking ST, Striker, Subsonic; T-Z; Talents p89-91; Perks p100. Detail_level=full com modificadores principais resumidos.",
    }
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"adicionadas: {added}, puladas: {skipped}")
    print(f"total no arquivo: {len(data['entries'])} / ~155")


if __name__ == "__main__":
    main()
