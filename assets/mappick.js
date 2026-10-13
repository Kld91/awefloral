/* أو فلورا · تحديد موقع التوصيل على الخريطة
   يفتح خريطة (OpenStreetMap عبر Leaflet، تتحمّل فقط لما العميل يفتحها). العميل يحرّك الخريطة تحت الدبوس،
   أو يضغط «موقعي الحالي»، أو يلصق رابط قوقل ماب/واتساب. الناتج رابط قوقل ماب يدخل في رسالة الطلب.
   الاستخدام: MapPick.attach(buttonEl, outEl, onChange) · MapPick.link() */
(function () {
  const AR = document.documentElement.lang !== 'en';
  const T = AR ? {
    btn: 'حدّد الموقع على الخريطة', change: 'تغيير الموقع', set: 'تم تحديد الموقع ✓', view: 'عرض', remove: 'حذف',
    title: 'موقع التوصيل', hint: 'حرّك الخريطة لين يصير الدبوس فوق البيت بالضبط.', mine: 'موقعي الحالي', ok: 'تأكيد الموقع',
    paste: 'أو الصق رابط قوقل ماب', pasteLbl: 'الصق رابط الموقع من قوقل ماب أو واتساب', pasteOk: 'استخدم الرابط', locating: 'نحدد موقعك…',
    denied: 'ما قدرنا نوصل لموقعك. فعّل خدمة الموقع أو حرّك الخريطة بنفسك.', badLink: 'ما قدرنا نقرأ الرابط. تأكد إنه رابط موقع.',
    far: 'الموقع يبدو خارج الرياض. تأكد منه قبل التأكيد.', loadErr: 'ما قدرنا نحمّل الخريطة. الصق رابط الموقع بدلها.',
    loading: 'نحمّل الخريطة…', close: 'إغلاق'
  } : {
    btn: 'Pin the location on a map', change: 'Change location', set: 'Location pinned ✓', view: 'View', remove: 'Remove',
    title: 'Delivery location', hint: 'Move the map until the pin sits on the exact building.', mine: 'My location', ok: 'Confirm location',
    paste: 'Or paste a Google Maps link', pasteLbl: 'Paste a location link from Google Maps or WhatsApp', pasteOk: 'Use link', locating: 'Finding you…',
    denied: 'We couldn’t get your location. Turn on location services or move the map yourself.', badLink: 'We couldn’t read that link. Make sure it’s a location link.',
    far: 'This looks outside Riyadh. Please double-check before confirming.', loadErr: 'The map didn’t load. Paste a location link instead.',
    loading: 'Loading the map…', close: 'Close'
  };
  const RIYADH = [24.7136, 46.6753];
  const SOURCES = [
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.'
  ];
  const KEY = 'awe_loc';
  let value = null, map = null, sheet = null, onChange = () => {}, outEl = null, btnEl = null, loading = null, styled = false;
  try { value = JSON.parse(sessionStorage.getItem(KEY) || 'null'); } catch (e) {}

  const gmaps = (lat, lng) => `https://maps.google.com/?q=${lat.toFixed(6)},${lng.toFixed(6)}`;
  const inRiyadh = (lat, lng) => lat > 24.2 && lat < 25.3 && lng > 46.2 && lng < 47.3;
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  function parseLink(s) {
    s = String(s || '').trim();
    if (!s) return null;
    const ok = (a, b) => { const lat = +a, lng = +b; return Math.abs(lat) <= 90 && Math.abs(lng) <= 180 ? { lat, lng } : null; };
    const m = s.match(/@(-?\d{1,2}\.\d+),\s*(-?\d{1,3}\.\d+)/) || s.match(/[?&](?:q|query|ll|destination|daddr)=(-?\d{1,2}\.\d+)(?:,|%2C)\s*(-?\d{1,3}\.\d+)/i)
      || s.match(/!3d(-?\d{1,2}\.\d+)!4d(-?\d{1,3}\.\d+)/) || s.match(/^(-?\d{1,2}\.\d+)\s*[, ]\s*(-?\d{1,3}\.\d+)$/);
    if (m) return ok(m[1], m[2]);
    const u = s.match(/https?:\/\/(?:maps\.app\.goo\.gl|goo\.gl\/maps|maps\.google\.[a-z.]+|(?:www\.)?google\.[a-z.]+\/maps|g\.co\/kgs)\S*/i);
    return u ? { url: u[0] } : null;
  }
  function link() { return value ? (value.url || gmaps(value.lat, value.lng)) : ''; }
  function paintOut() {
    if (!outEl || !btnEl) return;
    const l = link();
    outEl.hidden = !l;
    btnEl.querySelector('span').textContent = l ? T.change : T.btn;
    outEl.innerHTML = l ? `<b>${T.set}</b> · <a href="${esc(l)}" target="_blank" rel="noopener">${T.view}</a> · <button type="button" data-mp-remove>${T.remove}</button>` : '';
  }
  function set(v) {
    value = v;
    try { v ? sessionStorage.setItem(KEY, JSON.stringify(v)) : sessionStorage.removeItem(KEY); } catch (e) {}
    paintOut(); onChange(link());
  }

  function style() {
    if (styled) return; styled = true;
    const st = document.createElement('style');
    st.textContent = `.mp-btn{justify-self:start;min-height:40px;padding:0 14px;font-size:14px;gap:6px}.mp-btn svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.8}
.mp-out{display:block;font-size:13px;color:var(--accent,#1F8A4C)}.mp-out[hidden]{display:none}.mp-out a,.mp-out button{color:inherit;font:inherit;font-size:13px;text-decoration:underline;background:none;border:0;padding:0;cursor:pointer}.mp-out button{color:var(--muted,#8C918E)}
.mp-wrap{position:fixed;inset:0;z-index:80;background:rgba(0,0,0,.45);display:flex;align-items:flex-end;justify-content:center}
.mp-wrap[hidden]{display:none}.mp{width:min(480px,100%);height:min(92dvh,760px);background:#fff;display:flex;flex-direction:column;font:inherit;color:#111}
.mp-bar{display:flex;align-items:center;justify-content:space-between;padding:6px 8px 6px 16px;border-bottom:1px solid #eee}.mp-bar strong{font-size:16px}
.mp-x{border:0;background:none;font-size:18px;width:44px;height:44px;cursor:pointer;color:#111}.mp-map{position:relative;flex:1;background:#eef0ec}#mpMap{position:absolute;inset:0}
.mp-pin{position:absolute;left:50%;top:50%;width:30px;height:44px;transform:translate(-50%,-100%);z-index:500;pointer-events:none;fill:#1F8A4C;filter:drop-shadow(0 2px 2px rgba(0,0,0,.3))}
.mp-mine{position:absolute;z-index:500;top:12px;right:12px;border:1px solid #ddd;background:#fff;color:#111;padding:9px 14px;font:inherit;font-size:14px;font-weight:600;cursor:pointer;box-shadow:0 1px 4px rgba(0,0,0,.15)}
.mp-foot{padding:12px 16px calc(12px + env(safe-area-inset-bottom));display:grid;grid-template-columns:minmax(0,1fr);gap:10px;border-top:1px solid #eee}
.mp-hint{margin:0;font-size:13px;color:#555}.mp-hint.warn{color:#B3152E}
.mp-paste{display:flex;gap:8px}.mp-paste input{flex:1;min-width:0;width:auto;unicode-bidi:plaintext;border:1px solid #ddd;border-radius:0;padding:10px;font:inherit;font-size:16px}.mp-paste button{border:1px solid #ddd;background:#fff;color:#111;padding:0 12px;font:inherit;font-size:13px;cursor:pointer;white-space:nowrap}
.mp-ok{border:0;background:#1F8A4C;color:#fff;min-height:48px;font:inherit;font-size:15px;font-weight:700;cursor:pointer}`;
    document.head.appendChild(st);
  }

  function tag(kind, url) {
    return new Promise((res, rej) => {
      const el = document.createElement(kind === 'css' ? 'link' : 'script');
      if (kind === 'css') { el.rel = 'stylesheet'; el.href = url; } else { el.src = url; }
      el.onload = res; el.onerror = () => { el.remove(); rej(); };
      document.head.appendChild(el);
    });
  }
  function load() {
    if (window.L && window.L.map) return Promise.resolve();
    if (loading) return loading;
    let i = 0;
    const next = () => i >= SOURCES.length ? Promise.reject() :
      tag('js', SOURCES[i] + 'js').then(() => { tag('css', SOURCES[i] + 'css').catch(() => {}); }, () => { i++; return next(); });
    loading = next().catch(e => { loading = null; throw e; });
    return loading;
  }
  function build() {
    style();
    sheet = document.createElement('div');
    sheet.className = 'mp-wrap'; sheet.hidden = true; sheet.dir = AR ? 'rtl' : 'ltr';
    sheet.innerHTML = `<div class="mp" role="dialog" aria-modal="true" aria-label="${T.title}">
      <div class="mp-bar"><strong>${T.title}</strong><button type="button" class="mp-x" data-mp-close aria-label="${T.close}">✕</button></div>
      <div class="mp-map"><div id="mpMap" dir="ltr"></div><svg class="mp-pin" viewBox="0 0 24 36" aria-hidden="true"><path d="M12 0C5.4 0 0 5.3 0 11.9 0 20.8 12 36 12 36s12-15.2 12-24.1C24 5.3 18.6 0 12 0Z"/><circle cx="12" cy="12" r="4.5" fill="#fff"/></svg>
        <button type="button" class="mp-mine" data-mp-mine>${T.mine}</button></div>
      <div class="mp-foot"><p class="mp-hint" id="mpHint" aria-live="polite">${T.hint}</p>
        <div class="mp-paste"><input type="url" id="mpLink" placeholder="${T.paste}" aria-label="${T.pasteLbl}" autocomplete="off" inputmode="url"><button type="button" data-mp-paste>${T.pasteOk}</button></div>
        <button type="button" class="mp-ok" data-mp-ok>${T.ok}</button></div></div>`;
    document.body.appendChild(sheet);
    sheet.addEventListener('click', e => {
      if (e.target === sheet || e.target.closest('[data-mp-close]')) close();
      else if (e.target.closest('[data-mp-mine]')) locate();
      else if (e.target.closest('[data-mp-ok]')) confirm();
      else if (e.target.closest('[data-mp-paste]')) usePasted();
    });
    sheet.querySelector('#mpLink').addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); usePasted(); } });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && !sheet.hidden) { e.stopImmediatePropagation(); e.preventDefault(); close(); } }, true);
  }
  function hint(t, warn) { const h = sheet.querySelector('#mpHint'); h.textContent = t; h.classList.toggle('warn', !!warn); }
  function confirm() {
    const typed = parseLink(sheet.querySelector('#mpLink').value);
    if (!map && !typed) return hint(T.loadErr, true);
    if (typed && typed.url) { set(typed); return close(); }
    const c = map ? map.getCenter() : typed;
    set({ lat: +c.lat.toFixed(6), lng: +c.lng.toFixed(6) }); close();
  }
  function usePasted() {
    const v = parseLink(sheet.querySelector('#mpLink').value);
    if (!v) return hint(T.badLink, true);
    if (v.url || !map) { set(v); close(); return; }
    map.setView([v.lat, v.lng], 17);
    sheet.querySelector('#mpLink').value = '';
    hint(inRiyadh(v.lat, v.lng) ? T.hint : T.far, !inRiyadh(v.lat, v.lng));
  }
  function locate() {
    if (!navigator.geolocation) return hint(T.denied, true);
    hint(T.locating);
    navigator.geolocation.getCurrentPosition(p => {
      const { latitude: a, longitude: b } = p.coords;
      if (map) map.setView([a, b], 17);
      hint(inRiyadh(a, b) ? T.hint : T.far, !inRiyadh(a, b));
    }, () => hint(T.denied, true), { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 });
  }
  function open() {
    if (!sheet) build();
    sheet.hidden = false; sheet.querySelector('[data-mp-close]').focus({ preventScroll: true });
    sheet.querySelector('#mpLink').value = value && value.url ? value.url : '';
    if (!map) hint(T.loading);
    load().then(() => {
      const L = window.L, has = value && value.lat != null, start = has ? [value.lat, value.lng] : RIYADH;
      if (!map) {
        map = L.map('mpMap', { zoomControl: true, attributionControl: true }).setView(start, has ? 17 : 11);
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>' }).addTo(map);
        map.on('moveend', () => { const c = map.getCenter(); if (!inRiyadh(c.lat, c.lng) && map.getZoom() > 12) hint(T.far, true); });
      } else { map.setView(start, has ? 17 : map.getZoom()); }
      hint(T.hint);
      setTimeout(() => map.invalidateSize(), 120);
    }).catch(() => hint(T.loadErr, true));
  }
  function close() { if (sheet && !sheet.hidden) { sheet.hidden = true; if (btnEl) btnEl.focus({ preventScroll: true }); } }

  window.MapPick = {
    attach(button, out, cb) {
      style();
      btnEl = button; outEl = out; onChange = cb || onChange;
      button.classList.add('mp-btn'); out.classList.add('mp-out'); button.hidden = false;
      if (!button.querySelector('span')) button.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21Z"/><circle cx="12" cy="9.5" r="2.5"/></svg><span></span>';
      button.addEventListener('click', open);
      out.addEventListener('click', e => { if (e.target.closest('[data-mp-remove]')) set(null); });
      paintOut();
    },
    link, clear() { set(null); }, parseLink
  };
})();
