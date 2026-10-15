"""Product feed for the Holland import page (holland-feed.xml), for Google Merchant Center free listings.
Kept apart from merchant-feed.xml (gift bouquets; also read by the Instagram catalog and the gift Shopping campaign).
One item = the smallest quantity a customer can buy (the full bunch), priced as on the site (VAT included), with the
price per stem as unit pricing. Items: the main Holland types (make_holland_types.TYPES), a spread of colours each.
Run after every holland.json update (make_holland.py runs it).   usage: python3 _i18n/make_holland_feed.py [SITE_DIR]"""
import os, sys, html, datetime
R = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_holland_types as T
SITE = 'https://www.awefloral.com'
x = lambda s: html.escape(str(s or ''), quote=False)
PER_TYPE = 15

def pick(its):
    by = sorted(its, key=lambda i: (i['p1'], i['n']))
    out, seen = [], set()
    for i in by:
        if i.get('c') not in seen: out.append(i); seen.add(i.get('c'))
    for i in by:
        if len(out) >= PER_TYPE: break
        if i not in out: out.append(i)
    return out[:PER_TYPE]

def run():
    items = []
    for key, ar, en, slug, guide in T.TYPES:
        for it in pick(T.items_of(key)):
            q = int(it.get('s') or it.get('m') or 1)
            price = round(it['p1'] * q, 2)
            color = T.COLORS.get(it.get('c'), '')
            origin = T.ORIGIN.get(str(it.get('o') or '').upper(), '')
            title = f'{it.get("ca") or ar} هولندي{" " + color if color else ""} · ربطة {q} غصن · {it["n"]}'
            desc = (f'{it.get("ca") or ar} بالجملة من سوق هولندا{" (المنشأ: " + origin + ")" if origin else ""}'
                    f'{"، طول الساق " + it["l"] if it.get("l") else ""}. الربطة {q} غصن بسعر {it["p1"]:.2f} ريال للغصن، '
                    'شامل الشحن والتخليص والضريبة. شحنة كل ثلاثاء، والتوصيل مجاني داخل الرياض.')
            items.append(
                f'<item><g:id>nl-{it["id"]}</g:id><g:title>{x(title[:150])}</g:title><g:description>{x(desc)}</g:description>'
                f'<g:link>{SITE}/holland.html?id={it["id"]}</g:link><g:image_link>{SITE}{x(it["i"])}-l.webp</g:image_link>'
                f'<g:availability>in_stock</g:availability><g:price>{price:.2f} SAR</g:price>'
                f'<g:unit_pricing_measure>{q} ct</g:unit_pricing_measure><g:unit_pricing_base_measure>1 ct</g:unit_pricing_base_measure>'
                f'<g:min_handling_time>2</g:min_handling_time><g:max_handling_time>9</g:max_handling_time>'
                f'<g:brand>أو فلورا</g:brand><g:condition>new</g:condition><g:identifier_exists>no</g:identifier_exists>'
                f'<g:google_product_category>2802</g:google_product_category><g:product_type>ورد هولندي بالجملة &gt; {x(ar)}</g:product_type>'
                + (f'<g:color>{x(color)}</g:color>' if color else '') +
                f'<g:custom_label_0>holland</g:custom_label_0><g:custom_label_1>{x(slug)}</g:custom_label_1></item>')
    out = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0"><channel>'
           '<title>أو فلورا · ورد هولندي بالجملة</title><link>https://www.awefloral.com/holland.html</link>'
           f'<description>استيراد مباشر من هولندا، شحنة كل ثلاثاء للرياض · {datetime.date.today().isoformat()}</description>\n'
           + '\n'.join(items) + '\n</channel></rss>\n')
    open(os.path.join(R, 'holland-feed.xml'), 'w', encoding='utf-8').write(out)
    print(f'holland-feed.xml: {len(items)} items')
    return len(items)

if __name__ == '__main__':
    run()
