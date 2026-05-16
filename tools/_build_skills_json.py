"""Constrói gurps/data/skills.json a partir da extração + cleanup."""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "docs" / "gurps" / "_skills_list.json"
TARGET = ROOT / "gurps" / "data" / "skills.json"

raw = json.loads(RAW.read_text(encoding='utf-8'))

# Blacklist de falsos positivos
BLACKLIST_PATTERNS = [
    r'^The\b', r'^Type:', r'^[A-Z]+$',  # all-caps
    r'both provide', r'^Acrobatics\b\s+(Defaults?|This)',  # frases partidas
    r'^A\s', r'^An?\s', r'^From\b', r'^If\b',
    r'^Modifiers?:', r'^Skill\s+',
    r'^Specialties?', r'^Default\b',
]

# Outros nomes ruins ou que são fragmentos
HARD_BLACKLIST = {
    "The", "Type", "Mathematical Ability both provide a",
    "Acrobatics", "However",  # se aparecem mas não como skill name limpo
    "Examples include", "Note that",
}

def is_clean_name(name):
    if name in HARD_BLACKLIST:
        return False
    for pat in BLACKLIST_PATTERNS:
        if re.match(pat, name):
            return False
    # Tem que parecer nome de skill (palavras com inicial maiúscula)
    words = name.split()
    if len(words) > 5:
        return False
    # Primeira palavra maiúscula
    if not name[0].isupper():
        return False
    return True

# Normaliza names — limpa † e /TL (vira metadata)
def clean(entry):
    name = entry['name']
    has_tl = '/TL' in name
    has_spec = '†' in name  # marcador de especialização do livro
    name_clean = re.sub(r'/TL†?$', '', name).rstrip('†').strip()

    return {
        "id": re.sub(r'[^a-z0-9]+', '_', name_clean.lower()).strip('_'),
        "name_en": name_clean,
        "controlling_attribute": entry['attribute'],
        "difficulty": entry['difficulty'],
        "page_ref": entry['page'],
        "tl_dependent": has_tl,
        "requires_specialty": has_spec,
        "detail_level": "list_only",  # lista a partir do livro; descrições virão depois sob demanda
    }

# Filtra e converte
clean_entries = []
seen_ids = set()
for e in raw:
    if not is_clean_name(e['name']):
        continue
    c = clean(e)
    if c['id'] in seen_ids:
        continue
    seen_ids.add(c['id'])
    clean_entries.append(c)

# Sort por nome
clean_entries.sort(key=lambda x: x['name_en'])

out = {
    "$schema_version": "1.0",
    "source": {
        "book": "GURPS 4e — Basic Set: Characters",
        "chapter": 4,
        "pages": "167-233",
        "edition": "Fourth Edition"
    },
    "$progress": {
        "status": "list_extracted",
        "completion_date": "2026-05-16",
        "entries_in_file": len(clean_entries),
        "notes_pt": "Lista extraída via regex do PDF. Cada entry tem name/attribute/difficulty/page mas SEM descrições nem defaults — esses serão preenchidos sob demanda quando features necessitarem (autocomplete na ficha, validação). detail_level='list_only' indica isso.",
    },
    "$schema_notes": {
        "tl_dependent": "Skill tem variantes por TL (Tech Level)",
        "requires_specialty": "Skill exige escolha de especialização (marcador † no livro)",
        "detail_level": "'list_only' = só metadata básica; 'full' = inclui defaults + descrição"
    },
    "entries": clean_entries,
}
TARGET.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding='utf-8')
print(f"TOTAL: {len(clean_entries)} skills em skills.json")
