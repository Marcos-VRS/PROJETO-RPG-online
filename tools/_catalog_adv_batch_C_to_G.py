"""Append batch de vantagens C-final até G no advantages.json.
Rodado uma vez; reentrante por checagem de id duplicado.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "gurps" / "data" / "advantages.json"

NEW_ENTRIES = [
    # ===== C (continuação, pp 42-46) =====
    {
        "id": "clairsentience",
        "name_en": "Clairsentience",
        "name_pt": "Clarissentiência",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "fixed", "value": 50},
        "description_pt": "Desloca sentidos à distância (visão/audição/olfato) para um ponto até 10 jds (ampliável). 1 min de concentração + IQ roll (-5 se viewpoint fora de visão). Não vê através de sólidos mas funciona em escuridão. Variantes via limitações: Clairaudience (só ouvido, -30%), Clairvoyance (só visão, -10%), Clairosmia (só olfato, -60%), ESP -10%, Visible -10%.",
        "page_ref": 42,
        "detail_level": "full"
    },
    {
        "id": "claws",
        "name_en": "Claws",
        "name_pt": "Garras",
        "type": "physical",
        "origin": "exotic",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 3,  "name_pt": "Blunt Claws — garras curtas tipo cão; +1/dado em soco/chute"},
                {"value": 3,  "name_pt": "Hooves — cascos; +1/dado em chute, +1 DR só nos pés"},
                {"value": 5,  "name_pt": "Sharp Claws — garras curtas tipo gato; muda dano de esmagamento para cortante"},
                {"value": 8,  "name_pt": "Talons — garras longas; muda dano para cortante ou perfurante (escolha antes do roll)"},
                {"value": 11, "name_pt": "Long Talons — garras enormes; como Talons mas +1/dado"}
            ]
        },
        "description_pt": "Modifica todas as mãos e pés (sem desconto para garras só em alguns membros). Escolha uma variante; combina-se com Striking ST etc.",
        "page_ref": 42,
        "detail_level": "full"
    },
    {
        "id": "clerical_investment",
        "name_en": "Clerical Investment",
        "name_pt": "Investidura Clerical",
        "type": "social",
        "origin": "mundane",
        "cost": {"type": "fixed", "value": 5},
        "description_pt": "Sacerdote ordenado de religião reconhecida. Pode realizar casamentos, funerais e cerimônias; +1 em reaction rolls de co-religionários; uso de título (Padre, Irmã, Rabino). Inclui Religious Rank 0. Não confere poder divino — para isso, ver Blessed, Power Investiture ou True Faith.",
        "page_ref": 43,
        "detail_level": "full"
    },
    {
        "id": "clinging",
        "name_en": "Clinging",
        "name_pt": "Aderência",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 20},
        "description_pt": "Anda/escala em paredes e tetos sem Climbing roll. Move ao aderir = ½ Basic Move. Para parar queda: DX roll para tocar superfície + ST roll com -1 por 5 jds já caídos; falha reduz a altura da queda em 5 jds. Limitação Specific: só substância específica (comum -40%, incomum -60%, absurdo -80%).",
        "page_ref": 43,
        "detail_level": "full"
    },
    {
        "id": "combat_reflexes",
        "name_en": "Combat Reflexes",
        "name_pt": "Reflexos de Combate",
        "type": "mental",
        "origin": "mundane",
        "cost": {"type": "fixed", "value": 15},
        "description_pt": "+1 em todas defesas ativas, +1 em Fast-Draw, +2 em Fright Checks. Nunca 'congela' em surpresa, +6 para acordar/recuperar de stun. Lado tem +1 (ou +2 se você é líder) em rolls de initiative contra ataque-surpresa. Já incluído em Enhanced Time Sense — incompatível.",
        "page_ref": 43,
        "detail_level": "full"
    },
    {
        "id": "common_sense",
        "name_en": "Common Sense",
        "name_pt": "Bom Senso",
        "type": "mental",
        "origin": "mundane",
        "cost": {"type": "fixed", "value": 10},
        "description_pt": "Quando o jogador planeja algo que o GM considera idiota, o GM rola contra IQ secretamente. Em sucesso o GM avisa 'Tem certeza?'. Permite a um jogador impulsivo interpretar personagem ponderado.",
        "page_ref": 43,
        "detail_level": "full"
    },
    {
        "id": "compartmentalized_mind",
        "name_en": "Compartmentalized Mind",
        "name_pt": "Mente Compartimentalizada",
        "type": "mental",
        "origin": "exotic",
        "cost": {"type": "per_level", "value": 50},
        "description_pt": "Múltiplas mentes independentes. Cada compartimento adicional dá UM extra mental maneuver por turno (Concentrate em spell etc.), mas nunca mais que UM physical maneuver. Hipnose/magia/psi afetam compartimentos separadamente. Variantes pra veículos: Controls (25 pts/nível) e Dedicated Controls (10 pts/nível).",
        "page_ref": 43,
        "detail_level": "full"
    },
    {
        "id": "constriction_attack",
        "name_en": "Constriction Attack",
        "name_pt": "Ataque de Constrição",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 15},
        "description_pt": "Esmaga oponentes 'abraçando'. Após grapple bem-sucedido (SM da vítima ≤ seu), Quick Contest: seu ST vs ST ou HT (maior) da vítima a cada turno. Margem de vitória = dano. Vítima precisa ter SM ≤ seu.",
        "page_ref": 43,
        "detail_level": "full"
    },
    {
        "id": "contact_group",
        "name_en": "Contact Group",
        "name_pt": "Grupo de Contatos",
        "type": "social",
        "origin": "mundane",
        "cost": {"type": "variable", "formula": "Cost(Contact) × 5"},
        "description_pt": "Rede de contatos numa organização ou estrato social (corporação, sindicato, polícia, militares de uma cidade). Funciona como Contact mas com 'efetiva skill' que cobre uma categoria inteira (ex: 'business skills'). Custo: calcula como Contact e multiplica por 5.",
        "page_ref": 44,
        "detail_level": "full"
    },
    {
        "id": "contacts",
        "name_en": "Contacts",
        "name_pt": "Contatos",
        "type": "social",
        "origin": "mundane",
        "cost": {
            "type": "variable",
            "formula": "base × frequency_mult × reliability_mult",
            "details": {
                "effective_skill_base": {"12": 1, "15": 2, "18": 3, "21": 4, "supernatural": "+1"},
                "reliability_mult": {"completely_reliable": 3, "usually_reliable": 2, "somewhat_reliable": 1, "unreliable": 0.5}
            }
        },
        "description_pt": "Associado que fornece informação ou favores pequenos (rápidos, não-perigosos, baratos — escolha 2). Custo depende de: (1) efetiva skill 12/15/18/21 = base 1/2/3/4; (2) frequency of appearance (multiplicador, ver Frequency, p36); (3) reliability x0.5 a x3. GM rola contra freq quando você chama; em sucesso, rola skill. Bribery sobe reliability.",
        "page_ref": 44,
        "detail_level": "full"
    },
    {
        "id": "cultural_adaptability",
        "name_en": "Cultural Adaptability",
        "name_pt": "Adaptabilidade Cultural",
        "type": "mental",
        "origin": "exotic",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 10, "name_pt": "Todas culturas da sua raça"},
                {"value": 20, "name_pt": "Xeno-Adaptability — todas culturas do mundo, qualquer raça"}
            ]
        },
        "description_pt": "Imune ao -3 'cultural unfamiliarity' (ver Culture, p23). Cinematic.",
        "page_ref": 46,
        "detail_level": "full"
    },
    {
        "id": "cybernetics",
        "name_en": "Cybernetics",
        "name_pt": "Cibernética",
        "type": "physical",
        "origin": "mundane",
        "cost": {"type": "variable", "formula": "varia conforme implante"},
        "description_pt": "Trata implantes ciber como vantagens equivalentes: olho biônico = Infravision, armadura dérmica = DR, etc. Alguns implantes podem ter Temporary Disadvantage (Electrical p134, Maintenance p143) aplicada ao implante específico.",
        "page_ref": 46,
        "detail_level": "full"
    },

    # ===== D (pp 46-50) =====
    {
        "id": "damage_resistance",
        "name_en": "Damage Resistance",
        "name_pt": "Resistência a Dano (DR)",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "per_level", "value": 5},
        "description_pt": "DR natural do corpo — subtraído do dano após armadura mas antes do multiplicador de tipo. Humanos comuns não compram; criaturas com armadura natural compram DR 1-5; robôs/supers/supernaturais sem teto. Default não protege olhos nem contra ataques mentais. Diversos modificadores: Absorption (+80/+100%), Force Field (+20%), Hardened (+20%/nível), Reflection (+100%); limitations: Ablative -80%, Can't Wear Armor -40%, Directional -20 a -40%, Flexible -20%, Limited (var), Partial (por hit location), Semi-Ablative -20%, Tough Skin -40%. Pode ter 'layered defenses'.",
        "page_ref": 46,
        "detail_level": "full"
    },
    {
        "id": "danger_sense",
        "name_en": "Danger Sense",
        "name_pt": "Sentido de Perigo",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "fixed", "value": 15},
        "description_pt": "GM rola contra Per secretamente em situações de emboscada/desastre/risco. Em sucesso, você é avisado a tempo de agir. Roll 3-4 dá mais detalhe sobre a natureza do perigo. Incluído em Precognition (não pode ter ambos). Limitação ESP -10%.",
        "page_ref": 47,
        "detail_level": "full"
    },
    {
        "id": "daredevil",
        "name_en": "Daredevil",
        "name_pt": "Aventureiro Imprudente",
        "type": "mental",
        "origin": "mundane",
        "cost": {"type": "fixed", "value": 15},
        "description_pt": "Quando assume risco desnecessário (GM julga), +1 em todos skill rolls e pode re-rolar qualquer falha crítica nessa situação. Recompensa comportamento ousado.",
        "page_ref": 47,
        "detail_level": "full"
    },
    {
        "id": "dark_vision",
        "name_en": "Dark Vision",
        "name_pt": "Visão Escura",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 25},
        "description_pt": "Vê em escuridão absoluta sem luz, radar ou sônar. Sem penalidade de visão por escuridão (qualquer origem). Não vê cores no escuro por default. Enhancement Color Vision +20% permite cores.",
        "page_ref": 47,
        "detail_level": "full"
    },
    {
        "id": "destiny",
        "name_en": "Destiny",
        "name_pt": "Destino",
        "type": "mental",
        "origin": "supernatural",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 5,  "name_pt": "Minor — uma vitória significativa garantida"},
                {"value": 10, "name_pt": "Major — destinado a feito notável ou morte específica"},
                {"value": 15, "name_pt": "Great — grandeza na vida; nome conhecido"}
            ]
        },
        "description_pt": "Destino preordenado (forma vantajosa). GM determina natureza em segredo conforme valor. Pode ser inconveniente. Versão de desvantagem em p131. Após cumprido, pontos podem virar Reputation positiva.",
        "page_ref": 48,
        "detail_level": "full"
    },
    {
        "id": "detect",
        "name_en": "Detect",
        "name_pt": "Detectar",
        "type": "physical",
        "origin": "exotic",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 5,  "name_pt": "Rare — ex: fire magic, zombies, gold"},
                {"value": 10, "name_pt": "Occasional — ex: spellcasters, magic, undead"},
                {"value": 20, "name_pt": "Common — ex: humans, metal, fields"},
                {"value": 30, "name_pt": "Very Common — ex: all life, all energy"}
            ]
        },
        "description_pt": "Detecta substância/condição mesmo blindada. 1 seg concentração + Sense roll (GM rola). Em sucesso, direção e quantidade aproximada. IQ roll para análise (tipo, pureza). Acute Sense melhora. Modifiers: Precise +100%, Signal Detection +0%, Vague -50%.",
        "page_ref": 48,
        "detail_level": "full"
    },
    {
        "id": "digital_mind",
        "name_en": "Digital Mind",
        "name_pt": "Mente Digital",
        "type": "mental",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 5},
        "description_pt": "Mente é programa sapiente (IA, upload). Imune a 'Telepathic' e magia que afeta mentes vivas. Vulnerável a vírus, hacking. Pode ser desligado ou armazenado. Geralmente vem com Machine meta-trait e Reprogrammable.",
        "page_ref": 48,
        "detail_level": "full"
    },
    {
        "id": "discriminatory_hearing",
        "name_en": "Discriminatory Hearing",
        "name_pt": "Audição Discriminatória",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 15},
        "description_pt": "Identifica pessoas por voz e máquinas por 'sound signature'. Memoriza som: 1 min ouvindo + IQ roll (falha = espera 1 dia). +4 em qualquer tarefa que usa audição (além de Acute Hearing), +4 em Shadowing contra alvo barulhento. Limitation 'Only underwater' -30% simula sonar passivo.",
        "page_ref": 49,
        "detail_level": "full"
    },
    {
        "id": "discriminatory_smell",
        "name_en": "Discriminatory Smell",
        "name_pt": "Olfato Discriminatório",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 15},
        "description_pt": "Olfato sobre-humano. Reconhece pessoas/lugares/coisas por cheiro. Memoriza odor: 1 min cheirando + IQ roll (falha = espera 1 dia). +4 em tarefas de olfato, +4 em Tracking. Enhancement Emotion Sense +50% (Empathy por odor a até 2 jds).",
        "page_ref": 49,
        "detail_level": "full"
    },
    {
        "id": "discriminatory_taste",
        "name_en": "Discriminatory Taste",
        "name_pt": "Paladar Discriminatório",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 10},
        "description_pt": "Como Discriminatory Smell mas com paladar. Precisa ingerir pequena quantidade. IQ roll para reconhecer, skill apropriada (Chemistry, Cooking, Pharmacy, Poisons) para análise detalhada. +4 em tarefas de paladar. Não permite tracking.",
        "page_ref": 49,
        "detail_level": "full"
    },
    {
        "id": "doesnt_breathe",
        "name_en": "Doesn't Breathe",
        "name_pt": "Não Respira",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 20},
        "description_pt": "Não precisa de oxigênio. Imune a estrangulamento, toxinas inaladas. Ainda afetado por venenos de contato, pressão, vácuo (precisa Sealed, Pressure Support, Vacuum Support). Limitations: Gills -50% (só água c/ O₂), Oxygen Absorption -25% (precisa O₂ no meio), Oxygen Combustion -50% (sem O₂ → sufoca), Oxygen Storage de -50% a -10% (limitado por tempo).",
        "page_ref": 49,
        "detail_level": "full"
    },
    {
        "id": "doesnt_eat_or_drink",
        "name_en": "Doesn't Eat or Drink",
        "name_pt": "Não Come ou Bebe",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 10},
        "description_pt": "Não precisa de comida, água ou combustível. Corpo é alimentado por outro meio (solar, magia ambiente). Fonte rara pode justificar Dependency p130.",
        "page_ref": 50,
        "detail_level": "full"
    },
    {
        "id": "doesnt_sleep",
        "name_en": "Doesn't Sleep",
        "name_pt": "Não Dorme",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 20},
        "description_pt": "Não precisa dormir. Ignora qualquer efeito ruim de noites perdidas.",
        "page_ref": 50,
        "detail_level": "full"
    },
    {
        "id": "dominance",
        "name_en": "Dominance",
        "name_pt": "Dominância",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "fixed", "value": 20},
        "description_pt": "Infecta vítimas com condição sobrenatural (vampirismo, lycanthropy) e exerce controle absoluto. Especifica um ataque natural (Claws, Vampiric Bite etc.) que entrega infecção. Vítima rola 3d vs HP de injury; sob = infectado, vira mesma raça em 2d dias com Slave Mentality. Cada vítima precisa de pontos não-gastos para virar Ally.",
        "page_ref": 50,
        "detail_level": "full"
    },
    {
        "id": "duplication",
        "name_en": "Duplication",
        "name_pt": "Duplicação",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "per_level", "value": 35, "level_label": "por cópia"},
        "description_pt": "Divide-se em múltiplos corpos ('Dupes'), cada um com todo conhecimento e poderes. 1 seg + Concentrate para separar/mergir. Ao mergir, FP/HP é média. Se um Dupe morre, todos sofrem 2d + stunados, e perde os pontos. Sem Telesend não há coordenação especial. Enhancements: Duplicated Gear +100%, No Sympathetic Injury +20%. Limitations: Digital -60%, Shared Resources -40%.",
        "page_ref": 50,
        "detail_level": "full"
    },

    # ===== E (pp 51-55) =====
    {
        "id": "eidetic_memory",
        "name_en": "Eidetic Memory",
        "name_pt": "Memória Eidética",
        "type": "mental",
        "origin": "mundane",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 5,  "name_pt": "Eidetic Memory — automático lembra geral; IQ roll para detalhes"},
                {"value": 10, "name_pt": "Photographic Memory — automático lembra todos detalhes"}
            ]
        },
        "description_pt": "Não afeta compreensão, mas dá bônus em IQ rolls para aprendizado: +5 para Eidetic, +10 para Photographic.",
        "page_ref": 51,
        "detail_level": "full"
    },
    {
        "id": "elastic_skin",
        "name_en": "Elastic Skin",
        "name_pt": "Pele Elástica",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 20},
        "description_pt": "Altera pele e feições para duplicar outro da sua raça ou similar. 10 seg para mudar, 3 seg para voltar. Disguise roll para imitar indivíduo específico. +4 em todos Disguise rolls.",
        "page_ref": 51,
        "detail_level": "full"
    },
    {
        "id": "empathy",
        "name_en": "Empathy",
        "name_pt": "Empatia",
        "type": "mental",
        "origin": "supernatural",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 5,  "name_pt": "Sensitive — IQ -3; +1 em Detect Lies, Fortune-Telling, Psychology"},
                {"value": 15, "name_pt": "Empathy — IQ cheio; +3 nos mesmos skills"}
            ]
        },
        "description_pt": "Em primeiro encontro/reencontro, GM rola contra IQ secretamente e diz o que você 'sente' (em falha, mente). Só funciona em seres sapientes (IQ 6+). Para animais/plantas/espíritos use Animal Empathy, Plant Empathy, Spirit Empathy.",
        "page_ref": 51,
        "detail_level": "full"
    },
    {
        "id": "enhanced_defenses",
        "name_en": "Enhanced Defenses",
        "name_pt": "Defesas Aprimoradas",
        "type": "physical",
        "origin": "mundane",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 5,  "name_pt": "Enhanced Block — +1 Block com Cloak ou Shield (especialize)"},
                {"value": 5,  "name_pt": "Enhanced Parry (bare hands) — +1 Parry"},
                {"value": 5,  "name_pt": "Enhanced Parry (Melee Weapon skill) — +1 Parry numa skill específica"},
                {"value": 10, "name_pt": "Enhanced Parry (all parries) — +1 em todos parries"},
                {"value": 15, "name_pt": "Enhanced Dodge — +1 Dodge"}
            ]
        },
        "description_pt": "Cinematic. GM pode exigir Trained By A Master ou Weapon Master como pré-requisito. Múltiplos níveis podem ser permitidos por GM (custo por +1). Bônus >+3 quase sempre quebra o jogo.",
        "page_ref": 51,
        "detail_level": "full"
    },
    {
        "id": "enhanced_move",
        "name_en": "Enhanced Move",
        "name_pt": "Movimento Aprimorado",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "per_level", "value": 20, "half_level_cost": 10},
        "description_pt": "Cada nível dobra top speed num ambiente: Air, Ground, Space ou Water. Meio-nível (10 pts) multiplica por 1.5. Pré-requisitos: (Air) requer Flight; (Space) requer Flight com Space Flight; (Water) requer Amphibious ou Aquatic. Não afeta Basic Speed/Move/Dodge. Modifiers: Handling Bonus +5%/+1 (max +5), Handling Penalty -5%/-1, Newtonian -50% (delta-v), Road-Bound -50%.",
        "page_ref": 52,
        "detail_level": "full"
    },
    {
        "id": "enhanced_time_sense",
        "name_en": "Enhanced Time Sense",
        "name_pt": "Senso Temporal Aprimorado",
        "type": "mental",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 45},
        "description_pt": "Inclui Combat Reflexes (incompatível com este). Age sempre primeiro em combate (antes dos sem ETS); entre ETSs ordena por Basic Speed. Percebe coisas rápidas (frames de filme, burst transmissions, balas em voo a critério GM). Nunca tem penalty por rush mental. GM raramente pode forçar resposta imediata.",
        "page_ref": 52,
        "detail_level": "full"
    },
    {
        "id": "enhanced_tracking",
        "name_en": "Enhanced Tracking",
        "name_pt": "Rastreamento Aprimorado",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "per_level", "value": 5},
        "description_pt": "Cada nível permite Aim ou Evaluate aplicar a UM alvo adicional. Só rastreia alvos detectáveis; não pode Aim em mais alvos do que armas prontas.",
        "page_ref": 53,
        "detail_level": "full"
    },
    {
        "id": "extended_lifespan",
        "name_en": "Extended Lifespan",
        "name_pt": "Longevidade Aumentada",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "per_level", "value": 2},
        "description_pt": "Cada nível dobra: idade de maturidade (default 18), início de aging (50), aceleração de aging (70, 90). Acima de 7 níveis, prefira Unaging.",
        "page_ref": 53,
        "detail_level": "full"
    },
    {
        "id": "extra_arms",
        "name_en": "Extra Arms",
        "name_pt": "Braços Extras",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "per_level", "value": 10, "level_label": "por braço extra"},
        "description_pt": "Cada braço extra além de 2: 10 pts. Permite multitarefa não-combate. Em combate: sem Extra Attack você só ataca 1x/turno mesmo com vários braços, mas pode usar todos pra grapple (+2 por braço extra; +3 contra pin se tem mais braços). Modifiers: Extra-Flexible +50%, Long +100%/SM, Foot Manipulators -30%, No Physical Attack -50%, Short -50%, Weak -25%/-50%, Weapon Mount -80%.",
        "page_ref": 53,
        "detail_level": "full"
    },
    {
        "id": "extra_attack",
        "name_en": "Extra Attack",
        "name_pt": "Ataque Extra",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "per_level", "value": 25, "level_label": "por ataque extra"},
        "description_pt": "Cada nível = 1 ataque adicional por turno. Limitado pelo número de membros/armas naturais/poderes de ataque. Humano normal pode comprar até 1 (representa coordenação superior). Não elimina -4 da off hand. Pode usar para Feint. Em All-Out Attack todos seus ataques pegam o mesmo bônus.",
        "page_ref": 53,
        "detail_level": "full"
    },
    {
        "id": "extra_head",
        "name_en": "Extra Head",
        "name_pt": "Cabeça Extra",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "per_level", "value": 15, "level_label": "por cabeça"},
        "description_pt": "Cada cabeça extra é funcional (ears, eyes, mouth) e inclui 1 Extra Mouth + 1 nível de Enhanced Tracking sem custo. Cada uma tem brain backup com cópia de memória/personalidade/skills (não dá mental maneuvers extra — pra isso, Compartmentalized Mind). Dano em uma cabeça limita a 2×(HP/n_cabeças). Decapitação só mata aquela cabeça. Limitation Extraneous -20% (sem backup brain).",
        "page_ref": 54,
        "detail_level": "full"
    },
    {
        "id": "extra_legs",
        "name_en": "Extra Legs",
        "name_pt": "Pernas Extras",
        "type": "physical",
        "origin": "exotic",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 5,  "name_pt": "3-4 pernas — perde 1 = ½ Move"},
                {"value": 10, "name_pt": "5-6 pernas — cada perda -20% Move"},
                {"value": 15, "name_pt": "7+ pernas — cada perda -10% Move"}
            ]
        },
        "description_pt": "Pernas servem pra andar; se manipulam objetos use Extra Arms. Cada perna pode chutar (thrust/cr no reach normal). Modifiers: Long +100%/SM, Cannot Kick -50%. Beings c/ 2 pernas podem usar mods (1/10 do percent).",
        "page_ref": 54,
        "detail_level": "full"
    },
    {
        "id": "extra_life",
        "name_en": "Extra Life",
        "name_pt": "Vida Extra",
        "type": "mental",
        "origin": "supernatural",
        "cost": {"type": "per_level", "value": 25, "level_label": "por vida extra"},
        "description_pt": "Volta dos mortos. Cada uso consome 1 Extra Life e -25 pts. Limitations: Copy -20% (backup periódico em local específico), Requires Body -20%/-40% (volta desencarnado, precisa novo corpo).",
        "page_ref": 55,
        "detail_level": "full"
    },
    {
        "id": "extra_mouth",
        "name_en": "Extra Mouth",
        "name_pt": "Boca Extra",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "per_level", "value": 5, "level_label": "por boca extra"},
        "description_pt": "Bocas adicionais funcionais (respiram, comem, falam). Permite mordidas extras se tiver Extra Attack. Com Compartmentalized Mind, pode lançar 2 spells verbais ou conversar em paralelo. Difícil de silenciar/sufocar.",
        "page_ref": 55,
        "detail_level": "full"
    },

    # ===== F (pp 55-56) =====
    {
        "id": "favor",
        "name_en": "Favor",
        "name_pt": "Favor",
        "type": "social",
        "origin": "mundane",
        "cost": {"type": "variable", "formula": "Cost(Ally|Contact|Patron) / 5 (round up)"},
        "description_pt": "Ally/Contact/Patron one-shot. NPC ajuda UMA vez e descarrega. GM rola contra freq do parent advantage. Em sucesso, ajuda e some o Favor. Em 3-4 no roll, NPC ainda se sente em débito (Favor permanece).",
        "page_ref": 55,
        "detail_level": "full"
    },
    {
        "id": "fearlessness",
        "name_en": "Fearlessness",
        "name_pt": "Destemor",
        "type": "mental",
        "origin": "mundane",
        "cost": {"type": "per_level", "value": 2},
        "description_pt": "Adiciona nível ao Will em Fright Checks, resistência a Intimidation e fear sobrenatural. Subtrai nível de Intimidation rolls feitos contra você.",
        "page_ref": 55,
        "detail_level": "full"
    },
    {
        "id": "filter_lungs",
        "name_en": "Filter Lungs",
        "name_pt": "Pulmões Filtrantes",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 5},
        "description_pt": "Filtra contaminantes ordinários (poeira, pólen, fumaça, gás lacrimogêneo). NÃO filtra gás nervoso ou contact agents. Não necessário se tem Doesn't Breathe.",
        "page_ref": 55,
        "detail_level": "full"
    },
    {
        "id": "fit",
        "name_en": "Fit",
        "name_pt": "Em Forma",
        "type": "physical",
        "origin": "mundane",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 5,  "name_pt": "Fit — +1 em HT rolls; recupera FP em 2× normal"},
                {"value": 15, "name_pt": "Very Fit — +2 em HT rolls; perde FP em ½ normal, recupera em 2×"}
            ]
        },
        "description_pt": "Não melhora HT nem HT-based skills. FP só afeta perda por exertion/heat — não FP gasto em psi/magia.",
        "page_ref": 55,
        "detail_level": "full"
    },
    {
        "id": "flexibility",
        "name_en": "Flexibility",
        "name_pt": "Flexibilidade",
        "type": "physical",
        "origin": "mundane",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 5,  "name_pt": "Flexibility — +3 em Climbing/Escape/Erotic Art/break free; ignora -3 close-quarters"},
                {"value": 15, "name_pt": "Double-Jointed — +5 nesses skills; ignora -5 close-quarters"}
            ]
        },
        "description_pt": "Corpo flexível. Double-Jointed não estica/comprime mas dobra qualquer membro em qualquer direção.",
        "page_ref": 56,
        "detail_level": "full"
    },
    {
        "id": "flight",
        "name_en": "Flight",
        "name_pt": "Voo",
        "type": "physical",
        "origin": "exotic",
        "cost": {"type": "fixed", "value": 40},
        "description_pt": "Voo auto-propelido sem asas (default). Move = Basic Speed × 2 (sem fração); ajustável ±2pts/yd/s. Pode hover (Move 0). Sem mods especiais, também 'voa' meia-velocidade subaquático. Modifiers: Newtonian Space Flight +25%, Space Flight +50%. Limitations: Cannot Hover -15%, Controlled Gliding -45%, Gliding -50%, Lighter Than Air -10%, Low Ceiling -10/-20/-25%, Small Wings -10%, Space Flight Only -75%, Winged -25%.",
        "page_ref": 56,
        "detail_level": "full"
    },

    # ===== G (pp 56-57) =====
    {
        "id": "gadgeteer",
        "name_en": "Gadgeteer",
        "name_pt": "Inventor",
        "type": "mental",
        "origin": "mundane",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 25, "name_pt": "Gadgeteer — cinematic, mas leva dias/meses + dinheiro"},
                {"value": 50, "name_pt": "Quick Gadgeteer — minutos/horas, peças sucateadas"}
            ]
        },
        "description_pt": "Inventor nato. Modifica e cria gadgets conforme regras de Gadgeteering p475. Quick é unsuitable para campanhas realistas.",
        "page_ref": 56,
        "detail_level": "full"
    },
    {
        "id": "g_experience",
        "name_en": "G-Experience",
        "name_pt": "Experiência G",
        "type": "physical",
        "origin": "mundane",
        "cost": {
            "type": "options",
            "choices": [
                {"value": 1,  "name_pt": "1 gravidade específica"},
                {"value": 10, "name_pt": "G-Experience (All) — todas gravidades"}
            ]
        },
        "description_pt": "Sofre apenas ½ DX penalty pra gravidade diferente. Em gravidade baixa que ajude, ainda ganha +1 extra além do bônus normal. Custo: 1 pt por gravidade individual ou 10 pts pra todas.",
        "page_ref": 57,
        "detail_level": "full"
    },
    {
        "id": "gizmos",
        "name_en": "Gizmos",
        "name_pt": "Geringonças",
        "type": "mental",
        "origin": "mundane",
        "cost": {"type": "per_level", "value": 5, "level_label": "por gizmo (max 3)"},
        "description_pt": "Uma vez por sessão, saca item pequeno que 'estava no bolso' não-declarado anteriormente. Critérios: item que você possui mas não declarou; item que provavelmente possui dado seu conceito; gadget barato comum no seu TL. Item entra em jogo só no momento (não pode ser confiscado antes). Não-realista; GM pode limitar/proibir.",
        "page_ref": 57,
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
        "batch": "A-G (C-final + D + E + F + G)",
        "entries_in_file": len(data["entries"]),
        "total_estimated_in_book": 155,
        "next_letters": "H-K",
        "notes_pt": "Catálogo incremental. Entradas em D-G têm detail_level=full com modificadores principais resumidos. Para detalhes completos de cada Enhancement/Limitation, ver livro pp 102-116 (modifiers gerais) ou as páginas específicas referenciadas.",
    }
    TARGET.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"adicionadas: {added}, puladas (já existiam): {skipped}")
    print(f"total no arquivo: {len(data['entries'])} / ~155")


if __name__ == "__main__":
    main()
