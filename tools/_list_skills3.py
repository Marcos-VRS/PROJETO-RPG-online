"""Extração mais robusta de skills."""
import re, sys, io, json, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

txt = open('docs/gurps/_extracted_skills.txt', encoding='utf-8').read()
lines = txt.split('\n')

# Procura por "X/Y" onde X é attr e Y é difficulty (em qualquer linha)
attr_diff_inline = re.compile(r'\b(DX|IQ|HT|ST|Per|Will)/(Easy|Average|Hard|Very Hard)\b')

# Estratégia: achar todas ocorrências de attr/diff e ver qual é o nome do skill mais próximo
results = []
current_page = None
for i, line in enumerate(lines):
    m = re.match(r'^=+ BOOK PAGE (\d+) =+', line)
    if m:
        current_page = int(m.group(1))
        continue
    # match attr/diff inline
    matches = list(attr_diff_inline.finditer(line))
    for mat in matches:
        atr = mat.group(1)
        diff = mat.group(2)
        # nome do skill: vê linhas anteriores até achar linha curta, capitalized, sem 'Default'
        # Pode estar 1-3 linhas atrás
        for back in range(1, 8):
            if i-back < 0: break
            cand = lines[i-back].strip()
            if not cand: continue
            if 'Default' in cand or 'BOOK PAGE' in cand: continue
            words = cand.split()
            # Heurística: 1-6 palavras, primeira cap, não termina com . , ; :
            if 1 <= len(words) <= 6 and cand[0].isupper() and cand[-1] not in '.,;:!?':
                # Aceita
                results.append({
                    "name": cand,
                    "attribute": atr,
                    "difficulty": diff,
                    "page": current_page,
                })
                break

# Dedupe
seen = set()
unique = []
for r in results:
    if r['name'] not in seen and not re.match(r'^[A-Z]+$', r['name']):  # ignore all-caps headers
        seen.add(r['name'])
        unique.append(r)

print(f'TOTAL distinct skills: {len(unique)}')
pathlib.Path('docs/gurps/_skills_list.json').write_text(
    json.dumps(unique, indent=2, ensure_ascii=False), encoding='utf-8')
print('lista salva')
