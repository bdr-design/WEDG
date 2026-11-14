// Layout audit over every phone screen reachable from home (and الحراج's listing / sell), the phone small and enlarged.
// Env: PORT, SAVE (optional save JSON to seed). Prints per screen the audit's problems.
const { chromium } = require('playwright');
const fs = require('fs');
const PORT = process.env.PORT || 8961, AUDIT = process.env.AUDIT;
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 956, height: 440 } });
  p.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
  if (process.env.SAVE) await p.addInitScript((s) => { if (!sessionStorage.getItem('seeded')) { localStorage.setItem('marah.proto.marah.save', s); sessionStorage.setItem('seeded', '1'); } }, fs.readFileSync(process.env.SAVE, 'utf8'));
  await p.route('**/index.html', async (r) => { const res = await r.fetch(); await r.fulfill({ response: res, body: (await res.text()).replace('startEngine({ onSnapshot:', 'startEngine({ newGame: { seed: 4242 }, onSnapshot:') }); });
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.marahEngine && window.marahEngine.snapshot, null, { timeout: 600000 });
  await p.waitForTimeout(1500);
  await p.addScriptTag({ path: AUDIT }); await p.addScriptTag({ path: process.env.TYPE });
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot; });
  const screens = ['home', 'water', 'feed', 'milk', 'build', 'haraj', 'bank', 'mazayen', 'chats'];
  for (const size of ['small', 'big']) {
    for (const s of screens) {
      await p.evaluate(([s, size]) => { window.__phone.close(); window.__phone.toggle(); if (size === 'big') window.__phone.enlarge(); if (s !== 'home') window.__phone.openApp(s); if (size === 'small') window.__phone.shrink(); }, [s, size]);
      await p.waitForTimeout(700);
      const a = await p.evaluate(() => window.__audit());
      const ty = await p.evaluate(() => window.__typeAudit('phone'));
      const tk = ['split', 'prepNum', 'prepEnd', 'widow', 'digits', 'minus', 'hyphenMinus', 'parens', 'dot'].filter((k) => ty[k] && ty[k].length).map((k) => k + ':' + ty[k].length).join(',');
      const h = require('crypto').createHash('md5').update(a.texts.filter((t) => !/^\d+:\d+$/.test(t)).join('|')).digest('hex').slice(0, 8);
      console.log('SCREEN', size, s, 'below', a.scroll && a.scroll.below, 'texts', h, 'type', tk || '-');
      const bad = { clipped: a.clipped, ellipsis: a.ellipsis, outside: a.outside, split: a.split };
      const n = Object.values(bad).reduce((x, y) => x + y.length, 0);
      console.log(size, s, n ? JSON.stringify(bad) : 'clean', '|', (a.texts.slice(0, 3).join(' ')).slice(0, 60));
    }
  }
  // one listing and the sell page, enlarged
  await p.evaluate(() => { window.__phone.close(); window.__phone.toggle(); window.__phone.enlarge(); window.__phone.openApp('haraj'); });
  await p.waitForTimeout(700);
  await p.evaluate(() => R().querySelector('[data-go="listing"]')?.click()); await p.waitForTimeout(700);
  let a = await p.evaluate(() => window.__audit()); console.log('big listing', JSON.stringify({ c: a.clipped, o: a.outside, s: a.split }));
  await b.close();
})();
