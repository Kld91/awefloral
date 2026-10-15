"""Rebuild the item lists of the static wholesale pages (wholesale/*.html) from catalog.json, in the pages' current markup.
Prices follow the dashboard's Riyadh multiplier (_i18n/price_mul.py), the same as the shop page.
usage: python3 _i18n/make_wholesale_pages.py [SITE_DIR]"""
import json, re, sys, os, html, urllib.parse
SITE = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import price_mul as PM
cat = json.load(open(SITE + '/catalog.json', encoding='utf-8'))
WG = {'ورد جوري': 'roses', 'قرنفل': 'carnations', 'كريز': 'chrysanthemum', 'جربيرا': 'gerbera', 'هدرنجا': 'hydrangea', 'ليليوم': 'lilies',
      'أوركيد': 'orchids', 'توليب': 'tulips', 'بيبي روز': 'spray-roses', 'ليسيانثوس': 'lisianthus', 'زهور مميزة': 'special-flowers', 'أوراق خضراء': 'greenery'}
H1 = {'ورد جوري': 'جوري جملة', 'قرنفل': 'قرنفل جملة', 'كريز': 'كريز جملة', 'جربيرا': 'جربيرا جملة', 'هدرنجا': 'هدرنجا جملة', 'ليليوم': 'ليليوم جملة',
      'أوركيد': 'أوركيد جملة', 'توليب': 'توليب جملة', 'بيبي روز': 'بيبي روز جملة', 'ليسيانثوس': 'ليسيانثوس جملة', 'زهور مميزة': 'زهور مميزة جملة', 'أوراق خضراء': 'أوراق خضراء للتنسيق'}
AR_ORIGIN = {'SA': 'السعودية', 'NL': 'هولندا', 'KE': 'كينيا', 'ET': 'إثيوبيا', 'CO': 'كولومبيا', 'EC': 'الإكوادور', 'ZA': 'جنوب أفريقيا',
             'TH': 'تايلاند', 'LK': 'سريلانكا', 'NZ': 'نيوزيلندا', 'MY': 'ماليزيا', 'IT': 'إيطاليا', 'AU': 'أستراليا', 'ZW': 'زيمبابوي'}
WCOL = {'yellow': 'أصفر', 'green': 'أخضر', 'purple': 'بنفسجي', 'blue': 'أزرق', 'pink': 'وردي', 'white': 'أبيض', 'red': 'أحمر',
        'orange': 'برتقالي', 'lilac': 'ليلكي', 'cream': 'كريمي', 'apricot': 'مشمشي', 'bicolour': 'لونين', 'salmon': 'سلموني'}
esc = lambda s: html.escape(str(s), quote=True)
def money(n):
    v = round(float(n) + 1e-9, 2); t = str(int(v)) if v == int(v) else f'{v:.2f}'
    return f'<span class="mny"><i class="sar" role="img" aria-label="ر.س"></i><span class="num">{t}</span></span>'
def w_name(it): return (it.get('ca') or it.get('ga') or '') + (' ' + WCOL[it['c']] if it.get('c') in WCOL else '')
def w_unit(it): return {'piece': 'غصن', 'bunch': 'ربطة', 'stem': 'غصن', 'pot': 'أصيص', 'box': 'كرتون'}.get(it.get('u'), 'غصن')
def w_units(it, n):
    u = w_unit(it); return {'غصن': 'أغصان', 'ربطة': 'ربطات', 'كرتون': 'كراتين', 'أصيص': 'أصص'}.get(u, u) if 3 <= n <= 10 else u
def count(n): return 'صنف واحد' if n == 1 else 'صنفين' if n == 2 else f'{n} أصناف' if n <= 10 else f'{n} صنف'
today = cat['updated'][:10]
W = PM.apply_bn([it for it in cat['items'] if it.get('st', 0) > 0 and it.get('p1', 0) > 0], PM.get(SITE))
have = {g for g in WG if any(it['g'] == g for it in W)}
for g, slug in WG.items():
    f = f'{SITE}/wholesale/{slug}.html'
    s = open(f, encoding='utf-8').read()
    items = sorted([it for it in W if it['g'] == g], key=lambda it: (it['p1'], it['n']))
    rows = ''.join(
        f'<li><a href="/bunches.html?id={esc(it["id"])}" data-go="/bunches.html?id={esc(it["id"])}">'
        + (f'<img src="/img/n/{esc(it["i"])}.webp" alt="{esc(w_name(it))} – {esc(it["n"])}" loading="lazy" width="96" height="96">' if it.get('i') else '<span class="ph"></span>')
        + f'\n<span class="t"><b>{esc(w_name(it))}</b><span class="latin">{esc(it["n"])}</span><span>{esc(it.get("l") or "")}{(" · " + AR_ORIGIN[it["o"]]) if it.get("o") in AR_ORIGIN else ""} · من {it["s"]} {w_units(it, it["s"])}</span></span>'
        + f'\n<span class="r">{money(it["p1"])}<small>لل{w_unit(it)}</small></span></a></li>' for it in items)
    origins = sorted({AR_ORIGIN.get(it.get('o'), '') for it in items} - {''})
    if items:
        known = all(it.get('o') in AR_ORIGIN for it in items)
        intro = count(len(items)) + ((f' من {"، ".join(origins)}' if known else f'، منها من {"، ".join(origins)}') if origins else '') + '. بدون حد أدنى للطلب، والبيع بالربطة الكاملة. التوصيل مجاني داخل الرياض، كل أيام الأسبوع حتى الجمعة.'
    else:
        intro = 'ما هو متوفر في مخزون الرياض اليوم. تقدر تطلبه من جملة هولندا.'
    old_intro = re.search(r'<div class="pagehead pad"><h1>[^<]*</h1><p>([^<]*)</p>', s).group(1)
    s = s.replace(old_intro, intro)                                   # page text, meta description, og:description
    s = re.sub(r'ووقت التحديث \d{4}-\d\d-\d\d', 'ووقت التحديث ' + today, s)
    s = re.sub(r'\n<p class="sub" style="background:#fff8ec[^\n]*?<!--/shut-->', '', s)
    s = re.sub(r'<ul class="wlist">.*?</ul>', lambda m: f'<ul class="wlist">{rows}</ul>', s, count=1, flags=re.S)
    if not items:
        s = s.replace('<a class="btn primary" href="/bunches.html?g=' + urllib.parse.quote(g) + '">اطلب من صفحة الجملة</a>', '<a class="btn primary" href="/holland.html">جملة هولندا</a>')
    if items and items[0].get('i'):
        s = re.sub(r'(<meta property="og:image" content=")[^"]*(")', lambda m: m.group(1) + f'https://www.awefloral.com/img/n/{items[0]["i"]}-l.webp' + m.group(2), s, count=1)
    def ld(m):
        j = json.loads(m.group(1))
        for node in j.get('@graph', []):
            if node.get('@type') == 'CollectionPage':
                node['mainEntity'] = {'@type': 'ItemList', 'numberOfItems': len(items),
                                      'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': w_name(it) + ' – ' + it['n']} for i, it in enumerate(items)]}
        return '<script type="application/ld+json">' + json.dumps(j, ensure_ascii=False) + '</script>'
    s = re.sub(r'<script type="application/ld\+json">(.*?)</script>', ld, s, count=1, flags=re.S)
    others = ' · '.join(f'<a href="/wholesale/{v}.html">{esc(H1[gg])}</a>' for gg, v in WG.items() if gg != g and gg in have)
    s = re.sub(r'(<h2 class="sh0">أصناف جملة ثانية</h2><p class="more-links">).*?(</p>)', lambda m: m.group(1) + others + m.group(2), s, count=1, flags=re.S)
    open(f, 'w', encoding='utf-8').write(s)
    print(slug, len(items), intro[:60])
