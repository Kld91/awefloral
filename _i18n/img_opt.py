"""Serve product photos small and fast.

The product photos live on the delivery-app CDN as full-size originals (400 KB – 1.8 MB each, ~1450 px).
Pages show them at 130–430 px, so every <img> is pointed at wsrv.nl (a free, cached image proxy) that
returns a resized WebP (~10–40 KB). If the proxy ever fails, the inline onerror falls back to the original.
og:image / JSON-LD keep the originals (crawlers and Merchant Center want the full photo).

Idempotent. Runs on the Arabic pages; build_en.py calls it before building /en/.
usage: python3 img_opt.py [SITE_DIR]"""
import re, glob, os, sys

ORIG = 'https://media.thechefz.co/'
FALLBACK = ("if(this.src.indexOf('wsrv.nl')!=-1){this.removeAttribute('srcset');"
            "this.src='https://'+decodeURIComponent(this.src.split('url=')[1].split('&amp;')[0])}")


def opt(u, w):
    return f'https://wsrv.nl/?url={u[len("https://"):]}&amp;w={w}&amp;output=webp&amp;q=78&amp;we'


def fix_img(m):
    tag = m.group(0)
    src = re.search(r'\ssrc="(' + re.escape(ORIG) + r'[^"]+)"', tag)
    if not src or 'wsrv.nl' in tag:
        return tag
    u = src.group(1)
    wm = re.search(r'\swidth="(\d+)"', tag)
    w = int(wm.group(1)) if wm else 300
    if 'id="pimg"' in tag:              # main product photo: colour swatches swap its src, so no srcset
        new = f' src="{opt(u, 1000)}"'
    else:
        new = f' src="{opt(u, w)}" srcset="{opt(u, w)} 1x, {opt(u, w * 2)} 2x"'
    tag = tag.replace(src.group(0), new, 1)
    return tag[:-1] + f' onerror="{FALLBACK}">'


def fix_page(s):
    s = re.sub(r'<img\b[^>]*>', fix_img, s)
    # colour swatches on product pages (seo.js copies data-img into #pimg)
    s = re.sub(r'data-img="(' + re.escape(ORIG) + r'[^"]+)"', lambda m: f'data-img="{opt(m.group(1), 1000)}"', s)
    if 'wsrv.nl' in s and 'href="https://wsrv.nl"' not in s:
        s = s.replace('<meta charset="utf-8">', '<meta charset="utf-8"><link rel="preconnect" href="https://wsrv.nl">', 1)
    return s


def run(root):
    files = [f for f in glob.glob(os.path.join(root, '**', '*.html'), recursive=True)
             if not os.path.relpath(f, root).startswith(('en' + os.sep, '_'))]
    n = 0
    for f in files:
        s = open(f, encoding='utf-8').read()
        t = fix_page(s)
        if t != s:
            open(f, 'w', encoding='utf-8').write(t); n += 1
    return n


if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    print('img_opt: updated', run(os.path.abspath(root)), 'pages')
