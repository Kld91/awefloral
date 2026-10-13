/* أو فلورا service worker: الشبكة أولاً (دايم آخر نسخة)، والنسخة المحفوظة إذا انقطع النت */
const CACHE = 'awe-v2';
const CORE = ['./', 'index.html', 'bunches.html', 'catalog.json', 'icon-180.png', 'pwa.js'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).catch(() => {}).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  if (u.origin !== self.location.origin) return;
  // pages always re-check with the server (no stale copy from the phone's cache)
  const net = r.mode === 'navigate' ? fetch(r.url, { cache: 'no-cache', credentials: 'same-origin' }) : fetch(r);
  e.respondWith(
    net.then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(r, copy)); }
      return res;
    }).catch(() => caches.match(r, { ignoreSearch: true }).then(m => m || (r.mode === 'navigate' ? caches.match('./') : undefined)))
  );
});
