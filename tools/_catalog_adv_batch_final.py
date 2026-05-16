"""Batch final de vantagens: S-final + T-Z + Talents + Perks.
Fecha completude da seção Advantages do Basic Set: Characters.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "gurps" / "data" / "advantages.json"

NEW_ENTRIES = [
    # ===== S-final (pp 84-89) =====
    {"id":"morph","name_en":"Morph","name_pt":"Metamorfo","type":"physical","origin":"exotic",
     "cost":{"type":"variable","formula":"100 + (max_template - native_template)"},
     "description_pt":"Similar a Alternate Form mas sem lista fixa. Assume qualquer racial template existente, dentro de limite de pontos. Base 100 pts = templates ≤ nativo. Soma pontos pra subir teto. Memoriza forma (1 min concentração); IQ 'slots' = formas memorizadas. Forma vista/tocada pode ser assumida sem memorização. Mudanças cosméticas incluídas (imita indivíduo). Enhancement: Unlimited +50% (vira robôs/veículos). Limitations: Cosmetic -50%, Mass Conservation -20%, Retains Shape -20%.","page_ref":84,"detail_level":"full"},
    {"id":"shrinking","name_en":"Shrinking","name_pt":"Encolhimento","type":"physical","origin":"exotic",
     "cost":{"type":"per_level","value":5},
     "description_pt":"Encolhe à vontade. Cada nível: -1 SM, -1/seg. -6 SM = altura /10. Reduz Move, reach, dano, HP, DR proporcionalmente. -2 SM cada = peso /10. Sem carregar nada por default. Enhancements: Affects Others +50%/pessoa, Can Carry Objects +10 a +100%, Full Damage +100%, Full DR +30%, Full HP +30%, Full Move +30%.","page_ref":85,"detail_level":"full"},
    {"id":"signature_gear","name_en":"Signature Gear","name_pt":"Equipamento Característico","type":"social","origin":"mundane",
     "cost":{"type":"variable","formula":"1 pt = 50% starting wealth em goods"},
     "description_pt":"Posses distintivas não-relacionadas à riqueza. Cada ponto = até 50% da starting wealth média em goods (nunca cash). Se NPC rouba/extravia, GM dá chance de recuperar. Se perdido sem culpa, GM devolve pts ou substitui. Se vendido voluntariamente, pts perdidos.","page_ref":85,"detail_level":"full"},
    {"id":"silence","name_en":"Silence","name_pt":"Silêncio","type":"physical","origin":"mundane",
     "cost":{"type":"per_level","value":5},
     "description_pt":"Move/respira sem ruído. +2/nível em Stealth perfeitamente parado, +1/nível movendo (mesmo com armadura). Só ajuda em escuro, contra listening devices, criaturas cegas e quem depende de audição.","page_ref":85,"detail_level":"full"},
    {"id":"single_minded","name_en":"Single-Minded","name_pt":"Concentração Absoluta","type":"mental","origin":"mundane",
     "cost":{"type":"fixed","value":5},
     "description_pt":"+3 em rolls de tarefa mental longa em concentração exclusiva (GM julga útil). -5 para notar interrupções; Will para ignorar. GM pode regular que certas tarefas (inventar, magia, social) exigem atenção dividida — vantagem não aplica.","page_ref":85,"detail_level":"full"},
    {"id":"slippery","name_en":"Slippery","name_pt":"Escorregadio","type":"physical","origin":"exotic",
     "cost":{"type":"per_level","value":2,"level_label":"máx 5"},
     "description_pt":"Difícil de segurar. +1/nível em ST/DX/Escape para escapar restraints, break free em close combat, espremer por aberturas estreitas.","page_ref":85,"detail_level":"full"},
    {"id":"snatcher","name_en":"Snatcher","name_pt":"Subtraidor Dimensional","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":80},
     "description_pt":"Encontra item pequeno em mundo alternativo e 'puxa' através das dimensões. 10 seg concentração + visualização + IQ roll (max 14). Item ≤5 lbs, cabe em uma mão. Mão livre (-3 se amarrada). 2 FP por tentativa. Falha crítica = item errado (talvez perigoso). Items duram até voltar (Permanent enhancement segura). Enhancements: Permanent +300%. Limitations: Less Weight -5 a -30%, Specialized -5 a -25%, Stunning -10%, Unpredictable -25%.","page_ref":86,"detail_level":"full"},
    {"id":"social_chameleon","name_en":"Social Chameleon","name_pt":"Camaleão Social","type":"social","origin":"mundane",
     "cost":{"type":"fixed","value":5},
     "description_pt":"Sabe o que falar perto de 'social betters'. Imune a reaction penalties por Rank/Status. Em situações sem penalty, +1 em reactions de quem exige respeito (sacerdotes, reis). Cinematic.","page_ref":86,"detail_level":"full"},
    {"id":"social_regard","name_en":"Social Regard","name_pt":"Estima Social","type":"social","origin":"mundane",
     "cost":{"type":"per_level","value":5,"level_label":"por +1 reaction, máx +4"},
     "description_pt":"Membro de classe/raça/sexo bem-vista. Visível a quem te encontra. Não é Reputation (é 'privilege by association'). Tipos: Feared (deferência silenciosa), Respected (high Status virtual), Venerated (estranhos cuidam até quando atrapalha).","page_ref":86,"detail_level":"full"},
    {"id":"speak_underwater","name_en":"Speak Underwater","name_pt":"Fala Subaquática","type":"physical","origin":"exotic",
     "cost":{"type":"fixed","value":5},
     "description_pt":"Fala e ouve normalmente submerso. Enhancement: Interface Crossing +50% (também fala com quem está na superfície).","page_ref":87,"detail_level":"full"},
    {"id":"speak_with_animals","name_en":"Speak With Animals","name_pt":"Falar com Animais","type":"supernatural","origin":"supernatural",
     "cost":{"type":"fixed","value":25},
     "description_pt":"Conversa com animais. Qualidade depende do IQ do animal (insetos = emoções; chimpanzés/gatos = discussão). 1 min por pergunta/resposta. GM pode exigir reaction roll (+2 com comida). Limitations: Specialized — All land animals -40%, All aquatic -40%, classe -50%, família -60%, espécie -80%.","page_ref":87,"detail_level":"full"},
    {"id":"speak_with_plants","name_en":"Speak With Plants","name_pt":"Falar com Plantas","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":15},
     "description_pt":"Comunicação empática com plantas. Plantas terrestres IQ 0 (árvore grande pode ser 'mais sábia'). Sabe sobre seu bem-estar (água, pisoteamento) mas não escuta conversas próximas. Plantas normais cooperam sempre.","page_ref":87,"detail_level":"full"},
    {"id":"special_rapport","name_en":"Special Rapport","name_pt":"Rapport Especial","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":5},
     "description_pt":"Vínculo único com outra pessoa. Empathy potente que funciona só com essa pessoa, sem distância. Sabe quando o parceiro está em trouble/pain/lying/precisa de ajuda. Ambos precisam comprar. GM pode proibir contra Patrons.","page_ref":88,"detail_level":"full"},
    {"id":"spines","name_en":"Spines","name_pt":"Espinhos","type":"physical","origin":"exotic",
     "cost":{"type":"options","choices":[
         {"value":1,"name_pt":"Short Spines — 1-2\" longos; 1d-2 impaling, Reach C"},
         {"value":3,"name_pt":"Long Spines — 1-2 ft; 1d impaling, Reach C"}
     ]},
     "description_pt":"Espinhos em partes estratégicas do corpo. DX-4 free action contra cada foe em close combat (+2 se ataca por trás). Grapplers/slammers acertam-se automaticamente; slammers tomam DANO MÁXIMO.","page_ref":88,"detail_level":"full"},
    {"id":"spirit_empathy","name_en":"Spirit Empathy","name_pt":"Empatia Espiritual","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":10},
     "description_pt":"Empathy aplicada a espíritos. IQ roll p/ sentir intenções gerais. Influence skills (Diplomacy, Sex Appeal etc.) funcionam normalmente com espíritos. Não previne espíritos malignos de te perseguirem mas pode facilitar detectar planos. Limitation: Specialized -50% (classe específica: anjos, demônios, faerie etc.).","page_ref":88,"detail_level":"full"},
    {"id":"stretching","name_en":"Stretching","name_pt":"Elasticidade","type":"physical","origin":"exotic",
     "cost":{"type":"per_level","value":6},
     "description_pt":"Cada nível: +1 SM efetivo em uma parte do corpo (sem mudar SM total). Estica braços, pernas, pescoço. ±1 SM/segundo. Não aumenta dano (sem massa/músculo extra). Ideal pra máquinas com manipuladores telescópicos; supers 'rubber body' adicionam Elastic Skin + Double-Jointed + Morph + Super Jump.","page_ref":88,"detail_level":"full"},
    {"id":"striker","name_en":"Striker","name_pt":"Apêndice Ofensivo","type":"physical","origin":"exotic",
     "cost":{"type":"options","choices":[
         {"value":5,"name_pt":"Crushing ou Piercing"},
         {"value":6,"name_pt":"Large Piercing"},
         {"value":7,"name_pt":"Cutting"},
         {"value":8,"name_pt":"Impaling"}
     ]},
     "description_pt":"Parte do corpo pra striking aimed (chifres, tail, stinger). Reach C, thrust dano +1/dado. DX ou Brawling pra acertar. Pode parry (DX/2+3 ou Brawling parry). Enhancements: Long +75/+100%/SM. Limitations: Cannot Parry -40%, Clumsy -20%/-1, Limited Arc -40%, Weak -50%.","page_ref":88,"detail_level":"full"},
    {"id":"striking_st","name_en":"Striking ST","name_pt":"ST de Golpe","type":"physical","origin":"mundane",
     "cost":{"type":"per_level","value":5,"level_label":"por +1 ST"},
     "description_pt":"ST extra só para thrust/swing damage. Sem efeito em HP nem Basic Lift. Se ST normal tem No Fine Manipulators ou Size, aplica os mesmos em Striking ST.","page_ref":88,"detail_level":"full"},
    {"id":"subsonic_hearing","name_en":"Subsonic Hearing","name_pt":"Audição Subsônica","type":"physical","origin":"exotic",
     "cost":{"type":"options","choices":[
         {"value":0,"name_pt":"Só subsônica"},
         {"value":5,"name_pt":"Subsônica + sons normais"}
     ]},
     "description_pt":"Ouve <40 Hz: tempestades distantes, terremotos, manadas, veículos blindados. +1 em Tracking se quarry no chão.","page_ref":89,"detail_level":"full"},
    {"id":"subsonic_speech","name_en":"Subsonic Speech","name_pt":"Fala Subsônica","type":"physical","origin":"exotic",
     "cost":{"type":"options","choices":[
         {"value":0,"name_pt":"Só subsônica"},
         {"value":10,"name_pt":"Alternável com normal"}
     ]},
     "description_pt":"Inclui Subsonic Hearing. Fala lenta (½ velocidade), -2 em Fast-Talk e skills que dependem de versatilidade vocal. Carrega 2× a distância da fala normal.","page_ref":89,"detail_level":"full"},
    {"id":"super_climbing","name_en":"Super Climbing","name_pt":"Escalada Super","type":"physical","origin":"exotic",
     "cost":{"type":"per_level","value":3},
     "description_pt":"+1 Move/nível ao escalar ou usar Clinging.","page_ref":89,"detail_level":"full"},
    {"id":"super_jump","name_en":"Super Jump","name_pt":"Salto Super","type":"physical","origin":"exotic",
     "cost":{"type":"per_level","value":10},
     "description_pt":"Cada nível dobra distância/altura de jumping. Move ao saltar = max(Move normal, ⅕ max long jump). Pode jump-slam (no roll de jumping). Cai distância ≤ max high jump sem dano (+5 jds com Acrobatics).","page_ref":89,"detail_level":"full"},
    {"id":"super_luck","name_en":"Super Luck","name_pt":"Super Sorte","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":100},
     "description_pt":"1×/hora de jogo, dita resultado de UM die roll (em vez de rolar). Skill efetivo ≥3, e o resultado tem que ser possível em rolagem normal. Compatível com Luck normal mas só pode ter Super Luck 1×.","page_ref":89,"detail_level":"full"},
    {"id":"supernatural_durability","name_en":"Supernatural Durability","name_pt":"Resistência Sobrenatural","type":"physical","origin":"supernatural",
     "cost":{"type":"fixed","value":150},
     "description_pt":"'Vampiro/serial killer de filme'. Imune a shock/physical stun/knockout. Inclui High Pain Threshold. Em HP≥0, imune a crippling, Move full. Abaixo de 0 HP: ½ Move, pode crippling, NÃO morre exceto por item específico (Occasional+) — vai com Vulnerability. Exceção: dano single de 10×HP = morre. Pra morrer real, ferimento por item específico a -HP+, ou -5×HP automaticamente.","page_ref":89,"detail_level":"full"},

    # ===== T (pp 89-94) =====
    {"id":"talent_generic","name_en":"Talent","name_pt":"Talento","type":"mental","origin":"mundane",
     "cost":{"type":"per_level","value":"5/10/15","level_label":"depende do tamanho do grupo"},
     "description_pt":"Aptidão natural para grupo de skills relacionadas. Custo: Small (≤6 skills) 5 pts/nv, Medium (7-12) 10 pts/nv, Large (13+) 15 pts/nv. Cada nível: +1 em skills do grupo (mesmo default), +1 reaction de quem é impressionado pela aptidão, -10%/nv no tempo de aprender. Max 4 níveis por Talent. Custom Talents permitidos pelo GM.","page_ref":89,"detail_level":"full"},
    {"id":"talent_animal_friend","name_en":"Talent: Animal Friend","name_pt":"Talento: Amigo dos Animais","type":"mental","origin":"mundane",
     "cost":{"type":"per_level","value":5},
     "description_pt":"Skills: Animal Handling, Falconry, Packing, Riding, Teamster, Veterinary. Reaction bonus: todos animais.","page_ref":89,"detail_level":"full"},
    {"id":"talent_artificer","name_en":"Talent: Artificer","name_pt":"Talento: Artífice","type":"mental","origin":"mundane",
     "cost":{"type":"per_level","value":10},
     "description_pt":"Skills: Armoury, Carpentry, Electrician, Electronics Repair, Engineer, Machinist, Masonry, Mechanic, Smith. Reaction bonus: quem você atende.","page_ref":89,"detail_level":"full"},
    {"id":"talent_business_acumen","name_en":"Talent: Business Acumen","name_pt":"Talento: Visão de Negócios","type":"mental","origin":"mundane",
     "cost":{"type":"per_level","value":10},
     "description_pt":"Skills: Accounting, Administration, Economics, Finance, Gambling, Market Analysis, Merchant, Propaganda. Reaction bonus: quem faz negócios com você.","page_ref":89,"detail_level":"full"},
    {"id":"talent_gifted_artist","name_en":"Talent: Gifted Artist","name_pt":"Talento: Artista Talentoso","type":"mental","origin":"mundane",
     "cost":{"type":"per_level","value":5},
     "description_pt":"Skills: Artist, Jeweler, Leatherworking, Photography, Sewing. Reaction bonus: quem compra/critica sua obra.","page_ref":90,"detail_level":"full"},
    {"id":"talent_green_thumb","name_en":"Talent: Green Thumb","name_pt":"Talento: Bom Jardineiro","type":"mental","origin":"mundane",
     "cost":{"type":"per_level","value":5},
     "description_pt":"Skills: Biology, Farming, Gardening, Herb Lore, Naturalist. Reaction bonus: jardineiros e plantas sapientes.","page_ref":90,"detail_level":"full"},
    {"id":"talent_healer","name_en":"Talent: Healer","name_pt":"Talento: Curador","type":"mental","origin":"mundane",
     "cost":{"type":"per_level","value":10},
     "description_pt":"Skills: Diagnosis, Esoteric Medicine, First Aid, Pharmacy, Physician, Physiology, Psychology, Surgery, Veterinary. Reaction bonus: pacientes (passados e presentes).","page_ref":90,"detail_level":"full"},
    {"id":"talent_mathematical_ability","name_en":"Talent: Mathematical Ability","name_pt":"Talento: Habilidade Matemática","type":"mental","origin":"mundane",
     "cost":{"type":"per_level","value":10},
     "description_pt":"Skills: Accounting, Astronomy, Cryptography, Engineer, Finance, Market Analysis, Mathematics, Physics. Reaction bonus: engenheiros e cientistas.","page_ref":90,"detail_level":"full"},
    {"id":"talent_musical_ability","name_en":"Talent: Musical Ability","name_pt":"Talento: Habilidade Musical","type":"mental","origin":"mundane",
     "cost":{"type":"per_level","value":5},
     "description_pt":"Skills: Group Performance (Conducting), Musical Composition, Musical Influence, Musical Instrument, Singing. Reaction bonus: quem ouve/critica.","page_ref":91,"detail_level":"full"},
    {"id":"talent_outdoorsman","name_en":"Talent: Outdoorsman","name_pt":"Talento: Homem da Mata","type":"mental","origin":"mundane",
     "cost":{"type":"per_level","value":10},
     "description_pt":"Skills: Camouflage, Fishing, Mimicry, Naturalist, Navigation, Survival, Tracking. Reaction bonus: exploradores, nature lovers.","page_ref":91,"detail_level":"full"},
    {"id":"talent_smooth_operator","name_en":"Talent: Smooth Operator","name_pt":"Talento: Operador Suave","type":"mental","origin":"mundane",
     "cost":{"type":"per_level","value":15},
     "description_pt":"Skills: Acting, Carousing, Detect Lies, Diplomacy, Fast-Talk, Intimidation, Leadership, Panhandling, Politics, Public Speaking, Savoir-Faire, Sex Appeal, Streetwise. Reaction bonus: con artists, políticos, vendedores — só se NÃO está tentando manipulá-los.","page_ref":91,"detail_level":"full"},
    {"id":"teeth","name_en":"Teeth","name_pt":"Dentes","type":"physical","origin":"mundane",
     "cost":{"type":"options","choices":[
         {"value":0,"name_pt":"Blunt (default) — thrust-1 crushing"},
         {"value":1,"name_pt":"Sharp Teeth — thrust-1 cutting (carnívoro)"},
         {"value":1,"name_pt":"Sharp Beak — thrust-1 large piercing (ave de rapina)"},
         {"value":2,"name_pt":"Fangs — thrust-1 impaling (Smilodon)"}
     ]},
     "description_pt":"Mordida em close combat.","page_ref":91,"detail_level":"full"},
    {"id":"telecommunication","name_en":"Telecommunication","name_pt":"Telecomunicação","type":"physical","origin":"exotic",
     "cost":{"type":"options","choices":[
         {"value":10,"name_pt":"Infrared Communication — 500 jds line of sight"},
         {"value":15,"name_pt":"Laser Communication — 50 mi line of sight"},
         {"value":10,"name_pt":"Radio — 10 mi omnidirectional"},
         {"value":30,"name_pt":"Telesend — range ilimitado, long-distance modifiers"}
     ]},
     "description_pt":"Fala/imagens sem voz a longa distância. 1 seg + IQ roll pra establecer; depois sem concentração. Múltiplos contatos: -1/contato após 1º. Enhancements: Broadcast +50% (Telesend), Short Wave +50% (Radio), Universal +50%, Video +40%. Limitations: Racial -20%, Receive Only -50%, Send Only -50%, Telepathic -10%, Vague -50%.","page_ref":91,"detail_level":"full"},
    {"id":"telekinesis","name_en":"Telekinesis","name_pt":"Telecinese","type":"physical","origin":"exotic",
     "cost":{"type":"per_level","value":5},
     "description_pt":"Move objetos sem tocar. ST = TK level, Move = TK level, range max 10 jds. Concentrate maneuver pra agir. Pode grapple/strike, levitate (se tem ST pra próprio peso), throw (range = origem→target + target→destination penalty). Bônus +4 em tarefas que beneficiariam High Manual Dexterity (IQ roll). Limitations: Magnetic -50% (só ferro/níquel/cobalto), Psychokinetic -10%, Visible -20%.","page_ref":92,"detail_level":"full"},
    {"id":"telescopic_vision","name_en":"Telescopic Vision","name_pt":"Visão Telescópica","type":"physical","origin":"exotic",
     "cost":{"type":"per_level","value":5},
     "description_pt":"'Zoom' visual. Cada nível ignora -1 em Vision range penalties sempre, ou -2 com Aim. +1 Acc/nível em ranged attacks (Aim seconds = bonus). Não cumulativo com binoculars/scopes técnicos. Limitation: No Targeting -60%.","page_ref":92,"detail_level":"full"},
    {"id":"temperature_control","name_en":"Temperature Control","name_pt":"Controle de Temperatura","type":"physical","origin":"exotic",
     "cost":{"type":"per_level","value":5},
     "description_pt":"Altera temperatura ambiente até 20°/nível, taxa 2°/nv/seg de concentração. Raio 2 jds em até 10 jds. Não causa dano direto (use Innate Attack burning/fatigue). Limitations: Cold -50%, Heat -50%, Psychokinetic -10%.","page_ref":92,"detail_level":"full"},
    {"id":"temperature_tolerance","name_en":"Temperature Tolerance","name_pt":"Tolerância Térmica","type":"physical","origin":"mundane",
     "cost":{"type":"per_level","value":1},
     "description_pt":"Cada nível adiciona HT graus na 'comfort zone' (humano default 35-90°F = 55° wide). Distribui entre frio/calor. NÃO protege contra fogo/gelo a menos que dano seja só por temperatura ambiente. Realista: humanos 1-2.","page_ref":93,"detail_level":"full"},
    {"id":"temporal_inertia","name_en":"Temporal Inertia","name_pt":"Inércia Temporal","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":15},
     "description_pt":"Ancorado em probabilidade. Lembra ambas versões se história muda. Não é apagado em paradoxos. Drawback: existe 'você' em qualquer timeline encontrada. Só vale em settings com paradoxos/mudanças temporais.","page_ref":93,"detail_level":"full"},
    {"id":"tenure","name_en":"Tenure","name_pt":"Estabilidade no Cargo","type":"social","origin":"mundane",
     "cost":{"type":"fixed","value":5},
     "description_pt":"Cargo vitalício, só perdido por má conduta extraordinária (agressão, imoralidade grave). Emprego e salário garantidos. Comum: professores universitários, juízes, sacerdotes, senadores.","page_ref":93,"detail_level":"full"},
    {"id":"terrain_adaptation","name_en":"Terrain Adaptation","name_pt":"Adaptação ao Terreno","type":"physical","origin":"mundane",
     "cost":{"type":"options","choices":[
         {"value":0,"name_pt":"Funciona normal em terreno X, penalty em chão sólido"},
         {"value":5,"name_pt":"Funciona normal em ambos"}
     ]},
     "description_pt":"Sem DX/Move penalty em um tipo de terreno instável (gelo, areia, neve, etc.). Compre separado por tipo.","page_ref":93,"detail_level":"full"},
    {"id":"terror","name_en":"Terror","name_pt":"Terror","type":"supernatural","origin":"supernatural",
     "cost":{"type":"variable","formula":"30 + 10/-1 Fright Check"},
     "description_pt":"Quem te vê ou ouve faz Fright Check imediato. Compre penalties extras: 10 pts/-1. Vítimas +1 por Fright Check após o 1º em 24h. Sucesso = imune por 1 hora. Adicione Melee Attack limitation se só toque. Limitation: Always On -20% (frequentemente com Hideous Appearance+).","page_ref":93,"detail_level":"full"},
    {"id":"trained_by_a_master","name_en":"Trained By A Master","name_pt":"Treinado por um Mestre","type":"mental","origin":"mundane",
     "cost":{"type":"fixed","value":30},
     "description_pt":"Mestre de artes marciais. Metade do penalty pra Rapid Strike e Parry múltiplo (Judo, Karate, Melee Weapons). Foca 'chi' — pré-req pra cinematic skills: Flying Leap, Invisibility Art, Power Blow etc. GM pode exigir pré-reqs (Judo, Karate, Philosophy, Theology). Cinematic.","page_ref":93,"detail_level":"full"},
    {"id":"true_faith","name_en":"True Faith","name_pt":"Fé Verdadeira","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":15},
     "description_pt":"Fé religiosa profunda protege contra seres supernaturais malignos. Para usar: brandir símbolo, cantar, ou ação apropriada à religião. Em combate exige Concentrate. Enquanto asserts, nenhuma entidade maligna pode chegar a 1 jd. Force entrar = sai pelo caminho mais curto (Dread). Se não pode sair sem aproximar, Will roll: sucesso = corre pelo lado, falha = paralisado. Pact limitation intrínseca; não aplique de novo.","page_ref":94,"detail_level":"full"},
    {"id":"tunneling","name_en":"Tunneling","name_pt":"Escavação","type":"physical","origin":"exotic",
     "cost":{"type":"variable","formula":"30 + 5/Tunneling Move"},
     "description_pt":"Cava através de terra/pedra; expele entulho. Passagem cabe seu corpo. Em pedra = ½ Tunneling Move. GM checa colapso: 1×/min vs maior de Engineer(Mining), Prospecting-3, IQ-4. Modifica por dureza da rocha. -½ Tunneling Move = +1 no roll.","page_ref":94,"detail_level":"full"},

    # ===== U (pp 94-96) =====
    {"id":"ultrahearing","name_en":"Ultrahearing","name_pt":"Audição Ultrassônica","type":"physical","origin":"exotic",
     "cost":{"type":"options","choices":[
         {"value":0,"name_pt":"Só ultrassônica"},
         {"value":5,"name_pt":"Ultrassônica + normais"}
     ]},
     "description_pt":"Ouve >20 kHz. Detecta apitos de cão, sonar, motion detectors. Active sonar em 2× range efetivo.","page_ref":94,"detail_level":"full"},
    {"id":"ultrasonic_speech","name_en":"Ultrasonic Speech","name_pt":"Fala Ultrassônica","type":"physical","origin":"exotic",
     "cost":{"type":"options","choices":[
         {"value":0,"name_pt":"Só ultrassônica"},
         {"value":10,"name_pt":"Alternável com normal"}
     ]},
     "description_pt":"Inclui Ultrahearing. Muitas criaturas acham frequências sustentadas irritantes/dolorosas.","page_ref":94,"detail_level":"full"},
    {"id":"ultravision","name_en":"Ultravision","name_pt":"Ultravisão","type":"physical","origin":"exotic",
     "cost":{"type":"options","choices":[
         {"value":0,"name_pt":"Só UV (cego sem UV)"},
         {"value":10,"name_pt":"Visível + UV"}
     ]},
     "description_pt":"Vê UV (luz solar diurna mesmo nublada, lâmpadas fluorescentes). Bloqueado por vidro/sólido. +2 em Vision/Forensics/Observation/Search com UV. À noite, ignora -2 de darkness penalty (cumulative com Night Vision). Subaquático: halve vision penalties.","page_ref":94,"detail_level":"full"},
    {"id":"unaging","name_en":"Unaging","name_pt":"Imortalidade Etária","type":"physical","origin":"supernatural",
     "cost":{"type":"fixed","value":15},
     "description_pt":"Não envelhece naturalmente nem por meios sobrenaturais. Idade fixa em qualquer ponto escolhido. Sem aging rolls. Enhancement: Age Control +20% (envelhece/rejuvenesce até 10× normal).","page_ref":95,"detail_level":"full"},
    {"id":"unfazeable","name_en":"Unfazeable","name_pt":"Imperturbável","type":"mental","origin":"mundane",
     "cost":{"type":"fixed","value":15},
     "description_pt":"Imune a Fright Checks. Reaction modifiers raramente afetam. Trata estranhos com cortesia distante. Imune a Intimidation. Não emotionless — só não demonstra. Precisa roleplaying; incompatível com Phobias. Em campanha de horror, GM pode cobrar mais ou proibir.","page_ref":95,"detail_level":"full"},
    {"id":"universal_digestion","name_en":"Universal Digestion","name_pt":"Digestão Universal","type":"physical","origin":"exotic",
     "cost":{"type":"fixed","value":5},
     "description_pt":"Digere qualquer proteína animal/vegetal não-tóxica, por mais alienígena. Sem proteção contra veneno (use Resistant). Pode 'destruir evidência orgânica' comendo.","page_ref":95,"detail_level":"full"},
    {"id":"unkillable","name_en":"Unkillable","name_pt":"Indestrutível","type":"physical","origin":"supernatural",
     "cost":{"type":"options","choices":[
         {"value":50,"name_pt":"Unkillable 1 — não morre HT, sobrevive até -10×HP"},
         {"value":100,"name_pt":"Unkillable 2 — -10×HP vira esqueleto indestrutível, cura"},
         {"value":150,"name_pt":"Unkillable 3 — -10×HP vira forma incorpórea, reforma"}
     ]},
     "description_pt":"Não morre. Sofre dor, stun, knockout, crippling. Aging normal por default — combine com Unaging para imortal real. Limitations: Achilles' Heel -10 a -50%, Hindrance -5 a -25%, Reincarnation -20% (Unkillable 2/3), Trigger -5 a -25%.","page_ref":95,"detail_level":"full"},
    {"id":"unusual_background","name_en":"Unusual Background","name_pt":"Background Incomum","type":"social","origin":"mundane",
     "cost":{"type":"variable","formula":"GM decide; varia por raridade no setting"},
     "description_pt":"Catch-all pra justificar acesso a habilidades não-comuns no setting. GM define custo e benefícios. Pode ser 0 (background color) ou 50+ (acesso a Unkillable).","page_ref":96,"detail_level":"full"},

    # ===== V (pp 96-97) =====
    {"id":"vacuum_support","name_en":"Vacuum Support","name_pt":"Suporte a Vácuo","type":"physical","origin":"exotic",
     "cost":{"type":"fixed","value":5},
     "description_pt":"Imune a efeitos de vácuo/descompressão. NÃO dá oxigênio (precisa Doesn't Breathe). Geralmente acompanha Sealed + Radiation Tolerance + Temperature Tolerance.","page_ref":96,"detail_level":"full"},
    {"id":"vampiric_bite","name_en":"Vampiric Bite","name_pt":"Mordida Vampírica","type":"physical","origin":"supernatural",
     "cost":{"type":"variable","formula":"30 + 5/HP extra drenado/seg"},
     "description_pt":"Mordida drena vida + cura. Vítima precisa estar helpless/grappled/willing. Dano deve penetrar DR de armadura. 1 HP/seg drenado; cada 3 HP roubados curam 1 HP ou FP (sua escolha). Não passa HP/FP normal. Inclui Teeth (Sharp Teeth ou Sharp Beak — escolha).","page_ref":96,"detail_level":"full"},
    {"id":"versatile","name_en":"Versatile","name_pt":"Versátil","type":"mental","origin":"mundane",
     "cost":{"type":"fixed","value":5},
     "description_pt":"Imaginativo. +1 em tarefas de criatividade/invenção (Artist, Engineer p/ novas invenções, Gadgeteer).","page_ref":96,"detail_level":"full"},
    {"id":"vibration_sense","name_en":"Vibration Sense","name_pt":"Sentido Vibratório","type":"physical","origin":"exotic",
     "cost":{"type":"fixed","value":10},
     "description_pt":"Detecta localização/tamanho via vibrações (pele, whiskers, antenas). Especifique ar ou água. Não substitui visão. Sense roll com bonuses por tamanho/velocidade do alvo, penalty por range. Vento/correntes geram noise. Não funciona se fora do elemento ou em sealed suit. Enhancement: Universal +50% (ar + água).","page_ref":96,"detail_level":"full"},
    {"id":"visualization","name_en":"Visualization","name_pt":"Visualização","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":10},
     "description_pt":"Melhora chances visualizando sucesso. 1 min concentração + descrição detalhada + IQ roll. +1 por ponto de margem se cenário ≈ visualização. Halve se 'not quite same', /3 se 'clearly different'. GM pode dar +2 ou penalty por descrição. Inútil em combate (mudança rápida).","page_ref":96,"detail_level":"full"},
    {"id":"voice","name_en":"Voice","name_pt":"Voz","type":"physical","origin":"mundane",
     "cost":{"type":"fixed","value":10},
     "description_pt":"Voz clara, ressonante, atrativa. +2 em: Diplomacy, Fast-Talk, Mimicry, Performance, Politics, Public Speaking, Sex Appeal, Singing. +2 em qualquer reaction roll de quem te ouve.","page_ref":97,"detail_level":"full"},

    # ===== W (pp 97-99) =====
    {"id":"walk_on_air","name_en":"Walk on Air","name_pt":"Caminhar no Ar","type":"physical","origin":"supernatural",
     "cost":{"type":"fixed","value":20},
     "description_pt":"Ar, fumaça, gases servem de chão. Caminha 'escadas invisíveis' a Move normal. Não funciona em vácuo. Se cai/escorrega: DX roll/seg pra parar no ar; senão queda normal.","page_ref":97,"detail_level":"full"},
    {"id":"walk_on_liquid","name_en":"Walk on Liquid","name_pt":"Caminhar sobre Líquido","type":"physical","origin":"supernatural",
     "cost":{"type":"fixed","value":15},
     "description_pt":"Caminha sobre superfície de qualquer líquido. NÃO protege de dano por contato (lava, ácido fervente).","page_ref":97,"detail_level":"full"},
    {"id":"warp","name_en":"Warp","name_pt":"Teleporte","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":100},
     "description_pt":"Teletransporte. Vê destino, vê remotamente, ou visualiza (se já visitado). IQ roll com penalty de distância (10jds 0, 100jds -2, 1mi -3, 100mi -6, 1000mi -7, +1/×10). Preparation time bonus: 30s 0, 1min +1, ..., 8h +10. Removal -2/level (vista de 2ª mão). FP gasto: +1/FP (declarar antes). Carrega Basic Lift por default; Extra Carrying Capacity pra mais. Crítico falha = destino errado + 1d horas burnout. Pode dodge (instant -10). Enhancements: Blind +50%, Extra Carrying Capacity +10/+20/+30/+50%, Reliable +5%/+1 max +10, Warp Jump +10%/Jumper. Limitations: Hyperjump -25 a -50%, Naked -30%, Psionic Teleportation -10%, Range Limit -5%×(10+penalty).","page_ref":97,"detail_level":"full"},
    {"id":"weapon_master","name_en":"Weapon Master","name_pt":"Mestre em Armas","type":"physical","origin":"mundane",
     "cost":{"type":"options","choices":[
         {"value":20,"name_pt":"Uma arma específica"},
         {"value":25,"name_pt":"Duas armas usadas juntas (ex: broadsword+shield)"},
         {"value":30,"name_pt":"Classe pequena (fencing weapons, knightly)"},
         {"value":35,"name_pt":"Classe média (todas swords, ninja weapons)"},
         {"value":40,"name_pt":"Classe grande (bladed, one-handed)"},
         {"value":45,"name_pt":"Todas muscle-powered"}
     ]},
     "description_pt":"Treinamento alto com armas muscle-powered (não guns). +1/dado em thrust/swing se skill DX+1; +2/dado se DX+2+. Half penalty pra Rapid Strike e parry múltiplo. Familiaridade com todas armas da classe: Easy default DX-1, Average DX-2, Hard DX-3 (não compráveis a partir desse default). Pré-req pra cinematic skills (Blind Fighting, Power Blow). Cinematic.","page_ref":99,"detail_level":"full"},
    {"id":"wild_talent","name_en":"Wild Talent","name_pt":"Talento Selvagem","type":"mental","origin":"supernatural",
     "cost":{"type":"per_level","value":20},
     "description_pt":"Faz coisas sem saber como. 1×/sessão/nível: rola contra skill usando attribute base (IQ p/ IQ-based, etc.), sem default penalty. TL irrelevante. Aplica em skills sem default (precisa pré-reqs como Magery/Trained By Master). Sem efeito em skills que já sabe. Enhancement: Retention +25% (pode aprender o skill se tem 1 pt unspent). Limitations: Emergencies Only -30%, Focused -20%.","page_ref":99,"detail_level":"full"},

    # ===== Z (p100) =====
    {"id":"zeroed","name_en":"Zeroed","name_pt":"Apagado","type":"social","origin":"mundane",
     "cost":{"type":"fixed","value":10},
     "description_pt":"Não existe oficialmente. Em fantasy: 'wanderer misterioso', divinação não revela passado. Em hi-tech: sem registros. Mantém só por cash/commodities, contas blind. Se capturado: interrogatório severo (nonperson, sem direitos).","page_ref":100,"detail_level":"full"},

    # ===== PERKS (p100-101) — todos 1 pt =====
    {"id":"perk_deep_sleeper","name_en":"Perk: Deep Sleeper","name_pt":"Perk: Sono Pesado","type":"mental","origin":"mundane",
     "cost":{"type":"fixed","value":1},
     "description_pt":"Dorme em condições difíceis, atravessa perturbações. Sem efeitos ruins por qualidade do sono. IQ roll normal pra acordar (auto-sucesso com Combat Reflexes).","page_ref":100,"detail_level":"full"},
    {"id":"perk_fur","name_en":"Perk: Fur","name_pt":"Perk: Pelagem","type":"physical","origin":"mundane",
     "cost":{"type":"fixed","value":1},
     "description_pt":"Tem pelo. Previne queimaduras solares. Pelagem densa pode justificar 1-3 níveis de DR + Temperature Tolerance, espinhosa de Spines (comprados separados).","page_ref":100,"detail_level":"full"},
    {"id":"perk_honest_face","name_en":"Perk: Honest Face","name_pt":"Perk: Cara Honesta","type":"social","origin":"mundane",
     "cost":{"type":"fixed","value":1},
     "description_pt":"Parece honesto, confiável. Estranhos confidenciam; não escolhido como suspeito. Sem spot-check em alfândegas (a não ser causa específica). +1 em Acting pra 'parecer inocente'.","page_ref":100,"detail_level":"full"},
    {"id":"perk_no_hangover","name_en":"Perk: No Hangover","name_pt":"Perk: Sem Ressaca","type":"physical","origin":"mundane",
     "cost":{"type":"fixed","value":1},
     "description_pt":"Nunca tem ressaca. Não mitiga embriaguez, só elimina o pós.","page_ref":101,"detail_level":"full"},
    {"id":"perk_penetrating_voice","name_en":"Perk: Penetrating Voice","name_pt":"Perk: Voz Penetrante","type":"physical","origin":"mundane",
     "cost":{"type":"fixed","value":1},
     "description_pt":"Faz-se ouvir. Em ambiente barulhento, outros +3 em Hearing roll. GM pode dar +1 em Intimidation surpreendendo com grito.","page_ref":101,"detail_level":"full"},
    {"id":"perk_sanitized_metabolism","name_en":"Perk: Sanitized Metabolism","name_pt":"Perk: Metabolismo Limpo","type":"physical","origin":"exotic",
     "cost":{"type":"fixed","value":1},
     "description_pt":"Limpo. Sem mau hálito, suor excessivo, problemas de pele. -1 em tentativas de rastrear por cheiro, +1 em reactions em ambientes apertados.","page_ref":101,"detail_level":"full"},
    {"id":"perk_shtick","name_en":"Perk: Shtick","name_pt":"Perk: Marca Registrada","type":"social","origin":"mundane",
     "cost":{"type":"fixed","value":1},
     "description_pt":"Movimento cool ou feature que destaca. Sem bonus combat/reaction, não rende dinheiro, mas dá benefícios menores em jogo (GM discretion). Ex: roupas sempre impecáveis, corre/luta em saltos altos sem penalty.","page_ref":101,"detail_level":"full"},
]


def upgrade_summary_to_full(data, upgrades):
    """Atualiza entries que existiam como summary para full com texto rico."""
    by_id = {e["id"]: e for e in data["entries"]}
    upgraded = []
    for upg in upgrades:
        if upg["id"] in by_id:
            old = by_id[upg["id"]]
            old.update(upg)
            old["detail_level"] = "full"
            upgraded.append(upg["id"])
    return upgraded


# Entries que JÁ existem no JSON como summary — vou fazer upgrade pra full
UPGRADES = [
    {"id":"accessory","name_en":"Perk: Accessory","name_pt":"Perk: Acessório","type":"physical","origin":"mundane",
     "cost":{"type":"fixed","value":1},
     "description_pt":"Corpo incorpora ferramenta/gadget útil (sirene, vacuum cleaner) que dá benefício menor não-combate.","page_ref":100},
    {"id":"alcohol_tolerance","name_en":"Perk: Alcohol Tolerance","name_pt":"Perk: Tolerância ao Álcool","type":"physical","origin":"mundane",
     "cost":{"type":"fixed","value":1},
     "description_pt":"Metaboliza álcool eficientemente. Pode beber continuamente sem efeitos maiores. Binging afeta normalmente. +2 em HT rolls relacionados a bebida.","page_ref":100},
    {"id":"autotrance","name_en":"Perk: Autotrance","name_pt":"Perk: Autotranse","type":"mental","origin":"supernatural",
     "cost":{"type":"fixed","value":1},
     "description_pt":"Entra em transe à vontade. 1 min concentração + Will roll (-1 por tentativa adicional/hora). Transe dá +2 em rolls de contatar espíritos. Will pra sair (1 tentativa cada 5 min).","page_ref":101},
    {"id":"animal_friend","name_en":"Talent: Animal Friend","name_pt":"Talento: Amigo dos Animais","type":"mental","origin":"mundane",
     "cost":{"type":"per_level","value":5},
     "description_pt":"DUPLICATE de talent_animal_friend; mantido por compat. Skills: Animal Handling, Falconry, Packing, Riding, Teamster, Veterinary. Reaction bonus: animais.","page_ref":89},
    {"id":"artificer","name_en":"Talent: Artificer","name_pt":"Talento: Artífice","type":"mental","origin":"mundane",
     "cost":{"type":"per_level","value":10},
     "description_pt":"DUPLICATE; mantido. Skills: Armoury, Carpentry, Electrician, Electronics Repair, Engineer, Machinist, Masonry, Mechanic, Smith.","page_ref":89},
    {"id":"business_acumen","name_en":"Talent: Business Acumen","name_pt":"Talento: Visão de Negócios","type":"mental","origin":"mundane",
     "cost":{"type":"per_level","value":10},
     "description_pt":"DUPLICATE; mantido. Skills: Accounting, Administration, Economics, Finance, Gambling, Market Analysis, Merchant, Propaganda.","page_ref":89},
    {"id":"administrative_rank","name_en":"Administrative Rank","name_pt":"Rank Administrativo","type":"social","origin":"mundane",
     "cost":{"type":"per_level","value":5},
     "description_pt":"Hierarquia formal em organização (civil/govt). Pré-req Status apropriado. Cada nível: +1 reaction de subordinados, autoridade na esfera. Ver Rank p29.","page_ref":29},
    {"id":"alternate_form","name_en":"Alternate Form","name_pt":"Forma Alternativa","type":"physical","origin":"exotic",
     "cost":{"type":"variable","formula":"15 + 0.9×(form_cost - native_form_cost)"},
     "description_pt":"Switch on/off entre formas. Forma desenhada como racial template. 10 seg pra mudar. Fatigue/injury carregam entre formas (escalam). 1 forma: 15 pts (se ≤ nativa) ou 15 + 90% diferença. Formas adicionais: 15 pts cada (ou full se for a mais cara). Especifique influência externa que força reversão.","page_ref":83},
]


def main():
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    existing_ids = {e["id"] for e in data["entries"]}

    upgraded = upgrade_summary_to_full(data, UPGRADES)
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
        "status": "complete_advantages",
        "batch": "A-Z + Talents + Perks (Chapter 2 do Basic Set Characters)",
        "entries_in_file": len(data["entries"]),
        "total_estimated_in_book": 200,
        "completion_date": "2026-05-16",
        "notes_pt": "Catálogo de Vantagens fechado. Cobre Advantage List (pp 34-100), Talents standard (pp 89-91), Perks listados (pp 100-101). Todas entries com detail_level=full. Modificadores gerais (Enhancements/Limitations pp 101-116) na próxima etapa.",
    }
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"adicionadas: {added}")
    print(f"upgraded summary→full: {upgraded}")
    print(f"puladas (já existiam full): {skipped}")
    print(f"TOTAL no arquivo: {len(data['entries'])} entries")


if __name__ == "__main__":
    main()
