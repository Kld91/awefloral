"""Gift prices on every static page come from one place: the GIFTS list and the baby / lily products in index.html.

    python3 _i18n/prices.py .            check: lists every page whose price differs from index.html (exit 1 if any)
    python3 _i18n/prices.py . --fix      rewrite them, then run build_en.py

It covers product cards, product pages (shown price, data-price, JSON-LD, title and meta), the "or order it ready-made"
boxes and cards on the styling pages, "from N" on list pages (lowest card price), the flower-food line and the
Google Merchant feed (price, plus sale_price when there is a struck old price).
Prices are drawn the same way as in the shop: discount %, new price, struck old price, Saudi riyal sign."""
import re, os, sys, json, glob

R = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else '.'
FIX = '--fix' in sys.argv
SITE = 'https://www.awefloral.com'

# ---------- the source: index.html ----------
idx = open(os.path.join(R, 'index.html'), encoding='utf-8').read()
G = json.loads(re.search(r'const GIFTS = (\[[\s\S]*?\]);\s*\n', idx).group(1))
PRICE = {g['id']: (float(g['p']), float(g.get('w') or 0)) for g in G}
for k in ('baby', 'lily'):
    m = re.search(r"\n\s*" + k + r":\s*\{\s*id:'" + k + r"',[^\n]*?price:\s*(\d+(?:\.\d+)?)(?:, was:\s*(\d+(?:\.\d+)?))?,", idx)
    PRICE[k] = (float(m.group(1)), float(m.group(2) or 0))
FOOD = float(re.search(r"const FOOD = \{[^}]*price:\s*(\d+(?:\.\d+)?)", idx).group(1))

def fmt(n):
    v = round(float(n) + 1e-9, 2)
    return str(int(v)) if v == int(v) else f'{v:.2f}'
def sar(lang): return f'<i class="sar" role="img" aria-label="{"SAR" if lang == "en" else "ر.س"}"></i>'
def mny(n, lang): return f'<span class="mny">{sar(lang)}<span class="num">{fmt(n)}</span></span>'
def price_h(p, w, lang):
    off = round((1 - p / w) * 100) if w and w > p else 0
    return (f'<b class="off num">{off}%</b>' if off else '') + mny(p, lang) + (f'<s class="was">{mny(w, lang)}</s>' if off else '')

MNY_RE = r'<span class="mny"><i class="sar"[^>]*></i><span class="num">[\d.]+</span></span>'
PRICEH_RE = r'(?:<b class="off num">\d+%</b>)?' + MNY_RE + r'(?:<s class="was">' + MNY_RE + r'</s>)?'
OLD_TXT = r'<span class="num">[\d.]+</span> (?:ر\.س|SAR)|[\d.]+ (?:ر\.س|SAR)'   # plain text prices still waiting for the sign

# ---------- product page slug → product key ----------
SLUG = {}
for f in glob.glob(os.path.join(R, 'ward', '*.html')):
    m = re.search(r'data-pid="([^"]+)"[^>]*data-code="([^"]+)"', open(f, encoding='utf-8').read())
    if m: SLUG[os.path.basename(f)[:-5]] = m.group(2) if m.group(1).startswith('g') else m.group(1)
def of_slug(slug):
    k = SLUG.get(slug); return PRICE.get(k) if k else None

# styling page → the ready-made product it offers
READY = {}
for f in glob.glob(os.path.join(R, 'styling', '*.html')):
    m = re.search(r'<a class="sty-ready" href="/ward/([a-z0-9-]+)\.html"', open(f, encoding='utf-8').read())
    if m: READY[os.path.basename(f)[:-5]] = m.group(1)

def lang_of(s): return 'en' if re.search(r'<html lang="en"', s) else 'ar'

def reprice(s, rel):
    lang = lang_of(s)
    lows = []
    # 1. product cards
    def card(m):
        x = of_slug(m.group(2))
        if not x: return m.group(0)
        lows.append(x[0])
        return f'{m.group(1)}<span class="pr">{price_h(x[0], x[1], lang)}</span></a>'
    s = re.sub(r'(<a class="card" href="(?:/en)?/ward/([a-z0-9-]+)\.html(?:\?c=[a-z]+)?">(?:(?!</a>).)*?)<span class="pr(?: num)?">(?:' + PRICEH_RE + r'|[\d.]+ (?:ر\.س|SAR))</span></a>', card, s, flags=re.S)
    # 2. styling: "or order it ready-made" box
    def ready(m):
        x = of_slug(m.group(2))
        return f'{m.group(1)}<b class="pr">{price_h(x[0], x[1], lang)}</b>' if x else m.group(0)
    s = re.sub(r'(<a class="sty-ready" href="(?:/en)?/ward/([a-z0-9-]+)\.html">(?:(?!</a>).)*?)<b class="pr">' + PRICEH_RE + '</b>', ready, s, flags=re.S)
    # 3. styling cards: "ready-made N"
    def sty(m):
        x = of_slug(READY.get(m.group(2), ''))
        return f'{m.group(1)}{mny(x[0], lang)}' if x else m.group(0)
    s = re.sub(r'(<a class="sty-card" href="(?:/en)?/styling/([a-z0-9-]+)\.html">(?:(?!</a>).)*?(?:جاهز|Ready-made) )(?:' + MNY_RE + '|' + OLD_TXT + ')', sty, s, flags=re.S)
    # 4. product page
    m = re.search(r'<article class="product" data-pid="([^"]+)"[^>]*data-price="([\d.]+)"[^>]*data-code="([^"]+)"', s)
    if m:
        x = PRICE.get(m.group(3) if m.group(1).startswith('g') else m.group(1))
        if x:
            old = fmt(m.group(2))
            s = s.replace(m.group(0), m.group(0).replace(f'data-price="{m.group(2)}"', f'data-price="{fmt(x[0])}"'), 1)
            s = re.sub(r'<p class="price">(?:' + PRICEH_RE + r'|[\d.]+ ر\.س)', f'<p class="price">{price_h(x[0], x[1], lang)}', s, count=1)
            s = re.sub(r'("@type": "Offer"[^}]*?"price": ")[\d.]+(")', lambda q: f'{q.group(1)}{x[0]:.2f}{q.group(2)}', s)
            head, sep, body = s.partition('</head>')
            head = re.sub(r'(?<![\d.])' + re.escape(old) + r' (ر\.س|SAR)', lambda q: f'{fmt(x[0])} {q.group(1)}', head)
            s = head + sep + body
    # 5. flower food on product pages
    s = re.sub(r'<span(?: class="num")?>إضافة بـ (?:' + MNY_RE + r'|[\d.]+ ر\.س)</span>', f'<span>إضافة بـ {mny(FOOD, lang)}</span>', s)
    # 6. list pages: "from N" = the lowest card price
    if lows and 'class="pagehead' in s:
        lo = min(lows)
        def intro(q):
            return re.sub(r'من (?:' + MNY_RE + r'|[\d.]+ ر\.س)', f'من {mny(lo, lang)}', q.group(0))
        s = re.sub(r'<div class="pagehead[^"]*"><h1>.*?</h1><p>.*?</p>', intro, s, count=1, flags=re.S)
        head, sep, body = s.partition('</head>')
        head = re.sub(r'(<meta (?:name|property)="(?:description|og:description|twitter:description)" content="[^"]*?)من [\d.]+ ر\.س', lambda q: f'{q.group(1)}من {fmt(lo)} ر.س', head)
        s = head + sep + body
    return s

def feed(x):
    def item(m):
        gid = m.group(1); k = gid.split('-')[0] if gid.split('-')[0] in ('baby', 'lily') else gid
        v = PRICE.get(k)
        if not v: return m.group(0)
        it = re.sub(r'<g:sale_price>[^<]*</g:sale_price>', '', m.group(0))
        p, w = v
        tag = f'<g:price>{w:.2f} SAR</g:price><g:sale_price>{p:.2f} SAR</g:sale_price>' if w > p else f'<g:price>{p:.2f} SAR</g:price>'
        return re.sub(r'<g:price>[^<]*</g:price>', tag, it)
    return re.sub(r'<item><g:id>([^<]+)</g:id>.*?</item>', item, x, flags=re.S)

pages = [f for f in glob.glob(os.path.join(R, '*.html')) + glob.glob(os.path.join(R, '*', '*.html')) + glob.glob(os.path.join(R, 'en', '*', '*.html'))
         if os.path.relpath(f, R) not in ('index.html', 'index1.html', 'bunches.html', 'holland.html', 'track.html') and '/_i18n/' not in f]
# English product and list pages are rebuilt from the Arabic ones; only the English guide and styling pages are kept by hand
pages = [f for f in pages if '/en/' not in f.replace(os.path.abspath(R), '') or re.search(r'/en/(flowers|styling)/', f)]
diff = []
for f in sorted(pages):
    s = open(f, encoding='utf-8').read(); s2 = reprice(s, f)
    if s2 != s:
        diff.append(os.path.relpath(f, R))
        if FIX: open(f, 'w', encoding='utf-8').write(s2)
fp = os.path.join(R, 'merchant-feed.xml')
x = open(fp, encoding='utf-8').read(); x2 = feed(x)
if x2 != x:
    diff.append('merchant-feed.xml')
    if FIX: open(fp, 'w', encoding='utf-8').write(x2)
if FIX:
    print(f'repriced {len(diff)} files' + (' — now run: python3 _i18n/build_en.py .' if diff else ''))
else:
    for d in diff: print('price out of date:', d)
    print('prices OK' if not diff else f'{len(diff)} files differ from index.html — run with --fix')
    sys.exit(1 if diff else 0)
