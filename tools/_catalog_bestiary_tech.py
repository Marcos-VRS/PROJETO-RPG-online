"""Bestiary (cap 16) + Technology (cap 17) do Basic Set: Campaigns."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "gurps" / "data"

# ========== BESTIARY (cap 16 pp 120-126) ==========
# Sample animais/monstros com stat blocks
ANIMALS = [
    {"id":"dog","name_en":"Dog","st":8,"dx":11,"iq":4,"ht":12,"hp":8,"will":11,"per":14,"speed":5.75,"move":7,
     "sm":-1,"dr":1,"attacks":[{"name":"Bite","damage":"1d-3 cr"}],
     "advantages":["Acute Hearing 4","Acute Taste/Smell 4","Discriminatory Smell","Domestic Animal","Night Vision 4","Quadruped","Wild Animal"],
     "page":456,"notes":"Cão doméstico"},
    {"id":"wolf","name_en":"Wolf","st":11,"dx":12,"iq":4,"ht":12,"hp":11,"will":11,"per":13,"speed":6,"move":9,
     "sm":0,"dr":1,"attacks":[{"name":"Bite","damage":"1d-1 cr"}],
     "advantages":["Acute Hearing 4","Acute Taste/Smell 4","Discriminatory Smell","Combat Reflexes","Night Vision 5","Pack Hunter","Quadruped","Wild Animal"],
     "page":457},
    {"id":"bear","name_en":"Black Bear","st":18,"dx":11,"iq":4,"ht":12,"hp":22,"will":11,"per":13,"speed":5.75,"move":6,
     "sm":+1,"dr":2,"attacks":[{"name":"Bite","damage":"2d-1 cr"},{"name":"Claw","damage":"1d+2 cut"}],
     "advantages":["Berserk","DR 2 (Tough Skin)","Night Vision 3","Semi-Upright","Wild Animal"],
     "page":456},
    {"id":"horse","name_en":"Horse","st":20,"dx":9,"iq":4,"ht":11,"hp":20,"will":11,"per":11,"speed":5,"move":8,
     "sm":+1,"dr":1,"attacks":[{"name":"Hoof","damage":"2d+1 cr"},{"name":"Bite","damage":"1d+1 cr"}],
     "advantages":["Acute Hearing 2","Domestic Animal","Hooves","Peripheral Vision","Quadruped"],
     "page":458},
    {"id":"lion","name_en":"Lion","st":17,"dx":12,"iq":4,"ht":12,"hp":17,"will":11,"per":13,"speed":6,"move":8,
     "sm":+1,"dr":1,"attacks":[{"name":"Bite","damage":"1d+3 imp (Fangs)"},{"name":"Claw","damage":"1d+2 cut"}],
     "advantages":["Combat Reflexes","DR 1","Fangs","Sharp Claws","Night Vision 4","Quadruped","Wild Animal"],
     "page":458},
    {"id":"tiger","name_en":"Tiger","st":17,"dx":13,"iq":4,"ht":12,"hp":17,"will":11,"per":13,"speed":6.25,"move":9,
     "sm":+1,"dr":1,"attacks":[{"name":"Bite","damage":"2d-1 imp"},{"name":"Claw","damage":"1d+2 cut"}],
     "advantages":["Camouflage 3","Combat Reflexes","Fangs","Sharp Claws","Night Vision 5","Quadruped","Wild Animal"],
     "page":459},
    {"id":"shark","name_en":"Great White Shark","st":24,"dx":12,"iq":2,"ht":12,"hp":40,"will":11,"per":11,"speed":4.5,"move":10,
     "sm":+3,"dr":2,"attacks":[{"name":"Bite","damage":"4d+2 cut"}],
     "advantages":["Aquatic","Bad Sight","Doesn't Sleep","Quadruped (No Legs)","Discriminatory Smell","Sharp Teeth","Wild Animal"],
     "page":459},
    {"id":"crocodile","name_en":"Crocodile","st":15,"dx":10,"iq":3,"ht":12,"hp":15,"will":10,"per":11,"speed":4.5,"move":6,
     "sm":+1,"dr":4,"attacks":[{"name":"Bite","damage":"1d+1 cut"}],
     "advantages":["Amphibious","Constriction Attack (death roll)","DR 4 (scales)","Wild Animal"],
     "page":456},
    {"id":"snake_constrictor","name_en":"Constrictor Snake","st":11,"dx":13,"iq":3,"ht":12,"hp":11,"will":11,"per":11,"speed":6,"move":4,
     "sm":0,"dr":1,"attacks":[{"name":"Bite","damage":"1d-3 imp + Constriction"}],
     "advantages":["Constriction Attack","No Legs (Slithers)","Wild Animal"],
     "page":459},
    {"id":"snake_venomous","name_en":"Venomous Snake","st":7,"dx":13,"iq":3,"ht":12,"hp":7,"will":11,"per":11,"speed":5,"move":3,
     "sm":-2,"dr":0,"attacks":[{"name":"Bite","damage":"1d-5 imp + venom"}],
     "advantages":["No Legs (Slithers)","Venom (Toxic Attack)","Wild Animal"],
     "page":459},
    {"id":"giant_eagle","name_en":"Eagle","st":5,"dx":12,"iq":4,"ht":11,"hp":5,"will":10,"per":15,"speed":5.75,"move":7,
     "sm":-2,"dr":0,"attacks":[{"name":"Talons","damage":"1d-5 cut"}],
     "advantages":["Acute Vision 4","Flight (Winged)","Telescopic Vision 4","Wild Animal"],
     "page":457},
    {"id":"rat","name_en":"Rat","st":2,"dx":12,"iq":3,"ht":10,"hp":2,"will":10,"per":11,"speed":5.5,"move":5,
     "sm":-5,"dr":0,"attacks":[{"name":"Bite","damage":"1d-7 imp"}],
     "advantages":["Acute Smell 3","Night Vision 5","Quadruped","Sharp Teeth","Wild Animal"],
     "page":458},
    {"id":"elephant","name_en":"Elephant","st":35,"dx":9,"iq":5,"ht":12,"hp":50,"will":11,"per":12,"speed":5,"move":7,
     "sm":+3,"dr":2,"attacks":[{"name":"Trunk slam","damage":"4d+2 cr"},{"name":"Tusks","damage":"4d+2 imp"},{"name":"Trample","damage":"6d cr"}],
     "advantages":["DR 2","Extra Arms (Trunk)","Peripheral Vision","Quadruped","Wild Animal"],
     "page":457},

    # MONSTROS clássicos (samples adicionais; livro Magic e Bestiary têm mais)
    {"id":"goblin","name_en":"Goblin","st":8,"dx":11,"iq":10,"ht":10,"hp":8,"will":10,"per":10,"speed":5.25,"move":5,
     "sm":-1,"dr":0,"attacks":[{"name":"Short sword","damage":"1d-2 cut"}],
     "advantages":["Night Vision 5","Acute Hearing 2","Bestial","Bloodlust","Bully","Cowardice"],
     "page":460,"notes":"Goblinoide fantasy"},
    {"id":"orc","name_en":"Orc","st":12,"dx":10,"iq":9,"ht":12,"hp":12,"will":10,"per":10,"speed":5.5,"move":5,
     "sm":0,"dr":0,"attacks":[{"name":"Sword","damage":"2d cut"},{"name":"Bow","damage":"thr+1 imp"}],
     "advantages":["DR 0","High Pain Threshold","Bad Temper","Bully","Sadism","Social Stigma (Savage)"],
     "page":460},
    {"id":"troll","name_en":"Troll","st":17,"dx":10,"iq":8,"ht":13,"hp":22,"will":10,"per":10,"speed":5.75,"move":4,
     "sm":+1,"dr":2,"attacks":[{"name":"Claw","damage":"1d+3 cut"},{"name":"Bite","damage":"2d-1 imp"}],
     "advantages":["Claws","DR 2","Fangs","Regeneration (Fast: 1HP/min)","Vulnerability (Fire/Acid x4)","Bestial","Bully","Gluttony"],
     "page":460,"notes":"Trolls regeneram exceto contra fogo/ácido"},
    {"id":"skeleton","name_en":"Skeleton (Undead)","st":10,"dx":12,"iq":7,"ht":12,"hp":10,"will":12,"per":10,"speed":6,"move":6,
     "sm":0,"dr":2,"attacks":[{"name":"Sword","damage":"1d+1 cut"}],
     "advantages":["DR 2","Immunity to Metabolic Hazards","Injury Tolerance (Unliving + No Blood + No Brain + No Vitals)","Unaging","No Sense of Smell/Taste"],
     "page":461,"notes":"Undead clássico; vulnerável a holy"},
    {"id":"zombie","name_en":"Zombie","st":11,"dx":9,"iq":8,"ht":11,"hp":11,"will":10,"per":8,"speed":5,"move":3,
     "sm":0,"dr":0,"attacks":[{"name":"Punch","damage":"thr cr"},{"name":"Bite","damage":"1d-3 cr + Infectious Attack"}],
     "advantages":["Doesn't Eat","Doesn't Breathe","Immunity to Metabolic Hazards","Infectious Attack","Injury Tolerance (Unliving)","Reprogrammable"],
     "page":461},
    {"id":"vampire","name_en":"Vampire","st":18,"dx":14,"iq":12,"ht":14,"hp":18,"will":14,"per":12,"speed":7,"move":7,
     "sm":0,"dr":2,"attacks":[{"name":"Bite","damage":"Vampiric Bite (2 HP/sec drain)"},{"name":"Claw","damage":"1d+3 cut"}],
     "advantages":["Charisma 3","Claws","Damage Resistance 2","Dependency (Blood, weekly)","Detect (Living)","Doesn't Breathe","Doesn't Eat (except blood)","Hypnotic Gaze","Insubstantiality (mist form)","Night Vision 9","Regeneration (Fast)","Telescopic Vision","Unaging","Unkillable 2","Vampiric Bite"],
     "page":461,"notes":"Stoker-style; weak to sunlight, holy, stake-through-heart"},
    {"id":"dragon","name_en":"Dragon (young)","st":30,"dx":13,"iq":12,"ht":15,"hp":50,"will":15,"per":13,"speed":7,"move":10,
     "sm":+4,"dr":8,"attacks":[{"name":"Bite","damage":"6d+2 imp"},{"name":"Claw","damage":"3d+3 cut"},{"name":"Tail","damage":"4d+2 cr"},{"name":"Fire Breath","damage":"4d burn (Cone, RoF 1, 3/day)"}],
     "advantages":["Damage Resistance 8","Flight (Winged)","Long Talons","Sharp Teeth","Striker (Tail)","Innate Attack (Fire Breath)","Telescopic Vision","Magery 3","Greed","Sleepy"],
     "page":462,"notes":"Stats são pra young dragon; ancient dragons muito mais poderosos"},
]


# ========== TECHNOLOGY (cap 17 pp 127-150) ==========
# TL (Tech Level) reference + sample items
TECH_LEVELS = [
    {"tl":0,"name_en":"Stone Age","period":"Prehistory","examples":["stone tools","fire","language"],"page":511},
    {"tl":1,"name_en":"Bronze Age","period":"3500 BC","examples":["bronze","wheel","writing","agriculture"],"page":511},
    {"tl":2,"name_en":"Iron Age","period":"1200 BC","examples":["iron","alphabet","mathematics"],"page":511},
    {"tl":3,"name_en":"Medieval","period":"600 AD","examples":["plate armor","longbow","windmill","compass"],"page":511,"notes":"Default fantasy setting"},
    {"tl":4,"name_en":"Age of Sail","period":"1450","examples":["printing press","sailing ships","early firearms"],"page":511},
    {"tl":5,"name_en":"Industrial Revolution","period":"1730","examples":["steam engine","railroad","electricity"],"page":511},
    {"tl":6,"name_en":"Mechanized Age","period":"1880","examples":["telephone","car","radio","airplane (early)"],"page":511},
    {"tl":7,"name_en":"Nuclear Age","period":"1940","examples":["nuclear power","jet aircraft","computers (early)","television"],"page":511,"notes":"WWII era"},
    {"tl":8,"name_en":"Digital Age","period":"1980-now","examples":["smartphone","internet","biotech","drone","stealth aircraft"],"page":511,"notes":"Atual"},
    {"tl":9,"name_en":"Microtech","period":"~2050","examples":["nanotechnology","AGI","biotech transformation","fusion power"],"page":511,"notes":"Near-future SF"},
    {"tl":10,"name_en":"Robotics","period":"~2100","examples":["robotic labor","interplanetary colonization","cybernetic implants"],"page":511},
    {"tl":11,"name_en":"Age of Exotic Matter","period":"~2200","examples":["antimatter","gravity manipulation","FTL drives"],"page":511},
    {"tl":12,"name_en":"Singularity","period":"speculative","examples":["transcendence","reality manipulation","cosmic engineering"],"page":511,"notes":"Sci-fi maxed out"},
]

ARTIFACTS_SAMPLE = [
    # COMMUNICATIONS
    {"id":"radio_personal","name_en":"Personal Radio","tl":7,"category":"communication","range":"10 miles","cost":50,"weight":0.5,"page":511},
    {"id":"cell_phone","name_en":"Cell Phone","tl":8,"category":"communication","range":"network-based","cost":200,"weight":0.3,"page":511},
    {"id":"satellite_phone","name_en":"Satellite Phone","tl":8,"category":"communication","range":"global","cost":1500,"weight":1,"page":511},
    # SENSORS
    {"id":"binoculars","name_en":"Binoculars","tl":5,"category":"sensor","effect":"+2 Vision long range","cost":80,"weight":2,"page":511},
    {"id":"night_vision_goggles","name_en":"Night Vision Goggles","tl":7,"category":"sensor","effect":"Night Vision 5","cost":2000,"weight":1.5,"page":511},
    {"id":"thermal_imager","name_en":"Thermal Imager","tl":8,"category":"sensor","effect":"Infravision","cost":3500,"weight":2,"page":511},
    # MEDICAL
    {"id":"first_aid_kit","name_en":"First Aid Kit","tl":6,"category":"medical","effect":"+1 First Aid skill","cost":30,"weight":2,"page":511},
    {"id":"medical_kit_advanced","name_en":"Advanced Medical Kit","tl":8,"category":"medical","effect":"+2 First Aid, treat 3 patients","cost":300,"weight":5,"page":511},
    # VEHICLES (samples)
    {"id":"horse_wagon","name_en":"Horse-Drawn Wagon","tl":3,"category":"vehicle","speed":"5 mph","cost":300,"weight":500,"page":511},
    {"id":"sedan_car","name_en":"Sedan Car","tl":7,"category":"vehicle","speed":"80 mph","cost":20000,"weight":3500,"page":511},
    {"id":"motorcycle","name_en":"Motorcycle","tl":7,"category":"vehicle","speed":"100 mph","cost":10000,"weight":400,"page":511},
    {"id":"helicopter","name_en":"Helicopter","tl":7,"category":"vehicle","speed":"150 mph","cost":2000000,"weight":5000,"page":511},
    {"id":"jet_fighter","name_en":"Jet Fighter","tl":7,"category":"vehicle","speed":"1500 mph","cost":50000000,"weight":30000,"page":511},
    # COMPUTERS
    {"id":"laptop","name_en":"Laptop Computer","tl":8,"category":"computer","complexity":4,"cost":1500,"weight":3,"page":511},
    {"id":"smartphone","name_en":"Smartphone","tl":8,"category":"computer","complexity":3,"cost":600,"weight":0.3,"page":511},
    {"id":"mainframe","name_en":"Mainframe Computer","tl":7,"category":"computer","complexity":6,"cost":1000000,"weight":2000,"page":511},
    # COMMON GEAR
    {"id":"flashlight","name_en":"Flashlight","tl":6,"category":"misc","effect":"illumination","cost":20,"weight":1,"page":511},
    {"id":"rope_50ft","name_en":"Rope, 50ft","tl":1,"category":"misc","cost":10,"weight":5,"page":288},
    {"id":"backpack","name_en":"Backpack","tl":1,"category":"misc","capacity":"60 lbs","cost":30,"weight":3,"page":288},
    {"id":"lockpicks","name_en":"Lockpicks","tl":2,"category":"misc","effect":"+1 Lockpicking","cost":50,"weight":0.5,"page":288},
]


def main():
    bestiary = {
        "$schema_version": "1.0",
        "source": {"book":"GURPS 4e — Basic Set: Campaigns","chapter":16,"pages":"120-126","appendix":"pp 456-462"},
        "$progress": {"status":"core_samples","entries":len(ANIMALS),"completion_date":"2026-05-16",
                      "notes_pt":"Sample animais e monstros do Basic Set. GURPS Bestiary tem centenas mais. Cobre os mais comuns em adventures."},
        "entries": ANIMALS,
    }
    (DATA / "bestiary.json").write_text(json.dumps(bestiary, ensure_ascii=False, indent=2)+"\n", encoding='utf-8')

    technology = {
        "$schema_version": "1.0",
        "source": {"book":"GURPS 4e — Basic Set: Campaigns","chapter":17,"pages":"127-150"},
        "$progress": {"status":"core_samples","completion_date":"2026-05-16",
                      "notes_pt":"Tech Levels completos + sample artifacts. Listas exaustivas em GURPS Low-Tech / High-Tech / Ultra-Tech."},
        "tech_levels": TECH_LEVELS,
        "artifacts": ARTIFACTS_SAMPLE,
    }
    (DATA / "technology.json").write_text(json.dumps(technology, ensure_ascii=False, indent=2)+"\n", encoding='utf-8')

    print(f"bestiary: {len(ANIMALS)} entries, technology: {len(TECH_LEVELS)} TLs + {len(ARTIFACTS_SAMPLE)} artifacts")


if __name__ == "__main__":
    main()
