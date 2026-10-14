/* «نسّقها بنفسك» page: picks today's Riyadh wholesale varieties for each flower in the arrangement (catalog.json), lets the
   customer swap a variety, totals the price and puts them in the wholesale cart (bunches.html?add=id:q,…).
   A flower Riyadh doesn't have today comes from the Holland page (holland.json, loaded only then): we show its price per stem
   and a link to it, and leave it out of the total and the cart. */
(function () {
  var cfgEl = document.getElementById('styData');
  if (!cfgEl) return;
  var C = JSON.parse(cfgEl.textContent), EN = C.lang === 'en';
  var T = EN ? {
    cur: 'SAR', need: 'Used', get: 'You get', min: 'minimum', change: 'Change', close: 'Done', none: 'Not in stock in Riyadh today',
    holland: 'Find it in Dutch flowers', diff: 'Today’s colour differs from the photo', add: 'Add the flowers to cart',
    err: 'We could not load today’s stock. Refresh the page in a moment.', stem: 'stem', stems: 'stems', bunch: 'bunch', bunches: 'bunches',
    extra: 'The rest is extra for another vase', about: 'About', from: 'From Dutch flowers', see: 'See it in Dutch flowers',
    hol: 'Dutch flowers are not in the total: their prices change and they come by the box, so check them on their page.',
    shut: 'Riyadh wholesale orders are paused for now. Order this arrangement ready-made below, or find its flowers in Dutch flowers.'
  } : {
    cur: 'ر.س', need: 'يحتاج', get: 'تطلب', min: 'أقل كمية', change: 'غيّر الصنف', close: 'تم', none: 'مو متوفر اليوم في الرياض',
    holland: 'شوفه في ورد هولندا', diff: 'اللون المتوفر اليوم يختلف عن الصورة', add: 'أضف الورد للسلة',
    err: 'ما قدرنا نحمّل توفر اليوم. حدّث الصفحة بعد شوي.', stem: 'غصن', stems: 'أغصان', bunch: 'ربطة', bunches: 'ربطات',
    extra: 'الزيادة تكفي لفازة ثانية', about: 'عن', from: 'من ورد هولندا', see: 'شوفه في ورد هولندا',
    hol: 'ورد هولندا ما هو داخل في المجموع: سعره يتغير وينباع بالكرتون، فشوف تفاصيله في صفحته.',
    shut: 'طلبات ورد الجملة من الرياض متوقفة حالياً. اطلب التنسيقة جاهزة من تحت، أو شوف وردها في ورد هولندا.'
  };
  var pre = EN ? '/en' : '';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  // prices carry the Saudi riyal sign (styled in seo.css), number to its right in both languages
  var money = function (n) { var v = Math.round(n * 100) / 100; return '<span class="mny"><i class="sar" role="img" aria-label="' + T.cur + '"></i><span class="num">' + (Number.isInteger(v) ? v : v.toFixed(2)) + '</span></span>'; };
  var iso = function (d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
  var unitPrice = function (it, q) { return q >= it.m ? it.p2 : it.p1; };
  var fitQ = function (it, q) { return Math.min(it.st - it.st % it.s, Math.max(it.s, Math.ceil(q / it.s) * it.s)); };
  var KW = { white: /white|ivory|blanc/i, cream: /cream|ivory|vanilla/i, pink: /pink|rose\b/i, peach: /peach|salmon|apricot|coral/i, green: /green/i,
    yellow: /yellow|gold|lemon/i, lilac: /lilac|lavender|mauve/i, purple: /purple|violet/i, blue: /blue/i, red: /\bred\b/i, orange: /orange/i };
  var colourOf = function (it) {
    if (it.c) return it.c === 'apricot' || it.c === 'salmon' ? 'peach' : it.c;
    for (var k in C.variety) if (it.n.indexOf(k) > -1) return C.variety[k];
    for (var c in KW) if (KW[c].test(it.n)) return c;
    return '';
  };
  var ITEMS = [], HOL = null, sel = {}, rows = $('#styRows'), CLOSED = false;
  var img = function (it) { return it.h ? it.i + '.webp' : '/img/n/' + it.i + '.webp'; };   // holland.json carries its own /img/… paths
  // sold by the bunch (≈ 10 stems): flagged in the data, or eucalyptus sold by the piece at a bunch price
  var isBunch = function (it) { return it.u === 'bunch' || (it.s === 1 && /eucalyptus/i.test(it.n)); };
  var need = function (it, c) { return isBunch(it) ? Math.max(1, Math.ceil(c.stems / 10)) : c.stems; };
  var unit = function (it, n) { var b = isBunch(it), pl = EN ? n !== 1 : (n >= 3 && n <= 10); return pl ? (b ? T.bunches : T.stems) : (b ? T.bunch : T.stem); };
  var key = function (it) { return (it.h ? 'h:' : 'r:') + it.id; };
  var ofType = function (list, c) { return list.filter(function (it) { return c.types.indexOf(it.ca) > -1; }); };

  // Riyadh first, whenever it has the flower: ranked by what the customer pays for the stems needed (wholesale comes in packs),
  // with a penalty for another colour and for a substitute type. Holland only when Riyadh has none of it, ranked by colour then price per stem.
  function options(c) {
    var loc = ofType(ITEMS, c).filter(function (it) { return fitQ(it, need(it, c)) > 0; });
    var list = loc.length ? loc : ofType(HOL || [], c);
    return list.map(function (it) {
      var ci = c.colors.length ? c.colors.indexOf(colourOf(it)) : 0, ok = ci > -1, ti = c.types.indexOf(it.ca), q = fitQ(it, need(it, c));
      var score = it.h ? (ok ? ci : 50) * 1000 + ti * 100 + it.p1 : unitPrice(it, q) * q * (ok ? 1 + ci * 0.05 : 2) * (1 + ti * 0.6);
      return { it: it, ok: ok, score: score };
    }).sort(function (a, b) { return a.score - b.score || b.it.st - a.it.st; });
  }
  var needHolland = function () { return C.items.some(function (c) { return !ofType(ITEMS, c).length; }); };

  function line(c) {
    var o = options(c), cur = o.filter(function (x) { return key(x.it) === sel[c.k]; })[0] || o[0];
    if (!cur) return null;
    sel[c.k] = key(cur.it);
    var q = fitQ(cur.it, need(cur.it, c));
    return { c: c, o: o, cur: cur, q: q, sum: cur.it.h ? 0 : unitPrice(cur.it, q) * q };
  }

  function render() {
    var total = 0, add = [], dutch = false;
    rows.innerHTML = C.items.map(function (c, i) {
      var L = line(c), num = '<span class="sty-n">' + (i + 1) + '</span>';
      var guide = c.guide ? '<a class="sty-guide" href="' + pre + '/flowers/' + c.guide + '.html">' + T.about + ' ' + esc(c.gname) + '</a>' : '';
      if (!L) {
        return '<li class="sty-row off" id="row-' + c.k + '">' + num + '<div class="sty-main"><b>' + esc(c.name) + '</b><span class="sty-need">' + T.need + ' ' + c.stems + '</span>' +
          '<p class="sty-none">' + T.none + ' · <a href="' + pre + '/holland.html?q=' + encodeURIComponent(c.hq) + '">' + T.holland + '</a></p>' + guide + '</div></li>';
      }
      var it = L.cur.it, h = !!it.h, more = L.q > need(it, c);
      if (h) dutch = true; else { total += L.sum; add.push(it.id + ':' + L.q); }
      var alts = L.o.length > 1 ? '<div class="sty-alts" hidden>' + L.o.map(function (x) {
        return '<button type="button" data-k="' + c.k + '" data-id="' + key(x.it) + '" aria-pressed="' + (key(x.it) === key(it)) + '">' +
          '<img src="' + img(x.it) + '" alt="" loading="lazy" width="64" height="64"><span>' + esc(x.it.n) + '</span><small class="num">' + money(x.it.p1) + '</small></button>';
      }).join('') + '</div>' : '';
      var qty = h
        ? '<span class="sty-need">' + T.need + ' <span class="num">' + c.stems + '</span> · ' +
          (EN ? '<span class="num">' + money(it.p1) + '</span> per ' + unit(it, 1) : 'سعر ال' + unit(it, 1) + ' <span class="num">' + money(it.p1) + '</span>') + '</span>' +
          '<span class="sty-src">' + T.from + '</span>'
        : '<span class="sty-need">' + T.need + ' <span class="num">' + c.stems + '</span> · ' + T.get + ' <span class="num">' + L.q + '</span> ' + unit(it, L.q) +
          (more ? ' <small>(' + T.min + ')</small>' : '') + '</span>';
      var acts = '<span class="sty-acts">' + (L.o.length > 1 ? '<button type="button" class="sty-chg" data-chg="' + c.k + '" data-label="' + T.change + ' (' + L.o.length + ')">' + T.change + ' (' + L.o.length + ')</button>' : '') +
        (h ? '<a class="sty-hl" href="' + pre + '/holland.html?id=' + encodeURIComponent(it.id) + '">' + T.see + '</a>' : '') + guide + '</span>';
      return '<li class="sty-row' + (h ? ' nl' : '') + '" id="row-' + c.k + '">' + num +
        '<img class="sty-ph" src="' + img(it) + '" alt="" width="72" height="72" loading="lazy">' +
        '<div class="sty-main"><b>' + esc(c.name) + '</b><span class="sty-var">' + esc(it.n) + (it.l ? ' · ' + esc(EN ? it.l.replace('سم', 'cm') : it.l) : '') + '</span>' +
        qty + (L.cur.ok ? '' : '<span class="sty-diff">' + T.diff + '</span>') + acts + alts + '</div>' +
        (h ? '<span class="sty-sum"></span>' : '<b class="sty-sum num">' + money(L.sum) + '</b>') + '</li>';
    }).join('');
    var href = pre + '/bunches.html?add=' + add.join(',') + '&from=' + encodeURIComponent(C.slug);
    [].forEach.call(document.querySelectorAll('[data-total]'), function (el) { el.innerHTML = money(total); });
    // nothing from Riyadh stock to add (wholesale paused, or every flower comes from Holland): no total, no add button
    var none = CLOSED || !add.length;
    [].forEach.call(document.querySelectorAll('.sty-total, .sty-bar, [data-addall]'), function (el) { el.style.display = none ? 'none' : ''; });
    [].forEach.call(document.querySelectorAll('[data-addall]'), function (a) {
      if (add.length) { a.href = href; a.removeAttribute('aria-disabled'); } else { a.removeAttribute('href'); a.setAttribute('aria-disabled', 'true'); }
    });
    var extra = $('#styExtra');
    if (extra) {
      var over = C.items.some(function (c) { var L = line(c); return L && !L.cur.it.h && L.q > need(L.cur.it, c); });
      extra.hidden = !(over || dutch || CLOSED);
      extra.textContent = CLOSED ? T.shut : dutch ? T.hol + (over ? ' ' + T.extra + '.' : '') : T.extra;
    }
  }

  rows.addEventListener('click', function (e) {
    var b = e.target.closest('[data-chg]');
    if (b) { var box = b.closest('.sty-main').querySelector('.sty-alts'); if (box) { box.hidden = !box.hidden; b.textContent = box.hidden ? b.dataset.label : T.close; } return; }
    var p = e.target.closest('.sty-alts button');
    if (p) { sel[p.dataset.k] = p.dataset.id; render(); var r = document.getElementById('row-' + p.dataset.k); if (r) r.classList.add('flash'); }
  });

  // pins: tap a name to jump to its row; the eye button hides the names
  var fig = $('.sty-fig');
  if (fig) fig.addEventListener('click', function (e) {
    var t = e.target.closest('[data-pin]');
    if (t) { var r = document.getElementById('row-' + t.dataset.pin); if (r) { r.scrollIntoView({ behavior: 'smooth', block: 'center' }); r.classList.remove('flash'); void r.offsetWidth; r.classList.add('flash'); } return; }
    if (e.target.closest('[data-labels]')) { fig.classList.toggle('bare'); }
  });

  // keep every name inside the photo: flip it to the other side of its dot when it would run off the edge
  function fitPins() {
    if (!fig) return;
    var fr = fig.getBoundingClientRect(), pins = [].slice.call(fig.querySelectorAll('.sty-pin'));
    var out = function (r) { return r.left < fr.left + 4 || r.right > fr.right - 4; };
    var hits = function (p, r) { return pins.some(function (q) { if (q === p) return false; var o = q.querySelector('span').getBoundingClientRect(); return r.left < o.right && r.right > o.left && r.top < o.bottom && r.bottom > o.top; }); };
    pins.forEach(function (p) {
      var sp = p.querySelector('span'); if (!sp) return;
      var r = sp.getBoundingClientRect(); if (!out(r)) return;
      p.classList.toggle('r'); r = sp.getBoundingClientRect();
      if (!out(r) && !hits(p, r)) return;
      p.classList.toggle('r'); r = sp.getBoundingClientRect();   // keep the side, slide the name back inside the photo
      var dx = r.left < fr.left + 4 ? fr.left + 4 - r.left : fr.right - 4 - r.right;
      sp.style.transform = 'translateX(' + Math.round(dx) + 'px)';
    });
  }
  if (document.readyState === 'complete') fitPins(); else window.addEventListener('load', fitPins);
  var live = function (d, h) {
    var today = iso(new Date());
    return d.items.filter(function (it) { return it.st > 0 && it.p1 > 0 && (it.x || it.d >= today); }).map(function (it) { if (h) it.h = 1; return it; });
  };
  var fail = function () { rows.innerHTML = '<li class="sty-row off"><p class="sty-none">' + T.err + '</p></li>'; };
  fetch('/catalog.json', { cache: 'no-cache' }).then(function (r) { return r.json(); }).then(function (d) {
    CLOSED = !!d.closed; ITEMS = CLOSED ? [] : live(d, false);
    if (!needHolland()) { render(); return; }
    return fetch('/holland.json', { cache: 'no-cache' }).then(function (r) { return r.json(); })
      .then(function (h) { HOL = live(h, true); }, function () { HOL = []; }).then(render);
  }).catch(fail);
})();
