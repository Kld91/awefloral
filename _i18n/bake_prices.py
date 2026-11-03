"""Write the final selling prices into the published data files, so the margins never travel to the browser.
The multipliers (dashboard Prices tab) live outside the repo: python3 _i18n/bake_prices.py SITE_DIR /path/to/price_mul.json
Files done once carry "pb": 1 (parts: "_pb": 1) and are skipped next time; a fresh build writes base prices again.
Rounding is the order system's: up to the next 0.05. Our own stock keeps its listed price."""
import json, math, os, sys, glob, re
R, MF = sys.argv[1], sys.argv[2]
M = {k: float(v) for k, v in json.load(open(MF)).items()}
NL_B = {'مميز من هولندا', 'أوركيد واستوائي', 'بروتيا وجنوب أفريقيا', 'أغصان وتوت زينة', 'مجففات'}
adj = lambda p, k: p if not k or k == 1 else round(math.ceil(p * k / 0.05 - 1e-9) * 0.05, 2)
BOX = re.compile(r'\b(p\.? ?box|per box)\b', re.I)
def items(path, kfn, sep=(',', ':')):
    d = json.load(open(path, encoding='utf-8'))
    if d.get('pb'): return 'skip'
    n = 0
    for it in d.get('items', []):
        k = kfn(it)
        for f in ('p1', 'p2'):
            if it.get(f): it[f] = adj(float(it[f]), k)
        if BOX.search(it.get('n', '')) and int(it.get('s') or 1) == 1 and not it.get('u'): it['u'] = 'box'   # priced per box, say so
        n += 1
    d['pb'] = 1
    json.dump(d, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=sep)
    return n
print('catalog', items(R + '/catalog.json', lambda it: 1 if it.get('sb') == 'own' else M['bn']))
nl = lambda it: M['b'] if it.get('g') in NL_B else M['a']
print('holland', items(R + '/holland.json', nl))
for f in sorted(glob.glob(R + '/holland-all/*.json')): print(os.path.basename(f), items(f, nl))
for f in sorted(glob.glob(R + '/holland-all/p/*.json')):
    d = json.load(open(f, encoding='utf-8'))
    if d.get('_pb'): continue
    for k, a in d.items():
        if isinstance(a, list) and len(a) > 6:
            m = M['b'] if a[6] == 'b' else M['a']; a[0] = adj(float(a[0]), m); a[1] = adj(float(a[1] or a[0]), m)
    d['_pb'] = 1
    json.dump(d, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('parts done')
