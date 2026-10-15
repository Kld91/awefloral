"""Guides for flower shops (guides/<slug>.html): seasons of Dutch flowers, receiving a shipment, Dutch vs Kenyan roses.
The Arabic and English text live side by side below; the English goes into _i18n/segments.json + fixes.json so
build_en.py makes /en/guides/<slug>.html. Pages use the shell of the wholesale pages and are listed in sitemap.xml.
usage: python3 _i18n/make_guides.py [SITE_DIR]   (then build_en.py)"""
import json, os, re, sys, html, datetime

R = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
HERE = os.path.join(R, '_i18n')
SITE = 'https://www.awefloral.com'
esc = lambda s: html.escape(str(s or ''), quote=True)

SHIP = ('طلبات الأحد قبل 5 العصر توصل مع شحنة الثلاثاء، ونوصلها داخل الرياض الثلاثاء أو الأربعاء.',
        'Orders in by Sunday 5 pm arrive with the Tuesday shipment, and we deliver them within Riyadh on Tuesday or Wednesday.')

GUIDES = [
  dict(slug='dutch-flower-seasons',
    title=('مواسم الزهور الهولندية: وش يتوفر في كل وقت من السنة', 'Dutch Flower Seasons: What Is Available When'),
    desc=('دليل لمحلات الورد في الرياض: متى موسم التوليب والفاوانيا والرانونكولس والداليا، ووش يتوفر طول السنة من هولندا.',
          'A guide for Riyadh florists: when tulips, peonies, ranunculus and dahlias are in season, and what Holland offers all year.'),
    blocks=[
      ('p', 'أغلب الزهور الهولندية تنزرع في بيوت محمية، فتلقاها طول السنة. لكن فيه أصناف لها موسم واضح، يكون فيه أحلى شكل وأحسن سعر. هذا ملخص يساعدك ترتب طلباتك.',
            'Most Dutch flowers are grown under glass, so you can get them all year. Some varieties still have a clear season, when they look their best and cost the least. Here is a summary to help you plan your orders.'),
      ('h2', 'متوفرة طول السنة', 'Available all year'),
      ('p', 'الجوري والبيبي روز والليسيانثوس والكالا والجبسوفيلا والقرنفل والأوركيد. تتوفر كل أسبوع، والسعر يتحرك حسب الطلب، ويرتفع قبل المناسبات الكبيرة مثل يوم الأم.',
            'Roses, spray roses, lisianthus, calla, gypsophila, carnations and orchids. They are available every week; prices move with demand and rise before big occasions such as Mother’s Day.'),
      ('h2', 'التوليب', 'Tulips'),
      ('p', 'موسمه من نوفمبر إلى أبريل تقريباً. في بداية الموسم ونهايته تكون الأصناف أقل، وفي عزه تلقى ألوان وأشكال كثيرة، منها المزدوج والمهدب.',
            'The season runs from about November to April. There are fewer varieties at the start and end; at its peak you find many colours and forms, including double and fringed tulips.'),
      ('h2', 'الرانونكولس والأنيمون', 'Ranunculus and anemones'),
      ('p', 'من نوفمبر إلى أبريل تقريباً. الرانونكولس الهولندي معروف بكبر رأسه وكثرة بتلاته، والأنيمون يحلو في باقات الشتاء.',
            'From about November to April. Dutch ranunculus are known for large heads full of petals, and anemones are lovely in winter bouquets.'),
      ('h2', 'الفاوانيا', 'Peonies'),
      ('p', 'موسم الفاوانيا الهولندية الأساسي من مايو إلى يونيو، وأحياناً يبدأ من آخر أبريل. برا هالفترة الكميات قليلة والسعر أعلى، فإذا عندك مناسبة في الربيع اطلبها بدري.',
            'The main Dutch peony season is May to June, sometimes starting in late April. Outside it, quantities are small and prices higher, so if you have a spring event, order early.'),
      ('h2', 'الداليا', 'Dahlias'),
      ('p', 'من الصيف إلى الخريف، تقريباً من يوليو إلى أكتوبر.', 'From summer to autumn, roughly July to October.'),
      ('h2', 'الهدرنجا', 'Hydrangea'),
      ('p', 'متوفرة أغلب السنة من البيوت المحمية، وفي آخر الصيف والخريف تلقى الألوان العتيقة المتدرجة اللي تدوم أطول.',
            'Available most of the year from greenhouses; in late summer and autumn you find the antique, shaded colours that last longer.'),
      ('h2', 'البروتيا وزهور جنوب أفريقيا', 'Protea and South African flowers'),
      ('p', 'تجي عن طريق سوق هولندا من جنوب أفريقيا وغيرها، ومتوفرة أغلب السنة، وتدوم طويل في الفازة.',
            'They come through the Dutch market from South Africa and elsewhere, are available most of the year, and last a long time in the vase.'),
      ('note', 'الأسعار في هولندا تتغير يومياً حسب المزاد، والسعر في صفحتنا هو سعر لحظة الدفع.',
               'Prices in Holland change daily with the auction; the price on our page is the price at the moment you pay.'),
    ]),
  dict(slug='receiving-dutch-flowers',
    title=('أول ما توصلك الشحنة: كيف تجهّز الورد الهولندي عشان يدوم', 'When the Shipment Arrives: Preparing Dutch Flowers So They Last'),
    desc=('خطوات بسيطة لمحلات الورد: فتح الكراتين، قص الساق، الماء والمغذي، والتبريد، عشان يدوم الورد الهولندي أطول.',
          'Simple steps for florists: opening the boxes, cutting the stems, water and flower food, and cooling, so Dutch flowers last longer.'),
    blocks=[
      ('p', 'الورد يسافر من هولندا جاف ومبرد، والساعات الأولى بعد ما يوصل هي اللي تحدد كم بيعيش عندك. هذي الخطوات اللي نسويها نحن، وتقدر تسويها في محلك.',
            'Flowers travel from Holland dry and chilled, and the first hours after arrival decide how long they will last. These are the steps we follow, and you can follow them in your shop.'),
      ('ol', [
        ('افتح الكراتين أول ما توصل، وخلها في مكان بارد بعيد عن الشمس.', 'Open the boxes as soon as they arrive and keep them somewhere cool, out of the sun.'),
        ('اغسل الأسطل بماء وصابون أو معقم، لأن البكتيريا تسد الساق وتقصّر عمر الورد.', 'Wash the buckets with soap or a disinfectant: bacteria block the stems and shorten vase life.'),
        ('قص 2 إلى 3 سم من كل ساق بزاوية مائلة بسكين أو مقص حاد، وشيل الأوراق اللي بتكون تحت الماء.', 'Cut 2 to 3 cm off every stem at an angle with a sharp knife or shears, and strip any leaves that would sit under water.'),
        ('حط الورد في ماء نظيف مع مغذي الورد، وخله يشرب ساعتين على الأقل قبل التنسيق.', 'Put the flowers in clean water with flower food and let them drink for at least two hours before arranging.'),
        ('أفضل حرارة لأغلب الزهور بين 2 و8 درجات. الأوركيد والأنثوريوم ما تحب البرد الشديد، خلها فوق 12 درجة.', 'Most flowers keep best between 2 and 8 °C. Orchids and anthurium dislike the cold; keep them above 12 °C.'),
        ('أبعد الورد عن الفاكهة والخضار، لأنها تطلع غاز الإيثيلين اللي يذبّل الزهور بسرعة، خصوصاً القرنفل.', 'Keep flowers away from fruit and vegetables: they give off ethylene gas, which wilts flowers fast, carnations especially.'),
        ('في الليليوم شيل حبوب اللقاح البرتقالية أول ما تفتح الزهرة، عشان ما توسخ البتلات.', 'On lilies, remove the orange pollen as soon as each flower opens so it does not stain the petals.'),
        ('التوليب يطول بعد القص ويميل ناحية الضوء، فاحسب حسابه في التنسيق.', 'Tulips keep growing after cutting and bend towards the light, so allow for that in your arrangements.'),
      ]),
      ('note', 'وإذا وصلك صنف فيه مشكلة، صوّره وأرسله لنا خلال 6 ساعات من الاستلام، ونبدله أو نرجع لك المبلغ.',
               'If an item arrives with a problem, photograph it and send it to us within 6 hours of delivery, and we will replace it or refund you.'),
    ]),
  dict(slug='dutch-vs-kenyan-roses',
    title=('الورد الهولندي والكيني والإكوادوري: وش الفرق؟', 'Dutch, Kenyan and Ecuadorian Roses: What Is the Difference?'),
    desc=('مقارنة بسيطة لمحلات الورد في الرياض بين الجوري الهولندي والكيني والإكوادوري: الشكل والعمر والسعر، ومتى تختار كل واحد.',
          'A simple comparison for Riyadh florists of Dutch, Kenyan and Ecuadorian roses: look, vase life and price, and when to choose each.'),
    blocks=[
      ('p', 'لما نقول ورد هولندي، المقصود غالباً إنه يجي عن طريق سوق الزهور في هولندا، وهو أكبر سوق للزهور في العالم. جزء منه ينزرع في هولندا نفسها، وجزء يجي من مزارع في كينيا وإثيوبيا والإكوادور وكولومبيا ويتباع هناك.',
            'When people say Dutch flowers they usually mean flowers sold through the Dutch flower market, the largest in the world. Some are grown in Holland itself; others come from farms in Kenya, Ethiopia, Ecuador and Colombia and are sold there.'),
      ('h2', 'الجوري الهولندي', 'Dutch roses'),
      ('p', 'ينزرع في بيوت محمية، ومعروف بأصنافه المميزة وألوانه النادرة وجوري الحدائق. سعره أعلى، ويستاهل للباقات الفاخرة والعرائس.',
            'Grown under glass and known for special varieties, rare colours and garden roses. It costs more and is worth it for luxury and bridal work.'),
      ('h2', 'الجوري الكيني', 'Kenyan roses'),
      ('p', 'ينزرع على مرتفعات قريبة من خط الاستواء، فيطلع ساقه أقصر ورأسه أصغر شوي، لكنه قوي ويدوم في الفازة وسعره مناسب. يكثر في البيع اليومي وباقات المحلات.',
            'Grown at high altitude near the equator, with shorter stems and slightly smaller heads, but sturdy, long-lasting and well priced. It is the everyday choice for shop bouquets.'),
      ('h2', 'الجوري الإكوادوري والكولومبي', 'Ecuadorian and Colombian roses'),
      ('p', 'رأسه كبير وساقه طويلة وألوانه قوية، خصوصاً الإكوادوري. ينفع للتنسيقات الكبيرة والمناسبات.',
            'Large heads, long stems and strong colours, Ecuadorian roses especially. Good for large arrangements and events.'),
      ('h2', 'وش أختار؟', 'Which should I choose?'),
      ('p', 'للمناسبات الفاخرة والعرائس اختار الهولندي أو الإكوادوري، وللبيع اليومي والكميات الكبيرة الكيني يعطيك أفضل قيمة. وفي صفحة هولندا تلقى المنشأ مكتوب عند كل صنف.',
            'For luxury events and weddings choose Dutch or Ecuadorian; for everyday sales and large quantities, Kenyan gives the best value. On our Holland page the origin is shown on every item.'),
    ]),
]
INDEX = (('أدلة لمحلات الورد', 'Guides for Florists'),
         ('نصائح عملية لمحلات الورد والمنسقين: مواسم الزهور الهولندية، تجهيز الشحنة، والفرق بين أنواع الجوري.',
          'Practical notes for florists and designers: Dutch flower seasons, preparing a shipment, and the differences between roses.'))
FIXED = {SHIP[0]: SHIP[1], INDEX[0][0]: INDEX[0][1], INDEX[1][0]: INDEX[1][1],
         'تصفح الورد الهولندي': 'Browse Dutch flowers', 'أدلة ثانية': 'More guides', 'أصناف هولندا': 'Holland flower types'}

def shell(path, title, desc, body, ld, crumb):
    import make_holland_types as T          # same page shell as the Holland type pages
    url = SITE + path
    head = T.HEAD_COMMON.replace('<meta property="og:type" content="website">',
        f'<meta property="og:type" content="article">\n<meta property="og:title" content="{esc(title)} | أو فلورا">\n<meta property="og:description" content="{esc(desc)}">\n<meta property="og:url" content="{url}">\n<meta name="twitter:card" content="summary">')
    top = re.sub(r'href="/en/wholesale/tulips\.html"', f'href="/en{path}"', T.BODY_TOP)
    style = ('<style>.gd{max-width:720px}.gd p,.gd li{line-height:1.85;font-size:16px}.gd h2{margin:26px 0 6px;font-size:19px}'
             '.gd ol{padding-inline-start:20px}.gd li{margin:0 0 10px}.gd .note{background:#F4F2EE;border-radius:10px;padding:12px 14px;margin:18px 0}'
             '.gd .ship{background:#EEF6F0;color:#1F6B3A;border-radius:10px;padding:12px 14px;margin:18px 0}.gd-list a{display:block;padding:12px 0;border-top:1px solid #eee}'
             '.gd-list b{display:block;font-size:17px}.gd-list span{color:#555;font-size:14px}</style>')
    return f'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)} | أو فلورا</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}"><link rel="alternate" hreflang="ar" href="{url}"><link rel="alternate" hreflang="en" href="{SITE}/en{path}"><link rel="alternate" hreflang="x-default" href="{url}">
{head}<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{style}
</head>
{top}<main>
<nav class="crumbs" aria-label="المسار"><a href="/">الرئيسية</a> <span>/</span> {crumb}</nav>
{body}
</main>{T.BODY_END}'''

def links_html():
    return ' · '.join(f'<a href="/guides/{g["slug"]}.html">{esc(g["title"][0].split(":")[0])}</a>' for g in GUIDES)

def run():
    sys.path.insert(0, HERE)
    import make_holland_types as T
    os.makedirs(os.path.join(R, 'guides'), exist_ok=True)
    pairs, made = dict(FIXED), []
    today = datetime.date.today().isoformat()
    for g in GUIDES:
        path = f'/guides/{g["slug"]}.html'; url = SITE + path
        (tar, ten), (dar, den) = g['title'], g['desc']
        pairs[tar] = ten; pairs[dar] = den
        short = tar.split(':')[0]; pairs[short] = ten.split(':')[0]
        parts = []
        for b in g['blocks']:
            if b[0] == 'ol':
                parts.append('<ol>' + ''.join(f'<li>{esc(a)}</li>' for a, e in b[1]) + '</ol>')
                for a, e in b[1]: pairs[a] = e
            else:
                kind, a, e = b; pairs[a] = e
                parts.append({'h2': f'<h2>{esc(a)}</h2>', 'p': f'<p>{esc(a)}</p>', 'note': f'<p class="note">{esc(a)}</p>'}[kind])
        others = ' · '.join(f'<a href="/guides/{o["slug"]}.html">{esc(o["title"][0].split(":")[0])}</a>' for o in GUIDES if o is not g)
        types = ' · '.join(f'<a href="/holland/{t[3]}.html">{esc(T.LINK_AR(t[1]))}</a>' for t in T.TYPES if os.path.exists(os.path.join(R, 'holland', t[3] + '.html')))
        body = (f'<article class="gd pad"><h1>{esc(tar)}</h1>' + ''.join(parts) + f'<p class="ship">{esc(SHIP[0])}</p>'
                f'<p><a class="btn primary" href="/holland.html">تصفح الورد الهولندي</a></p>'
                f'<h2>أصناف هولندا</h2><p class="more-links">{types}</p><h2>أدلة ثانية</h2><p class="more-links">{others}</p></article>')
        ld = {'@context': 'https://schema.org', '@graph': [T.FLORIST,
              {'@type': 'BreadcrumbList', 'itemListElement': [
                  {'@type': 'ListItem', 'position': 1, 'name': 'الرئيسية', 'item': SITE + '/'},
                  {'@type': 'ListItem', 'position': 2, 'name': INDEX[0][0], 'item': SITE + '/guides/'},
                  {'@type': 'ListItem', 'position': 3, 'name': short, 'item': url}]},
              {'@type': 'Article', 'headline': tar, 'description': dar, 'url': url, 'inLanguage': 'ar', 'dateModified': today,
               'author': {'@id': SITE + '/#florist'}, 'publisher': {'@id': SITE + '/#florist'}}]}
        crumb = f'<a href="/guides/">{esc(INDEX[0][0])}</a> <span>/</span> <span aria-current="page">{esc(short)}</span>'
        open(os.path.join(R, path.lstrip('/')), 'w', encoding='utf-8').write(shell(path, tar, dar, body, ld, crumb)); made.append(path)
    # the list of guides
    lst = ''.join(f'<a href="/guides/{g["slug"]}.html"><b>{esc(g["title"][0])}</b><span>{esc(g["desc"][0])}</span></a>' for g in GUIDES)
    body = f'<article class="gd pad"><h1>{esc(INDEX[0][0])}</h1><p>{esc(INDEX[1][0])}</p><nav class="gd-list">{lst}</nav></article>'
    ld = {'@context': 'https://schema.org', '@graph': [T.FLORIST, {'@type': 'CollectionPage', 'name': INDEX[0][0], 'url': SITE + '/guides/'}]}
    out = shell('/guides/', INDEX[0][0], INDEX[1][0], body, ld, f'<span aria-current="page">{esc(INDEX[0][0])}</span>')
    open(os.path.join(R, 'guides', 'index.html'), 'w', encoding='utf-8').write(out); made.insert(0, '/guides/')
    added = T.add_translations(pairs)
    sm_path = os.path.join(R, 'sitemap.xml'); sm = open(sm_path, encoding='utf-8').read()
    sm = re.sub(r'<url><loc>' + re.escape(SITE) + r'(?:/en)?/guides/[^<]*</loc>.*?</url>', '', sm, flags=re.S)
    sm = sm.replace('</urlset>', ''.join(f'<url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod><priority>0.6</priority></url>' for p in made) + '</urlset>')
    open(sm_path, 'w', encoding='utf-8').write(sm)
    print(f'guides: {len(made)} pages, {added} new translations')
    return made

if __name__ == '__main__':
    run()
