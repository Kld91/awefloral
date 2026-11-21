// The website on Cloudflare: files are served straight from the static assets (free, no script run).
// This script only runs when no file matches the address, to keep GitHub Pages' behaviour:
// /en/ → /en/index.html, /about → /about.html, /guides → /guides/ , anything else → 404.html with status 404.
// A shared product link (/?p=<id> or /en/?p=<id>) gets that product's name and photo in its preview (WhatsApp, X, iMessage…),
// from assets/og.json; the page itself is the same shop page, which opens the product.
const SITE = 'https://www.awefloral.com';
const WH = /^\/(en\/)?((bunches|holland|holland-small|stock|accessories|business)\.html|(holland|wholesale)\/[a-z0-9-]*(\.html)?)$/;
export default {
  async fetch(req, env) {
    const u = new URL(req.url), p = u.pathname;
    const get = async path => { const r = await env.ASSETS.fetch(new Request(new URL(path, u), req)); return r.status === 404 ? null : r; };
    // wholesale lives on Rawnbatat (www.rawnbatat.com): its pages are built into /rb/ (_cf/make_rb.py)
    const rbHost = /(^|\.)rawnbatat\.com$/.test(u.hostname);
    if (rbHost) {
      if (u.hostname !== 'www.rawnbatat.com') return Response.redirect('https://www.rawnbatat.com' + p + u.search, 301);
      if (p === '/' || p === '/index.html') return (await get('/rb/bunches.html')) || notFound(env, u, req);
      if (p === '/en/' || p === '/en/index.html') return (await get('/rb/en/bunches.html')) || notFound(env, u, req);
      if (p === '/sitemap.xml' || p === '/robots.txt') return (await get('/rb' + p)) || notFound(env, u, req);
      const f = p.endsWith('/') ? p + 'index.html' : /\.[a-z0-9]{1,8}$/i.test(p) ? p : p + '.html';
      const r = await get('/rb' + f); if (r) return r;
      if (p.endsWith('/')) return Response.redirect('https://www.rawnbatat.com' + p.replace(/\/$/, '.html'), 301);
      return Response.redirect('https://www.awefloral.com' + p + u.search, 301);   // gift-shop pages stay on Awe Floral
    }
    if (WH.test(p)) return Response.redirect('https://www.rawnbatat.com' + p + u.search, 301);   // old wholesale addresses
    if (p.endsWith('/')) {
      const r = await get(p + 'index.html'); if (!r) return notFound(env, u, req);
      const pid = u.searchParams.get('p') || '';
      if ((p === '/' || p === '/en/') && /^[a-z0-9-]{2,24}$/i.test(pid)) { try { return await withProduct(env, u, req, r, pid, p === '/en/'); } catch (e) {} }
      return r;
    }
    if (!/\.[a-z0-9]{1,8}$/i.test(p)) {
      const r = await get(p + '.html'); if (r) return r;
      if (await get(p + '/index.html')) return Response.redirect(new URL(p + '/' + u.search, u).toString(), 301);
    }
    return notFound(env, u, req);
  }
};
async function notFound(env, u, req) {
  const nf = await env.ASSETS.fetch(new Request(new URL('/404.html', u), req));
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
