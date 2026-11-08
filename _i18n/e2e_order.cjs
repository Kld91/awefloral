// Order smoke test: loads the Arabic and English shop, builds the order body the checkout sends for every product
// (and every colour), and checks it the way the dashboard does. Fails (exit 1) on any page error or rejected field.
// Run from the repo root: node _i18n/e2e_order.cjs   (serves the folder on a local port itself)
const { chromium } = require('playwright'), http = require('http'), fs = require('fs'), path = require('path');
const ROOT = process.argv[2] || '.';
const IMG_OK = /^https:\/\/(www\.awefloral\.com\/img\/[fbnp]\/|media\.thechefz\.co\/)[A-Za-z0-9_\-./]{4,200}$/;
const srv = http.createServer((q, r) => { let f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0])); if (f.endsWith('/')) f += 'index.html';
  fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); return r.end(); } r.writeHead(200, { 'content-type': f.endsWith('.html') ? 'text/html' : f.endsWith('.js') ? 'text/javascript' : f.endsWith('.css') ? 'text/css' : 'application/octet-stream' }); r.end(d); }); });
(async () => {
  await new Promise(ok => srv.listen(0, ok)); const base = 'http://127.0.0.1:' + srv.address().port;
  const b = await chromium.launch(); let fail = 0;
  for (const pg of ['/index.html', '/en/index.html']) {
    const p = await b.newPage(), errs = [];
    p.on('pageerror', e => errs.push(String(e.message || e)));
    await p.route('**/*', r => r.request().url().startsWith(base) ? r.continue() : r.abort());
    await p.goto(base + pg, { waitUntil: 'domcontentloaded' }); await p.waitForTimeout(1500);
    const res = await p.evaluate(() => { const bad = []; let n = 0;
      for (const [pid, pr] of Object.entries(PRODUCTS)) for (const c of (pr.img ? Object.keys(pr.img) : (pr.colors ? Object.keys(pr.colors) : ['']))) {
        n++; try { cart.length = 0; cart.push({ pid, color: c, qty: 1, food: false, adds: [] }); const o = orderData('', 'tap'); const it = o.items[0];
          if (!it.n || !(it.p > 0) || !it.img) bad.push([pid, c, 'missing ' + (!it.n ? 'name ' : '') + (!(it.p > 0) ? 'price ' : '') + (!it.img ? 'photo' : '')]); else bad.push(['_img', it.img]);
        } catch (e) { bad.push([pid, c, 'ERR ' + e.message]); } }
      cart.length = 0; return { n, bad }; });
    const imgs = res.bad.filter(x => x[0] === '_img').map(x => x[1]), bad = res.bad.filter(x => x[0] !== '_img');
    imgs.filter(u => !IMG_OK.test(u)).forEach(u => bad.push(['photo link the dashboard refuses', u]));
    imgs.forEach(u => { const m = u.match(/^https:\/\/www\.awefloral\.com(\/img\/.*)$/); if (m && !fs.existsSync(path.join(ROOT, m[1]))) bad.push(['photo file missing', m[1]]); });
    console.log(pg, res.n, 'products/colours,', bad.length, 'problems,', errs.length, 'page errors');
    bad.concat(errs.map(e => ['page error', e])).slice(0, 40).forEach(x => console.log('  ✗', JSON.stringify(x)));
    fail += bad.length + errs.length; await p.close();
  }
  await b.close(); srv.close(); process.exit(fail ? 1 : 0);
})();
