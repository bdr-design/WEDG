// Runs the typography audit (type_audit.js) over everything the 3D prototype shows: every screen the phone's apps
// reach (enlarged, and its home small), every place's card from its pin and a camel's card, the test meter closed
// and open, and the loading line; at the owner's screen (956 x 440), device scale 1, no pictures.
//
// Phases, each one page load (PHASES=new,short,found by default):
//   new    a new game (seed 4242), the start's camel registered at the open festival by the engine, so the
//          treatment man's chat has its message; the map's cards; the meter
//   short  the save scratchpad/t10/saves/short.json (feed and water short, on account) if SAVES names its folder
//   found  the save found.json (a treatment found: الحراج's card)
// Output: OUT/audit_<phase>.json (every surface's findings) and a table on stdout (tool/page_checks/type_table.cjs
// prints the before/after table from two OUT folders).
//
// Run: build and serve the page as longpress.cjs says, then
//   PORT=<port> OUT=<folder> [SAVES=<folder of saves>] NODE_PATH=$(npm root -g) node tool/page_checks/type_audit.cjs
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 8940, OUT = process.env.OUT || '.', SAVES = process.env.SAVES || '';
const PHASES = (process.env.PHASES || 'new,short,found').split(',');
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };
const AUDIT = path.join(__dirname, 'type_audit.js');
fs.mkdirSync(OUT, { recursive: true });
const log = (...a) => console.log(...a);

async function openPage(b, save) {
  const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 1 });
  const p = await ctx.newPage();
  p.on('pageerror', (e) => log('PAGE ERROR', e.message));
  if (save) await p.addInitScript(([v]) => { if (!sessionStorage.getItem('seeded')) { localStorage.clear(); localStorage.setItem('marah.proto.marah.save', v); sessionStorage.setItem('seeded', '1'); } }, [fs.readFileSync(save, 'utf8')]);
  await p.goto(`http://127.0.0.1:${PORT}/index.html#fps`, { waitUntil: 'domcontentloaded' });
  await p.addScriptTag({ path: AUDIT });
  const loading = await p.evaluate(() => (document.getElementById('status').hidden ? null : window.__typeAudit('#status')));
  await p.waitForFunction(() => document.getElementById('status').hidden && window.marahEngine && window.marahEngine.snapshot, null, { timeout: 900000 });
  await p.evaluate(() => {
    window.R = () => [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot;
    window.T = () => R().querySelector('.scr').innerText.replace(/\s+/g, ' ');
  });
  return { ctx, p, loading };
}
const settle = (p) => p.waitForFunction(() => !/يجهّز/.test(window.T()), null, { timeout: 30000 }).catch(() => {}).then(() => p.waitForTimeout(300));
const home = (p) => p.evaluate(async () => { for (let i = 0; i < 6; i++) { const b = R().querySelector('.back'); if (!b) break; b.click(); await new Promise((r) => setTimeout(r, 120)); } });
const audit = (p, where) => p.evaluate((w) => window.__typeAudit(w), where);

// every screen reachable from the phone's home, each once (by its target: a data-go, or a tab of الحراج)
async function crawlPhone(p, tag, res) {
  await p.evaluate(() => { if (window.__phone.state === 'closed') window.__phone.toggle(); });
  await p.waitForTimeout(400);
  res[`${tag} phone small: home`] = await audit(p, 'phone');
  await p.evaluate(() => window.__phone.enlarge()); await p.waitForTimeout(400);
  const seen = new Set(['home']), queue = [{ path: [], name: 'home' }];
  while (queue.length) {
    const { path: steps, name } = queue.shift();
    await home(p);
    let ok = true;
    for (const s of steps) {
      ok = await p.evaluate((s) => { const e = R().querySelectorAll(s.sel)[s.n]; if (!e) return false; e.click(); return true; }, s);
      if (!ok) break;
      await settle(p);
    }
    if (!ok) { res[`${tag} phone: ${name}`] = { error: 'not reached' }; continue; }
    res[`${tag} phone: ${name}`] = await audit(p, 'phone');
    // the scrolled end too, when the screen is longer than the phone
    const long = await p.evaluate(() => { const b = R().querySelector('.body'); if (!b || b.scrollHeight <= b.clientHeight + 4) return false; b.scrollTop = b.scrollHeight; return true; });
    if (long) { await p.waitForTimeout(200); res[`${tag} phone: ${name} (end)`] = await audit(p, 'phone'); }
    const next = await p.evaluate(() => [...R().querySelectorAll('[data-go], [data-act="tab"]')].map((e, i, all) => {
      const sel = e.dataset.act === 'tab' ? `[data-act="tab"][data-p="${e.dataset.p}"]` : `[data-go="${e.dataset.go}"]`;
      return { key: e.dataset.act === 'tab' ? 'tab ' + e.dataset.p : e.dataset.go, sel, n: [...R().querySelectorAll(sel)].indexOf(e) };
    }));
    for (const t of next) if (!seen.has(t.key) && t.key !== 'home') { seen.add(t.key); queue.push({ path: [...steps, { sel: t.sel, n: t.n }], name: t.key }); }
  }
  await home(p);
  await p.evaluate(() => window.__phone.close()); await p.waitForTimeout(300);
}
// every pin's card, and a camel's card from the first row of a card that lists camels; the meter
async function crawlMap(p, tag, res) {
  const pins = await p.evaluate(() => [...document.querySelectorAll('#labels .lbl')].map((l, i) => { const r = l.getBoundingClientRect(); return { i, x: Math.round(r.x + r.width / 2), y: Math.round(r.y + Math.min(15, r.height / 2)), w: r.width, aria: l.getAttribute('aria-label') || l.className }; }).filter((q) => q.w > 0));
  for (const pin of pins) {
    await p.evaluate(() => document.querySelector('#pop .x')?.click());
    await p.waitForTimeout(200);
    const pt = await p.evaluate((i) => { const l = document.querySelectorAll('#labels .lbl')[i]; if (!l) return null; const r = l.getBoundingClientRect(); return r.width ? { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + Math.min(15, r.height / 2)) } : null; }, pin.i);
    if (!pt) continue;
    await p.mouse.click(pt.x, pt.y); await p.waitForTimeout(700);
    const title = await p.evaluate(() => { const pop = document.getElementById('pop'); return pop.hidden ? null : (pop.querySelector('h2')?.textContent || '').trim(); });
    if (!title || res[`${tag} card: ${title}`]) continue;
    res[`${tag} card: ${title}`] = await audit(p, '#pop');
    const row = await p.evaluate(() => { const r = document.querySelector('#pop .list .row'); if (!r) return false; r.click(); return true; });
    if (row) {
      await p.waitForTimeout(700);
      const t2 = await p.evaluate(() => (document.getElementById('pop').hidden ? null : (document.querySelector('#pop h2')?.textContent || '').trim()));
      if (t2 && t2 !== title && !res[`${tag} card: ${t2}`]) res[`${tag} card: ${t2} (from ${title})`] = await audit(p, '#pop');
    }
  }
  await p.evaluate(() => document.querySelector('#pop .x')?.click()); await p.waitForTimeout(300);
  await p.waitForFunction(() => !/يسخّن/.test(document.getElementById('meter').textContent), null, { timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(1200);
  res[`${tag} meter (closed)`] = await audit(p, '#meter');
  await p.evaluate(() => document.getElementById('meter').click()); await p.waitForTimeout(1500);
  res[`${tag} meter (open)`] = await audit(p, '#meter');
  await p.evaluate(() => document.getElementById('meter').click()); await p.waitForTimeout(300);
}

(async () => {
  const b = await chromium.launch(LAUNCH);
  const res = {};
  for (const phase of PHASES) {
    const save = phase === 'new' ? null : SAVES && path.join(SAVES, phase + '.json');
    if (phase !== 'new' && !(save && fs.existsSync(save))) { log('no save for', phase); continue; }
    const { ctx, p, loading } = await openPage(b, save);
    if (loading) res[`${phase} loading line`] = loading;
    if (phase === 'new') {
      // a new game, a camel with a round at the open festival bought and entered (the chat's message comes of it)
      log('new game', await p.evaluate(async () => {
        const e = window.marahEngine;
        await e.startOver({ seed: 4242 });
        for (let i = 0; i < 400 && !(e.snapshot && e.snapshot.date === '2026-10-01' && e.snapshot.herd.total === 2); i++) await new Promise((r) => setTimeout(r, 25));
        const S = e.snapshot, f = S.festivals.find((x) => !x.done && S.today >= x.opensOn && S.today <= x.closesOn);
        if (!f) return 'no open festival';
        // (the start's own camel, owned long enough: a camel bought today cannot be entered, ownershipTooRecent)
        const d = (await e.festival(f.id)).festival, row = d.register.find((x) => x.round && !x.error);
        if (!row) return 'nothing to register: ' + JSON.stringify(d.register.map((x) => [x.camel.name, x.error && x.error.code]));
        const r = await e.dispatch({ type: 'enterRound', festival: f.id, round: row.round, camels: [row.camel.id] });
        return 'entered ' + row.camel.name + ': ' + JSON.stringify(r.ok ? true : r.error);
      }));
      await p.waitForTimeout(800);
      await crawlMap(p, phase, res);
    }
    await crawlPhone(p, phase, res);
    res[`${phase} faces`] = await p.evaluate(() => window.__faces());
    await ctx.close();
    fs.writeFileSync(path.join(OUT, 'audit.json'), JSON.stringify(res, null, 1));
  }
  await b.close();
  fs.writeFileSync(path.join(OUT, 'audit.json'), JSON.stringify(res, null, 1));
  log(require('./type_table.cjs').table(res));
})();
