"""Product pages (ward/*.html) take their ingredient list from the shop's product record (GIFTS in index.html),
so the page a search lands on and the product sheet always say the same. usage: python3 _i18n/sync_ward_specs.py SITE_DIR"""
import json, re, sys, glob, html
R = sys.argv[1]
idx = open(R + '/index.html', encoding='utf-8').read()
G = json.loads(re.search(r'const GIFTS = (\[.*?\]);\n', idx, re.S).group(1))
D = {str(g['id']): g.get('d', '') for g in G}
ch = 0
for f in sorted(glob.glob(R + '/ward/*.html')):
    s = open(f, encoding='utf-8').read()
    m = re.search(r'"sku": "(\d+)"', s); sp = re.search(r'<p class="spec">تتكون من: (.*?)</p>', s)
    if not m or not sp or not D.get(m.group(1)): continue
    old, new = html.unescape(sp.group(1)), D[m.group(1)]
    if old == new: continue
    s2 = s.replace(sp.group(1), html.escape(new, quote=False)).replace(old, new)
    open(f, 'w', encoding='utf-8').write(s2); ch += 1; print(f.split('/')[-1], '|', old, '→', new)
print('pages updated', ch)
