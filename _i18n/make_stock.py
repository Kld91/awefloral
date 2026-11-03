"""Build stock.html (our own stock: sb 'own' in catalog.json) from bunches.html. Same code, cart and checkout; only our own items,
its own dashboard lock (/avail own.closed) and its own wording. Re-run after editing bunches.html, then build_en.py.
usage: python3 _i18n/make_stock.py [SITE_DIR]"""
import re, os, sys
R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
s = open(os.path.join(R, 'bunches.html'), encoding='utf-8').read()
REPL = [
    ("const OWN_ONLY = false;", "const OWN_ONLY = true;"),
    ("const SHUT_KEY = 'bn';", "const SHUT_KEY = 'own';"),
    ('<title>ورد جملة الرياض · بنشات ورد طبيعي بدون حد أدنى | أو فلورا</title>', '<title>من مخزوننا · كريز سبراي بالجملة في الرياض | أو فلورا</title>'),
    (re.compile(r'<meta name="description" content="[^"]*">'), '<meta name="description" content="ورد من مخزوننا في الرياض: كريز سبراي بطول 70–80 سم، بنش 10 أغصان، بسعر واضح للغصن، ويوصلك نفس اليوم مع توصيل مجاني. اطلب وادفع من الموقع.">'),
    (re.compile(r'<meta property="og:title" content="[^"]*">'), '<meta property="og:title" content="من مخزوننا · كريز سبراي بالجملة | أو فلورا">'),
    ('https://www.awefloral.com/bunches.html', 'https://www.awefloral.com/stock.html'),
    ('href="/en/bunches.html"', 'href="/en/stock.html"'),
    ('https://www.awefloral.com/en/bunches.html', 'https://www.awefloral.com/en/stock.html'),
    ('<h1>بنشات الورد</h1>', '<h1>من مخزوننا</h1>'),
    ('<span class="num" id="heroCount"></span> صنف من هولندا وكينيا وكولومبيا والسعودية</p>', '<span class="num" id="heroCount"></span> صنف جاهز في مستودعنا بالرياض</p>'),
    ('<b>طلبات الجملة من الرياض متوقفة مؤقتاً</b>', '<b>أصناف مخزوننا متوقفة مؤقتاً</b>'),
    (re.compile(r'\n\s*<a class="ownb" id="ownBan".*?<!--/own-->', re.S), ''),
]
for a, b in REPL:
    if isinstance(a, re.Pattern): s, n = a.subn(b, s)
    else: n = s.count(a); s = s.replace(a, b)
    if not n: raise SystemExit('not found: ' + (a.pattern if isinstance(a, re.Pattern) else a)[:90])
s = s.replace('<a class="btn" href="bunches.html"', '<a class="btn" href="stock.html"')
open(os.path.join(R, 'stock.html'), 'w', encoding='utf-8').write(s)
print('stock.html built')
