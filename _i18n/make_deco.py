"""Build accessories.html (florists' accessories that ride on the weekly Holland shipment) from holland.html.
Same cart, payment and 300 SAR minimum as the Holland page; the data is accessories.json (built privately, prices only).
Orders are Holland-shipment orders (NL-), priced by the order worker from holland-all/p/.
Run after make_holland.py:  python3 _i18n/make_deco.py SITE_DIR"""
import os, re, sys
R = sys.argv[1] if len(sys.argv) > 1 else '.'
s = open(os.path.join(R, 'holland.html'), encoding='utf-8').read()

def rep(a, b, n=1):
    global s
    if s.count(a) < 1: raise SystemExit('make_deco: not found: ' + a[:70])
    s = s.replace(a, b) if n == 0 else s.replace(a, b, n)

rep("fetch('holland.json'", "fetch('accessories.json'")
rep("const PAGE_KEY = 'holland';", "const PAGE_KEY = 'deco';")
s = re.sub(r'<title>[^<]*</title>', '<title>إكسسوارات المنسّقين بالجملة: مزهريات، تغليف، إسفنج | أو فلورا</title>', s, count=1)
s = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="مزهريات زجاج وسيراميك، ورق وسيلوفان تغليف، شرائط، إسفنج زهور ومغذي، من هولندا مع شحنة الثلاثاء. السعر شامل الشحن والتخليص والضريبة، والتوصيل مجاني داخل الرياض.">', s, count=1)
s = s.replace('https://www.awefloral.com/holland.html', 'https://www.awefloral.com/accessories.html')
s = re.sub(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="إكسسوارات المنسّقين بالجملة | أو فلورا">', s, count=1)
# the type photos are flower photos: the accessories use their own first photo
s = re.sub(r'const TYPE_IMG = \{.*?\};', 'const TYPE_IMG = {};', s, count=1, flags=re.S)
# hero: title, line, and a link back to the flowers; no gerbera photo, no flower story
s = re.sub(r'\s*<img class="adx-ph"[^>]*>', '', s, count=1)
rep('<h1>ورد هولندي بالجملة</h1>', '<h1>إكسسوارات المنسّقين</h1>')
s, k = re.subn(r'<p>بالربطة الكاملة · السعر شامل الشحن والتخليص والضريبة · توصيل مجاني بالرياض · <a href="holland-small.html">تبي كمية صغيرة؟</a>(?: · <a href="accessories.html">إكسسوارات المنسّقين</a>)?</p>',
                '<p>مزهريات وتغليف وإسفنج من هولندا مع شحنة الثلاثاء · السعر شامل الشحن والتخليص والضريبة · <a href="holland.html">ورد هولندا بالجملة</a></p>', s, count=1)
if k != 1: raise SystemExit('make_deco: hero line not found')
s = re.sub(r'\n    <section class="why".*?\n    </section>', '', s, count=1, flags=re.S)
rep('placeholder="ابحث: رانونكولس، كالا، توليب…"', 'placeholder="ابحث: فازة زجاج، ورق تغليف، إسفنج…"')
s = re.sub(r'\s*<p class="tlinks">.*?</p>', '', s, count=1, flags=re.S)   # links to the flower type pages
open(os.path.join(R, 'accessories.html'), 'w', encoding='utf-8').write(s)
print('accessories.html written')
