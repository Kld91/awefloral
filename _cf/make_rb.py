# -*- coding: utf-8 -*-
"""Split the build: wholesale pages move to Rawnbatat (www.rawnbatat.com), the gift shop stays on Awe Floral.
Run on dist/ after cf-build.sh copies the site:
  - each wholesale page is copied, rebranded, to dist/rb/<path> and removed from its old place
    (the site worker serves dist/rb/* on the Rawnbatat host and 301s the old Awe Floral addresses there);
  - Awe Floral pages link to the wholesale pages on the new domain;
  - each domain gets its own sitemap and robots.txt.
Data files (catalog.json, holland.json, ...) stay where they are: the pages and the payment worker read them from either host."""
import os, re, sys, glob

D = sys.argv[1] if len(sys.argv) > 1 else 'dist'
AWE, RB = 'https://www.awefloral.com', 'https://www.rawnbatat.com'
# the wholesale pages (Arabic and English)
WH = re.compile(r'^(en/)?(bunches|holland|holland-small|stock|accessories|business)\.html$|^(en/)?(holland|wholesale)/[a-z0-9-]+\.html$')
PATH = r'(?:en/)?(?:(?:bunches|holland|holland-small|stock|accessories|business)\.html|(?:holland|wholesale)/(?:[a-z0-9-]+\.html)?)'

def pages():
    for f in glob.glob(os.path.join(D, '**', '*.html'), recursive=True):
        r = os.path.relpath(f, D).replace(os.sep, '/')
        if not r.startswith('rb/'): yield f, r

NAV_AR = [('/', 'الرئيسية'), ('/holland.html', 'مستورد من العالم'), ('/holland-small.html', 'كميات صغيرة'), ('/stock.html', 'من مخزوننا'), ('/accessories.html', 'إكسسوارات'), ('/business.html', 'حساب المحل')]
NAV_EN = [('/en/', 'Home'), ('/en/holland.html', 'Imported'), ('/en/holland-small.html', 'Small boxes'), ('/en/stock.html', 'Our stock'), ('/en/accessories.html', 'Accessories'), ('/en/business.html', 'Shop account')]

# the import pages: flowers from markets worldwide, not «Holland» (applied to the pages and to their data files alike)
WORLD = [
    ("NL:'هولندا'", "NL:'@@NLAR@@'"), ("NL:'Holland'", "NL:'@@NLEN@@'"),
    ('الورد الهولندي والكيني والإكوادوري', 'الورد المستورد من كينيا والإكوادور وكولومبيا وغيرها'),
    ('مميز من هولندا', 'أصناف مميزة مستوردة'), ('مواسم الزهور الهولندية', 'مواسم الزهور المستوردة'),
    ('أصناف هولندية مميزة', 'أصناف مستوردة مميزة'), ('المزارع والمزادات في هولندا', 'المزارع والمزادات العالمية'),
    ('سوق هولندا', 'السوق العالمي'), ('أسعار هولندا', 'أسعار السوق العالمي'), ('شحنة هولندا', 'شحنة الاستيراد'),
    ('استيراد هولندا', 'الاستيراد من العالم'), ('جملة هولندا', 'جملة الاستيراد'), ('أصناف هولندا', 'الأصناف المستوردة'),
    ('في هولندا', 'في السوق العالمي'), ('من هولندا', 'من الخارج'),
    ('الهولندية', 'المستوردة'), ('هولندية', 'مستوردة'), ('الهولندي', 'المستورد'), ('هولندي', 'مستورد'), ('هولندا', 'الاستيراد'),
    ('Dutch, Kenyan and Ecuadorian Roses', 'Imported Roses from Kenya, Ecuador and beyond'), ('Dutch specials', 'Imported specials'),
    ('the Dutch market', 'the world flower market'), ('Dutch market', 'world flower market'),
    ('Dutch farms and auctions', 'farms and auctions worldwide'), ('Dutch flowers', 'Imported flowers'),
    ('the Holland shipment', 'the import shipment'), ('from the Netherlands', 'from abroad'), ('in the Netherlands', 'on the world market'),
    ('Import from Holland', 'Imported from around the world'), ('import from Holland', 'import from around the world'),
    ('from Holland', 'from abroad'), ('Holland import', 'World import'), ('Holland varieties', 'Imported varieties'),
]
WORLD_RX = [(re.compile(r'\bDutch\b'), 'Imported'), (re.compile(r'\bHolland\b'), 'Imported')]
def world(h):
    for a, b in WORLD: h = h.replace(a, b)
    for rx, b in WORLD_RX: h = rx.sub(b, h)
    return h.replace('@@NLAR@@', 'هولندا').replace('@@NLEN@@', 'Netherlands')

def nav(rel, en):
    here = '/' + rel
    if rel in ('bunches.html', 'en/bunches.html'): here = '/en/' if en else '/'
    items = ''.join('<a href="%s"%s>%s</a>' % (u, ' aria-current="page"' if u == here else '', t) for u, t in (NAV_EN if en else NAV_AR))
    return '<nav class="tabs" style="display:flex;overflow-x:auto;white-space:nowrap;gap:6px;scrollbar-width:none" aria-label="%s">%s</nav>' % ('Sections' if en else 'الأقسام', items)

def rebrand(h, rel):
    en = rel.startswith('en/')
    h = re.sub(r'<nav class="tabs"[^>]*>.*?</nav>', lambda m: nav(rel, en), h, count=1, flags=re.S)
    h = h.replace(AWE + '/' + rel, RB + '/' + rel)
    # canonical / hreflang / og:url of the other language version of the same page
    other = rel[3:] if en else 'en/' + rel
    h = h.replace(AWE + '/' + other, RB + '/' + other)
    # links back to the gift shop (not the logo, which is the wholesale home here)
    h = re.sub(r'(<a(?![^>]*class="logo")[^>]*href=")\./(")', r'\1' + AWE + r'/\2', h)
    h = re.sub(r'href="/#', 'href="' + AWE + '/#', h)
    h = h.replace('جملة أو فلورا', 'روع النباتات').replace('أو فلورا', 'روع النباتات')
    h = h.replace('Awe Floral wholesale', 'Rawnbatat').replace('Awe Floral', 'Rawnbatat')
    # site pages that stay on Awe Floral (about, terms, delivery, guides, ...): absolute links there
    h = re.sub(r'href="/(?!' + PATH + r'|assets/|img/|en/"|#)([a-z][^"]*)"', lambda m: 'href="' + AWE + '/' + m.group(1) + '"', h)
    h = world(h)
    # a product's smallest quantity is not the order minimum: name it «أقل كمية» so it doesn't read as the cart minimum
    h = h.replace("'أقل طلب '", "'أقل كمية '").replace('<span class="tpk">أقل طلب ', '<span class="tpk">أقل كمية ').replace('الأصناف اللي أقل طلب لها', 'الأصناف اللي أقل كمية منها')
    h = h.replace("'Min order '", "'Min qty '").replace('<span class="tpk">Min order ', '<span class="tpk">Min qty ').replace('>Lowest order total<', '>Lowest minimum qty total<')
    # what «no minimum» means, and each section's own minimum and delivery promise, in the top bar
    base = rel[3:] if en else rel
    ann = {('bunches.html', 0): 'جملة · بدون حد أدنى، تقدر تطلب ربطة وحدة · توصيل مجاني داخل الرياض، ونفس اليوم للطلبات الصباحية',
           ('stock.html', 0): 'من مخزوننا في الرياض · بدون حد أدنى، تقدر تطلب ربطة وحدة · يوصلك نفس اليوم',
           ('holland.html', 0): 'مستورد · الحد الأدنى 300 ر.س · اطلب قبل الأحد 5 العصر ويوصلك الأربعاء',
           ('holland-small.html', 0): 'كميات صغيرة · الحد الأدنى 150 ر.س · اطلب قبل الأحد 5 العصر ويوصلك الأربعاء',
           ('bunches.html', 1): 'Wholesale · No minimum, one bunch is fine · Free delivery in Riyadh, same day for morning orders',
           ('stock.html', 1): 'From our Riyadh stock · No minimum, one bunch is fine · Delivered the same day',
           ('holland.html', 1): 'Imported · Minimum order 300 SAR · Order by Sunday 5 pm, delivered Wednesday',
           ('holland-small.html', 1): 'Small boxes · Minimum order 150 SAR · Order by Sunday 5 pm, delivered Wednesday'}.get((base, int(en)))
    if ann: h = re.sub(r'(<div class="announce" id="announce">)[^<]*(</div>)', lambda m: m.group(1) + ann + m.group(2), h, count=1)
    h = re.sub(r'(<a class="logo"[^>]*><b>[^<]*</b><span>)[^<]*(</span>)', lambda m: m.group(1) + ('Wholesale' if en else 'جملة') + m.group(2), h)
    # no «install Awe Floral» prompt on the wholesale site
    h = re.sub(r'<link rel="manifest"[^>]*>', '', h)
    h = re.sub(r'<script src="/?pwa\.js"[^>]*></script>', '', h)
    h = h.replace('"https://www.awefloral.com/#florist"', '"' + RB + '/#org"')
    # prices come from the supplier list (updated by hand); Riyadh availability is live: the date is the prices' date
    h = h.replace("'آخر تحديث للأسعار والتوفر: '", "'آخر تحديث للأسعار: '").replace("'Prices and availability last updated: '", "'Prices last updated: '")
    h = h.replace('<span class="tpk">أقل كمية ', '<span class="tpk">العبوات تبدأ من ').replace('<span class="tpk">Min qty ', '<span class="tpk">Packs from ')
    h = h.replace("const TRACK = '" + AWE + "/track.html'", "const TRACK = '" + RB + "/track.html'").replace("const TRACK = '" + AWE + "/en/track.html'", "const TRACK = '" + RB + "/en/track.html'")
    # «my orders» on this site: the wholesale orders placed from this browser (not the gift shop's account page)
    h = re.sub(r'(id="mineBtn" href=")[^"]*(")', lambda m: m.group(1) + ('/en/orders.html' if en else '/orders.html') + m.group(2), h)
    h = h.replace('aria-label="حسابي وطلباتي"', 'aria-label="طلباتي بالجملة"').replace('aria-label="My account and orders"', 'aria-label="My wholesale orders"')
    # the import pages: the basket minimum, shown before choosing
    mn = {'holland.html': 300, 'holland-small.html': 150}.get(base)
    if mn:
        # right under the page title, in the line about full bunches and prices
        lead = ('<p>Full bunches · ', '<p>Basket minimum %d SAR incl. VAT, mix any varieties · Full bunches · ' % mn) if en else ('<p>بالربطة الكاملة · ', '<p><b>الحد الأدنى للسلة %d ر.س شامل الضريبة، وتقدر تجمع أكثر من صنف</b> · بالربطة الكاملة · ' % mn)
        h = h.replace(lead[0], lead[1], 1)
    return h

ORD = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rb_orders.html'), encoding='utf-8').read()
def orders_pages():
    for en in (False, True):
        T = {'LANG': 'en' if en else 'ar', 'DIR': 'ltr' if en else 'rtl', 'ISEN': 'true' if en else 'false', 'BRAND': 'Rawnbatat' if en else 'روع النباتات',
             'TITLE': 'My wholesale orders' if en else 'طلباتي بالجملة', 'HOME': '/en/' if en else '/', 'BACK': 'Shop' if en else 'تسوّق',
             'HINT': 'Orders placed from this device. On another device, open the order link we sent you on WhatsApp, or sign in from Shop account.' if en
                     else 'الطلبات اللي سويتها من هذا الجهاز. من جهاز ثاني، افتح رابط الطلب اللي أرسلناه لك على الواتساب، أو ادخل من «حساب المحل».'}
        h = ORD
        for k, v in T.items(): h = h.replace('{{' + k + '}}', v)
        out = os.path.join(D, 'rb', 'en' if en else '', 'orders.html')
        os.makedirs(os.path.dirname(out), exist_ok=True); open(out, 'w', encoding='utf-8').write(h)

def main():
    n_rb = n_link = 0
    for f, rel in list(pages()):
        if WH.match(rel):
            h = open(f, encoding='utf-8').read()
            out = os.path.join(D, 'rb', rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, 'w', encoding='utf-8').write(rebrand(h, rel))
            os.remove(f); n_rb += 1
        elif rel in ('track.html', 'en/track.html'):   # the order page: on both sites (the page sends each order to its own one)
            out = os.path.join(D, 'rb', rel); os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, 'w', encoding='utf-8').write(rebrand(open(f, encoding='utf-8').read(), rel))
    for f in [os.path.join(D, 'holland.json')] + glob.glob(os.path.join(D, 'holland-all', '*.json')):
        if os.path.exists(f): x = open(f, encoding='utf-8').read(); open(f, 'w', encoding='utf-8').write(world(x))
    # Awe Floral pages: wholesale links go to the new domain
    rx = re.compile(r'href="(https://www\.awefloral\.com/|/|\./)?(' + PATH + r')([?#][^"]*)?"')
    for f, rel in pages():
        h = open(f, encoding='utf-8').read()
        base = os.path.dirname(rel)
        def fix(m):
            pre, p = m.group(1), m.group(2)
            if pre in (None, './') and base and not p.startswith(base + '/'): p = base + '/' + p   # relative to the page's folder
            return 'href="' + RB + '/' + p + (m.group(3) or '') + '"'
        h2 = rx.sub(fix, h)
        # relative links inside a folder (e.g. en/ pages linking to "bunches.html")
        if h2 != h: n_link += 1; open(f, 'w', encoding='utf-8').write(h2)
    # sitemaps
    sm = os.path.join(D, 'sitemap.xml')
    if os.path.exists(sm):
        x = open(sm, encoding='utf-8').read()
        urls = re.findall(r'<url>.*?</url>', x, re.S)
        keep, moved = [], []
        for u in urls:
            loc = re.search(r'<loc>([^<]+)</loc>', u).group(1)
            rel = loc.replace(AWE + '/', '')
            (moved if WH.match(rel) else keep).append(u)
        head = x[:x.index('<url>')]
        open(sm, 'w', encoding='utf-8').write(head + '\n'.join(keep) + '\n</urlset>\n')
        rbm = [u.replace(AWE + '/', RB + '/') for u in moved]
        rbm.insert(0, '<url><loc>' + RB + '/</loc><priority>1.0</priority></url>')
        open(os.path.join(D, 'rb', 'sitemap.xml'), 'w', encoding='utf-8').write(head + '\n'.join(rbm) + '\n</urlset>\n')
    orders_pages()
    open(os.path.join(D, 'rb', 'robots.txt'), 'w').write('User-agent: *\nAllow: /\nSitemap: ' + RB + '/sitemap.xml\n')
    print('rawnbatat pages:', n_rb, '· awefloral pages relinked:', n_link)

main()
