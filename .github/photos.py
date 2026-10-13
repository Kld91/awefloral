"""Keep a copy of every product photo the site uses under img/, so all photos load from awefloral.com.

Run by .github/workflows/photos.yml after the catalogues change. It reads the photo codes the pages use
(holland.json, catalog.json, the HTML pages, sitemap.xml and img/want.txt), fetches the ones that are missing,
saves a small and a large WebP for each, and deletes copies that no page uses any more.
The source addresses come from the IMG_SRC repository secret and are never printed or written to the repo."""
import glob, io, json, os, re, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = dict(zip('fbn', os.environ.get('IMG_SRC', '').split()))
SMALL, LARGE = 400, 900          # list photo / product-sheet photo (longest side, px; never upscaled)
Q_SMALL, Q_LARGE = 80, 84
VERSION = '2'                    # bump to rebuild every copy (e.g. after changing sizes or quality)
REF = re.compile(r'/img/([fbn])/([A-Za-z0-9-]{8,80}?)(?:-l)?\.webp')
CODE = re.compile(r'[A-Za-z0-9-]{8,80}')


def wanted():
    w = set()
    for name, kind in (('holland.json', None), ('catalog.json', 'n')):
        p = os.path.join(ROOT, name)
        if not os.path.exists(p):
            continue
        for it in json.load(open(p, encoding='utf-8')).get('items', []):
            i = it.get('i') or ''
            m = re.fullmatch(r'/img/([fbn])/([A-Za-z0-9-]+)', i)
            if m:
                w.add(m.groups())
            elif kind and CODE.fullmatch(i):
                w.add((kind, i))
    for f in glob.glob(os.path.join(ROOT, '**', '*.html'), recursive=True) + [os.path.join(ROOT, 'sitemap.xml')]:
        if os.path.exists(f):
            w.update(REF.findall(open(f, encoding='utf-8').read()))
    p = os.path.join(ROOT, 'img', 'want.txt')
    if os.path.exists(p):
        for line in open(p, encoding='utf-8'):
            k, _, i = line.strip().partition('/')
            if k in 'fbn' and k and CODE.fullmatch(i):
                w.add((k, i))
    return w


def fetch(url, tries=4):
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; awefloral-photos)'})
            with urllib.request.urlopen(req, timeout=40) as r:
                im = Image.open(io.BytesIO(r.read()))
                im.load()
            return im
        except urllib.error.HTTPError as e:
            if e.code == 404 or t == tries - 1:
                raise
        except Exception:
            if t == tries - 1:
                raise
        time.sleep(2 + 4 * t)


def save(im, size, path, q):
    im = im.copy()
    im.thumbnail((size, size), Image.LANCZOS)
    if im.mode not in ('RGB', 'RGBA'):
        im = im.convert('RGB')
    tmp = path + '.tmp'
    im.save(tmp, 'WEBP', quality=q, method=6)
    os.replace(tmp, path)


def one(ki):
    k, i = ki
    d = os.path.join(ROOT, 'img', k)
    sm, lg = os.path.join(d, i + '.webp'), os.path.join(d, i + '-l.webp')
    if not REBUILD and os.path.exists(sm) and os.path.exists(lg):
        return 'have'
    base = SRC[k]
    try:
        if k == 'n':
            big = small = fetch(base + i)
        else:
            try:
                big = small = fetch(base + i + '-full.jpg')          # both sizes from the full photo: sharper
            except Exception:
                big = small = fetch(base + i + '-thumb.jpg')
        save(big, LARGE, lg, Q_LARGE)
        save(small, SMALL, sm, Q_SMALL)
        return 'new'
    except Exception as e:
        print('no photo for', k + '/' + i, '(' + type(e).__name__ + ')')   # never print the source address
        return 'fail'


VFILE = os.path.join(ROOT, 'img', 'version.txt')
REBUILD = (open(VFILE).read().strip() if os.path.exists(VFILE) else '') != VERSION


def main():
    if set(SRC) != set('fbn'):
        sys.exit('IMG_SRC secret is missing or incomplete')
    w = sorted(wanted())
    for k in 'fbn':
        os.makedirs(os.path.join(ROOT, 'img', k), exist_ok=True)
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(one, w))
    if res.count('fail') <= len(res) // 10:
        open(VFILE, 'w').write(VERSION + '\n')
    keep = {os.path.join(ROOT, 'img', k, i + s) for k, i in w for s in ('.webp', '-l.webp')}
    gone = 0
    for f in glob.glob(os.path.join(ROOT, 'img', '[fbn]', '*.webp')):
        if f not in keep:
            os.remove(f); gone += 1
    print(f"photos used: {len(w)} · new: {res.count('new')} · already here: {res.count('have')} · "
          f"not available: {res.count('fail')} · removed: {gone}")
    # guard: no public file may point at a supplier address (skipped while img/want.txt marks the switch-over)
    if not os.path.exists(os.path.join(ROOT, 'img', 'want.txt')):
        hosts = {re.sub(r'^https?://([^/]+).*', r'\1', u) for u in SRC.values()}
        bad = [os.path.relpath(f, ROOT) for f in glob.glob(os.path.join(ROOT, '**', '*'), recursive=True)
               if os.path.isfile(f) and f.endswith(('.html', '.json', '.xml', '.js', '.txt', '.py'))
               and any(h in open(f, encoding='utf-8', errors='ignore').read() for h in hosts)]
        if bad:
            sys.exit('supplier address found in: ' + ', '.join(bad))


if __name__ == '__main__':
    main()
