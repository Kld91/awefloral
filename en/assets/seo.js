/* Static pages: cart badge, colour switch, add to cart (same cart as the shop), source + measurement. */
(function(){
  var API = 'https://awe-dashboard.le77en.workers.dev';
  var store = { get: function(k){ try { return localStorage.getItem(k); } catch(e){ return null; } },
                set: function(k, v){ try { localStorage.setItem(k, v); } catch(e){} } };
  var $ = function(s){ return document.querySelector(s); };

  /* where the visitor came from: ?src=… wins, then a search engine referrer, then what we stored before */
  var src = '';
  try { src = (new URLSearchParams(location.search).get('src') || '').toLowerCase(); } catch(e){}
  if(!src && /(^|\.)(google|bing|yahoo|duckduckgo|yandex)\./i.test((document.referrer.split('/')[2] || ''))) src = 'seo';
  if(src) store.set('awe_src', src); else src = store.get('awe_src') || 'direct';

  var vid = store.get('awe_vid'); if(!vid){ vid = Math.random().toString(36).slice(2, 12); store.set('awe_vid', vid); }
  function beacon(type, extra){
    var body = JSON.stringify(Object.assign({ type: type, vid: vid, src: src, page: 'seo' }, extra || {}));
    try { if(navigator.sendBeacon && navigator.sendBeacon(API + '/t', body)) return; } catch(e){}
    try { fetch(API + '/t', { method: 'POST', body: body, keepalive: true, mode: 'no-cors' }); } catch(e){}
  }
  function gev(name, p){ try { if(window.gtag) gtag('event', name, Object.assign({ source: src, site_section: 'seo' }, p || {})); } catch(e){} }
  /* Meta pixel, the same one as the shop: an Instagram ad that opens a product page is measured from the first page */
  if(!window.fbq){
    var fq = window.fbq = function(){ fq.callMethod ? fq.callMethod.apply(fq, arguments) : fq.queue.push(arguments); };
    window._fbq = fq; fq.push = fq; fq.loaded = true; fq.version = '2.0'; fq.queue = [];
    var fs = document.createElement('script'); fs.async = true; fs.src = 'https://connect.facebook.net/en_US/fbevents.js'; document.head.appendChild(fs);
    fbq('init', '2899070727159254'); fbq('track', 'PageView');
  }
  function fev(name, p){ try { if(window.fbq) fbq('track', name, Object.assign({ currency: 'SAR' }, p || {})); } catch(e){} }

  function cart(){ try { var c = JSON.parse(store.get('awe_cart') || '[]'); return Array.isArray(c) ? c : []; } catch(e){ return []; } }
  function badge(){ var n = cart().reduce(function(s, i){ return s + (i.qty || 0); }, 0); var b = $('#badge'); if(b){ b.hidden = !n; b.textContent = n; } }
  badge();

  beacon('visit', { ref: (document.referrer || '').slice(0, 120) });

  var art = $('article.product');
  if(art){
    var pid = art.dataset.pid, name = art.dataset.name, price = +art.dataset.price, color = '';
    var sw = document.querySelectorAll('#sw [data-c]');
    function pick(btn){
      color = btn.dataset.c;
      for(var i = 0; i < sw.length; i++) sw[i].setAttribute('aria-pressed', sw[i] === btn);
      var im = $('#pimg'); if(im && btn.dataset.img){ im.src = btn.dataset.img; im.alt = name + ' – ' + btn.textContent.trim(); }
    }
    if(sw.length){
      var want = ''; try { want = new URLSearchParams(location.search).get('c') || ''; } catch(e){}
      var first = sw[0]; for(var i = 0; i < sw.length; i++) if(sw[i].dataset.c === want) first = sw[i];
      pick(first);
      for(var j = 0; j < sw.length; j++) sw[j].addEventListener('click', function(){ pick(this); });
    }
    // when it arrives: today until 8 pm Riyadh time (the shop offers the same slots at checkout), otherwise tomorrow
    var pr = $('.product .price');
    if(pr){ var hr = 0; try { hr = +new Intl.DateTimeFormat('en-US', { timeZone: 'Asia/Riyadh', hour: 'numeric', hourCycle: 'h23' }).format(new Date()); } catch(e){ hr = new Date().getHours(); }
      var eta = document.createElement('p'); eta.className = 'eta'; eta.textContent = hr < 20 ? 'Order now for delivery today' : 'Order now for delivery tomorrow'; pr.insertAdjacentElement('afterend', eta); }
    // customer reviews (published from the dashboard): this product's, or the shop's once there are a few
    (function(){
      var code = art.dataset.code, h1 = art.querySelector('h1'); if(!code || !h1 || !window.fetch) return;
      var TAG = { fresh: 'Fresh flowers', look: 'Beautiful arrangement', wrap: 'Neat wrapping', ontime: 'Arrived on time', card: 'Gift card', service: 'Friendly service' };
      var e = function(t){ return String(t == null ? '' : t).replace(/[&<>"']/g, function(c){ return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
      var nRev = function(n){ return n === 1 ? '1 review' : n === 2 ? '2 reviews' : n <= 10 ? n + ' reviews' : n + ' reviews'; };
      var stars = function(n){ var f = Math.round(n); return '<span class="rvs" aria-label="' + n + ' / 5">' + Array(f + 1).join('★') + '<i>' + Array(6 - f).join('★') + '</i></span>'; };
      var mon = function(ts){ try { return new Intl.DateTimeFormat(document.documentElement.lang === 'en' ? 'en-GB' : 'en-GB', { month: 'long', year: 'numeric' }).format(new Date(ts)); } catch(x){ return ''; } };
      fetch(API + '/reviews?n=6&pid=' + encodeURIComponent(code)).then(function(r){ return r.ok ? r.json() : null; }).then(function(d){
        if(!d) return;
        var own = d.product && d.product.count ? d.product : null, src = own || (d.count >= 3 ? d : null); if(!src) return;
        var line = document.createElement('a'); line.className = 'rvline'; line.href = '#reviews';
        line.innerHTML = stars(src.avg) + '<span class="num">' + src.avg + '</span><span>' + (own ? nRev(own.count) : 'Shop rating · ' + nRev(d.count)) + '</span>';
        h1.insertAdjacentElement('afterend', line);
        var list = (own ? own.list : d.list).filter(function(v){ return v.text; }).slice(0, 6); if(!list.length) return;
        var box = document.createElement('section'); box.className = 'rvbox'; box.id = 'reviews';
        box.innerHTML = '<h2>' + (own ? 'Reviews of this product' : 'What our customers say') + '</h2><p class="rvhead"><b class="num">' + src.avg + '</b>' + stars(src.avg) + '<span>' + nRev(src.count) + '</span></p>' +
          list.map(function(v){ return '<figure class="rvc">' + stars(v.stars) + '<blockquote dir="auto">' + e(v.text) + '</blockquote><figcaption><b>' + e(v.name || 'Awe Floral customer') + '</b>' +
            (v.items && v.items[0] ? ' · ' + e(v.items[0]) : '') + ' · ' + mon(v.ts) + '<span class="rvok">Bought on the site</span></figcaption>' +
            (v.reply ? '<p class="rvr"><b>Reply from Awe Floral</b>' + e(v.reply) + '</p>' : '') + '</figure>'; }).join('');
        var rows = art.querySelector('ul.rows'); if(rows) rows.insertAdjacentElement('afterend', box); else art.appendChild(box);
      }).catch(function(){});
    })();
    var fid = function(){ return sw.length && color ? art.dataset.code + '-' + color : art.dataset.code; };   // the product feed id (baby-red, 13172449 …)
    var meta = function(){ return { value: price, content_type: 'product', content_ids: [fid()], contents: [{ id: fid(), quantity: 1, item_price: price }] }; };
    var item = function(){ return { item_id: fid(), item_name: name, item_category: art.dataset.cat, item_brand: 'Awe Floral', price: price, quantity: 1,
      item_variant: color ? ($('#sw [aria-pressed="true"]') || {}).textContent : undefined }; };
    gev('view_item', { currency: 'SAR', value: price, items: [item()] });
    fev('ViewContent', meta());
    try { var sn = JSON.parse(store.get('awe_seen') || '[]').filter(function(x){ return x !== pid; }); sn.unshift(pid); store.set('awe_seen', JSON.stringify(sn.slice(0, 12))); } catch(e){}   // recently viewed, shown on the shop's home
    beacon('view', { pid: pid, pn: name, value: price });
    var adding = false;
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
