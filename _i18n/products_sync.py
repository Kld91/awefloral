# -*- coding: utf-8 -*-
"""Products follow the dashboard's editor («تعديل المنتجات»): names, descriptions, section, price, struck price and photo
are written into index.html (GIFTS, the baby / lily lines, PHOTOS), new products are added, and their photos are saved
to img/p/<code>-1.webp (1200x900) and -1s.webp (480x360). English names and descriptions go into the translations.
After it: python3 _i18n/prices.py . --fix && python3 _i18n/build_en.py .   (the hourly job runs all three)
usage: python3 _i18n/products_sync.py [SITE_DIR] [SOURCE]   SOURCE = the dashboard URL (default) or a JSON file for tests
prints "changed" when index.html or a photo changed."""
import io, json, os, re, sys, subprocess, urllib.request
R = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
API = 'https://awe-dashboard.le77en.workers.dev'
SRC = sys.argv[2] if len(sys.argv) > 2 else API + '/catalog/ed'
HERE = os.path.dirname(os.path.abspath(__file__))
CATS = set('ABVSRHLFC')
APPLIED = os.path.join(HERE, 'products_applied.json')   # code -> photo id already saved, so photos are fetched once


def get(url, raw=False):
    req = urllib.request.Request(url, headers={'user-agent': 'awefloral-products-sync', 'cache-control': 'no-cache'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read() if raw else json.load(r)


def load_ed():
    if SRC.startswith('https://'): return (get(SRC) or {}).get('ed') or {}
    return (json.load(open(SRC, encoding='utf-8')) or {}).get('ed') or {}


def photo(code, img_id):
    """Save the dashboard photo as the product's main photo (cover-cropped 4:3, as the other product photos)."""
    from PIL import Image
    if SRC.startswith('https://'): data = get(API + '/catalog/img?id=' + img_id, raw=True)
    else: data = open(os.path.join(os.path.dirname(SRC), img_id), 'rb').read()   # tests: the photo file sits next to the JSON
    im = Image.open(io.BytesIO(data)).convert('RGB')
    for name, (W, H), q in (('-1.webp', (1200, 900), 82), ('-1s.webp', (480, 360), 78)):
        k = max(W / im.width, H / im.height)
        t = im.resize((max(W, round(im.width * k)), max(H, round(im.height * k))), Image.LANCZOS)
        x, y = (t.width - W) // 2, (t.height - H) // 2
        t.crop((x, y, x + W, y + H)).save(os.path.join(R, 'img', 'p', code + name), 'WEBP', quality=q, method=6)


def num(v):
    v = round(float(v), 2)
    return int(v) if v == int(v) else v


def run():
    ed = load_ed()
    if not isinstance(ed, dict): sys.exit('no edits from the dashboard; nothing changed')
    fp = os.path.join(R, 'index.html'); html = open(fp, encoding='utf-8').read(); before = html
    m = re.search(r'const GIFTS = (\[[\s\S]*?\]);\s*\n', html)
    gifts = json.loads(m.group(1)); by = {str(g['id']): g for g in gifts}
    pm = re.search(r'const PHOTOS = (\{[^\n]*?\});', html); photos = json.loads(pm.group(1))
    applied = json.load(open(APPLIED)) if os.path.exists(APPLIED) else {}
    pairs, pics = {}, 0
    for code, e in sorted(ed.items()):
        if not isinstance(e, dict) or not re.fullmatch(r'\d{4,12}|baby|lily', code): continue
        if code in ('baby', 'lily'):   # the colour products: name and prices on their own line in PRODUCTS
            def line(mm):
                t = mm.group(0)
                if e.get('ar'): t = re.sub(r"name:'[^']*'", "name:'" + e['ar'].replace("'", '’') + "'", t, count=1)
                if e.get('en'): t = re.sub(r"en:'[^']*'", "en:'" + e['en'].replace("'", '’') + "'", t, count=1)
                if e.get('p'): t = re.sub(r'price:\s*[\d.]+', 'price:' + str(num(e['p'])), t, count=1)
                if 'w' in e:
                    if re.search(r'was:\s*[\d.]+', t): t = re.sub(r'was:\s*[\d.]+', 'was:' + str(num(e['w'] or 0)), t, count=1)
                return t
            html = re.sub(r"\n\s*" + code + r":\s*\{\s*id:'" + code + r"',[^\n]*", line, html, count=1)
            continue
        g = by.get(code)
        if g is None:
            if not e.get('n') or not e.get('ar') or not e.get('p') or e.get('c') not in CATS: continue
            g = {'id': code, 'c': e['c'], 'en': e.get('en') or e['ar'], 'ar': e['ar'], 'p': num(e['p']), 'i': '', 'd': e.get('d', ''), 'w': num(e.get('w') or 0)}
            sub = next((i for i, x in enumerate(gifts) if x.get('c') == 'Z'), len(gifts))   # new products go before the subscription entry
            gifts.insert(sub, g); by[code] = g
        for k in ('ar', 'en', 'd'):
            if e.get(k): g[k] = e[k]
        if e.get('c') in CATS: g['c'] = e['c']
        if e.get('p'): g['p'] = num(e['p'])
        if 'w' in e: g['w'] = num(e['w'] or 0)
        if e.get('img') and applied.get(code) != e['img']:
            try:
                photo(code, e['img']); applied[code] = e['img']; pics += 1
                photos[code] = max(1, int(photos.get(code, 0) or 0))
            except Exception as err:
                print('photo failed', code, err)
        if e.get('en') and e.get('ar'): pairs[e['ar']] = e['en']
        if e.get('de') and e.get('d'): pairs[e['d']] = e['de']
    html = html[:m.start(1)] + json.dumps(gifts, ensure_ascii=False, separators=(',', ':')) + html[m.end(1):]
    pm = re.search(r'const PHOTOS = (\{[^\n]*?\});', html)
    html = html[:pm.start(1)] + json.dumps(photos, ensure_ascii=False, separators=(',', ':')) + html[pm.end(1):]
    if html != before: open(fp, 'w', encoding='utf-8').write(html)
    json.dump(applied, open(APPLIED, 'w'), separators=(',', ':'), sort_keys=True)
    if pairs:
        pf = os.path.join(HERE, '_pairs_products.json'); json.dump(pairs, open(pf, 'w', encoding='utf-8'), ensure_ascii=False)
        subprocess.run([sys.executable, os.path.join(HERE, 'add_tr.py'), R, pf], check=True, stdout=subprocess.DEVNULL); os.remove(pf)
    print(f'products: {len(ed)} edits, {pics} new photos')
    if html != before or pics: print('changed')


if __name__ == '__main__':
    run()
