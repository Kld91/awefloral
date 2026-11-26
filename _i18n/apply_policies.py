"""Policy pages (privacy, terms, returns, delivery, about) in formal Arabic and English (Khalid, 27 Nov 2026).
The page bodies live in _i18n/policies/<name>.ar.html and <name>.en.html; this puts them into the Arabic pages,
and build_en.py calls it again (--en) so the English pages take the written English text, not a machine swap.
usage: python3 _i18n/apply_policies.py [SITE_DIR] [--en]"""
import os, re, sys
R = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
EN = '--en' in sys.argv
P = os.path.join(R, '_i18n', 'policies')
DESC = {
  'privacy': ('سياسة الخصوصية في أو فلورا: البيانات التي نجمعها، وأغراض استخدامها، والجهات التي تُشارك معها، وحقوق العملاء.',
              'Awe Floral privacy policy: the data we collect, how we use it, who we share it with, and your rights.'),
  'terms': ('الشروط والأحكام للطلب والدفع والتوصيل والإلغاء في متجر أو فلورا، التابع لشركة روع النباتات للتجارة في الرياض.',
            'Terms and conditions for ordering, payment, delivery and cancellation at Awe Floral, part of Raw Alnabatat Trading Co., Riyadh.'),
  'returns': ('إذا وصل المنتج تالفاً أو مختلفاً عن الطلب، راسلنا خلال 6 ساعات من التوصيل لاستبداله أو استرداد المبلغ كاملاً.',
              'If an item arrives damaged or incorrect, message us within 6 hours of delivery for a replacement or a full refund.'),
  'delivery': ('توصيل الورد داخل الرياض في اليوم والساعة التي تختارها، مع التواصل مع المستلم في طلبات الهدايا، والدفع بمدى أو Apple Pay أو تمارا.',
               'Flower delivery in Riyadh on the day and hour you choose; for gifts we contact the recipient. Pay by mada, Apple Pay or Tamara.'),
  'about': ('أو فلورا متجر ورد في الرياض تابع لشركة روع النباتات للتجارة، يدير أقسام الورد الطبيعي في السوبرماركت، ويوصل الباقات والفازات داخل الرياض.',
            'Awe Floral is a flower store in Riyadh, part of Raw Alnabatat Trading Co., running fresh-flower sections in supermarkets and delivering bouquets and vases across Riyadh.'),
}
n = 0
for k, (da, de) in DESC.items():
    src = os.path.join(P, '%s.%s.html' % (k, 'en' if EN else 'ar'))
    page = os.path.join(R, 'en' if EN else '', k + '.html')
    if not (os.path.exists(src) and os.path.exists(page)): continue
    h = open(page, encoding='utf-8').read(); body = open(src, encoding='utf-8').read()
    h2 = re.sub(r'<main>.*?</main>', lambda m: '<main>' + body + '</main>', h, count=1, flags=re.S)
    d = de if EN else da
    h2 = re.sub(r'(<meta (?:name="description"|property="og:description") content=")[^"]*(")', lambda m: m.group(1) + d + m.group(2), h2)
    if h2 != h: open(page, 'w', encoding='utf-8').write(h2); n += 1
print('policy pages', 'en' if EN else 'ar', n)
