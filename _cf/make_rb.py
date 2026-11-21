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
    # no «install Awe Floral» prompt on the wholesale site
    h = re.sub(r'<link rel="manifest"[^>]*>', '', h)
    h = re.sub(r'<script src="/?pwa\.js"[^>]*></script>', '', h)
    h = h.replace('"https://www.awefloral.com/#florist"', '"' + RB + '/#org"')
    return h

def main():
    n_rb = n_link = 0
    for f, rel in list(pages()):
        if WH.match(rel):
            h = open(f, encoding='utf-8').read()
            out = os.path.join(D, 'rb', rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, 'w', encoding='utf-8').write(rebrand(h, rel))
            os.remove(f); n_rb += 1
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
    open(os.path.join(D, 'rb', 'robots.txt'), 'w').write('User-agent: *\nAllow: /\nSitemap: ' + RB + '/sitemap.xml\n')
    print('rawnbatat pages:', n_rb, '· awefloral pages relinked:', n_link)

main()
