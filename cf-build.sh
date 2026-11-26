#!/usr/bin/env bash
# Build for Cloudflare (Workers static assets): copy the site into dist/, leaving out the repo's tooling and
# source data (folders starting with _ , .github, scripts) — the same files GitHub Pages (Jekyll) leaves out.
set -euo pipefail
rm -rf dist && mkdir dist
tar --exclude=./.git --exclude=./.github --exclude=./dist --exclude='./_[!h]*' --exclude='./_i18n' --exclude='./_cf' --exclude=./node_modules \
    --exclude='*.py' --exclude='*.sh' --exclude=./wrangler.jsonc --exclude=./CNAME --exclude=./.gitignore \
    -cf - . | tar -xf - -C dist
echo "files: $(find dist -type f | wc -l)"
python3 _cf/make_rb.py dist
# iPhone underlines long numbers (CR, VAT) as phone links: the pages say which numbers are phones themselves (27 Nov 2026)
python3 - <<'PY'
import glob
n = 0
for f in glob.glob('dist/**/*.html', recursive=True):
    h = open(f, encoding='utf-8').read()
    if 'format-detection' in h or '<head>' not in h: continue
    open(f, 'w', encoding='utf-8').write(h.replace('<head>', '<head>\n<meta name="format-detection" content="telephone=no">', 1)); n += 1
print('format-detection', n)
PY
