"""Arabic side of the bilingual site: hreflang alternates, an 'English' switch, and the payment-return language hop.
Idempotent: safe to run again."""
import re, glob, os
R = '/home/claude/kld91/awefloral'
SITE = 'https://www.awefloral.com'
os.chdir(R)
SKIP = {'index1.html', 'bunches1.html', 'links.html', '404.html'}
files = [f for f in glob.glob('*.html') + glob.glob('occasions/*.html') + glob.glob('ward/*.html') + glob.glob('wholesale/*.html') if f not in SKIP]

def en_url(ar):
    assert ar.startswith(SITE + '/'), ar
    return SITE + '/en/' + ar[len(SITE) + 1:]

def alt_block(ar):
    return (f'<link rel="alternate" hreflang="ar" href="{ar}"><link rel="alternate" hreflang="en" href="{en_url(ar)}">'
            f'<link rel="alternate" hreflang="x-default" href="{ar}">')

n = 0
for f in files:
    s = open(f, encoding='utf-8').read(); o = s
    m = re.search(r'<link rel="canonical" href="([^"]+)">', s)
    if not m: print('no canonical', f); continue
    ar = m.group(1)
    if f == 'wholesale/index.html': ar = SITE + '/wholesale/'
    if 'hreflang="en"' not in s:
        s = s.replace(m.group(0), m.group(0) + ('' if f == 'wholesale/index.html' else alt_block(ar)), 1)
    path = en_url(ar)[len(SITE):]
    # visible switch
    if 'data-lang="en"' not in s:
        if 'class="cartlink"' in s:
            s = s.replace('<a class="cartlink"', f'<a class="langlink" data-lang="en" href="{path}" hreflang="en" lang="en">English</a><a class="cartlink"', 1)
        elif f == 'index.html':
            s = s.replace('<div class="icons">\n      <button class="ib" type="button" data-search',
                          '<div class="icons">\n      <a class="ib langlink" data-lang="en" href="/en/" hreflang="en" lang="en" aria-label="English">EN</a>\n      <button class="ib" type="button" data-search', 1)
        elif f == 'bunches.html':
            s = s.replace('<div style="display:flex;gap:2px">\n        <a class="icon-btn" href="./"',
                          '<div style="display:flex;gap:2px;align-items:center">\n        <a class="icon-btn langlink" data-lang="en" href="/en/bunches.html" hreflang="en" lang="en" aria-label="English">EN</a>\n        <a class="icon-btn" href="./"', 1)
    if s != o:
        open(f, 'w', encoding='utf-8').write(s); n += 1

# styles for the switch
css = 'assets/seo.css'
c = open(css, encoding='utf-8').read()
if '.langlink' not in c:
    c += '\n.langlink{margin-inline-start:auto;padding:8px 10px;font-size:13px;font-weight:700;color:var(--ink);text-decoration:none}\n'
    open(css, 'w', encoding='utf-8').write(c)
for f, rule in [('index.html', '.ib.langlink{font-size:13px;font-weight:700;text-decoration:none;color:var(--ink)}'),
                ('bunches.html', '.icon-btn.langlink{font-size:13px;font-weight:700;text-decoration:none;color:var(--ink)}')]:
    s = open(f, encoding='utf-8').read()
    if rule not in s:
        s = s.replace('</style>', rule + '\n</style>', 1); open(f, 'w', encoding='utf-8').write(s)

# index: keep the route when switching language; payment return hops to the page the customer paid from
s = open('index.html', encoding='utf-8').read()
hop = "document.addEventListener('click', e => { const a = e.target.closest('a[data-lang]'); if(a && location.hash.length > 2) a.href = a.getAttribute('href').split('#')[0] + location.hash; }, true);\n"
if hop not in s:
    s = s.replace("/* ---------- online payment (Tap) ---------- */", hop + "/* ---------- online payment (Tap) ---------- */", 1)
a = "store.set('awe_pending', JSON.stringify({ id: ORDER_ID, total, msg, items: cartItems(), at: Date.now() }));"
b = "store.set('awe_pending', JSON.stringify({ id: ORDER_ID, total, msg, items: cartItems(), at: Date.now(), lang: document.documentElement.lang }));"
if a in s: s = s.replace(a, b, 1)
a = """  if(!m) return;
  try { history.replaceState(null, '', location.pathname + (location.hash || '')); } catch(e){}
  let pend = {}; try { pend = JSON.parse(store.get('awe_pending') || '{}') || {}; } catch(e){}"""
b = """  if(!m) return;
  let pend = {}; try { pend = JSON.parse(store.get('awe_pending') || '{}') || {}; } catch(e){}
  if(pend.id === m[1] && pend.lang && pend.lang !== document.documentElement.lang){ location.replace((pend.lang === 'en' ? '/en/' : '/') + location.search); return; }
  try { history.replaceState(null, '', location.pathname + (location.hash || '')); } catch(e){}"""
if a in s: s = s.replace(a, b, 1)
open('index.html', 'w', encoding='utf-8').write(s)
print('patched', n, 'files')
