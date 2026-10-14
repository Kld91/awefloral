"""Build holland.html (wholesale import from the Netherlands) from bunches.html.
The two pages share all code; this swaps the data file, the wording, the cart key and the delivery rules.
Re-run after editing bunches.html, then run build_en.py.  usage: python3 _i18n/make_holland.py [SITE_DIR]"""
import re, os, sys

R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SITE = 'https://www.awefloral.com'
s = open(os.path.join(R, 'bunches.html'), encoding='utf-8').read()

WHEN = 'شحنة هولندا الأسبوعية'
FAQ = """const FAQ = [
  ['متى يوصل الطلب؟', 'نستورد من هولندا كل أسبوع. نجمع الطلبات ونشحنها مع شحنتنا الأسبوعية، ونأكد لك موعد الوصول على الواتساب. الكميات الكبيرة ننسقها معك خلال يومين.'],
  ['ليش الكمية بالربطة الكاملة؟', 'نطلب لك من المزارع والمزادات في هولندا بنفس الكمية اللي تنباع فيها هناك، والطلب هناك ما يتلغى. عشان كذا البيع بالربطة الكاملة.'],
  ['السعر يشمل إيش؟', 'سعر الغصن شامل الشحن من هولندا والتخليص والضريبة. أسعار هولندا تتغير كل يوم، والسعر اللي تدفعه هو المكتوب لحظة الدفع.'],
  ['لو ما توفر الصنف؟', 'السعر يثبت لك لحظة الدفع. وإذا ما توفر صنف من طلبك في هولندا، نرجع لك قيمته كاملة أو نعطيك بديل توافق عليه.'],
  ['كيف أدفع؟', 'تدفع من الموقع بمدى أو Apple Pay أو بطاقة. الدفع كامل مقدماً، ونطلب من هولندا بعد الدفع، وبعدها الطلب ما يتلغى.'],
  ['كم رسوم التوصيل؟', 'التوصيل مجاني داخل الرياض.'],
  ['اللون بيكون نفس الصورة؟', 'الورد طبيعي، فاللون والشكل ممكن يختلف شوي حسب الموسم والشحنة. الصورة توضح الصنف.'],
  ['وصلني ورد فيه مشكلة؟', 'إذا وصل مكسور أو ذابل أو غير اللي طلبته، صوّره وأرسله لنا خلال 6 ساعات من الاستلام، ونبدله أو نرجع لك المبلغ.']
];"""

REPL = [
    ('<title>ورد جملة الرياض · بنشات ورد طبيعي بدون حد أدنى | أو فلورا</title>',
     '<title>ورد هولندي بالجملة في الرياض · استيراد مباشر أسبوعي | أو فلورا</title>'),
    (re.compile(r'<meta name="description" content="[^"]*">'),
     '<meta name="description" content="استيراد مباشر من هولندا بالجملة: رانونكولس، كالا، توليب، أنيمون، فاوانيا، بروتيا وغيرها. شحنة أسبوعية للرياض، والسعر شامل الشحن والتخليص والضريبة.">'),
    ('content="ورد جملة الرياض · بنشات ورد طبيعي | أو فلورا"', 'content="ورد هولندي بالجملة · استيراد مباشر | أو فلورا"'),
    (re.compile(r'<meta property="og:description" content="[^"]*">'),
     '<meta property="og:description" content="أصناف هولندية مميزة بالجملة، شحنة أسبوعية للرياض، شامل الشحن والتخليص والضريبة.">'),
    (SITE + '/bunches.html', SITE + '/holland.html'),                     # canonical, og:url, hreflang, JSON-LD
    ('"name": "ورد جملة الرياض"', '"name": "ورد هولندي بالجملة"'),
    ('"name": "الجملة", "item": "' + SITE + '/holland.html"',
     '"name": "الجملة", "item": "' + SITE + '/bunches.html"}, {"@type": "ListItem", "position": 3, "name": "استيراد من هولندا", "item": "' + SITE + '/holland.html"'),
    ('href="/en/bunches.html"', 'href="/en/holland.html"'),
    (SITE + '/en/bunches.html', SITE + '/en/holland.html'),               # hreflang="en" points at the English Holland page
    ('<p>بنشات الورد بالجملة</p>', '<p>استيراد من هولندا بالجملة</p>'),
    ('<div class="announce" id="announce">جملة · بدون حد أدنى · توصيل مجاني داخل الرياض</div>',
     '<div class="announce" id="announce">استيراد مباشر من هولندا · جملة · شحنة كل أسبوع</div>'),
    ('<span>بنشات الورد</span></a>', '<span>استيراد هولندا</span></a>'),
    ('<a href="holland.html">هولندا</a></nav>', '<a href="holland.html" aria-current="page">هولندا</a></nav>'),
    ('placeholder="ابحث: هدرنجا، توليب، Avalanche…"', 'placeholder="ابحث: رانونكولس، كالا، توليب…"'),
    ('<h1>بنشات الورد</h1>', '<h1>ورد هولندي بالجملة</h1>'),
    ('صنف من هولندا وكينيا وكولومبيا والسعودية</p>', 'صنف من مزارع ومزادات هولندا</p>'),
    ('بالربطة الكاملة · توصيل مجاني · بدون سجل تجاري · شامل الضريبة',
     'بالربطة الكاملة · توصيل مجاني داخل الرياض · شامل الشحن والتخليص والضريبة'),
    ('<p id="promise" style="margin:4px 0 0;padding:9px 12px;border-radius:8px;background:#EEF6F0;color:#1F6B3A;font-size:14px;line-height:1.5">توصيل مجاني داخل الرياض، ونفس اليوم للطلبات الصباحية.</p>',
     '<p class="hint" style="margin:0">نستورد كل أسبوع، والكميات الكبيرة ننسقها معك خلال يومين. طلبات جملة، والدفع مقدماً، والطلب ما يتلغى بعد الدفع.</p>'
     '<p style="margin:4px 0 0;font-size:13px"><a href="bunches.html">تبي ورد يوصل بكرة؟ شوف الجملة المتوفرة في الرياض ←</a></p>'),
    (re.compile(r'\n\s*<a class="nl" href="holland\.html".*?</a><!--/nl-->', re.S), ''),   # the Holland banner links here, so drop it
    ('<span>البيع بالربطة الكاملة، والسعر المكتوب للغصن.</span>', '<span>الكمية بالربطة الكاملة مثل ما تجي من هولندا.</span>'),
    ('<b>ادفع من الموقع</b><span>مدى أو Apple Pay أو بطاقة، من الموقع مباشرة.</span>',
     '<b>ادفع مقدماً من الموقع</b><span>مدى أو Apple Pay أو بطاقة، من الموقع مباشرة. بعد الدفع نطلب من هولندا والطلب ما يتلغى.</span>'),
    ('<b>نجهّز طلبك ونوصله</b><span>داخل الرياض، والتوصيل مجاني.</span>',
     '<b>نطلبه من هولندا ونوصله</b><span>مع الشحنة الأسبوعية، ونأكد لك موعد الوصول على الواتساب. التوصيل مجاني داخل الرياض.</span>'),
    ("const PAY_OK_NOTE = '", "const PAY_OK_NOTE = 'نطلبه مع شحنة هولندا الجاية، ونأكد لك موعد الوصول على الواتساب.'; const PAY_OK_NOTE_RIYADH = '"),
    ("const PEND_KEY = 'awe_bpending';", "const PEND_KEY = 'awe_hpending';"),
    ("const LEAD_ON = false;", "const LEAD_ON = true;"),   # «أقل من كرتون»: interest that we put together into one box
    ('<span>الأسعار شاملة ضريبة القيمة المضافة. ولو نقص صنف بعد الدفع، نعرض عليك بديل أو نرجع قيمته كاملة</span>',
     '<span>الأسعار شاملة الشحن من هولندا والتخليص والضريبة، والسعر يثبت لك لحظة الدفع</span>'),
    ("const IMG = '/img/n/';", "const IMG = '';   // holland.json carries /img/f|b/<code> paths\nconst NL_WHEN = '" + WHEN + "';"),
    ("fetch('catalog.json'", "fetch('holland.json'"),
    ("const newOrderId = () => { const d = new Date(); return 'BN-'", "const newOrderId = () => { const d = new Date(); return 'NL-'"),   # NL orders: no online payment, price confirmed first
    ("page: 'bunches' }", "page: 'holland' }"),
    ("kind:'bunch'", "kind:'holland'"),
    ("'awe_bcart'", "'awe_hcart'"),
    ("const r = ryNow(), t = new Date(r.year, r.month - 1, r.day); if(r.hour >= CUTOFF) t.setDate(t.getDate() + 1); return t; }",
     "const t = new Date(); t.setHours(0,0,0,0); t.setDate(t.getDate()+7); return t; }"),   # weekly import
    ('<li>نوصل داخل الرياض كل أيام الأسبوع، حتى الجمعة.</li>', '<li>نوصل داخل الرياض أول ما توصل الشحنة الأسبوعية، كل أيام الأسبوع حتى الجمعة.</li>'),   # weekly import: no 1 pm rule
    ("const SAME_DAY = true;", "const SAME_DAY = false;"),   # same-day rule is for Riyadh stock only
    ('`<button class="chip" type="button" data-f="express" aria-pressed="${state.express}">${esc(dayLabel(iso(deliverDate({ x:true }))))}</button>`', "''"),
    ('${esc(dayLabel(iso(deliverDate(it))))}', '${esc(NL_WHEN)}'),
    ('<span>شامل الضريبة · التوصيل مجاني داخل الرياض</span>', '<span>شامل الشحن من هولندا والتخليص والضريبة · التوصيل مجاني داخل الرياض</span>'),
    ('`السلام عليكم، طلب بنشات من موقع ${STORE.name}`', '`السلام عليكم، طلب جملة استيراد من هولندا من موقع ${STORE.name}`, \'الدفع مقدماً، والطلب ما يتلغى بعد الدفع\''),
    ('<label for="fDate">يوم التوصيل</label>', '<label for="fDate">التاريخ المناسب لك</label>'),
    ('<span class="hint">نوصل كل أيام الأسبوع، حتى الجمعة</span>', '<span class="hint">نأكد موعد وصول الشحنة على الواتساب</span>'),
    ('<p class="hint" style="margin:0">نستورد كل أسبوع،',      # prices move every day: say so up front
     '<p style="margin:2px 0 0;padding:8px 10px;border-radius:8px;background:#FFF6EC;color:#8A5A1F;font-size:13px">'
     'الأسعار تتغير يومياً حسب سوق هولندا والموسم والكميات، والسعر اللي تدفعه هو المكتوب لحظة الدفع.</p>'
     '<p class="hint" style="margin:0">نستورد كل أسبوع،'),
]

for a, b in REPL:
    if isinstance(a, re.Pattern):
        s, n = a.subn(b, s)
    else:
        n = s.count(a); s = s.replace(a, b)
    if not n:
        raise SystemExit('not found: ' + (a.pattern if isinstance(a, re.Pattern) else a)[:90])

s, n = re.subn(r'const FAQ = \[.*?\n\];', FAQ.replace('\\', '\\\\'), s, count=1, flags=re.S)
if not n:
    raise SystemExit('FAQ not found')
open(os.path.join(R, 'holland.html'), 'w', encoding='utf-8').write(s)
print('holland.html written')
