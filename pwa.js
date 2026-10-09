/* أو فلورا: تطبيق الويب (تثبيت على الشاشة الرئيسية + عمل بدون إنترنت) */
(function(){
  if('serviceWorker' in navigator) window.addEventListener('load', function(){ navigator.serviceWorker.register('sw.js').catch(function(){}); });
  var standalone = (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone;
  function get(k){ try { return localStorage.getItem(k); } catch(e){ return null; } }
  function set(k, v){ try { localStorage.setItem(k, v); } catch(e){} }
  if(standalone) return;
  var visits = (+get('awe_visits') || 0) + 1; set('awe_visits', visits);
  if(visits < 2 || Date.now() < (+get('awe_install_off') || 0)) return;
  var ua = navigator.userAgent, ios = /iphone|ipad|ipod/i.test(ua) && !/crios|fxios|edgios/i.test(ua), deferred = null;
  function show(text, action){
    if(document.getElementById('installBar')) return;
    var bar = document.createElement('div'); bar.id = 'installBar'; bar.dir = 'rtl'; bar.setAttribute('role', 'status');
    bar.style.cssText = 'position:fixed;left:50%;transform:translateX(-50%);bottom:calc(78px + env(safe-area-inset-bottom,0px));z-index:40;width:min(452px,calc(100% - 24px));display:flex;align-items:center;gap:10px;padding:10px 12px;background:#fff;border:1px solid #E2E2E2;box-shadow:0 6px 20px rgba(0,0,0,.12);font-family:"IBM Plex Sans Arabic",Tahoma,sans-serif;font-size:13.5px;color:#111';
    bar.innerHTML = '<img src="icon-180.png" alt="" width="36" height="36" style="flex:0 0 36px">' +
      '<span style="flex:1 1 auto;line-height:1.45">' + text + '</span>' +
      (action ? '<button type="button" data-i="go" style="border:0;background:#1F8A4C;color:#fff;font-family:inherit;font-weight:600;font-size:13px;padding:8px 14px;cursor:pointer">تثبيت</button>' : '') +
      '<button type="button" data-i="x" aria-label="إغلاق" style="border:0;background:none;font-size:22px;line-height:1;cursor:pointer;color:#8C918E;padding:0 4px">×</button>';
    bar.addEventListener('click', function(e){
      var b = e.target.closest('[data-i]'); if(!b) return;
      if(b.getAttribute('data-i') === 'go' && action) action();
      bar.remove(); set('awe_install_off', Date.now() + 14 * 864e5);
    });
    document.body.appendChild(bar);
  }
  if(ios) setTimeout(function(){ show('ثبّت أو فلورا على جوالك: اضغط زر المشاركة، ثم «إضافة إلى الشاشة الرئيسية»'); }, 4000);
  window.addEventListener('beforeinstallprompt', function(e){ e.preventDefault(); deferred = e; show('ثبّت أو فلورا على جوالك', function(){ deferred.prompt(); }); });
})();
