"""Build the English site (/en/) from the Arabic pages.
Every Arabic text run is swapped for its English translation (segments.json + out*.json), then the page is
turned left-to-right and its links pointed at /en/.  Re-run after editing the Arabic pages; any Arabic run
without a translation is reported (and left in place) so it can be added.
usage: python3 build_en.py [SITE_DIR]"""
import re, json, glob, os, sys, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
R = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/kld91/awefloral'
sys.path.insert(0, HERE); import img_opt
print('img_opt: updated', img_opt.run(os.path.abspath(R)), 'Arabic pages')
EN = os.path.join(R, 'en')
SITE = 'https://www.awefloral.com'

segs = json.load(open(os.path.join(HERE, 'segments.json'), encoding='utf-8'))
T = {}
for p in sorted(glob.glob(os.path.join(HERE, 'out*.json'))):
    T.update(json.load(open(p, encoding='utf-8'))['t'])
FIX = json.load(open(os.path.join(HERE, 'fixes.json'), encoding='utf-8')) if os.path.exists(os.path.join(HERE, 'fixes.json')) else {}
T.update(FIX)
MAP = {s['ar']: T[str(s['id'])] for s in segs if str(s['id']) in T}
AR = re.compile(r'[؀-ۿ](?:[؀-ۿً-ٟ0-9 ،؛؟!\.\-–·×%+:/()«»‏]|(?<=\s)[a-zA-Z]+(?=\s))*[؀-ۿ0-9\.!؟)]?')
KEEP = re.compile(r'^(?:شركة )?روع النباتات(?: للتجارة)?$')
MISSING = {}
# a sentence whose only change is a number (a price, a count) reuses the translation of the same sentence with the old number
NUM = re.compile(r'\d+(?:[.,]\d+)*')
SKEL = {}
for _ar, _en in MAP.items(): SKEL.setdefault(NUM.sub('#', _ar), (_ar, _en))
def by_numbers(seg):
    hit = SKEL.get(NUM.sub('#', seg))
    if not hit: return None
    ar0, out = hit; old, new = NUM.findall(ar0), NUM.findall(seg)
    if len(old) != len(new): return None
    subs = {}
    for i, (a, b) in enumerate(zip(old, new)):
        if a == b: continue
        pat = r'(?<![\d.,])' + re.escape(a) + r'(?![\d]|[.,]\d)'
        if len(re.findall(pat, out)) != 1: return None
        tok = '\x00%d\x00' % i; out = re.sub(pat, tok, out); subs[tok] = b
    for t, b in subs.items(): out = out.replace(t, b)
    return out

def tr(s, where):
    def f(m):
        raw = m.group(0); seg = raw.strip()
        if not seg: return raw
        if seg not in MAP:
            en = by_numbers(seg)
            if en is not None: MAP[seg] = en; return raw[:len(raw) - len(raw.lstrip())] + en + raw[len(raw.rstrip()):]
            if not KEEP.match(seg) and not re.fullmatch(r'[٠-٩۰-۹]+', seg): MISSING.setdefault(seg, where)
            return raw
        lead = raw[:len(raw) - len(raw.lstrip())]; trail = raw[len(raw.rstrip()):]
        return lead + MAP[seg] + trail
    return AR.sub(f, s)

def tr_wa(s, where):
    # prefilled WhatsApp messages are URL-encoded
    def f(m):
        txt = urllib.parse.unquote(m.group(2))
        q = re.fullmatch(r'السلام عليكم، عندي سؤال عن (.+) \((https?://[^)]+)\)', txt)
        if q:
            name = q.group(1).strip()
            en = MAP.get(name) or tr(name, where)
            m10 = re.fullmatch(r'10 (.+)', name)
            if name not in MAP and m10 and m10.group(1) in MAP: en = '10 ' + MAP[m10.group(1)]
            txt = f'Hi, I have a question about {en} ({localize_links(q.group(2))})'
        else:
            txt = tr(txt, where)
        return m.group(1) + urllib.parse.quote(txt, safe='')
    return re.sub(r'(wa\.me/\d+\?text=)([^"\'&\s<>]+)', f, s)

PAGE = r'(?:[a-z0-9-]+\.html|occasions/|ward/|wholesale/|flowers/|styling/|#|\?|(?=["\'`<\s]))'
PATHS = r'(?:[a-z0-9-]+\.html|occasions/|ward/|wholesale/|flowers/|styling/)'
def localize_links(s):
    s = re.sub(r'((?:href|data-go|action)=")/(?=' + PAGE + ')', r'\1/en/', s)   # href="/", href="/#/cart", href="/x.html"
    s = re.sub(r'(?<=["\'`])/(?=' + PATHS + ')', '/en/', s)                    # "/x.html" anywhere (never a bare "/")
    s = s.replace("location.href = '/' +", "location.href = '/en/' +")
    s = re.sub(re.escape(SITE) + r'/(?!en/)(?=' + PAGE + r'|$)', SITE + '/en/', s)  # absolute page URLs
    s = s.replace('/en/assets/', '/assets/')                                   # shared assets stay
    s = re.sub(r'src="/assets/seo\.js(\?v=\d+)?"', r'src="/en/assets/seo.js\1"', s)   # English product script: add-to-cart goes to the English store
    for f in ('favicon.svg', 'icon-180.png', 'manifest.webmanifest', 'pwa.js'):   # root files, shared by both languages
        s = s.replace(f'href="{f}"', f'href="/{f}"').replace(f'src="{f}"', f'src="/{f}"')
    return s

def ltr(s):
    s = s.replace('<html lang="ar" dir="rtl">', '<html lang="en" dir="ltr">').replace(' dir="rtl"', ' dir="ltr"')
    s = s.replace('/assets/fonts/plex-400-arabic.woff2" as="font"', '/assets/fonts/plex-400-latin.woff2" as="font"')   # English pages need the Latin cut first
    s = s.replace('content="ar_SA"', 'content="en_US"').replace("'ar-SA-u-ca-gregory-nu-latn'", "'en-GB'").replace("'ar-SA'", "'en-GB'")
    s = s.replace('d="m9 5 7 7-7 7"', 'd="m15 5-7 7 7 7"').replace('d="M9 6l6 6-6 6"', 'd="M15 6l-6 6 6 6"')
    s = s.replace(' ←', ' →').replace('←', '→')
    s = s.replace('text-align:right', 'text-align:left')
    s = re.sub(r'(\.side\{[^}]*?)right:calc\(', r'\1left:calc(', s)
    s = s.replace('.slide i{position:absolute;bottom:18px;left:18px', '.slide i{position:absolute;bottom:18px;right:18px')
    s = s.replace('.slide > i{position:absolute;bottom:18px;left:18px', '.slide > i{position:absolute;bottom:18px;right:18px')
    return s

def swap_lang_link(s, ar_path):
    s = re.sub(r'<a class="langlink" data-lang="en" href="[^"]*" hreflang="en" lang="en">English</a>',
               f'<a class="langlink" data-lang="ar" href="{ar_path}" hreflang="ar" lang="ar">عربي</a>', s)
    s = re.sub(r'<a class="(ib|icon-btn) langlink" data-lang="en" href="[^"]*" hreflang="en" lang="en" aria-label="English">EN</a>',
               lambda m: f'<a class="{m.group(1)} langlink" data-lang="ar" href="{ar_path}" hreflang="ar" lang="ar" aria-label="العربية">عربي</a>', s)
    return s

def tidy(s):
    s = re.sub(r'\b([A-Z][A-Za-z]+) – \1\b', r'\1', s)          # "Aralia – Aralia"
    return s

def build_page(rel):
    src = open(os.path.join(R, rel), encoding='utf-8').read()
    alts = re.findall(r'<link rel="alternate" hreflang="[^"]+" href="[^"]+">', src)
    s = src
    for a in alts: s = s.replace(a, '', 1)
    m = re.search(r'<link rel="canonical" href="([^"]+)">', s)
    ar_url = m.group(1) if m else SITE + '/'
    if rel == 'wholesale/index.html': ar_url = SITE + '/wholesale/'
    s = tr_wa(s, rel)
    s = tr(s, rel)
    s = localize_links(s)
    s = ltr(s)
    s = swap_lang_link(s, ar_url[len(SITE):])
    s = tidy(s)
    if alts and m:
        s = s.replace(f'<link rel="canonical" href="{localize_links(m.group(1))}">', f'<link rel="canonical" href="{localize_links(m.group(1))}">' + ''.join(alts), 1)
    return s

def page_specific(rel, s):
    if rel in ('bunches.html', 'holland.html'):
        s = s.replace('const uPlural = (it, n) => (n >= 3 && n <= 10) ?', 'const uPlural = (it, n) => (n !== 1) ?')
        s = s.replace("`${a.length.toLocaleString('en')} item`", "`${a.length.toLocaleString('en')} item${a.length === 1 ? '' : 's'}`")
        s = s.replace("`${n.toLocaleString('en')} item`", "`${n.toLocaleString('en')} items`")   # type tiles (n > 1 here)
        s = s.replace("`${ts.length} types`", "`${ts.length} type${ts.length === 1 ? '' : 's'}`")
    return s

SKIP = {'index1.html', 'bunches1.html', 'links.html', '404.html'}
files = [f for f in sorted(glob.glob(os.path.join(R, '*.html')) + glob.glob(os.path.join(R, 'occasions/*.html')) +
                           glob.glob(os.path.join(R, 'ward/*.html')) + glob.glob(os.path.join(R, 'wholesale/*.html')))]
files = [os.path.relpath(f, R) for f in files]
files = [f for f in files if f not in SKIP and not f.startswith('en/')]
count = 0
for rel in files:
    out = os.path.join(EN, rel); os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w', encoding='utf-8').write(page_specific(rel, build_page(rel))); count += 1

# data + script used by English pages
cat = json.load(open(os.path.join(R, 'catalog.json'), encoding='utf-8'))
def tr_obj(o):
    if isinstance(o, str): return tidy(tr(o, 'catalog.json'))
    if isinstance(o, list): return [tr_obj(x) for x in o]
    if isinstance(o, dict): return {tr_obj(k): tr_obj(v) for k, v in o.items()}
    return o
json.dump(tr_obj(cat), open(os.path.join(EN, 'catalog.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
if os.path.exists(os.path.join(R, 'holland.json')):   # Holland import catalogue (holland.html)
    hol = json.load(open(os.path.join(R, 'holland.json'), encoding='utf-8'))
    json.dump(tr_obj(hol), open(os.path.join(EN, 'holland.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    # the grower's full list (holland-all/<section>.json); the price parts in holland-all/p/ are read by the order worker only
    import glob as _g
    os.makedirs(os.path.join(EN, 'holland-all'), exist_ok=True)
    for f in _g.glob(os.path.join(EN, 'holland-all', '*.json')):
        os.remove(f)
    for f in sorted(_g.glob(os.path.join(R, 'holland-all', '*.json'))):
        part = json.load(open(f, encoding='utf-8'))
        json.dump(tr_obj(part), open(os.path.join(EN, 'holland-all', os.path.basename(f)), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
os.makedirs(os.path.join(EN, 'assets'), exist_ok=True)
js = open(os.path.join(R, 'assets/seo.js'), encoding='utf-8').read()
open(os.path.join(EN, 'assets/seo.js'), 'w', encoding='utf-8').write(ltr(localize_links(tr(js, 'assets/seo.js'))))

# sitemap: add the English URLs
sm = open(os.path.join(R, 'sitemap.xml'), encoding='utf-8').read()
sm = re.sub(r'\s*<url><loc>' + re.escape(SITE) + r'/en/.*?</url>', '', sm, flags=re.S)
locs = re.findall(r'<loc>(' + re.escape(SITE) + r'/[^<]*)</loc>', sm)
add = ''.join(f'<url><loc>{SITE}/en/{u[len(SITE) + 1:]}</loc></url>' for u in locs if not u.endswith(('.jpg', '.png')))
sm = sm.replace('</urlset>', add + '</urlset>')
open(os.path.join(R, 'sitemap.xml'), 'w', encoding='utf-8').write(sm)

print(f'built {count} pages + catalog + seo.js; sitemap +{len(locs)}')
if MISSING:
    print(f'UNTRANSLATED ({len(MISSING)}):')
    for k, v in list(MISSING.items())[:60]: print('  ', v, '|', k)
    if os.environ.get('MISSING_JSON'): json.dump(MISSING, open(os.environ['MISSING_JSON'], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
