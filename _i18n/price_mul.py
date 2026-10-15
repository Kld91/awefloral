"""Price multipliers set from the dashboard (Prices tab): the order system publishes them on /pay/methods as
price.mul = {a: everyday Holland, b: special Holland, bn: Riyadh}. The pages re-price in the browser; the static pages
(Holland type pages, wholesale pages) and holland-feed.xml use the same multipliers through this module.
Rounding is the order system's: up to the next 0.05.
usage (check only): python3 _i18n/price_mul.py [SITE_DIR]  -> prints the live multipliers and whether they changed"""
import os, sys, json, math, urllib.request
API = 'https://awe-dashboard.le77en.workers.dev/pay/methods'
NL_B = {'مميز من هولندا', 'أوركيد واستوائي', 'بروتيا وجنوب أفريقيا', 'أغصان وتوت زينة', 'مجففات'}   # special groups (class b)
ONE = {'a': 1, 'b': 1, 'bn': 1}

def path(R): return os.path.join(R, '_i18n', 'price_mul.json')

def live():
    """The multipliers the order system charges with now, or None when it can't be reached."""
    try:
        with urllib.request.urlopen(urllib.request.Request(API, headers={'accept': 'application/json', 'user-agent': 'awe-build'}), timeout=10) as r:
            m = (json.load(r).get('price') or {}).get('mul') or {}
        return {k: float(m.get(k) or 1) for k in ONE}
    except Exception:
        return None

def saved(R):
    try: return {k: float(v) for k, v in json.load(open(path(R))).items() if k in ONE}
    except Exception: return dict(ONE)

def get(R):
    """Live multipliers (kept in _i18n/price_mul.json), or the last ones kept when the order system can't be reached."""
    m = live()
    if m is None: return saved(R)
    if m != saved(R): json.dump(m, open(path(R), 'w'), separators=(',', ':'))
    return m

def adj(p, k):
    if not k or k == 1: return p
    return round(math.ceil(p * k / 0.05 - 1e-9) * 0.05, 2)

def apply_nl(items, m):   # Holland items, by group
    for it in items:
        k = m['b'] if it.get('g') in NL_B else m['a']
        for f in ('p1', 'p2'):
            if it.get(f): it[f] = adj(it[f], k)
    return items

def apply_bn(items, m):   # Riyadh stock
    for it in items:
        for f in ('p1', 'p2'):
            if it.get(f): it[f] = adj(it[f], m['bn'])
    return items

if __name__ == '__main__':
    R = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    before, now = saved(R), live()
    print(json.dumps({'saved': before, 'live': now}))
    if now is not None and now != before:
        json.dump(now, open(path(R), 'w'), separators=(',', ':')); print('changed')
