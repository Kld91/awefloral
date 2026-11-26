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
POL = r'(?:en/)?(?:terms|returns|delivery|about|orders|privacy)\.html"'   # the wholesale policy pages (built from _cf/rb_policies)
PATH = r'(?:en/)?(?:(?:bunches|holland|holland-small|stock|accessories|business)\.html|(?:holland|wholesale)/(?:[a-z0-9-]+\.html)?)'

def pages():
    for f in glob.glob(os.path.join(D, '**', '*.html'), recursive=True):
        r = os.path.relpath(f, D).replace(os.sep, '/')
        if not r.startswith('rb/'): yield f, r

NAV_AR = [('/', 'الرئيسية'), ('/holland-small.html', 'كميات صغيرة'), ('/accessories.html', 'إكسسوارات'), ('/business.html', 'حساب المحل')]   # Riyadh stock (bunches, stock) is off for now; it comes back later as «اكسبرس»
NAV_EN = [('/en/', 'Home'), ('/en/holland-small.html', 'Small boxes'), ('/en/accessories.html', 'Accessories'), ('/en/business.html', 'Shop account')]

# the import pages: flowers from markets worldwide, not «Holland» (applied to the pages and to their data files alike)
WORLD = [
    ("NL:'هولندا'", "NL:'@@NLAR@@'"), ("NL:'Holland'", "NL:'@@NLEN@@'"), ('<span>هولندا</span>', '<span>@@NLAR@@</span>'), ('<span>Netherlands</span>', '<span>@@NLEN@@</span>'),
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
    if rel in ('holland.html', 'en/holland.html'): here = '/en/' if en else '/'
    items = ''.join('<a href="%s"%s>%s</a>' % (u, ' aria-current="page"' if u == here else '', t) for u, t in (NAV_EN if en else NAV_AR))
    return '<nav class="tabs" style="display:flex;overflow-x:auto;white-space:nowrap;gap:6px;scrollbar-width:none" aria-label="%s">%s</nav>' % ('Sections' if en else 'الأقسام', items)

from urllib.parse import quote
WA_AR_OLD = 'text=' + quote('السلام عليكم، أبي أعرف المتاح من جملة الرياض')
WA_AR_NEW = 'text=' + quote('السلام عليكم، عندي استفسار عن طلب جملة')
base_of = lambda rel: rel[3:] if rel.startswith('en/') else rel
import json
def ld(txt):
    # structured data: the seller is Rawnbatat (not the gift shop's Florist entry), every address on this site
    try: j = json.loads(txt)
    except Exception: return txt
    def walk(x):
        if isinstance(x, dict):
            if x.get('@type') == 'Florist':
                return {'@type': 'WholesaleStore', '@id': RB + '/#org', 'name': 'روع النباتات', 'alternateName': 'Rawnbatat', 'legalName': x.get('legalName', 'شركة روع النباتات للتجارة'),
                        'url': RB + '/', 'vatID': x.get('vatID'), 'telephone': x.get('telephone'), 'address': x.get('address'), 'areaServed': x.get('areaServed'), 'currenciesAccepted': 'SAR'}
            if x.get('@type') == 'BreadcrumbList' and isinstance(x.get('itemListElement'), list):
                its = [i for i in x['itemListElement'] if not re.search(r'/(en/)?(bunches|stock)\.html$', str(i.get('item', '')))]
                for n, i in enumerate(its, 1): i['position'] = n
                x['itemListElement'] = its
            return {k: walk(v) for k, v in x.items() if v is not None}
        if isinstance(x, list): return [walk(v) for v in x]
        if isinstance(x, str):
            x = re.sub(re.escape(AWE) + r'/(en/)?#florist', RB + '/#org', x)
            x = re.sub(re.escape(AWE) + r'/(' + PATH + r')', RB + r'/\1', x)
            if x in (AWE + '/', AWE + '/en/'): x = x.replace(AWE, RB)
            return x
        return x
    return json.dumps(walk(j), ensure_ascii=False)

_BADGE = '<div style="background:#fff;border:1px solid #E4E1DA;border-radius:10px;padding:9px 11px"><b style="display:block;font-size:13.5px">%s</b><span style="font-size:12.5px;color:#5A5F67;line-height:1.6">%s</span></div>'
def _trust(about, badges, more, href):
    return ('<div class="rb-trust" style="margin:6px 0 10px"><p style="margin:0 0 8px;color:#4A4F57;line-height:1.75">%s <a href="%s" style="color:inherit">%s</a></p>' % (about, href, more)
            + '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px">' + ''.join(_BADGE % b for b in badges) + '</div></div>')
TRUST_AR = _trust('روع النباتات شركة سعودية في الرياض، نستورد الورد بأنفسنا كل أسبوع ونبيعه بالجملة للمحلات والفنادق ومنظمي المناسبات. نورّد لفروع سلسلة سوبرماركت كبرى في الرياض، ولدينا مستودع مركزي وغرفة تبريد في الرياض.',
    [('سجل تجاري ورقم ضريبي', 'شركة روع النباتات للتجارة · س.ت 7030369826'), ('استيراد أسبوعي', 'اطلب قبل الأحد 5 العصر، ويوصلك الأربعاء'),
     ('ضمان الكمية', 'إذا نقص صنف نرجع قيمته كاملة أو بديل توافق عليه'), ('دفع آمن', 'مدى والبطاقات عبر Tap، أو تمارا')], 'من نحن ←', '/about.html')
TRUST_EN = _trust('Rawnbatat is a Saudi company in Riyadh. We import our own flowers every week and sell them wholesale to florists, hotels and event planners. We supply the branches of a major supermarket chain in Riyadh, and have a central warehouse and cold room in Riyadh.',
    [('Registered company', 'Raw Alnabatat Trading Co. · CR 7030369826'), ('Weekly import', 'Order by Sunday 5 pm, delivered Wednesday'),
     ('Quantity guarantee', 'A missing variety is refunded in full, or a substitute you approve'), ('Secure payment', 'mada and cards via Tap, or Tamara')], 'About us →', '/en/about.html')
FAQ_AR = ("  ['مين روع النباتات؟', 'شركة روع النباتات للتجارة في الرياض (سجل تجاري 7030369826، رقم ضريبي 311382735100003). نستورد الورد بأنفسنا كل أسبوع، ونورّد لفروع سلسلة سوبرماركت كبرى في الرياض، ولدينا مستودع مركزي وغرفة تبريد في الرياض.'],\n"
          "  ['فيه حساب للمحلات والمنشآت؟', 'نعم. من صفحة «حساب المحل» تشحن رصيد مسبق وتطلب منه، أو تطلب حساب آجل للمنشآت بعد التحقق من السجل التجاري.'],\n")
FAQ_EN = ("  ['Who is Rawnbatat?', 'Raw Alnabatat Trading Co., Riyadh (CR 7030369826, VAT 311382735100003). We import our own flowers every week, supply the branches of a major supermarket chain in Riyadh, and have a central warehouse and cold room in Riyadh.'],\n"
          "  ['Is there an account for shops and companies?', 'Yes. From Shop account you can top up a prepaid balance and order from it, or apply for credit after we check your commercial registration.'],\n")

def rebrand(h, rel):
    en = rel.startswith('en/')
    h = re.sub(r'<nav class="tabs"[^>]*>.*?</nav>', lambda m: nav(rel, en), h, count=1, flags=re.S)
    # «book now, pay after we confirm» is switched off at checkout (RESERVE_ON = false): no page promises it
    if 'const RESERVE_ON = false' in h:
        for x, y in [('احجز بدون دفع ونرسل لك رابط الدفع بعد التأكيد، أو ادفع الحين بمدى', 'ادفع بمدى'),
                     ('لك خيارين: تدفع الحين من الموقع (مدى أو Apple Pay أو بطاقة أو تمارا)، أو تحجز بدون دفع ونرسل لك رابط الدفع على الواتساب بعد ما نأكد الكميات والسعر. ادفع قبل', 'تدفع من الموقع بمدى أو Apple Pay أو بطاقة أو تمارا. ادفع قبل'),
                     ('احجز بدون دفع وادفع بعد التأكيد، أو ادفع الحين. ', ''),
                     ('Book without paying and we send you the payment link once confirmed, or pay now with mada', 'Pay with mada'),
                     ('Two ways: pay now on the site (mada, Apple Pay, card or Tamara), or book without paying and we send you the payment link on WhatsApp once we confirm the quantities and price. Pay before', 'Pay on the site with mada, Apple Pay, card or Tamara. Pay before'),
                     ('Book without paying and pay once confirmed, or pay now. ', '')]:
            h = h.replace(x, y)
    h = re.sub(r'<a class="icon-btn" href="\./" aria-label="(باقات الهدايا|Gift bouquets)">.*?</a>', '', h, flags=re.S)
    h = h.replace('<a href="./">الباقات والهدايا ←</a>', '').replace('<a href="./">Bouquets and gifts →</a>', '')
    h = h.replace("  ['وصلني ورد فيه مشكلة؟'", FAQ_AR + "  ['وصلني ورد فيه مشكلة؟'", 1).replace("  ['Problem with your flowers?'", FAQ_EN + "  ['Problem with your flowers?'", 1)
    h = re.sub(r'<script type="application/ld\+json">(.*?)</script>', lambda m: '<script type="application/ld+json">' + ld(m.group(1)) + '</script>', h, flags=re.S)
    h = h.replace(AWE + '/' + rel, RB + '/' + rel)
    # every wholesale address on Awe Floral (item lists, breadcrumbs, the other pages) is on this site now
    h = re.sub(re.escape(AWE) + r'/(' + PATH + r')', RB + r'/\1', h)
    # the cart opens on the home page here (the type pages have no cart of their own), not the gift shop's cart
    h = h.replace('href="/#/cart" data-go="/#/cart"', 'href="%s?cart=1" data-go="%s?cart=1"' % (('/en/',) * 2 if en else ('/',) * 2))
    h = h.replace('href="/en/#/cart" data-go="/en/#/cart"', 'href="/en/?cart=1" data-go="/en/?cart=1"')
    if base_of(rel) in ('holland.html', 'holland-small.html'):
        h = h.replace('</body>', '<script>if(/[?&]cart=1\\b/.test(location.search))addEventListener("load",function(){var b=document.getElementById("cartBtn");if(b)b.click()})</script></body>', 1)
    # «sign in» and «my orders» in the cart: this site's orders page and shop account
    h = h.replace('<a href="/#/orders">سجّل دخول</a>', '<a href="/business.html">سجّل دخول</a>').replace('<a href="/en/#/orders">Sign in</a>', '<a href="/en/business.html">Sign in</a>')
    h = h.replace('href="/#/orders"', 'href="/orders.html"').replace('href="/en/#/orders"', 'href="/en/orders.html"')
    # Riyadh stock is off: the WhatsApp question and the closed notice are about the import orders
    h = h.replace(WA_AR_OLD, WA_AR_NEW).replace('text=Hello%2C%20I%20would%20like%20to%20know%20what%20is%20available%20in%20Riyadh%20wholesale', 'text=Hello%2C%20I%20have%20a%20question%20about%20a%20wholesale%20order')
    h = h.replace('جملة الرياض متوقفة مؤقتاً', 'الطلب متوقف مؤقتاً').replace('Riyadh wholesale orders are paused for now', 'Ordering is paused for now').replace('Riyadh wholesale paused', 'Ordering paused')
    # canonical / hreflang / og:url of the other language version of the same page
    other = rel[3:] if en else 'en/' + rel
    h = h.replace(AWE + '/' + other, RB + '/' + other)
    # links back to the gift shop (not the logo, which is the wholesale home here)
    h = re.sub(r'(<a(?![^>]*class="logo")[^>]*href=")\./(")', r'\1' + AWE + r'/\2', h)
    h = re.sub(r'href="/#', 'href="' + AWE + '/#', h)
    h = h.replace('جملة أو فلورا', 'روع النباتات').replace('أو فلورا', 'روع النباتات')
    h = h.replace('Awe Floral wholesale', 'Rawnbatat').replace('Awe Floral', 'Rawnbatat')
    # site pages that stay on Awe Floral (about, terms, delivery, guides, ...): absolute links there
    h = re.sub(r'href="/(?!' + PATH + r'|' + POL + r'|assets/|img/|en/"|en/\?|#)([a-z][^"]*)"', lambda m: 'href="' + AWE + '/' + m.group(1) + '"', h)
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
    # Riyadh same-day stock is off for now: no link promising tomorrow's delivery
    h = h.replace('<a href="bunches.html">تبي ورد يوصل بكرة؟ شوف الجملة المتوفرة في الرياض ←</a>', '<span>اكسبرس الرياض (توصيل نفس اليوم) قريباً</span>')
    h = h.replace('<a href="bunches.html">Need flowers tomorrow? See wholesale stock in Riyadh →</a>', '<span>Riyadh Express (same-day delivery) coming soon</span>')
    # who we are, in one line under the home page title
    if base == 'holland.html':
        who = TRUST_EN if en else TRUST_AR
        h = h.replace('<h1>' + ('Imported flowers wholesale' if en else 'ورد مستورد بالجملة') + '</h1>', '<h1>' + ('Imported flowers wholesale' if en else 'ورد مستورد بالجملة') + '</h1>' + who, 1)
    if base == 'holland-small.html':
        h = h.replace('<h1>ورد مستورد بكميات صغيرة</h1><p>', '<h1>ورد مستورد بكميات صغيرة</h1><p><b>الحد الأدنى للسلة 150 ر.س شامل الضريبة</b> · ', 1)
    # nothing on this site points at the gift shop: its assets come from here, its pages and Instagram are not linked
    h = re.sub(re.escape(AWE) + r'/(img/|icon-|favicon|apple-touch|og\.jpg)', RB + r'/\1', h)
    h = h.replace('href="' + AWE + '/en/track.html', 'href="/en/track.html').replace('href="' + AWE + '/track.html', 'href="/track.html')
    h = re.sub(r'<a\b[^>]*href="https?://(?:www\.)?awefloral\.com[^"]*"[^>]*>.*?</a>', '', h, flags=re.S)
    h = re.sub(r'<a\b[^>]*href="https?://(?:www\.)?instagram\.com/awefloral[^"]*"[^>]*>.*?</a>', '', h, flags=re.S)
    h = re.sub(r'<a\b[^>]*href="mailto:info@awefloral\.com"[^>]*>.*?</a>', '', h, flags=re.S)
    h = h.replace('info@awefloral.com', '')
    h = h.replace("'https://www.awefloral.com' + u", "'" + RB + "' + u")
    if base == 'holland.html':   # the home page of this site
        h = h.replace('"' + RB + '/holland.html"', '"' + RB + '/"').replace('"' + RB + '/en/holland.html"', '"' + RB + '/en/"')
    if base in ('holland.html', 'holland-small.html'):   # preserved (stabilised) flowers: their own note and care, not the cut-flower ones
        h = h.replace("kind = (g && g.kind) || 'cut'", "kind = it.pv ? 'preserved' : ((g && g.kind) || 'cut')")
        h = h.replace("const care = [...(kind === 'cut'", "const care = [...(kind === 'preserved' ? PV_CARE : []), ...(kind === 'cut'")
        h = h.replace("const PV_NOTE = ", "const PV_CARE = %s;\nconst PV_NOTE_PV = %s;\nconst PV_NOTE = " % (
            "['Do not put it in water or spray it.', 'Keep it somewhere dry, away from direct sun and humidity.', 'Hold it by the stem or base: the petals are delicate.']" if en else
            "['لا تحطه في الماء ولا ترشه.', 'خله في مكان جاف بعيد عن الشمس المباشرة والرطوبة.', 'امسكه من الساق أو القاعدة، لأن البتلات حساسة.']",
            "'Preserved (stabilised) natural flower: it keeps its shape and colour for a long time without water.'" if en else
            "'ورد طبيعي معالَج (مشمّع): يحافظ على شكله ولونه فترة طويلة بدون ماء.'"), 1)
        h = h.replace(": PV_NOTE)}", ": kind === 'preserved' ? PV_NOTE_PV : PV_NOTE)}")
        h = h.replace("} طبيعي بالجملة${", "} ${it.pv ? 'دائم (مشمّع)' : 'طبيعي'} بالجملة${").replace("} — natural, sold wholesale${", "} — ${it.pv ? 'preserved' : 'natural'}, sold wholesale${")
    if base == 'accessories.html':   # supplies, not flowers: no «natural flowers» line, no flower-care note, a «how to use» tab
        h = h.replace("kind = (g && g.kind) || 'cut'", "kind = (g && g.kind) || 'supply'")
        # the «how to use» tab and section only when the item has usage notes
        h = re.sub(r'(<button type="button" data-jump="pv-care">\$\{kind === .supply. \? .[^\']*. : .[^\']*.\}</button>)', lambda m: '${care.length || cautions.length ? `' + m.group(1) + '` : \'\'}', h, count=1)
        h = re.sub(r'(<section class="pv-sec" id="pv-care">\s*)(<h4>.*?</h4>)', lambda m: m.group(1) + '${care.length || cautions.length ? `' + m.group(2) + '` : \'\'}', h, count=1, flags=re.S)
        h = h.replace("} طبيعي بالجملة${", "} بالجملة${").replace("} — natural, sold wholesale${", "}, sold wholesale${")
    if base == 'accessories.html':   # its English version (the source page points at the import page)
        h = h.replace('hreflang="en" href="' + RB + '/en/holland.html"', 'hreflang="en" href="' + RB + '/en/accessories.html"').replace('data-lang="en" href="/en/holland.html"', 'data-lang="en" href="/en/accessories.html"')
    if base == 'holland-small.html':   # the server checks this page's basket minimum (150 SAR) and sends the payer back here
        h = h.replace('JSON.stringify(Object.assign({ vid: VID, src: SRC,', "JSON.stringify(Object.assign({ vid: VID, pg: 'small', src: SRC,")
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

POLICY = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rb_policy.html'), encoding='utf-8').read()
POL_NAMES = [('about', 'من نحن', 'About us'), ('terms', 'شروط البيع', 'Terms of sale'), ('delivery', 'التوصيل', 'Delivery'), ('returns', 'الجودة والاسترجاع', 'Quality and returns')]
def policy_pages():
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rb_policies')
    for en in (False, True):
        lg = 'en' if en else 'ar'
        links = ''.join('<a href="%s/%s.html">%s</a>' % ('/en' if en else '', k, e if en else a) for k, a, e in POL_NAMES)
        links += '<a href="%s/privacy.html">%s</a>' % ('/en' if en else '', 'Privacy' if en else 'الخصوصية')
        legal = ('Raw Alnabatat Trading Co. · Riyadh · CR 7030369826 · VAT 311382735100003 · WhatsApp <a href="https://wa.me/966539804321" dir="ltr">0539804321</a>' if en
                 else 'شركة روع النباتات للتجارة · الرياض · سجل تجاري 7030369826 · الرقم الضريبي 311382735100003 · واتساب <a href="https://wa.me/966539804321" dir="ltr">0539804321</a>')
        # privacy: one policy for the whole company (the gift shop's page), shown here under this site's name
        pv = open(os.path.join(D, 'en' if en else '', 'privacy.html'), encoding='utf-8').read()
        pv = re.search(r'<main>(.*?)</main>', pv, re.S).group(1)
        pv = re.sub(r'<nav[^>]*class="crumbs".*?</nav>', '', pv, flags=re.S)
        pv = re.sub(r'<a [^>]*href="[^"]*"[^>]*>الرئيسية</a>\s*/\s*|<a [^>]*href="[^"]*"[^>]*>Home</a>\s*/\s*', '', pv)
        pv = pv.replace(' (أو فلورا)', '').replace('(أو فلورا)', '').replace(' (Awe Floral)', '').replace('(Awe Floral)', '')
        pv = re.sub(r'href="/(?!/)', 'href="' + AWE + '/', pv)
        for k, a, e in POL_NAMES + [('privacy', 'الخصوصية', 'Privacy')]:
            own = os.path.join(src, '%s.%s.html' % (k, lg))   # the wholesale site's own privacy page (27 Nov): no gift-shop sections, no links to the gift shop
            body = open(own, encoding='utf-8').read() if os.path.exists(own) else pv
            title = re.search(r'<h1>(.*?)</h1>', body).group(1)
            desc = re.sub(r'<[^>]+>', '', re.search(r'<p>(.*?)</p>', body, re.S).group(1))[:155]
            T = {'LANG': lg, 'DIR': 'ltr' if en else 'rtl', 'TITLE': title, 'BRAND': 'Rawnbatat' if en else 'روع النباتات', 'DESC': desc.replace('"', "'"),
                 'PATH': ('en/' if en else '') + k + '.html', 'AR': k + '.html', 'EN': 'en/' + k + '.html', 'HOME': '/en/' if en else '/', 'WS': 'Wholesale' if en else 'جملة',
                 'OTHER': k + '.html' if en else 'en/' + k + '.html', 'OLANG': 'ar' if en else 'en', 'OLABEL': 'عربي' if en else 'English', 'BODY': body, 'LINKS': links, 'LEGAL': legal}
            h = POLICY
            for kk, v in T.items(): h = h.replace('{{' + kk + '}}', v)
            out = os.path.join(D, 'rb', 'en' if en else '', k + '.html')
            os.makedirs(os.path.dirname(out), exist_ok=True); open(out, 'w', encoding='utf-8').write(h)
        if not en:   # this site's «not found» page
            body = '<h1>الصفحة غير موجودة · Page not found</h1><p>الرابط اللي فتحته ما عاد موجود. <a href="/">ارجع للرئيسية</a> أو راسلنا على الواتساب.</p><p dir="ltr">This link no longer exists. <a href="/en/">Go to the home page</a>.</p>'
            h = POLICY
            for kk, v in dict(T, TITLE='الصفحة غير موجودة', BODY=body, DESC='', PATH='', AR='', EN='en/').items(): h = h.replace('{{' + kk + '}}', v)
            h = h.replace('<link rel="canonical" href="https://www.rawnbatat.com/">', '<meta name="robots" content="noindex">')
            open(os.path.join(D, 'rb', '404.html'), 'w', encoding='utf-8').write(h)

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
    for f in [os.path.join(D, 'holland.json'), os.path.join(D, 'en', 'holland.json')] + glob.glob(os.path.join(D, 'holland-all', '*.json')) + glob.glob(os.path.join(D, 'en', 'holland-all', '*.json')):
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
    policy_pages()
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
        # this site's sitemap: its open pages (Riyadh stock is off), the home page as /
        rbm = []
        for f in sorted(glob.glob(os.path.join(D, 'rb', '**', '*.html'), recursive=True)):
            r = os.path.relpath(f, os.path.join(D, 'rb')).replace(os.sep, '/')
            if re.match(r'^(en/)?((bunches|stock|orders|track)\.html|wholesale/)', r): continue
            loc = RB + '/' + ({'holland.html': '', 'en/holland.html': 'en/'}.get(r, r))
            pr = '1.0' if r in ('holland.html', 'en/holland.html') else '0.6' if '/' in r.replace('en/', '', 1) else '0.8'
            rbm.append('<url><loc>%s</loc><priority>%s</priority></url>' % (loc, pr))
        open(os.path.join(D, 'rb', 'sitemap.xml'), 'w', encoding='utf-8').write(head + '\n'.join(rbm) + '\n</urlset>\n')
    orders_pages()
    open(os.path.join(D, 'rb', 'robots.txt'), 'w').write('User-agent: *\nAllow: /\nSitemap: ' + RB + '/sitemap.xml\n')
    print('rawnbatat pages:', n_rb, '· awefloral pages relinked:', n_link)

main()
