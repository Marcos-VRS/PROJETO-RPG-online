"""Extrai spells do PDF + monta gurps/data/spells.json."""
import re, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "gurps" / "data" / "spells.json"

txt = (ROOT / "docs" / "gurps" / "_extracted_magic.txt").read_text(encoding='utf-8')
lines = txt.split('\n')

spell_class_re = re.compile(r'^(Regular|Area|Missile|Information|Special|Blocking|Resisted)(\s*\(VH\))?\s*$')

# Identifica colégio corrente baseado em headers no texto
college_headers = {
    'Air Spells': 'Air',
    'Body Control Spells': 'Body Control',
    'Communication and Empathy Spells': 'Communication and Empathy',
    'Earth Spells': 'Earth',
    'Enchantment Spells': 'Enchantment',
    'Fire Spells': 'Fire',
    'Gate Spells': 'Gate',
    'Healing Spells': 'Healing',
    'Knowledge Spells': 'Knowledge',
    'Light and Darkness Spells': 'Light and Darkness',
    'Meta-Spells': 'Meta',
    'Mind Control Spells': 'Mind Control',
    'Movement Spells': 'Movement',
    'Necromantic Spells': 'Necromantic',
    'Protection and Warning Spells': 'Protection and Warning',
    'Water Spells': 'Water',
}

current_college = None
current_page = None
spells = []

for i, line in enumerate(lines):
    pm = re.match(r'^=+ BOOK PAGE (\d+) =+', line)
    if pm:
        current_page = int(pm.group(1))
        continue
    L = line.strip()
    # College header
    for key, val in college_headers.items():
        if L == key or L.replace('  ', ' ') == key:
            current_college = val
            break
    # Spell entry
    if i+1 < len(lines):
        L1 = L
        L2 = lines[i+1].strip()
        m = spell_class_re.match(L2)
        if m and L1 and 1 <= len(L1.split()) <= 4 and L1[0].isupper() and not L1.endswith('.') and ':' not in L1:
            if not re.match(r'^(College|Class|Type|This|These|Spell)\s', L1):
                spell_class = m.group(1)
                very_hard = bool(m.group(2))
                spells.append({
                    "id": re.sub(r'[^a-z0-9]+', '_', L1.lower()).strip('_'),
                    "name_en": L1,
                    "college": current_college or "Unknown",
                    "class": spell_class,
                    "difficulty": "Very Hard" if very_hard else "Hard",  # default IQ/Hard, (VH) marker
                    "controlling_attribute": "IQ",
                    "page_ref": current_page,
                    "detail_level": "list_only",
                })

# Dedupe by id
seen = set()
unique = []
for s in spells:
    if s['id'] not in seen:
        seen.add(s['id'])
        unique.append(s)

unique.sort(key=lambda x: (x['college'], x['name_en']))

out = {
    "$schema_version": "1.0",
    "source": {
        "book": "GURPS 4e — Basic Set: Characters",
        "chapter": 5,
        "pages": "234-253",
        "edition": "Fourth Edition"
    },
    "$progress": {
        "status": "list_extracted",
        "completion_date": "2026-05-16",
        "entries_in_file": len(unique),
        "notes_pt": "93 spells do Basic Set por colégio. Metadata: name/college/class/difficulty/page. Description/duration/cost/time/prereqs serão preenchidos sob demanda. Sistema completo em GURPS Magic supplement.",
    },
    "$schema_notes": {
        "class_values": ["Regular","Area","Missile","Information","Special","Blocking","Resisted"],
        "default_difficulty": "Hard (IQ/Hard) — (VH) marca Very Hard"
    },
    "entries": unique,
}
TARGET.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
print(f"TOTAL: {len(unique)} spells em spells.json")
