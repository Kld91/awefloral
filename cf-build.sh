#!/usr/bin/env bash
# Build for Cloudflare (Workers static assets): copy the site into dist/, leaving out the repo's tooling and
# source data (folders starting with _ , .github, scripts) — the same files GitHub Pages (Jekyll) leaves out.
set -euo pipefail
rm -rf dist && mkdir dist
tar --exclude=./.git --exclude=./.github --exclude=./dist --exclude='./_*' --exclude=./node_modules \
    --exclude='*.py' --exclude='*.sh' --exclude=./wrangler.jsonc --exclude=./CNAME --exclude=./.gitignore \
    -cf - . | tar -xf - -C dist
echo "files: $(find dist -type f | wc -l)"
