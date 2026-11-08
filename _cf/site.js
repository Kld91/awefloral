// The website on Cloudflare: files are served straight from the static assets (free, no script run).
// This script only runs when no file matches the address, to keep GitHub Pages' behaviour:
// /en/ → /en/index.html, /about → /about.html, /guides → /guides/ , anything else → 404.html with status 404.
export default {
  async fetch(req, env) {
    const u = new URL(req.url), p = u.pathname;
    const get = async path => { const r = await env.ASSETS.fetch(new Request(new URL(path, u), req)); return r.status === 404 ? null : r; };
    if (p.endsWith('/')) { const r = await get(p + 'index.html'); if (r) return r; }
    else if (!/\.[a-z0-9]{1,8}$/i.test(p)) {
      const r = await get(p + '.html'); if (r) return r;
      if (await get(p + '/index.html')) return Response.redirect(new URL(p + '/' + u.search, u).toString(), 301);
    }
    const nf = await env.ASSETS.fetch(new Request(new URL('/404.html', u), req));
    return new Response(nf.body, { status: 404, headers: { 'content-type': 'text/html; charset=utf-8' } });
  }
};
