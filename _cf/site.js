// The website on Cloudflare: files are served straight from the static assets (free, no script run).
// It runs first for every address but /assets/ and /img/ (each host serves its own pages); otherwise it keeps GitHub Pages' behaviour, to keep GitHub Pages' behaviour:
// /en/ → /en/index.html, /about → /about.html, /guides → /guides/ , anything else → 404.html with status 404.
// A shared product link (/?p=<id> or /en/?p=<id>) gets that product's name and photo in its preview (WhatsApp, X, iMessage…),
// from assets/og.json; the page itself is the same shop page, which opens the product.
const SITE = 'https://www.awefloral.com';
const WH = /^\/(en\/)?((bunches|holland|holland-small|stock|accessories|business)\.html|(holland|wholesale)\/[a-z0-9-]*(\.html)?)$/;
// photos and the order notice from the dashboard, served from the shop's own address: customers never see the dashboard's address
const API = 'https://awe-dashboard.le77en.workers.dev';
const MEDIA = /^\/m\/(card\/img|ugc\/img|track\/photo|track\/invoice)$/;
// Awe Floral never links to the wholesale site (Rawnbatat): any such link left in a page is dropped on the way out
const WS_LINK = /^\/?(en\/)?((bunches|holland|holland-small|accessories|business)\.html|(holland|wholesale)\/)/i;
export default {
  async fetch(req, env) {
    const u = new URL(req.url), p = u.pathname;
    if (MEDIA.test(p)) return media(req, u, p);
    const get = async path => { const r = await env.ASSETS.fetch(new Request(new URL(path, u), req)); return r.status === 404 ? null : r; };
    // wholesale lives on Rawnbatat (www.rawnbatat.com): its pages are built into /rb/ (_cf/make_rb.py)
    const rbHost = /(^|\.)rawnbatat\.com$/.test(u.hostname);
    if (rbHost) {
      if (u.hostname !== 'www.rawnbatat.com') return Response.redirect('https://www.rawnbatat.com' + p + u.search, 301);
      // the home page is the imports for now; Riyadh stock (bunches, stock, wholesale/) is off until it returns as «Express»
      if (p === '/' || p === '/index.html') return (await get('/rb/holland.html')) || notFound(env, u, req);
      if (p === '/en/' || p === '/en/index.html') return (await get('/rb/en/holland.html')) || notFound(env, u, req);
      if (/^\/(en\/)?((bunches|stock)\.html|wholesale\/.*)$/.test(p)) return Response.redirect('https://www.rawnbatat.com' + (p.startsWith('/en/') ? '/en/' : '/'), 302);
      if (p === '/en') return Response.redirect('https://www.rawnbatat.com/en/', 301);
      if (p === '/sitemap.xml' || p === '/robots.txt') return (await get('/rb' + p)) || notFound(env, u, req);
      const f = p.endsWith('/') ? p + 'index.html' : /\.[a-z0-9]{1,8}$/i.test(p) ? p : p + '.html';
      const r = await get('/rb' + f); if (r) return r;
      if (!/\.(html|xml|txt)$/i.test(f)) { const a = await env.ASSETS.fetch(req); if (a.status !== 404) return a; }   // data, scripts, styles and images are shared
      if (p.endsWith('/')) return Response.redirect('https://www.rawnbatat.com' + p.replace(/\/$/, '.html'), 301);
      if (WH.test(p)) return Response.redirect('https://www.rawnbatat.com' + (p.startsWith('/en/') ? '/en/' : '/'), 302);   // a wholesale page that is gone (a type out of season): the home page, never a loop to Awe Floral
      return Response.redirect('https://www.awefloral.com' + p + u.search, 301);   // gift-shop pages stay on Awe Floral
    }
    if (WH.test(p)) return Response.redirect('https://www.rawnbatat.com' + p + u.search, 301);   // old wholesale addresses
    if (!/\.[a-z0-9]{1,8}$/i.test(p) && !p.endsWith('/') && WH.test(p + '.html')) return Response.redirect('https://www.rawnbatat.com' + p + '.html' + u.search, 301);   // the same, without .html
    if (!p.endsWith('/')) { const a = await env.ASSETS.fetch(req); if (a.status !== 404) return noWs(a); }   // the script runs first (so each host gets its own pages): the files as they are
    if (p.endsWith('/')) {
      const r = await get(p + 'index.html'); if (!r) return notFound(env, u, req);
      const pid = u.searchParams.get('p') || '';
      if ((p === '/' || p === '/en/') && /^[a-z0-9-]{2,24}$/i.test(pid)) { try { return noWs(await withProduct(env, u, req, r, pid, p === '/en/')); } catch (e) {} }
      return noWs(r);
    }
    if (!/\.[a-z0-9]{1,8}$/i.test(p)) {
      const r = await get(p + '.html'); if (r) return noWs(r);
      if (await get(p + '/index.html')) return Response.redirect(new URL(p + '/' + u.search, u).toString(), 301);
    }
    return notFound(env, u, req);
  }
};
function noWs(r) {
  if (!/text\/html/.test(r.headers.get('content-type') || '')) return r;
  return new HTMLRewriter().on('a[href]', { element(e) { const h = (e.getAttribute('href') || '').replace(/^https?:\/\/(www\.)?awefloral\.com/i, '');
    if (/rawnbatat\.com/i.test(h) || WS_LINK.test(h)) e.remove(); } }).transform(r);
}
async function media(req, u, p) {
  if (req.method !== 'GET' && req.method !== 'HEAD') return new Response(null, { status: 405 });
  const pub = !p.startsWith('/m/track/');   // review and customer photos are public and cached; order photos and notices are not
  const r = await fetch(API + p.slice(2) + u.search, { method: req.method, headers: { accept: req.headers.get('accept') || '*/*' }, ...(pub ? { cf: { cacheEverything: true, cacheTtl: 86400 } } : {}) });
  const h = new Headers();
  for (const k of ['content-type', 'content-length', 'content-disposition', 'etag', 'last-modified']) { const v = r.headers.get(k); if (v) h.set(k, v); }
  h.set('cache-control', pub && r.ok ? 'public, max-age=86400' : 'private, no-store');
  return new Response(r.body, { status: r.status, headers: h });
}
async function notFound(env, u, req) {
  const nf = await env.ASSETS.fetch(new Request(new URL(/(^|\.)rawnbatat\.com$/.test(u.hostname) ? '/rb/404.html' : '/404.html', u), req));
  return new Response(nf.body, { status: 404, headers: { 'content-type': 'text/html; charset=utf-8' } });
}
async function withProduct(env, u, req, page, pid, en) {
  const j = await env.ASSETS.fetch(new Request(new URL('/assets/og.json', u), req));
  if (!j.ok) return page;
  const it = (await j.json())[pid]; if (!it) return page;
  const name = en ? it[1] : it[0], img = SITE + it[2], url = SITE + (en ? '/en/' : '/') + '?p=' + encodeURIComponent(pid);
  const title = name + (en ? ' · Awe Floral' : ' · أو فلورا');
  const desc = en ? 'Order it from Awe Floral, delivered in Riyadh.' : 'اطلبها من أو فلورا، توصيل داخل الرياض.';
  const set = v => ({ element(e) { e.setAttribute('content', v); } });
  const drop = { element(e) { e.remove(); } };
  return new HTMLRewriter()
    .on('meta[property="og:title"]', set(title)).on('meta[property="og:description"]', set(desc))
    .on('meta[property="og:url"]', set(url)).on('meta[property="og:image"]', set(img))
    .on('meta[property="og:image:width"]', drop).on('meta[property="og:image:height"]', drop)
    .transform(new Response(page.body, page));
}
