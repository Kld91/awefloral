"""Holland colours: the supplier's colour field is sometimes wrong (Ranunculus "Dark Pink" filed as orange).
When the variety name itself says a colour and the field says another, the name wins. Run after build_holland*.
usage: python3 _i18n/fix_colours.py SITE_DIR"""
import json, re, sys, glob
R = sys.argv[1]
WORDS = [('hot pink', 'hot pink'), ('dark pink', 'dark pink'), ('light pink', 'light pink'), ('pink', 'pink'), ('white', 'white'), ('red', 'red'),
         ('yellow', 'yellow'), ('orange', 'orange'), ('purple', 'purple'), ('lilac', 'lilac'), ('lavender', 'lavender'), ('peach', 'peach'),
         ('cream', 'cream'), ('green', 'green'), ('blue', 'blue'), ('salmon', 'salmon'), ('burgundy', 'burgundy'), ('cerise', 'cerise')]
FAM = {'hot pink': 'pink', 'dark pink': 'pink', 'light pink': 'pink', 'cerise': 'pink', 'lavender': 'lilac'}
SKIP = re.compile(r'kaaps|roze|ice cream|rood|bordeaux|ruby|baby blue|mix|splash|hart|heart|bicol|two ?tone|edge|eye|centre|center|stripe|/|\+|lilac \(syringa|lavend|preserved|dried|dyed|bleached|frost|glit', re.I)
def said(n):
    if SKIP.search(n): return ''
    # only a colour that closes the name ("… Dark Pink Extra", "… White 60cm"): inside a name it is often part of the variety
    l = ' ' + re.sub(r'\s+(extra|select|premium|special|super|xl|\d+\s*cm|\d+)\b.*$', '', n.lower().replace('-', ' ')) + ' '
    if not any(l.rstrip().endswith(' ' + w) for w, _ in WORDS): return ''
    found = []
    for w, c in WORDS:
        if re.search(r'\s' + w + r'\s', l) and not any(w in x for x in found): found.append(w)
    fam = {FAM.get(w, w) for w in found}
    return dict(WORDS)[found[0]] if len(fam) == 1 else ''
tot = 0
for f in ['holland.json'] + sorted(glob.glob('holland-all/*.json')):
    p = R + '/' + f; d = json.load(open(p, encoding='utf-8')); n = 0
    for it in d.get('items', []):
        s = said(it.get('n', '')); c = (it.get('c') or '').lower()
        if s and c and c not in ('mixed', 'various colours', 'bicolour', 'bicolor') and s != c and FAM.get(s, s) != FAM.get(c, c): it['c'] = s; n += 1
    if n: json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    tot += n; print(f, n)
print('fixed', tot)
