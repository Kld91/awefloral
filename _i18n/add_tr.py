# -*- coding: utf-8 -*-
"""Add or update English translations: python3 add_tr.py SITE_DIR pairs.json  (pairs.json = {"arabic": "english", ...})"""
import json, os, sys
R, P = sys.argv[1], sys.argv[2]
sp, fp = os.path.join(R, '_i18n', 'segments.json'), os.path.join(R, '_i18n', 'fixes.json')
segs = json.load(open(sp, encoding='utf-8')); fix = json.load(open(fp, encoding='utf-8'))
pairs = json.load(open(P, encoding='utf-8'))
by = {}
for s in segs: by.setdefault(s['ar'], s['id'])
nid = max(int(s['id']) for s in segs) + 1; added = 0
for ar, en in pairs.items():
    if ar in by: fix[str(by[ar])] = en; continue
    segs.append({'id': nid, 'ar': ar, 'file': '', 'ctx': 'manual'}); fix[str(nid)] = en; by[ar] = nid; nid += 1; added += 1
json.dump(segs, open(sp, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
json.dump(fix, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('pairs', len(pairs), 'new segments', added)
