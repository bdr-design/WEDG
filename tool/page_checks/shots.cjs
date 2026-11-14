// Pictures of the phone's screens (and a camel's card) for a before/after pair: a new game (seed 4242, the start's
// camel registered so the dealer's chat exists), each screen reached by its path of taps from home, the phone
// enlarged, at device scale 2, the game's frames held while each is taken.
//   PORT=<port> OUT=<folder> SCREENS=water,feed,sell,... NODE_PATH=$(npm root -g) node tool/page_checks/shots.cjs
// A screen is a path: 'water', 'haraj>tab mine>sell' ... ; 'card' is نورة's card from الحوش's pin.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const PORT = process.env.PORT || 8940, OUT = process.env.OUT || '.';
const SCREENS = (process.env.SCREENS || 'water,feed,sell,haraj,bank,chats>chat,chats>chat>strength,card').split(',');
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };
fs.mkdirSync(OUT, { recursive: true });
(async () => {
  const b = await chromium.launch(LAUNCH);
  const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: +(process.env.SCALE || 2) });
  const p = await ctx.newPage();
  p.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
  await p.goto(`http://127.0.0.1:${PORT}/index.html`, { timeout: 600000, waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => document.getElementById('status').hidden && window.marahEngine && window.marahEngine.snapshot, null, { timeout: 900000 });
  console.log(await p.evaluate(async () => {
    window.R = () => [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot;
    window.T = () => R().querySelector('.scr').innerText.replace(/\s+/g, ' ');
    const e = window.marahEngine;
    await e.startOver({ seed: 4242 });
    for (let i = 0; i < 400 && !(e.snapshot && e.snapshot.date === '2026-10-01' && e.snapshot.herd.total === 2); i++) await new Promise((r) => setTimeout(r, 25));
    // the engine's clock held: every picture of one day
    await new Promise((r) => { const id = 990001; const h = (m) => { const d = typeof m.data === 'string' ? JSON.parse(m.data) : m.data; if (d && d.id === id) { e.worker.removeEventListener('message', h); r(); } }; e.worker.addEventListener('message', h); e.worker.postMessage(JSON.stringify({ op: 'pause', id })); setTimeout(r, 3000); });
    const S = e.snapshot, f = S.festivals.find((x) => !x.done && S.today >= x.opensOn && S.today <= x.closesOn);
    const d = (await e.festival(f.id)).festival, row = d.register.find((x) => x.round && !x.error);
    return JSON.stringify((await e.dispatch({ type: 'enterRound', festival: f.id, round: row.round, camels: [row.camel.id] })).ok);
  }));
  const hold = () => p.evaluate(() => { window.__raf = window.requestAnimationFrame; window.requestAnimationFrame = () => 0; });
  const release = () => p.evaluate(() => { window.requestAnimationFrame = window.__raf; });
  for (const sc of SCREENS) {
    const file = path.join(OUT, sc.replace(/[> ]+/g, '_') + '.png');
    if (sc === 'card') {
      await p.evaluate(() => { window.__phone.close(); document.querySelector('#pop .x')?.click(); });
      await p.waitForTimeout(500);
      const pin = await p.evaluate(() => { for (const l of document.querySelectorAll('#labels .lbl')) { const r = l.getBoundingClientRect(); if (r.width && r.x > 80 && r.x < 560) return { x: r.x + r.width / 2, y: r.y + 15 }; } return null; });
      if (pin) await p.mouse.click(pin.x, pin.y);
      await p.waitForTimeout(800);
      await p.evaluate(() => document.querySelector('#pop .list .row')?.click());
      await p.waitForTimeout(1500);
      await hold();
      const r = await p.evaluate(() => { const b = document.getElementById('pop').getBoundingClientRect(); return { x: b.x, y: b.y, width: b.width, height: b.height }; });
      await p.screenshot({ path: file, clip: r, timeout: 600000 });
      await release();
      console.log('shot', file);
      continue;
    }
    await p.evaluate(() => { document.querySelector('#pop .x')?.click(); if (window.__phone.state === 'closed') window.__phone.toggle(); window.__phone.enlarge(); });
    await p.evaluate(async () => { for (let i = 0; i < 6; i++) { const b = R().querySelector('.back'); if (!b) break; b.click(); await new Promise((r) => setTimeout(r, 150)); } });
    let ok = true;
    for (const step of sc === 'home' ? [] : sc.split('>')) {
      ok = await p.evaluate((s) => { const e = s.startsWith('tab ') ? R().querySelector(`[data-act="tab"][data-p="${s.slice(4)}"]`) : R().querySelector(`[data-go="${s}"]`); if (!e) return false; e.click(); return true; }, step);
      if (!ok) break;
      await p.waitForFunction(() => !/يجهّز/.test(window.T()), null, { timeout: 30000 }).catch(() => {});
      await p.waitForTimeout(400);
    }
    if (!ok) { console.log('not reached', sc); continue; }
    await p.waitForTimeout(500);
    await hold();
    const box = await p.evaluate(() => { const r = R().querySelector('.dev').getBoundingClientRect(); return { x: r.x, width: r.width }; });
    await p.screenshot({ path: file, clip: { x: Math.max(0, box.x - 4), y: 0, width: box.width + 8, height: 440 }, timeout: 600000 });
    await release();
    console.log('shot', file);
  }
  await b.close();
})();
