"""Build holland.html (wholesale import from the Netherlands) from bunches.html.
The two pages share all code; this swaps the data file, the wording, the cart key and the delivery rules.
Re-run after editing bunches.html, then run build_en.py.  usage: python3 _i18n/make_holland.py [SITE_DIR]"""
import re, os, sys

R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SITE = 'https://www.awefloral.com'
s = open(os.path.join(R, 'bunches.html'), encoding='utf-8').read()

NL_JS = r"""function nlShip(){   // the next Tuesday shipment: orders in by Sunday 5 pm Riyadh time land in Riyadh that Tuesday, delivered Tuesday or Wednesday
  const r = ryNow(), today = new Date(r.year, r.month - 1, r.day), now = new Date(r.year, r.month - 1, r.day, r.hour, r.minute || 0);
  const close = new Date(today); close.setDate(close.getDate() + (7 - today.getDay()) % 7); close.setHours(NL_CLOSE_H, 0, 0, 0);
  if(now >= close) close.setDate(close.getDate() + 7);
  const arrive = new Date(close.getFullYear(), close.getMonth(), close.getDate() + 2);
  return { close, arrive, left: Math.round((close - now) / 6e4) };
}
function deliverDate(it){ return nlShip().arrive; }
function nlWhen(){ let d = ''; try { d = new Intl.DateTimeFormat('ar-SA-u-ca-gregory-nu-latn', { weekday:'long', day:'numeric', month:'long' }).format(nlShip().arrive); } catch(e){ d = iso(nlShip().arrive); } return 'شحنة ' + d; }
function paintEta(){
  const el = $('#nlEta'); if(!el) return;
  const s = nlShip(), h = Math.floor(s.left / 60), m = s.left % 60;
  const when = s.left <= 24 * 60 ? 'آخر طلب بعد ' + [h ? h + ' س' : '', m ? m + ' د' : ''].filter(Boolean).join(' ') : 'اطلب قبل الأحد 5 العصر';
  el.innerHTML = '<b>' + esc(nlWhen()) + '</b> · ' + esc(when) + esc('، ويوصلك الثلاثاء أو الأربعاء') + ' · ' + esc('توصيل مجاني');
}"""
FAQ = """const FAQ = [
  ['متى يوصل الطلب؟', 'شحنة هولندا توصل الرياض كل ثلاثاء. الطلبات اللي توصلنا قبل الأحد الساعة 5 العصر تلحق شحنة الثلاثاء، ونوصلها لك الثلاثاء أو الأربعاء، ونأكد لك الوقت على الواتساب. الكميات الكبيرة ننسقها معك خلال يومين.'],
  ['ليش الكمية بالربطة الكاملة؟', 'نطلب لك من المزارع والمزادات في هولندا بنفس الكمية اللي تنباع فيها هناك، والطلب هناك ما يتلغى. عشان كذا البيع بالربطة الكاملة.'],
  ['السعر يشمل إيش؟', 'سعر الغصن شامل الشحن من هولندا والتخليص والضريبة. أسعار هولندا تتغير كل يوم، والسعر اللي تدفعه هو المكتوب لحظة الدفع.'],
  ['لو ما توفر الصنف؟', 'السعر يثبت لك لحظة الدفع. وإذا ما توفر صنف من طلبك في هولندا، نرجع لك قيمته كاملة أو نعطيك بديل توافق عليه.'],
  ['كيف أدفع؟', 'تدفع من الموقع بمدى أو Apple Pay أو بطاقة. الدفع كامل مقدماً، ونطلب من هولندا بعد الدفع، وبعدها الطلب ما يتلغى.'],
  ['كم رسوم التوصيل؟', 'التوصيل مجاني داخل الرياض.'],
  ['اللون بيكون نفس الصورة؟', 'الورد طبيعي، فاللون والشكل ممكن يختلف شوي حسب الموسم والشحنة. الصورة توضح الصنف.'],
  ['وصلني ورد فيه مشكلة؟', 'إذا وصل مكسور أو ذابل أو غير اللي طلبته، صوّره وأرسله لنا خلال 6 ساعات من الاستلام، ونبدله أو نرجع لك المبلغ.']
];"""

WHY_ITEMS = [
    ('انتظام التوريد', 'مواعيد وصول غير ثابتة تُربك التخطيط للأسبوع.',
     'شحنة أسبوعية ثابتة كل ثلاثاء، وآخر موعد للطلب الأحد الساعة 5 مساءً.'),
    ('توفّر الأصناف', 'تشكيلة محدودة لدى المورّد المحلي، ومتشابهة بين المحلات.',
     'أكثر من 3000 صنف من سوق هولندا، تختارها باللون والطول وبلد المنشأ.'),
    ('تلبية طلبات العملاء', 'الاعتذار عن طلبات بسبب نقص صنف بعينه.',
     'تطلب الصنف المحدد الذي يريده عميلك، بالربطة ودون حدّ أدنى للطلب.'),
    ('تكلفة الاستيراد والهدر', 'شحنات كبيرة لخفض التكلفة، ينتهي جزء منها تالفاً.',
     'شحنة مشتركة تتوزّع عليها التكاليف، وتدفع ثمن ما طلبته فقط، بسعر يشمل الشحن والتخليص والضريبة.'),
    ('ثبات الجودة', 'تفاوت الجودة من شحنة إلى أخرى.',
     'شحن جوي مباشر من هولندا إلى الرياض، ومواصفات واضحة لكل صنف قبل الطلب.'),
]
WHY_CSS = ('<style>'
    '.why{margin-top:8px;padding-top:26px;border-top:1px solid var(--ink)}'
    '.why .eb{font-size:12px;letter-spacing:.04em;color:var(--muted);margin:0 0 10px}'
    '.why h2{font-size:25px;line-height:1.6;font-weight:700;margin:0 0 14px;white-space:normal;max-width:620px}'
    '.why .wl{color:#3A3A3A;font-size:15px;line-height:2;margin:0 0 26px;max-width:680px}'
    '.why .stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px;margin:0 0 8px;padding:18px 0;border-block:1px solid var(--line)}'
    '.why .stats b{display:block;font-family:var(--f-logo);font-weight:400;font-size:32px;line-height:1.1;margin-bottom:6px}'
    '.why .stats span{display:block;font-size:12.5px;line-height:1.7;color:#555}'
    '.why .src{font-size:11.5px;color:var(--muted);margin:0 0 30px}'
    '.why h3{font-size:16px;font-weight:700;margin:0 0 4px}'
    '.why .ch{list-style:none;margin:0 0 30px;padding:0;counter-reset:c}'
    '.why .ch li{display:grid;grid-template-columns:38px minmax(0,1fr);gap:4px 10px;padding:16px 0;border-bottom:1px solid var(--line);counter-increment:c}'
    '.why .ch li::before{content:"0" counter(c);font-size:12.5px;color:var(--muted);padding-top:3px;font-variant-numeric:tabular-nums}'
    '.why .ch dl{margin:8px 0 0;display:grid;grid-template-columns:52px minmax(0,1fr);gap:6px 10px;font-size:14px;line-height:1.8}'
    '.why .ch dt{color:var(--muted);font-size:12.5px;padding-top:2px}.why .ch dd{margin:0}.why .ch dd.s{color:var(--ink);font-weight:500}.why .ch dd.p{color:#666}'
    '.why .flow{list-style:none;margin:12px 0 18px;padding:0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;counter-reset:f}'
    '.why .flow li{border-top:2px solid var(--ink);padding-top:10px;counter-increment:f;font-size:13px;line-height:1.7;color:#555}'
    '.why .flow li b{display:block;color:var(--ink);font-size:14.5px;margin-bottom:2px}'
    '.why .cta{font-size:13.5px;color:#555;margin:0}.why .cta a{color:var(--ink);font-weight:600}'
    '@media(max-width:560px){.why h2{font-size:20px}.why .stats{grid-template-columns:1fr;gap:14px}.why .stats b{font-size:28px}.why .flow{grid-template-columns:repeat(2,minmax(0,1fr))}}'
    '</style>')
WHY_HTML = (
    '\n    <section class="why" aria-labelledby="whyH">' + WHY_CSS +
    '\n      <p class="eb">لمحلات الورد ومنسّقي المناسبات</p>'
    '\n      <h2 id="whyH">التنوّع الذي يحتاجه محلك، دون أعباء الاستيراد</h2>'
    '\n      <p class="wl">يعتمد السوق المحلي في معظمه على الجوري الكيني والإثيوبي، بينما تأتي الأصناف التي تصنع الفارق من هولندا. '
    'غير أن استيرادها بشكل مستقل يفرض كمية كاملة من كل صنف، وتكاليف شحن وتخليص ثابتة على كل شحنة؛ فيضطر المحل إلى شراء ما يفوق حاجته، ويتحمّل الهدر في النهاية.</p>'
    '\n      <div class="stats"><div><b>71%</b><span>من واردات المملكة من الورد مصدرها كينيا وإثيوبيا</span></div>'
    '<div><b dir="ltr">16%</b><span>فقط من هولندا، مصدر التنوّع في الأصناف</span></div>'
    '<div><b dir="ltr">3,000+</b><span>صنف من سوق هولندا متاح للطلب كل أسبوع</span></div></div>'
    '\n      <p class="src">المصدر: بيانات التجارة الدولية لواردات الزهور المقطوفة إلى المملكة، 2023.</p>'
    '\n      <h3>خمسة تحديات، ونموذج واحد يعالجها</h3>'
    '\n      <ol class="ch">' + ''.join(
        f'<li><div><h3 style="font-size:15.5px">{t}</h3><dl><dt>التحدي</dt><dd class="p">{p}</dd><dt>الحل</dt><dd class="s">{s}</dd></dl></div></li>'
        for t, p, s in WHY_ITEMS) + '</ol>'
    '\n      <h3>كيف يعمل النموذج</h3>'
    '\n      <ol class="flow"><li><b>الطلب</b>طوال الأسبوع عبر الموقع</li><li><b>التجميع</b>نوحّد طلبات المحلات في طلب واحد</li>'
    '<li><b>الشحن</b>جواً مع شحنة الثلاثاء</li><li><b>التسليم</b>تخليص وتوصيل مجاني داخل الرياض</li></ol>'
    '\n      <p class="cta">للطلب الدوري، يمكنك <a href="/business.html">فتح حساب للمحلات</a> والشراء من رصيدك.</p>'
    '\n    </section>')

REPL = [
    ('<title>ورد جملة الرياض · بنشات ورد طبيعي بدون حد أدنى | أو فلورا</title>',
     '<title>ورد هولندي بالجملة في الرياض · استيراد مباشر أسبوعي | أو فلورا</title>'),
    (re.compile(r'<meta name="description" content="[^"]*">'),
     '<meta name="description" content="استيراد مباشر من هولندا بالجملة: رانونكولس، كالا، توليب، أنيمون، فاوانيا، بروتيا وغيرها. شحنة كل ثلاثاء للرياض، والسعر شامل الشحن والتخليص والضريبة.">'),
    ('content="ورد جملة الرياض · بنشات ورد طبيعي | أو فلورا"', 'content="ورد هولندي بالجملة · استيراد مباشر | أو فلورا"'),
    (re.compile(r'<meta property="og:description" content="[^"]*">'),
     '<meta property="og:description" content="أصناف هولندية مميزة بالجملة، شحنة كل ثلاثاء للرياض، شامل الشحن والتخليص والضريبة.">'),
    (SITE + '/bunches.html', SITE + '/holland.html'),                     # canonical, og:url, hreflang, JSON-LD
    ('"name": "ورد جملة الرياض"', '"name": "ورد هولندي بالجملة"'),
    ('"name": "الجملة", "item": "' + SITE + '/holland.html"',
     '"name": "الجملة", "item": "' + SITE + '/bunches.html"}, {"@type": "ListItem", "position": 3, "name": "استيراد من هولندا", "item": "' + SITE + '/holland.html"'),
    ('href="/en/bunches.html"', 'href="/en/holland.html"'),
    (SITE + '/en/bunches.html', SITE + '/en/holland.html'),               # hreflang="en" points at the English Holland page
    ('<p>بنشات الورد بالجملة</p>', '<p>استيراد من هولندا بالجملة</p>'),
    ('<div class="announce" id="announce">جملة · بدون حد أدنى · توصيل مجاني داخل الرياض</div>',
     '<div class="announce" id="announce">استيراد مباشر من هولندا · جملة · شحنة كل ثلاثاء</div>'),
    ('<span>بنشات الورد</span></a>', '<span>استيراد هولندا</span></a>'),
    ('<a href="holland.html">هولندا</a></nav>', '<a href="holland.html" aria-current="page">هولندا</a></nav>'),
    ('placeholder="ابحث: هدرنجا، توليب، Avalanche…"', 'placeholder="ابحث: رانونكولس، كالا، توليب…"'),
    ('<h1>بنشات الورد</h1>', '<h1>ورد هولندي بالجملة</h1>'),
    ('صنف من هولندا وكينيا وكولومبيا والسعودية</p>', 'صنف من مزارع ومزادات هولندا</p>'),
    ('بالربطة الكاملة · توصيل مجاني · بدون سجل تجاري · شامل الضريبة',
     'بالربطة الكاملة · توصيل مجاني داخل الرياض · شامل الشحن والتخليص والضريبة'),
    ('<p class="bulkn" id="bulkNote" hidden></p>', '<p id="nlEta" style="margin:4px 0 0;padding:9px 12px;border-radius:8px;background:#EEF6F0;color:#1F6B3A;font-size:14px;line-height:1.5"><b>شحنة كل ثلاثاء</b> · اطلب قبل الأحد 5 العصر، ويوصلك الثلاثاء أو الأربعاء · توصيل مجاني</p>' + '<p class="bulkn" id="bulkNote" hidden></p>'),   # the shipment date sits right under the page title
    ('<p id="promise" style="margin:4px 0 0;padding:9px 12px;border-radius:8px;background:#EEF6F0;color:#1F6B3A;font-size:14px;line-height:1.5">توصيل مجاني داخل الرياض، ونفس اليوم للطلبات الصباحية.</p>',
     '<p class="hint" style="margin:0">نستورد كل أسبوع، والكميات الكبيرة ننسقها معك خلال يومين. طلبات جملة، والدفع مقدماً، والطلب ما يتلغى بعد الدفع.</p>'
     '<p id="toBn" hidden style="margin:4px 0 0;font-size:13px"><a href="bunches.html">تبي ورد يوصل بكرة؟ شوف الجملة المتوفرة في الرياض ←</a></p>'),
    (re.compile(r'\n\s*<a class="nl" href="holland\.html".*?<!--/nl-->', re.S), ''),   # the Holland banner links here, so drop it
    # consulting-style section for florists and buyers: the supply problems, then how the weekly shared shipment solves them
    ('\n    <section>\n      <div class="head"><h2>كيف تطلب</h2></div>', WHY_HTML + '\n    <section>\n      <div class="head"><h2>كيف تطلب</h2></div>'),
    ('<span>البيع بالربطة الكاملة، والسعر المكتوب للغصن.</span>', '<span>تُباع بالربطة الكاملة كما تُشحن من هولندا، والسعر المعروض للساق الواحدة.</span>'), ('<b>اختر الأصناف والكميات</b>', '<b>اختر أصنافك</b>'),
    ('<b>ادفع من الموقع</b><span>مدى أو Apple Pay أو بطاقة، من الموقع مباشرة.</span>',
     '<b>ادفع عبر الموقع</b><span>مدى أو Apple Pay أو بطاقة أو تمارا. يُحجز طلبك من هولندا فور الدفع، لذا لا يمكن إلغاؤه.</span>'),
    ('<b>نجهّز طلبك ونوصله</b><span>داخل الرياض، والتوصيل مجاني.</span>',
     '<b>التسليم الثلاثاء أو الأربعاء</b><span>الطلبات قبل الأحد الساعة 5 مساءً تُشحن يوم الثلاثاء، والتوصيل مجاني داخل الرياض.</span>'),
    ("const PAY_OK_NOTE = '", "const PAY_OK_NOTE = 'نطلبه مع شحنة الثلاثاء، ونوصله لك الثلاثاء أو الأربعاء، ونأكد لك الوقت على الواتساب.'; const PAY_OK_NOTE_RIYADH = '"),
    ("const PEND_KEY = 'awe_bpending';", "const PEND_KEY = 'awe_hpending';"),
    ("const LEAD_ON = false;", "const LEAD_ON = true;"),
    ("const SHUT_KEY = 'bn';", "const SHUT_KEY = '';"),   # the Riyadh pause switch does not apply to the Holland page   # «أقل من كرتون»: interest that we put together into one box
    ('<span>الأسعار شاملة ضريبة القيمة المضافة. ولو نقص صنف بعد الدفع، نعرض عليك بديل أو نرجع قيمته كاملة</span>',
     '<span>الأسعار شاملة الشحن من هولندا والتخليص والضريبة، والسعر يثبت لك لحظة الدفع</span>'),
    ("const IMG = '/img/n/';", "const IMG = '';   // holland.json carries /img/f|b/<code> paths\nconst NL_CLOSE_H = 17;   // weekly shipment: orders close Sunday 5 pm Riyadh time, the shipment lands in Riyadh on Tuesday"),
    ("fetch('catalog.json'", "fetch('holland.json'"),
    ("const newOrderId = () => { const d = new Date(); return 'BN-'", "const newOrderId = () => { const d = new Date(); return 'NL-'"),   # NL orders: no online payment, price confirmed first
    ("page: 'bunches' }", "page: 'holland' }"),
    ("kind:'bunch'", "kind:'holland'"),
    ("'awe_bcart'", "'awe_hcart'"),
    (re.compile(r'function deliverDate\(it\)\{.*?\n  return dt;\n\}', re.S), lambda m: NL_JS),   # weekly import: the Tuesday shipment
    ("function paintPromise(){\n  if(!SAME_DAY) return;", "function paintPromise(){\n  if(!SAME_DAY) return paintEta();"),
    ('<li>نوصل داخل الرياض كل أيام الأسبوع، حتى الجمعة.</li>', '<li>الطلبات قبل الأحد 5 العصر تلحق شحنة الثلاثاء، ونوصلها داخل الرياض الثلاثاء أو الأربعاء.</li>'),   # weekly import: no 1 pm rule
    ("const SAME_DAY = true;", "const SAME_DAY = false;"),   # same-day rule is for Riyadh stock only
    ('`<button class="chip" type="button" data-f="express" aria-pressed="${state.express}">${esc(dayLabel(iso(deliverDate({ x:true }))))}</button>`', "''"),
    ('${esc(dayLabel(iso(deliverDate(it))))}', '${esc(nlWhen())}'),
    ('<span>شامل الضريبة · التوصيل مجاني داخل الرياض</span>', '<span>شامل الشحن من هولندا والتخليص والضريبة · التوصيل مجاني داخل الرياض</span>'),
    ('`السلام عليكم، طلب بنشات من موقع ${STORE.name}`', '`السلام عليكم، طلب جملة استيراد من هولندا من موقع ${STORE.name}`, \'الدفع مقدماً، والطلب ما يتلغى بعد الدفع\''),
    ('<label for="fDate">يوم التوصيل</label>', '<label for="fDate">التاريخ المناسب لك</label>'),
    ('<span class="hint">نوصل كل أيام الأسبوع، حتى الجمعة</span>', '<span class="hint">أقرب موعد مع شحنة الثلاثاء، ونأكد لك الوقت على الواتساب</span>'),
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

# static pages for the main types (holland/<slug>.html) and crawlable links to them under «كيف تطلب»
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_holland_types
MADE = make_holland_types.run() if os.path.exists(os.path.join(R, 'holland.json')) else []
if MADE:
    import make_holland_feed; make_holland_feed.run()   # holland-feed.xml for Google Merchant Center (free listings)
STEPS_END = '</ol>\n    </section>\n  </main>'
if s.count(STEPS_END) != 1:
    raise SystemExit('steps section end not found')
s = s.replace(STEPS_END, '</ol>\n    </section>' + make_holland_types.links_html(MADE) + '\n  </main>')

s, n = re.subn(r'const FAQ = \[.*?\n\];', FAQ.replace('\\', '\\\\'), s, count=1, flags=re.S)
if not n:
    raise SystemExit('FAQ not found')
open(os.path.join(R, 'holland.html'), 'w', encoding='utf-8').write(s)
print('holland.html written')
