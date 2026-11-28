/* Static pages: cart badge, colour switch, add to cart (same cart as the shop), source + measurement. */
(function(){
  var API = 'https://awe-dashboard.le77en.workers.dev';
  var store = { get: function(k){ try { return localStorage.getItem(k); } catch(e){ return null; } },
                set: function(k, v){ try { localStorage.setItem(k, v); } catch(e){} } };
  var $ = function(s){ return document.querySelector(s); };

  /* a discount code in the link (?cpn=AWE10, from an ad): kept for this visit, the shop's cart applies it */
  try { var cq = new URLSearchParams(location.search).get('cpn'); if(cq && /^[A-Za-z0-9]{3,16}$/.test(cq)) sessionStorage.setItem('awe_cpn', cq.toUpperCase()); } catch(e){}

  /* where the visitor came from: ?src=… wins, then a search engine referrer, then what we stored before */
  var src = '';
  try { var qs = new URLSearchParams(location.search); src = (qs.get('src') || (qs.has('gclid') || qs.has('gbraid') || qs.has('wbraid') ? 'gads' : qs.has('ttclid') ? 'tiktok' : '')).toLowerCase(); } catch(e){}   // a Google Ads click carries gclid
  if(!src && /(^|\.)(google|bing|yahoo|duckduckgo|yandex)\./i.test((document.referrer.split('/')[2] || ''))) src = 'seo';
  if(src) store.set('awe_src', src); else src = store.get('awe_src') || 'direct';

  var vid = store.get('awe_vid'); if(!vid){ vid = Math.random().toString(36).slice(2, 12); store.set('awe_vid', vid); }
  function beacon(type, extra){
    if(navigator.webdriver) return;   // the hourly site check
    var body = JSON.stringify(Object.assign({ type: type, vid: vid, src: src, page: 'seo' }, extra || {}));
    try { if(navigator.sendBeacon && navigator.sendBeacon(API + '/t', body)) return; } catch(e){}
    try { fetch(API + '/t', { method: 'POST', body: body, keepalive: true, mode: 'no-cors' }); } catch(e){}
  }
  function gev(name, p){ try { if(window.gtag) gtag('event', name, Object.assign({ source: src, site_section: 'seo' }, p || {})); } catch(e){} }
  /* Meta pixel, the same one as the shop: an Instagram ad that opens a product page is measured from the first page */
  if(!window.fbq && !navigator.webdriver){
    var fq = window.fbq = function(){ fq.callMethod ? fq.callMethod.apply(fq, arguments) : fq.queue.push(arguments); };
    window._fbq = fq; fq.push = fq; fq.loaded = true; fq.version = '2.0'; fq.queue = [];
    var fs = document.createElement('script'); fs.async = true; fs.src = 'https://connect.facebook.net/en_US/fbevents.js'; document.head.appendChild(fs);
    fbq('set', 'autoConfig', false, '2899070727159254');   // no automatic button scanning (slow taps)
    fbq('init', '2899070727159254'); fbq('track', 'PageView');
  }
  /* TikTok pixel: off since TikTok ads stopped (29 Oct 2026), as on the shop */
  function tev(name, p){ try { if(!window.ttq) return; var n = { ViewContent:'ViewContent', AddToCart:'AddToCart', InitiateCheckout:'InitiateCheckout', Purchase:'CompletePayment', Lead:'SubmitForm' }[name]; if(!n) return; p = p || {}; var ids = p.content_ids || []; ttq.track(n, { value: p.value, currency: 'SAR', content_type: 'product', contents: ids.map(function(id){ return { content_id: String(id) }; }) }); } catch(e){} }
  function fev(name, p){ tev(name, p); try { if(window.fbq) fbq('track', name, Object.assign({ currency: 'SAR' }, p || {})); } catch(e){} }

  function cart(){ try { var c = JSON.parse(store.get('awe_cart') || '[]'); return Array.isArray(c) ? c : []; } catch(e){ return []; } }
  function badge(){ var n = cart().reduce(function(s, i){ return s + (i.qty || 0); }, 0); var b = $('#badge'); if(b){ b.hidden = !n; b.textContent = n; } }
  badge();

  beacon('visit', { ref: (document.referrer || '').slice(0, 120) });

  var art = $('article.product');
  if(art){
    var pid = art.dataset.pid, name = art.dataset.name, price = +art.dataset.price, color = '';
    var sw = document.querySelectorAll('#sw [data-c]');
    var OFFL = [], userPicked = false;   // switched-off products, and single colours as pid:color (from the dashboard, via /avail)
    function pick(btn){
      color = btn.dataset.c;
      for(var i = 0; i < sw.length; i++) sw[i].setAttribute('aria-pressed', sw[i] === btn);
      var im = $('#pimg'); if(im && btn.dataset.img){ im.src = btn.dataset.img; im.alt = name + ' – ' + btn.textContent.trim(); }
      if(typeof applyAvail === 'function') applyAvail();
    }
    if(sw.length){
      var want = ''; try { want = new URLSearchParams(location.search).get('c') || ''; } catch(e){}
      var first = sw[0]; for(var i = 0; i < sw.length; i++) if(sw[i].dataset.c === want) first = sw[i];
      pick(first);
      for(var j = 0; j < sw.length; j++) sw[j].addEventListener('click', function(){ userPicked = true; var cn = art.querySelector('.cnote'); if(cn) cn.remove(); pick(this); });
    }
    // when it arrives: today until 10 pm Riyadh time (the shop offers the same slots at checkout), otherwise tomorrow
    var pr = $('.product .price');
    if(pr){ var hr = 0; try { hr = +new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Riyadh', hour: 'numeric', hourCycle: 'h23' }).format(new Date()); } catch(e){ hr = new Date().getHours(); }
      var eta = document.createElement('p'); eta.className = 'eta'; var dy = ''; try { dy = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Riyadh' }).format(new Date()); } catch(e){} eta.textContent = hr < 22 && ['2026-11-01'].indexOf(dy) < 0 ? 'اطلب الحين ويوصل اليوم' : 'اطلب الحين ويوصل بكرة'; pr.insertAdjacentElement('afterend', eta); }
    // customer reviews (published from the dashboard): this product's, or the shop's once there are a few
    (function(){
      var code = art.dataset.code, h1 = art.querySelector('h1'); if(!code || !h1 || !window.fetch) return;
      var TAG = { fresh: 'الورد طازج', look: 'التنسيق حلو', wrap: 'التغليف مرتب', ontime: 'وصل في موعده', card: 'الكرت', service: 'التعامل' };
      var e = function(t){ return String(t == null ? '' : t).replace(/[&<>"']/g, function(c){ return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
      var nRev = function(n){ return n === 1 ? 'تقييم واحد' : n === 2 ? 'تقييمين' : n <= 10 ? n + ' تقييمات' : n + ' تقييم'; };
      var stars = function(n){ var f = Math.round(n); return '<span class="rvs" aria-label="' + n + ' / 5">' + Array(f + 1).join('★') + '<i>' + Array(6 - f).join('★') + '</i></span>'; };
      var mon = function(ts){ try { return new Intl.DateTimeFormat(document.documentElement.lang === 'en' ? 'en-GB' : 'ar-SA-u-ca-gregory-nu-latn', { month: 'long', year: 'numeric' }).format(new Date(ts)); } catch(x){ return ''; } };
      fetch(API + '/reviews?n=6&pid=' + encodeURIComponent(code)).then(function(r){ return r.ok ? r.json() : null; }).then(function(d){
        if(!d) return;
        var own = d.product && d.product.count ? d.product : null, src = own || (d.count >= 3 ? d : null); if(!src) return;
        var line = document.createElement('a'); line.className = 'rvline'; line.href = '#reviews';
        line.innerHTML = stars(src.avg) + '<span class="num">' + src.avg + '</span><span>' + (own ? (own.count >= 20 ? nRev(own.count) : 'تقييم العملاء') : 'تقييم المتجر' + (d.count >= 20 ? ' · ' + nRev(d.count) : '')) + '</span>';
        h1.insertAdjacentElement('afterend', line);
        var list = (own ? own.list : d.list).filter(function(v){ return v.text; }).slice(0, 6); if(!list.length) return;
        var box = document.createElement('section'); box.className = 'rvbox'; box.id = 'reviews';
        box.innerHTML = '<h2>' + (own ? 'تقييمات هالمنتج' : 'آراء عملائنا') + '</h2><p class="rvhead"><b class="num">' + src.avg + '</b>' + stars(src.avg) + '<span>' + (src.count >= 20 ? nRev(src.count) : '') + '</span></p>' +
          list.map(function(v){ return '<figure class="rvc">' + stars(v.stars) + '<blockquote dir="auto">' + e(v.text) + '</blockquote><figcaption><b>' + e(v.name || 'عميل أو فلورا') + '</b>' +
            (v.items && v.items[0] ? ' · ' + e(v.items[0]) : '') + ' · ' + mon(v.ts) + '<span class="rvok">اشترى من الموقع</span></figcaption>' +
            (v.reply ? '<p class="rvr"><b>رد أو فلورا</b>' + e(v.reply) + '</p>' : '') + '</figure>'; }).join('');
        var rows = art.querySelector('ul.rows'); if(rows) rows.insertAdjacentElement('afterend', box); else art.appendChild(box);
      }).catch(function(){});
    })();
    var fid = function(){ return sw.length && color ? art.dataset.code + '-' + color : art.dataset.code; };   // the product feed id (baby-red, 13172449 …)
    var meta = function(){ return { value: price, content_type: 'product', content_ids: [fid()], contents: [{ id: fid(), quantity: 1, item_price: price }] }; };
    var item = function(){ return { item_id: fid(), item_name: name, item_category: art.dataset.cat, item_brand: 'أو فلورا', price: price, quantity: 1,
      item_variant: color ? ($('#sw [aria-pressed="true"]') || {}).textContent : undefined }; };
    gev('view_item', { currency: 'SAR', value: price, items: [item()] });
    fev('ViewContent', meta());
    try { var sn = JSON.parse(store.get('awe_seen') || '[]').filter(function(x){ return x !== pid; }); sn.unshift(pid); store.set('awe_seen', JSON.stringify(sn.slice(0, 12))); } catch(e){}   // recently viewed, shown on the shop's home
    beacon('view', { pid: pid, pn: name, value: price });
    var adding = false;
    // the dashboard's availability switches: a product switched off can't be added here either (same list as the shop and the cart)
    var soldOut = function(){
      var b = $('#addBtn'); if(!b || b.dataset.out) return; b.dataset.out = '1'; adding = true;
      // not a dead end: the main button takes them to what's in stock in the same kind (most ad visitors land here)
      var CAT = { 'باقات ورد': 'B', 'بيبي روز': 'B', 'دوار الشمس': 'B', 'فازات ورد': 'V', 'ورد جوري': 'B' }, to = CAT[art.dataset.cat] ? '/#/c/' + CAT[art.dataset.cat] : '/';
      var nb = b.cloneNode(false); nb.id = 'addBtn'; nb.dataset.out = '1'; nb.disabled = false; nb.textContent = 'خلصت · شوف البدائل المتوفرة';
      nb.onclick = function(e){ e.preventDefault(); var l = document.querySelector('.soldout a'); if(l) l.click(); else location.href = to; }; b.parentNode.replaceChild(nb, b); b = nb;
      var et = art.querySelector('.eta'); if(et) et.hidden = true;
      var n = document.createElement('p'); n.className = 'soldout'; n.innerHTML = 'هالباقة خلصت اليوم. <a href="' + to + '" data-go="' + to + '">شوف المتوفر الحين</a>';
      b.parentNode.insertAdjacentElement('beforebegin', n);
    };
    var isOff = function(c){ return OFFL.indexOf(pid) >= 0 || (!!c && OFFL.indexOf(pid + ':' + c) >= 0); };
    var applyAvail = function(){
      // colours that are off today: dimmed and not pickable; if the shown colour is off, move to one that's on
      var on = null;
      for(var i = 0; i < sw.length; i++){ var o = isOff(sw[i].dataset.c); sw[i].disabled = o; sw[i].style.opacity = o ? '.4' : ''; sw[i].style.textDecoration = o ? 'line-through' : ''; if(!o && !on) on = sw[i]; }
      // the colour in the link (?c=) is back on (an old list on this phone had it off): show it again, unless the customer picked another
      var wb = null; for(var w = 0; w < sw.length; w++) if(want && sw[w].dataset.c === want) wb = sw[w];
      if(wb && !userPicked && !isOff(want) && color !== want){ var cn0 = art.querySelector('.cnote'); if(cn0) cn0.remove(); pick(wb); return; }
      if(sw.length && isOff(color) && on && on.dataset.c !== color){
        if(wb && color === want && !userPicked && !art.querySelector('.cnote')){ var cn = document.createElement('p'); cn.className = 'cnote sub'; cn.textContent = 'خلص اليوم:' + ' ' + wb.textContent.trim() + ' · ' + 'نعرض لك:' + ' ' + on.textContent.trim(); var swb = $('#sw'); if(swb) swb.insertAdjacentElement('afterend', cn); }
        pick(on); return; }
      if(isOff(color)) soldOut();
      else { var b = $('#addBtn'), n = art.querySelector('.soldout'); if(b && b.dataset.out){ delete b.dataset.out; adding = false; b.disabled = false; b.textContent = 'أضف للسلة'; if(n) n.remove(); var et = art.querySelector('.eta'); if(et) et.hidden = false; } }
    };
    try { OFFL = JSON.parse(store.get('awe_off') || '[]'); if(isOff(color) || (sw.length && OFFL.indexOf(pid) < 0)) applyAvail(); } catch(x){}   // the list the shop saved on this device: no flash of "add" first
    if(window.fetch) fetch(API + '/avail').then(function(r){ return r.ok ? r.json() : null; }).then(function(d){
      if(!d || !Array.isArray(d.off)) return;
      try { store.set('awe_off', JSON.stringify(d.off)); } catch(x){}
      OFFL = d.off; applyAvail();   // also brings a product back if it's in stock again since this device last looked
    }).catch(function(){});
    window.addEventListener('pageshow', function(e){ if(e.persisted){ var b = $('#addBtn'); adding = !!(b && b.dataset.out); } });   // back from the cart (iOS keeps the page): the add button works again
    $('#addBtn').addEventListener('click', function(){
      if(adding) return; adding = true;
      var c = cart(), key = pid + '|' + color + '|0', ex = null;
      for(var i = 0; i < c.length; i++) if(c[i].key === key) ex = c[i];
      if(ex) ex.qty += 1; else c.push({ key: key, pid: pid, color: color, food: false, qty: 1 });
      store.set('awe_cart', JSON.stringify(c));
      gev('add_to_cart', { currency: 'SAR', value: price, items: [item()] });
      fev('AddToCart', meta());
      beacon('add', { pid: pid, pn: name, value: price });
      var to = (document.documentElement.lang === 'en' ? '/en/' : '/') + (src && src !== 'direct' ? '?src=' + encodeURIComponent(src) : '') + '#/cart';
      setTimeout(function(){ location.href = to; }, 250);   // a moment for the add-to-cart to reach Meta and Google before the page changes
    });
    var ask = $('#askBtn'); if(ask) ask.addEventListener('click', function(){ gev('whatsapp_question', { item_name: name }); });
  }

  /* product lists (sections, colours, occasions, "more like this"): hide products switched off in the dashboard today,
     the same /avail list the shop and the product page use. A card links to /ward/<slug>.html (?c=<colour> for one colour);
     its photo /img/p/<code>-… gives the product id g<code>. If every card in a list is off, the list stays as it is. */
  (function(){
    var cards = document.querySelectorAll('a.card[href*="/ward/"]'); if(!cards.length) return;
    var CPID = { 'baby-rose-bouquet': 'baby', 'lily-vase': 'lily' },   // products with colours: off as pid:colour; the card without a colour is off when every colour is
        COLS = { baby: ['bicolor', 'cream', 'fuchsia', 'lightpink', 'orange', 'pink', 'red', 'yellow'], lily: ['lpink', 'lred', 'lwhite'] };
    function keyOf(a){
      var h = a.getAttribute('href') || '', m = h.match(/\/ward\/([^/?#]+)\.html(?:\?c=([^&#]+))?/), c = m && m[2], cp = m && CPID[m[1]];
      if(cp && c) return [cp + ':' + c];
      if(cp) return COLS[cp].map(function(x){ return cp + ':' + x; });
      var im = a.querySelector('img'), s = im ? (im.getAttribute('src') || '') : '', k = s.match(/\/img\/p\/(\d+)-/);
      return k ? ['g' + k[1]] : [];
    }
    function hide(off){
      if(!off || !off.length) return;
      var set = {}; for(var i = 0; i < off.length; i++) set[String(off[i])] = 1;
      var groups = [];
      Array.prototype.forEach.call(cards, function(a){
        var p = a.parentNode, g = null; for(var j = 0; j < groups.length; j++) if(groups[j].p === p) g = groups[j];
        if(!g){ g = { p: p, all: [], out: [] }; groups.push(g); }
        var ks = keyOf(a), o = ks.length && (ks.every(function(k){ return set[k]; }) || (ks[0].indexOf(':') > 0 && set[ks[0].split(':')[0]]));
        g.all.push(a); if(o) g.out.push(a);
      });
      groups.forEach(function(g){ var keep = g.out.length >= g.all.length;
        g.all.forEach(function(a){ a.hidden = !keep && g.out.indexOf(a) >= 0; if(a.hidden) a.style.display = 'none'; else a.style.display = ''; }); });
    }
    try { hide(JSON.parse(store.get('awe_off') || '[]')); } catch(x){}
    if(window.fetch) fetch(API + '/avail', { cache: 'no-store' }).then(function(r){ return r.ok ? r.json() : null; }).then(function(d){
      if(!d || !Array.isArray(d.off)) return; try { store.set('awe_off', JSON.stringify(d.off)); } catch(x){}
      Array.prototype.forEach.call(cards, function(a){ a.hidden = false; a.style.display = ''; }); hide(d.off);
    }).catch(function(){});
  })();

  /* links into the shop keep the source */
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('a[data-go]'); if(!a || !src || src === 'direct') return;
    var go = a.getAttribute('data-go'), i = go.indexOf('#'), path = i < 0 ? go : go.slice(0, i), hash = i < 0 ? '' : go.slice(i);
    if(/[?&]src=/.test(path)) return;
    a.href = path + (path.indexOf('?') < 0 ? '?' : '&') + 'src=' + encodeURIComponent(src) + hash;
  }, true);
  /* product photos: swipe between them, the bars show which one is showing */
  Array.prototype.forEach.call(document.querySelectorAll('.pimg.gal'), function(g){
    var tr = g.querySelector('.gal-tr'), dots = g.querySelectorAll('.gal-dots i');
    function at(){ var i = Math.round(Math.abs(tr.scrollLeft) / (tr.clientWidth || 1));
      for(var j = 0; j < dots.length; j++) dots[j].className = j === i ? 'on' : ''; }
    tr.addEventListener('scroll', at, { passive: true }); at();
  });
})();
