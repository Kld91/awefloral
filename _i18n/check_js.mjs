// Syntax check for every inline script on the shop pages (Arabic and English). usage: node _i18n/check_js.mjs
import fs from 'fs'; import vm from 'vm';
const pages = ['index.html', 'bunches.html', 'holland.html', 'track.html', 'links.html', 'en/index.html', 'en/bunches.html', 'en/holland.html', 'en/track.html'];
let bad = 0;
for (const f of pages) {
  if (!fs.existsSync(f)) continue;
  const h = fs.readFileSync(f, 'utf8'), re = /<script(?![^>]*\bsrc=)(?![^>]*ld\+json)[^>]*>([\s\S]*?)<\/script>/g; let m, i = 0;
  while ((m = re.exec(h))) { i++; try { new vm.Script(m[1]); } catch (e) { bad++; console.log('BAD', f, 'script', i, e.message); } }
}
for (const f of ['assets/seo.js', 'en/assets/seo.js', 'assets/styling.js', 'pwa.js', 'sw.js']) { if (!fs.existsSync(f)) continue; try { new vm.Script(fs.readFileSync(f, 'utf8')); } catch (e) { bad++; console.log('BAD', f, e.message); } }
console.log(bad ? 'SCRIPT ERRORS ' + bad : 'scripts OK'); process.exit(bad ? 1 : 0);
