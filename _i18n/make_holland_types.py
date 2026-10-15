"""Static pages for the main Holland flower types (holland/<slug>.html), e.g. «توليب هولندي بالجملة في الرياض».
Each page is built from holland.json (varieties, colours, prices) and the flower notes in bunches.html (GUIDE),
links into holland.html for ordering, and is listed in sitemap.xml. English translations of the page text are
added to _i18n/segments.json + fixes.json so build_en.py turns them into /en/holland/<slug>.html.
Run after every holland.json update (make_holland.py runs it), then run build_en.py.
usage: python3 _i18n/make_holland_types.py [SITE_DIR]"""
import json, os, re, sys, html, subprocess, datetime, urllib.parse

R = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
HERE = os.path.join(R, '_i18n')
SITE = 'https://www.awefloral.com'
esc = lambda s: html.escape(str(s or ''), quote=True)

# key in holland.json (ca), Arabic name, English name, page slug, flower-guide page (flowers/<x>.html) or ''
TYPES = [
    ('توليب', 'توليب', 'Tulips', 'tulips', ''),
    ('ورد جوري', 'ورد جوري', 'Roses', 'roses', 'rose'),
    ('بيبي روز', 'بيبي روز', 'Spray Roses', 'spray-roses', 'spray-rose'),
    ('فاوانيا', 'فاوانيا', 'Peonies', 'peonies', 'peony'),
    ('رانونكولس', 'رانونكولس', 'Ranunculus', 'ranunculus', 'ranunculus'),
    ('هدرنجا', 'هدرنجا', 'Hydrangea', 'hydrangea', 'hydrangea'),
    ('كالا', 'كالا', 'Calla Lilies', 'calla', 'calla'),
    ('ليسيانثوس', 'ليسيانثوس', 'Lisianthus', 'lisianthus', 'lisianthus'),
    ('ليليوم', 'ليليوم', 'Lilies', 'lilies', 'lily'),
    ('أوركيد', 'أوركيد', 'Orchids', 'orchids', 'orchid'),
    ('بروتيا', 'بروتيا', 'Protea', 'protea', 'protea'),
    ('جبسوفيلا', 'جبسوفيلا', 'Gypsophila', 'gypsophila', 'gypsophila'),
]
LINK_AR = lambda ar: f'{ar} هولندي'
LINK_EN = lambda en: f'Dutch {en}'

# notes for types the shop's flower notes (GUIDE in bunches.html) do not cover: (arabic, english)
OWN = {
    'كالا': dict(life='7 إلى 10 أيام', level='سهل', scent='بدون',
        about=('زهرة على شكل قمع وساقها ناعمة بدون أوراق، شكلها أنيق وبسيط. من أكثر الزهور طلباً في باقات العرائس والتنسيقات الحديثة.',
               'A funnel-shaped bloom on a smooth, leafless stem, clean and elegant. One of the most requested flowers for bridal bouquets and modern arrangements.'),
        style=('تحلو لحالها في فازة طويلة، أو مجموعة من لون واحد مربوطة بشريطة.',
               'Beautiful on its own in a tall vase, or as a single-colour bunch tied with a ribbon.'),
        care=[('حط لها ماء قليل، تقريباً 5 سم، لأن ساقها تمتص الماء بسرعة وتلين إذا غرقت.',
               'Give it shallow water, about 5 cm: the stem drinks fast and goes soft if it sits too deep.')]),
    'فاوانيا': dict(life='5 إلى 7 أيام', level='متوسط', scent='خفيفة',
        about=('زهرة كبيرة كثيفة البتلات، تنفتح من كرة صغيرة لزهرة ضخمة خلال أيام. موسمها قصير، والهولندي منها من أجمل الأنواع.',
               'A large, densely petalled bloom that opens from a tight bud into a huge flower within days. The season is short, and Dutch peonies are among the finest.'),
        style=('خلها نجمة الباقة مع جوري الحدائق أو الأوكالبتوس، ولا تزحمها بزهور كبيرة ثانية.',
               'Let it be the star of the bouquet with garden roses or eucalyptus, and do not crowd it with other large flowers.'),
        care=[('إذا تبيها تفتح أسرع حطها في ماء دافي ومكان دافي، وإذا تبيها تتأخر خلها في مكان بارد.',
               'For faster opening, put it in warm water in a warm room; to hold it back, keep it somewhere cool.')]),
    'رانونكولس': dict(life='7 إلى 10 أيام', level='متوسط', scent='بدون',
        about=('بتلات رقيقة كثيرة فوق بعض مثل الورق، وألوانه ناعمة ودافية. يدوم طويل في الفازة ويكمل يتفتح.',
               'Layer upon layer of tissue-thin petals in soft, warm colours. It lasts well in the vase and keeps opening.'),
        style=('يحلو مع الأنيمون والتوليب في باقات الربيع، أو لحاله في فازة صغيرة.',
               'Lovely with anemones and tulips in spring bouquets, or on its own in a small vase.'),
        care=[('ساقه مجوفة وطرية، قصه بسكين حادة وغيّر الماء كل يومين.',
               'The stem is hollow and soft: cut it with a sharp knife and change the water every two days.')]),
    'جبسوفيلا': dict(life='7 إلى 10 أيام', level='سهل', scent='خفيفة', dry='ينشف ويبقى حلو',
        about=('زهور بيضاء صغيرة كثيرة مثل الغيم، تعطي الباقة نعومة وتملا الفراغات. تنفع لحالها في باقات كبيرة أو كحشوة.',
               'Clouds of tiny white flowers that soften a bouquet and fill the gaps. Works on its own in big bunches or as a filler.'),
        style=('لحالها في باقة كبيرة مستديرة، أو مع الجوري الأحمر لشكل كلاسيكي.',
               'On its own in a big round bouquet, or with red roses for a classic look.'),
        care=[('تنشف بسهولة وتبقى حلوة، فإذا خلصت مدتها في الماء علقها مقلوبة.',
               'It dries easily and stays pretty, so when it is done in water, hang it upside down.')]),
    'أوركيد': dict(life='3 أسابيع أو أكثر', level='سهل', scent='بدون تقريباً',
        about=('أوركيد قطف بأنواعه: فاندا وسيمبيديوم ودندروبيوم وغيرها. من أطول الزهور عمراً في الفازة، ويعطي فخامة للتنسيقات الكبيرة.',
               'Cut orchids of every kind: vanda, cymbidium, dendrobium and more. Among the longest-lasting flowers in a vase, they bring luxury to large arrangements.'),
        style=('غصن واحد في فازة شفافة يكفي، أو استخدمه في تنسيقات الطاولات والمناسبات.',
               'A single stem in a clear vase is enough, or use it in table and event arrangements.'),
        care=[('رش الزهور بالماء من بعيد، وخله بعيد عن الفاكهة والمكيف المباشر.',
               'Mist the flowers lightly from a distance, and keep it away from fruit and direct air-conditioning.')]),
}

# fixed Arabic text on every page and its English (most of these already exist in the translations)
WHY = ('نطلبه لك من المزارع والمزادات في هولندا مع شحنة الثلاثاء، والسعر شامل الشحن والتخليص والضريبة، وتطلب بالربطة الكاملة بدون حد أدنى للصناديق.',
       'We order it for you from Dutch farms and auctions with the Tuesday shipment. The price includes freight, clearance and VAT, and you order by the full bunch with no minimum number of boxes.')
FIXED = {
    WHY[0]: WHY[1],
    'اطلب قبل الأحد 5 العصر، ويوصلك الثلاثاء أو الأربعاء · توصيل مجاني': 'Order by Sunday 5 pm, delivered Tuesday or Wednesday · Free delivery',
    'شوف كل الأصناف واطلب': 'See all varieties and order',
    'من الأصناف المتوفرة': 'Some of the varieties available',
    'الأصناف': 'Varieties', 'الألوان': 'Colours', 'السعر يبدأ من': 'Prices from',
    'عن الزهرة': 'About the flower',
    'أصناف هولندا ثانية': 'More from Holland',
    'اقرأ عنه في دليل الورد': 'Read about it in the flower guide',
    'أسئلة متكررة': 'Frequently asked questions',
    'طول الساق': 'Stem length', 'الربطة': 'Bunch', 'أصناف هولندا': 'Holland flower types',
}

# ---------------------------------------------------------------- data
D = json.load(open(os.path.join(R, 'holland.json'), encoding='utf-8'))
import price_mul as PM
ITEMS = PM.apply_nl(D['items'], PM.get(R))   # the dashboard's margins, as on the page
src = open(os.path.join(R, 'bunches.html'), encoding='utf-8').read()
def js_const(name):   # an object literal from bunches.html, read with node
    a = src.index('const ' + name + ' = {') + len('const ' + name + ' = ')
    b = src.index('\n};', a) + 2 if name == 'GUIDE' else src.index('}', a) + 1   # GUIDE spans many lines; the others are one flat line
    lit = src[a:b]
    return json.loads(subprocess.check_output(['node', '-e', 'process.stdout.write(JSON.stringify(eval("(" + require("fs").readFileSync(0, "utf8") + ")")))'], input=lit.encode()))
GUIDE = js_const('GUIDE'); COLORS = js_const('AR_COLORS'); ORIGIN = js_const('AR_ORIGIN')
FAQ = dict(re.findall(r"\['([^']+)', '([^']+)'\]", open(os.path.join(HERE, 'make_holland.py'), encoding='utf-8').read().split('const FAQ = [')[1].split('];')[0]))
FAQ_PICK = ['متى يوصل الطلب؟', 'السعر يشمل إيش؟', 'ليش الكمية بالربطة الكاملة؟', 'لو ما توفر الصنف؟']

def items_of(key):
    ok = lambda x: (str(x.get('o') or '').upper() != 'IL' and x.get('p1', 0) > 0 and x.get('i') and not str(x['i']).startswith('@')
                    and os.path.exists(os.path.join(R, str(x['i']).lstrip('/') + '.webp')))
    return [x for x in ITEMS if ok(x) and (x.get('ca') == key or (key == 'أوركيد' and str(x.get('ca') or '').startswith('أوركيد')))]

def money(v): return f'{v:.2f}'
def cm(l):
    m = re.match(r'(\d+)', str(l or '')); return int(m.group(1)) if m else None
def notes(key):
    if key in OWN:
        o = OWN[key]
        return dict(life=o['life'], level=o['level'], scent=o['scent'], dry=o.get('dry', ''), about=o['about'][0], style=o['style'][0], care=[c[0] for c in o['care']])
    g = GUIDE.get(key) or {}
    return dict(life=g.get('life', ''), level=g.get('level', ''), scent=g.get('scent', ''), dry=g.get('dry', ''), about=g.get('about', ''), style=g.get('style', ''), care=g.get('care', []))

# ---------------------------------------------------------------- page shell (from a wholesale page)
tpl = open(os.path.join(R, 'wholesale', 'tulips.html'), encoding='utf-8').read()
HEAD_COMMON = tpl[tpl.index('<meta name="theme-color"'):tpl.index('<script type="application/ld+json">')]
HEAD_COMMON = re.sub(r'<meta property="og:(title|description|url|image)"[^>]*>\n?', '', HEAD_COMMON)
HEAD_COMMON = re.sub(r'<meta name="twitter:card"[^>]*>\n?', '', HEAD_COMMON)
FLORIST = json.loads(tpl[tpl.index('<script type="application/ld+json">') + 35:tpl.index('</script>', tpl.index('<script type="application/ld+json">'))])['@graph'][0]
BODY_TOP = tpl[tpl.index('<body'):tpl.index('<main>')]
BODY_END = tpl[tpl.index('</main>') + len('</main>'):]
STYLE = ('<style>.ht-facts{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 4px;padding:0;list-style:none}.ht-facts li{background:#F4F2EE;border-radius:10px;padding:8px 12px;font-size:13px;color:#555}'
         '.ht-facts b{display:block;font-size:17px;color:#1F2433}.ht-ship{margin:10px 0 0;padding:9px 12px;border-radius:8px;background:#EEF6F0;color:#1F6B3A;font-size:14px;line-height:1.5}'
         '.ht-info{width:100%;border-collapse:collapse;margin:8px 0;font-size:14px}.ht-info th{text-align:start;color:#666;font-weight:500;padding:6px 0;width:42%}.ht-info td{padding:6px 0}.ht-info tr+tr{border-top:1px solid #eee}'
         '.ht-faq details{border-top:1px solid #eee;padding:10px 0}.ht-faq summary{font-weight:600;cursor:pointer}.ht-faq p{margin:6px 0 0;color:#444}.ht-sec p,.ht-sec li{line-height:1.7}</style>')

def page(t, its):
    key, ar, en, slug, guide = t
    path = f'/holland/{slug}.html'; url = SITE + path
    n = notes(key)
    cols = sorted({x['c'] for x in its if x.get('c') in COLORS})
    pmin = min(x['p1'] for x in its)
    lens = sorted(v for v in (cm(x.get('l')) for x in its) if v)
    # one per colour (cheapest), then the rest by price, up to 24
    by = sorted(its, key=lambda x: (x['p1'], x['n']))
    pick, seen = [], set()
    for x in by:
        if x.get('c') not in seen: pick.append(x); seen.add(x.get('c'))
    for x in by:
        if len(pick) >= 24: break
        if x not in pick: pick.append(x)
    pick = sorted(pick[:24], key=lambda x: (x['p1'], x['n']))
    h1 = f'{ar} هولندي بالجملة في الرياض'
    title_core = f'{h1} · شحنة كل ثلاثاء'
    desc = f'{ar} من هولندا بالجملة في الرياض: {len(its)} صنف تبدأ من {money(pmin)} ريال للغصن، شامل الشحن والتخليص والضريبة. شحنة كل ثلاثاء، والتوصيل مجاني داخل الرياض.'
    img0 = SITE + pick[0]['i'] + '-l.webp'
    rows = []
    for x in pick:
        cname = COLORS.get(x.get('c'), '')
        spec = [f'<span>{esc(x["l"])}</span>' if x.get('l') else '', f'<span>{esc(ORIGIN.get(str(x.get("o") or "").upper(), ""))}</span>' if ORIGIN.get(str(x.get('o') or '').upper()) else '',
                f'<span>الربطة <span class="num">{int(x.get("s") or x.get("m") or 1)}</span></span>']
        rows.append(f'<li><a href="/holland.html?id={x["id"]}" data-go="/holland.html?id={x["id"]}"><img src="{esc(x["i"])}.webp" alt="{esc(x["n"])}" loading="lazy" width="96" height="96">'
                    f'<span class="t"><b>{esc(x.get("ca") or ar)}</b>{f" <span>{esc(cname)}</span>" if cname else ""}<span class="latin">{esc(x["n"])}</span><span>{" · ".join(s for s in spec if s)}</span></span>'
                    f'<span class="r"><span class="mny"><i class="sar" role="img" aria-label="ر.س"></i><span class="num">{money(x["p1"])}</span></span><small>للغصن</small></span></a></li>')
    info = [('يبقى في الفازة', n['life']), ('سهولة العناية', n['level']), ('الريحة', n['scent']), ('التجفيف', n['dry']),
            ('طول الساق', f'{lens[0]} – {lens[-1]} سم' if lens and lens[0] != lens[-1] else (f'{lens[0]} سم' if lens else ''))]
    info = ''.join(f'<tr><th scope="row">{esc(k)}</th><td>{esc(v)}</td></tr>' for k, v in info if v)
    care = ''.join(f'<li>{esc(c)}</li>' for c in n['care'])
    faqs = [(q, FAQ[q]) for q in FAQ_PICK if q in FAQ]
    others = ' · '.join(f'<a href="/holland/{o[3]}.html">{esc(LINK_AR(o[1]))}</a>' for o in TYPES if o[3] != slug)
    q = urllib.parse.quote(key)
    ld = {'@context': 'https://schema.org', '@graph': [FLORIST,
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'الرئيسية', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'هولندا', 'item': SITE + '/holland.html'},
            {'@type': 'ListItem', 'position': 3, 'name': LINK_AR(ar), 'item': url}]},
        {'@type': 'CollectionPage', 'name': h1, 'url': url, 'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(pick),
            'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': x['n'], 'url': SITE + '/holland.html?id=' + x['id']} for i, x in enumerate(pick)]}},
        {'@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': a, 'acceptedAnswer': {'@type': 'Answer', 'text': b}} for a, b in faqs]}]}
    body_top = BODY_TOP.replace('href="/en/wholesale/tulips.html"', f'href="/en/holland/{slug}.html"')
    out = f'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title_core)} | أو فلورا</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}"><link rel="alternate" hreflang="ar" href="{url}"><link rel="alternate" hreflang="en" href="{SITE}/en{path}"><link rel="alternate" hreflang="x-default" href="{url}">
{HEAD_COMMON.replace('<meta property="og:type" content="website">', f'<meta property="og:type" content="website">\n<meta property="og:title" content="{esc(title_core)} | أو فلورا">\n<meta property="og:description" content="{esc(desc)}">\n<meta property="og:url" content="{url}">\n<meta property="og:image" content="{img0}">\n<meta name="twitter:card" content="summary_large_image">')}<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{STYLE}
</head>
{body_top}<main>
<nav class="crumbs" aria-label="المسار"><a href="/">الرئيسية</a> <span>/</span> <a href="/holland.html">هولندا</a> <span>/</span> <span aria-current="page">{esc(LINK_AR(ar))}</span></nav>
<div class="pagehead pad"><h1>{esc(h1)}</h1><p>{esc(n['about'])}</p><p>{esc(WHY[0])}</p>
<ul class="ht-facts"><li><span>الأصناف</span><b class="num">{len(its)}</b></li><li><span>الألوان</span><b class="num">{len(cols)}</b></li><li><span>السعر يبدأ من</span><b><span class="mny"><i class="sar" role="img" aria-label="ر.س"></i><span class="num">{money(pmin)}</span></span></b></li></ul>
<p class="ht-ship">اطلب قبل الأحد 5 العصر، ويوصلك الثلاثاء أو الأربعاء · توصيل مجاني</p>
<p class="sub">الأسعار تتغير يومياً حسب سوق هولندا والموسم والكميات، والسعر اللي تدفعه هو المكتوب لحظة الدفع.</p>
<a class="btn primary" href="/holland.html?t={q}">شوف كل الأصناف واطلب</a></div>
<h2 class="sh0 pad" style="margin:22px 0 4px">من الأصناف المتوفرة</h2>
<ul class="wlist">{''.join(rows)}</ul>
<section class="sec pad ht-sec"><h2 class="sh0">عن الزهرة</h2><table class="ht-info"><tbody>{info}</tbody></table>
{f'<h3>كيف تنسّقه</h3><p>{esc(n["style"])}</p>' if n['style'] else ''}{f'<h3>العناية عشان يدوم أكثر</h3><ul>{care}</ul>' if care else ''}{f'<p><a href="/flowers/{guide}.html">اقرأ عنه في دليل الورد</a></p>' if guide else ''}</section>
<section class="sec pad ht-faq"><h2 class="sh0">أسئلة متكررة</h2>{''.join(f'<details><summary>{esc(a)}</summary><p>{esc(b)}</p></details>' for a, b in faqs)}</section>
<section class="sec pad"><h2 class="sh0">أصناف هولندا ثانية</h2><p class="more-links">{others}</p></section>
</main>{BODY_END}'''
    pairs = {h1: f'Dutch {en} Wholesale in Riyadh', title_core: f'Dutch {en} Wholesale in Riyadh · Shipment Every Tuesday',
             desc: f'Dutch {en} wholesale in Riyadh: {len(its)} varieties from {money(pmin)} riyals a stem, including freight, clearance and VAT. A shipment every Tuesday, with free delivery within Riyadh.',
             LINK_AR(ar): LINK_EN(en)}
    if key in OWN:
        o = OWN[key]; pairs[o['about'][0]] = o['about'][1]; pairs[o['style'][0]] = o['style'][1]
        for a, b in o['care']: pairs[a] = b
    return path, out, pairs

def add_translations(pairs):
    sp, fp = os.path.join(HERE, 'segments.json'), os.path.join(HERE, 'fixes.json')
    segs = json.load(open(sp, encoding='utf-8')); fix = json.load(open(fp, encoding='utf-8'))
    NUM = re.compile(r'\d+(?:[.,]\d+)*')
    by = {}; skel = set()
    for s in segs: by.setdefault(s['ar'], s['id']); skel.add(NUM.sub('#', s['ar']))
    nid = max(int(s['id']) for s in segs) + 1; added = 0
    for ar, en in pairs.items():
        if ar in by: continue                                         # keep the translation the site already uses
        if NUM.search(ar) and NUM.sub('#', ar) in skel: continue      # same sentence, other numbers: build_en reuses it
        segs.append({'id': nid, 'ar': ar, 'file': '', 'ctx': 'holland-types'}); fix[str(nid)] = en; by[ar] = nid; skel.add(NUM.sub('#', ar)); nid += 1; added += 1
    json.dump(segs, open(sp, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump(fix, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return added

def run():
    os.makedirs(os.path.join(R, 'holland'), exist_ok=True)
    pairs, made = dict(FIXED), []
    for t in TYPES:
        its = items_of(t[0])
        if len(its) < 3: continue                     # out of season: no thin page
        path, out, pr = page(t, its); pairs.update(pr)
        open(os.path.join(R, path.lstrip('/')), 'w', encoding='utf-8').write(out); made.append(path)
    for f in os.listdir(os.path.join(R, 'holland')):        # a type that went out of season loses its page
        if f.endswith('.html') and '/holland/' + f not in made: os.remove(os.path.join(R, 'holland', f))
    added = add_translations(pairs)
    sm_path = os.path.join(R, 'sitemap.xml'); sm = open(sm_path, encoding='utf-8').read()
    sm = re.sub(r'<url><loc>' + re.escape(SITE) + r'(?:/en)?/holland/[^<]*</loc>.*?</url>', '', sm, flags=re.S)
    today = datetime.date.today().isoformat()
    sm = sm.replace('</urlset>', ''.join(f'<url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod><priority>0.8</priority></url>' for p in made) + '</urlset>')
    open(sm_path, 'w', encoding='utf-8').write(sm)
    print(f'holland type pages: {len(made)} written, {added} new translations')
    return made

def links_html(made):
    """Static links to the type pages for holland.html (crawlable), in the shared page's markup."""
    return ('\n    <section>\n      <div class="head"><h2>أصناف هولندا</h2></div>\n      <p class="tlinks" style="line-height:2;margin:0 0 8px">'
            + ' · '.join(f'<a href="/holland/{t[3]}.html">{esc(LINK_AR(t[1]))}</a>' for t in TYPES if f'/holland/{t[3]}.html' in made) + '</p>'
            + '\n      <p class="tlinks" style="line-height:2;margin:0 0 8px"><a href="/guides/">أدلة لمحلات الورد</a>: ' + guide_links() + '</p>\n    </section>')

def guide_links():
    import make_guides
    return make_guides.links_html()

if __name__ == '__main__':
    run()
