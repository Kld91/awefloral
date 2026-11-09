# -*- coding: utf-8 -*-
"""assets/fg.json: which flowers each product has (from FG_IN in index.html) + each flower's name and photo,
so where.html can send a gift's recipient to the flower guide for what they received. Run on every build."""
import json, os, re, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
s = open(os.path.join(R, 'index.html'), encoding='utf-8').read()
fin = json.loads(re.search(r'const FG_IN = (\{.*?\});', s).group(1))
fg = {k: {'n': n, 'i': i} for k, n, i in re.findall(r"'([a-z-]+)':\{n:'([^']+)',m:'[^']*',i:'([^']+)'\}", s[s.find('const FG = {'):s.find('const FG_IN')])}
keys = [k for k in fg if os.path.exists(os.path.join(R, 'flowers', k + '.html'))]
out = {'in': {p: [k for k in v if k in keys] for p, v in fin.items()}, 'fg': {k: fg[k] for k in keys}}
json.dump(out, open(os.path.join(R, 'assets', 'fg.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('fg.json', len(out['in']), 'products,', len(out['fg']), 'flowers')

# assets/og.json: each product's name and photo, so a shared link (/?p=<id>) shows that product's picture, not the shop's default
gifts = json.loads(re.search(r'const GIFTS = (\[.*?\]);\n', s).group(1))
photos = json.loads(re.search(r'const PHOTOS = (\{.*?\});', s).group(1))
imgv = dict(re.findall(r"'(\d+)':(\d+)", re.search(r'const IMGV = (\{.*?\});', s).group(1)))
og = {}
for g in gifts:
    if str(g['id']) not in photos: continue
    v = imgv.get(str(g['id'])); og['g' + str(g['id'])] = [g['ar'], g.get('en') or g['ar'], '/img/p/%s-1.webp%s' % (g['id'], '?v=' + v if v else '')]
for pid, img in (('baby', '/img/p/baby-red-1.webp'), ('lily', '/img/p/lily-lwhite-1.webp')):
    m = re.search(r"\b%s: \{ id:'%s', name:'([^']+)', en:'([^']+)'" % (pid, pid), s)
    if m: og[pid] = [m.group(1), m.group(2), img]
json.dump(og, open(os.path.join(R, 'assets', 'og.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('og.json', len(og), 'products')
