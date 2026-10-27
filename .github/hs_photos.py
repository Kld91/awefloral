"""Copy product photos listed in _i18n/hs_photos.json ({code: photo URL}) to img/p/<code>-1.webp (1200x900) and
-1s.webp (480x360), cover-cropped 4:3 like the other product photos. Photos already saved are skipped.
Run by .github/workflows/hs-photos.yml when the list changes."""
import io, json, os, urllib.request
from PIL import Image
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
todo = json.load(open(os.path.join(R, '_i18n', 'hs_photos.json')))
n = 0
for code, url in todo.items():
    if not code.isdigit(): continue
    out = os.path.join(R, 'img', 'p', code)
    if os.path.exists(out + '-1.webp') and os.path.exists(out + '-1s.webp'): continue
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; awefloral-photos)'})
    im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=40).read())).convert('RGB')
    for name, (W, H), q in (('-1.webp', (1200, 900), 82), ('-1s.webp', (480, 360), 78)):
        k = max(W / im.width, H / im.height)
        t = im.resize((max(W, round(im.width * k)), max(H, round(im.height * k))), Image.LANCZOS)
        x, y = (t.width - W) // 2, (t.height - H) // 2
        t.crop((x, y, x + W, y + H)).save(out + name, 'WEBP', quality=q, method=6)
    n += 1
print('saved', n)
