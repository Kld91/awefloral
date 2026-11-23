// The live site, opened like a customer on a phone. Each step that goes wrong becomes one line (Arabic) in status.json;
// the dashboard worker reads it hourly and sends it to the owner's Telegram. Nothing is ordered or paid:
// the payment call is sent with ?dry=1, which prices the cart on the server and stops before saving or charging.
import { chromium, devices } from 'playwright';
import { writeFileSync } from 'fs';

const SITE = process.env.SITE || 'https://www.awefloral.com';
const API = 'https://awe-dashboard.le77en.workers.dev';
const fails = [], notes = [];
const fail = (m) => { fails.push(m); console.log('FAIL', m); };
const third = /facebook|fbevents|googletagmanager|google-analytics|doubleclick|gstatic|tiktok|snap|clarity|tamara|tap\.company|goSell/i;

const browser = await chromium.launch();
const ctx = await browser.newContext({ ...devices['iPhone 13'], locale: 'ar-SA' });

async function page(label, fresh) {
  const c = fresh ? await browser.newContext({ ...devices['iPhone 13'], locale: 'ar-SA' }) : ctx;
  const p = await c.newPage(), errs = [];
  p.on('pageerror', e => errs.push(String(e.message || e).slice(0, 140)));
  p.on('console', m => { if (m.type() === 'error' && !third.test(m.text()) && !third.test((m.location() || {}).url || '')) errs.push(m.text().slice(0, 140)); });
  p.on('response', r => { const u = r.url(); if (r.status() >= 500 && !third.test(u)) errs.push('HTTP ' + r.status() + ' ' + u.slice(0, 100)); });
  p.errs = () => { const e = errs.filter(x => !/Failed to load resource.*(404|net::ERR)/.test(x) && !/\/pay(\b|$)|status of 409/.test(x)); if (e.length) fail(label + ': خطأ في الصفحة: ' + e[0]); };
  return p;
}
const step = async (label, fn) => { try { await fn(); } catch (e) { fail(label + ': ' + String(e.message || e).split('\n')[0].slice(0, 160)); } };

// 1. home page shows products
await step('الصفحة الرئيسية', async () => {
  const p = await page('الصفحة الرئيسية');
  const r = await p.goto(SITE + '/', { waitUntil: 'domcontentloaded', timeout: 45000 });
  if (!r || r.status() !== 200) throw new Error('ما فتحت (HTTP ' + (r && r.status()) + ')');
  await p.waitForSelector('a.card', { timeout: 20000 });
  const n = await p.$$eval('a.card', a => a.length);
  if (n < 8) fail('الصفحة الرئيسية: تطلع ' + n + ' منتجات بس');
  p.errs(); await p.close();
});

// 2. a customer's way: an in-stock product → cart → checkout form → pay (dry)
async function buy(label, pick) {
  await step(label, async () => {
    const p = await page(label, true);   // its own browser: an empty cart
    await p.goto(SITE + '/#/c/all', { waitUntil: 'domcontentloaded', timeout: 45000 });
    await p.waitForSelector('a.card', { timeout: 20000 });
    await p.waitForFunction(() => window.__availAt || (typeof OFF !== 'undefined' && OFF.size > 0), null, { timeout: 20000 }).catch(() => {});   // today's availability, so no sold-out pick
    await p.waitForTimeout(800);
    const pid = await p.evaluate(pick);
    if (!pid) { notes.push(label + ': no product'); await p.close(); return; }
    await p.goto(SITE + '/?p=' + pid, { waitUntil: 'domcontentloaded' });
    await p.waitForSelector('#psAdd', { state: 'visible', timeout: 20000 }).catch(() => {});
    if (!(await p.$('#psAdd:visible'))) { notes.push(label + ': ' + pid + ' sold out on open, skipped'); await p.close(); return; }   // switched off between the list and the open
    await p.waitForFunction(() => window.ps && ps.pid && $('#psAdd') && !$('#psAdd').disabled, null, { timeout: 15000 }).catch(() => {});
    for (let k = 0; k < 3 && !(await p.evaluate(() => cart.length)); k++) {   // a slow phone network: give the page time, then tap again
      await p.waitForTimeout(1500 + k * 1500); await p.click('#psAdd').catch(() => {});
      await p.waitForFunction(() => cart.length > 0, null, { timeout: 6000 }).catch(() => {});
    }
    await p.evaluate(() => openCart()); await p.waitForTimeout(1500);
    const gross = await p.evaluate(() => cartGross());
    if (!(gross > 0)) throw new Error('السلة فاضية بعد «أضف للسلة» (' + pid + ' · الزر: ' + (await p.evaluate(() => ($('#psAdd') || {}).textContent || '—')).trim().slice(0, 40) + ')');
    const fee = await p.evaluate(() => smallFee());
    if (gross < 65 && fee !== 10) fail(label + ': رسوم التوصيل ما طلعت لطلب ' + gross);
    if (gross >= 65 && fee !== 0) fail(label + ': رسوم توصيل على طلب ' + gross);
    // the form, like a customer: an order for themselves, Saudi mobile, tomorrow, first open hour, an address (the name is optional, under «إضافات»)
    await p.waitForSelector('#fPhone', { state: 'visible', timeout: 10000 });
    await p.evaluate(() => { const s = $('#whoSelf'); if (s && !s.checked) { s.checked = true; s.dispatchEvent(new Event('change', { bubbles: true })); } const n = $('#fName'); if (n) n.value = 'فحص الموقع'; });
    await p.fill('#fPhone', '0500000000');
    await p.evaluate(() => {
      const d = $('#fDate'), t = new Date(Date.now() + 3 * 36e5 + 864e5).toISOString().slice(0, 10);
      d.value = t; d.dataset.touched = '1'; d.dispatchEvent(new Event('change', { bubbles: true })); d.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await p.waitForTimeout(500);
    await p.evaluate(() => { const s = $('#fSlot'), o = [...s.options].find(x => !x.disabled && x.value); if (o) { s.value = o.value; s.dispatchEvent(new Event('change', { bubbles: true })); } });
    if (await p.$('#fAddr')) await p.fill('#fAddr', 'حي الرمال، شارع تجربة').catch(() => {});
    await p.waitForTimeout(400);
    const errs = await p.evaluate(() => validate(false));
    if (Object.keys(errs).length) throw new Error('النموذج ما قبل: ' + Object.values(errs)[0]);
    // the payment call goes to the server's dry run: priced exactly, nothing saved or charged
    let sent = null, got = null;
    await p.route(API + '/pay', async route => {
      sent = JSON.parse(route.request().postData() || '{}');
      const r = await fetch(API + '/pay?dry=1', { method: 'POST', headers: { 'content-type': 'application/json' }, body: route.request().postData() });
      got = { status: r.status, body: await r.json().catch(() => ({})) };
      await route.fulfill({ status: 409, contentType: 'application/json', body: JSON.stringify({ error: 'busy' }) });   // stop here: the page shows «try again», nothing was made
    });
    const btn = await p.$('#payBtn:not([hidden])');
    if (!btn) throw new Error('زر «ادفع الآن» ما ظهر');
    await btn.click();
    for (let i = 0; i < 30 && !got; i++) await p.waitForTimeout(500);
    if (!got) throw new Error('الضغط على «ادفع الآن» ما أرسل طلب الدفع');
    if (got.status !== 200 || !got.body.dry) throw new Error('السيرفر رفض الدفع: ' + got.status + ' ' + JSON.stringify(got.body).slice(0, 120));
    const tot = Number(sent.total ?? (sent.order || {}).total);
    if (Math.abs(got.body.total - tot) > 0.01) throw new Error('سعر السلة ' + tot + ' غير سعر السيرفر ' + got.body.total + ' (العميل بيطلع له خطأ عند الدفع)');
    notes.push(label + ': ' + pid + ' ' + tot);
    p.errs(); await p.close();
  });
}
const firstIn = (lo, hi) => `(() => { const a = ALL().filter(p => avail(p) && p.price >= ${lo} && p.price < ${hi} && !/^gsub/.test(p.id)).sort((x, y) => x.price - y.price); return a.length ? a[0].id : ''; })()`;
await buy('شراء طلب عادي', firstIn(100, 400));
await buy('شراء طلب صغير', firstIn(1, 65));

// 3. the English shop, a landing page from the ads, the order page, the feeds
await step('الموقع الإنجليزي', async () => {
  const p = await page('الموقع الإنجليزي');
  const r = await p.goto(SITE + '/en/', { waitUntil: 'domcontentloaded', timeout: 45000 });
  if (!r || r.status() !== 200) throw new Error('ما فتح');
  await p.waitForSelector('a.card', { timeout: 20000 });
  p.errs(); await p.close();
});
await step('صفحة منتج من الإعلانات', async () => {
  const p = await page('صفحة منتج من الإعلانات');
  const r = await p.goto(SITE + '/ward/baby-rose-bouquet.html', { waitUntil: 'domcontentloaded', timeout: 45000 });
  if (!r || r.status() !== 200) throw new Error('ما فتحت');
  await p.waitForSelector('#addBtn', { timeout: 15000 });
  p.errs(); await p.close();
});
await step('صفحة متابعة الطلب', async () => {
  const p = await page('صفحة متابعة الطلب');
  const r = await p.goto(SITE + '/track.html', { waitUntil: 'domcontentloaded', timeout: 45000 });
  if (!r || r.status() !== 200) throw new Error('ما فتحت');
  await p.waitForTimeout(2500); p.errs(); await p.close();
});
await step('ملف المنتجات للإعلانات', async () => {
  const r = await fetch(SITE + '/merchant-feed.xml?t=' + Date.now());
  const x = await r.text(), n = (x.match(/<item>/g) || []).length, inS = (x.match(/in_stock/g) || []).length;
  if (r.status !== 200 || n < 50) throw new Error('فيه ' + n + ' منتج بس');
  if (inS < 15) fail('ملف المنتجات للإعلانات: ' + inS + ' منتج متوفر بس');
});
await step('فحص الدفع في السيرفر', async () => {
  const j = await (await fetch(API + '/hc')).json();
  if (!j.ok) throw new Error(Object.entries(j.checks || {}).filter(([, v]) => !v.ok).map(([k, v]) => k + ' ' + v.why).join(' · '));
});

await browser.close();
const run = process.env.GITHUB_RUN_ID ? `https://github.com/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID}` : '';
writeFileSync(process.env.OUT || 'status.json', JSON.stringify({ at: Date.now(), fails, notes, run }, null, 1));
console.log(JSON.stringify({ fails, notes }, null, 1));
