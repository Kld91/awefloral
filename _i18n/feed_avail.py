# -*- coding: utf-8 -*-
"""Product feed follows the dashboard's «التوفر» switches: products switched off show as out_of_stock in
merchant-feed.xml (Google Merchant Center and the Instagram catalog read this file), and in_stock again when switched on.
Run: python3 _i18n/feed_avail.py .   (reads the public list at the dashboard worker's /avail; a file path instead of the URL works for tests)"""
import json, os, re, sys, urllib.request
R = sys.argv[1] if len(sys.argv) > 1 else '.'
SRC = sys.argv[2] if len(sys.argv) > 2 else 'https://awe-dashboard.le77en.workers.dev/avail'
if SRC.startswith('https://'):
    req = urllib.request.Request(SRC, headers={'user-agent': 'awefloral-feed-sync', 'cache-control': 'no-cache'})
    data = json.load(urllib.request.urlopen(req, timeout=25))
else:
    data = json.load(open(SRC, encoding='utf-8'))
off = data.get('off')
if not isinstance(off, list): print('no list from the dashboard; feed left as it is'); sys.exit(0)   # exit 0: the product/price sync steps after this still run
off = set(off)

def is_off(gid):
    m = re.match(r'^(baby|lily)-([a-z]+)$', gid)
    if m: return m[1] in off or f'{m[1]}:{m[2]}' in off   # the whole product, or that colour
    return ('g' + gid) in off

# products kept in stock in the feed (Instagram / Google ads) even while closed on the site (manager's choice):
# _i18n/feed_keep_on.json = ["20750583", ...]; the site's own switch and the product pages still follow the dashboard
KEEP = set()
try: KEEP = set(map(str, json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'feed_keep_on.json')))))
except Exception: pass
_is_off = is_off
is_off = lambda gid: gid not in KEEP and _is_off(gid)

fp = os.path.join(R, 'merchant-feed.xml')
x = open(fp, encoding='utf-8').read()
ITEM = re.compile(r'<item>.*?</item>', re.S)
ids = [re.search(r'<g:id>([^<]+)</g:id>', it).group(1) for it in ITEM.findall(x)]
n_off = sum(is_off(g) for g in ids)
if ids and n_off > 0.8 * len(ids):   # safety: a broken list must not empty the shop on Google and Instagram
    print(f'safety stop: {n_off} of {len(ids)} products would go out of stock; feed left as it is'); sys.exit(0)

def fix(m):
    it = m.group(0); gid = re.search(r'<g:id>([^<]+)</g:id>', it).group(1)
    return re.sub(r'<g:availability>[^<]*</g:availability>', f'<g:availability>{"out_of_stock" if is_off(gid) else "in_stock"}</g:availability>', it)
x2 = ITEM.sub(fix, x)
if x2 != x:
    open(fp, 'w', encoding='utf-8').write(x2)
print(f'feed: {len(ids) - n_off} in stock, {n_off} out of stock' + (' (updated)' if x2 != x else ' (no change)'))

# product pages (ward/ and en/ward/): the schema.org Offer follows the same switches, so search shows "out of stock" too
import glob
PG = re.compile(r'data-pid="(g\d+|baby|lily)"')
# baby rose / lily: out of stock when the product is off or every one of its colours is off
COLS = {k: [g for g in ids if g.startswith(k + '-')] for k in ('baby', 'lily')}
pg_off = lambda pid: (pid in off or (bool(COLS[pid]) and all(f'{pid}:{g.split("-", 1)[1]}' in off for g in COLS[pid]))) if pid in COLS else pid in off
nw = 0
for f in glob.glob(os.path.join(R, 'ward', '*.html')) + glob.glob(os.path.join(R, 'en', 'ward', '*.html')):
    h = open(f, encoding='utf-8').read(); m = PG.search(h)
    if not m: continue
    av = 'https://schema.org/' + ('OutOfStock' if pg_off(m.group(1)) else 'InStock')
    h2 = re.sub(r'"availability": *"https://schema\.org/\w+"', '"availability": "' + av + '"', h)
    if h2 != h: open(f, 'w', encoding='utf-8').write(h2); nw += 1
print(f'product pages: {nw} updated')
