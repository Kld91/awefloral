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
    var item = function(){ return { item_id: art.dataset.code, item_name: name, item_category: art.dataset.cat, item_brand: 'أو فلورا', price: price, quantity: 1,
      item_variant: color ? ($('#sw [aria-pressed="true"]') || {}).textContent : undefined }; };
    gev('view_item', { currency: 'SAR', value: price, items: [item()] });
    beacon('view', { pid: pid, pn: name, value: price });
    $('#addBtn').addEventListener('click', function(){
      var c = cart(), key = pid + '|' + color + '|0', ex = null;
      for(var i = 0; i < c.length; i++) if(c[i].key === key) ex = c[i];
      if(ex) ex.qty += 1; else c.push({ key: key, pid: pid, color: color, food: false, qty: 1 });
      store.set('awe_cart', JSON.stringify(c));
      gev('add_to_cart', { currency: 'SAR', value: price, items: [item()] });
      beacon('add', { pid: pid, pn: name, value: price });
      location.href = '/' + (src && src !== 'direct' ? '?src=' + encodeURIComponent(src) : '') + '#/cart';
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
})();
