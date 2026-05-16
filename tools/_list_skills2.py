"""Lista skills do PDF — agora com regex correto: ATR/DIFICULDADE aparece ANTES do nome."""
import re, sys, io, json, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

txt = open('docs/gurps/_extracted_skills.txt', encoding='utf-8').read()
lines = txt.split('\n')

attr_diff = re.compile(r'^(DX|IQ|HT|ST|Per|Will)/(Easy|Average|Hard|Very Hard|E|A|H|VH)\s*$', re.IGNORECASE)
# Default line vem depois do nome
default_line = re.compile(r'^Defaults?:', re.IGNORECASE)

results = []
i = 0
while i < len(lines)-2:
    L = lines[i].strip()
    m = attr_diff.match(L)
    if m:
        atr = m.group(1).upper()
        diff = m.group(2).upper()
        # Próxima linha non-empty deve ser o nome
        j = i + 1
        while j < len(lines) and not lines[j].strip():
            j += 1
        if j < len(lines):
            name = lines[j].strip()
            # Verifica se default vem depois
            k = j + 1
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines) and default_line.match(lines[k].strip()):
                # Achou
                results.append({
                    "name": name,
                    "attribute": atr,
                    "difficulty": diff,
                })
        i = j + 1
    else:
        i += 1

# Dedupe
seen = set()
unique = []
for r in results:
    if r['name'] not in seen:
        seen.add(r['name'])
        unique.append(r)

print(f'TOTAL distinct skills: {len(unique)}')
for r in unique:
    print(f"  {r['name']:<35} {r['attribute']}/{r['difficulty']}")

pathlib.Path('docs/gurps/_skills_list.json').write_text(
    json.dumps(unique, indent=2, ensure_ascii=False), encoding='utf-8')
print(f'\nlista salva em _skills_list.json')
