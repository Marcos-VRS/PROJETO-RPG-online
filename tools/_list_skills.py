import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

txt = open('docs/gurps/_extracted_skills.txt', encoding='utf-8').read()
lines = txt.split('\n')
matches = []
# Skill header: "Skill Name" + linha com "DX/E" "IQ/A" etc. ou "see X"
attr_diff = re.compile(r'^(DX|IQ|HT|ST|Per|Will)/(E|A|H|VH)\b')
see_other = re.compile(r'^see\s+\w')
for i in range(len(lines)-1):
    L1 = lines[i].strip()
    L2 = lines[i+1].strip()
    if not L1 or 'BOOK PAGE' in L1 or 'SKILL' in L1 or 'CHAPTER' in L1:
        continue
    # Nome geralmente 1-5 palavras, capitalizado, sem pontuação
    words = L1.split()
    if 1 <= len(words) <= 6 and all(w[0].isupper() or w in ('the','of','and','to','a','in','on','with') for w in words):
        if attr_diff.match(L2) or see_other.match(L2):
            matches.append((L1, L2))

seen = set()
for n, t in matches:
    if n not in seen:
        print(f'{n:<40} | {t}')
        seen.add(n)
print(f'\nTOTAL distinct skills: {len(seen)}')
