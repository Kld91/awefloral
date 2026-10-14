"""Product feed photos as JPEG.

Meta's catalog does not deliver ads for products whose photos are WebP (the ad preview says the product set has
"no valid products"), while Google takes either. The site keeps its WebP photos; the feed points at JPEG copies
in img/feed/ (max 1080 px, quality 84), made from the same WebP files.

Idempotent: converts only missing or older copies, then rewrites the feed links.
usage: python3 _i18n/feed_jpg.py [SITE_DIR]"""
import os, re, sys
from PIL import Image

R = sys.argv[1] if len(sys.argv) > 1 else '.'
SITE = 'https://www.awefloral.com/'
fp = os.path.join(R, 'merchant-feed.xml')
x = open(fp, encoding='utf-8').read()
out = os.path.join(R, 'img', 'feed'); os.makedirs(out, exist_ok=True)
made = 0

def jpg(m):
    global made
    tag, rel = m.group(1), m.group(2)
    src = os.path.join(R, rel)
    name = os.path.splitext(os.path.basename(rel))[0] + '.jpg'
    dst = os.path.join(out, name)
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        im = Image.open(src)
        if im.mode in ('RGBA', 'LA', 'P'):
            bg = Image.new('RGB', im.size, (255, 255, 255)); im = im.convert('RGBA'); bg.paste(im, mask=im.split()[-1]); im = bg
        else:
            im = im.convert('RGB')
        im.thumbnail((1080, 1080), Image.LANCZOS)
        im.save(dst, 'JPEG', quality=84, optimize=True, progressive=True)
        made += 1
    return f'<g:{tag}>{SITE}img/feed/{name}</g:{tag}>'

x2 = re.sub(r'<g:(image_link|additional_image_link)>' + re.escape(SITE) + r'(img/(?!feed/)[^<]+\.webp)</g:\1>', jpg, x)
if x2 != x: open(fp, 'w', encoding='utf-8').write(x2)
left = re.findall(r'<g:(?:additional_)?image_link>[^<]+\.webp<', x2)
print(f'{made} JPEG made, feed {"updated" if x2 != x else "unchanged"}, WebP links left: {len(left)}')
sys.exit(1 if left else 0)
