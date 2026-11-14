// T18B reviewer: the boxes and texts of every phone screen reachable from home (data-go and الحراج's tabs), enlarged
// and small, on a fixed game (seed 4242, 1 October, the engine's clock paused so nothing moves). Each screen: its
// innerText, and every element inside .scr that draws text or is a leaf, as [path, x, y, w, h, text] relative to the
// screen (rounded to 0.5 px); the scrolled end too when it scrolls. Phase 2 runs it on the worker's build and
// compares (cmp_boxes.cjs): every screen but home and the new apps' must be the same.
//   PORT=<port> OUT=<file.json> NODE_PATH=$(npm root -g) node boxes.cjs
const { chromium } = require('playwright');
const fs = require('fs');
const PORT = process.env.PORT || 8971, OUT = process.env.OUT || 'boxes.json';
const SKIP = new Set((process.env.SKIP || '').split(',').filter(Boolean));
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };
(async () => {
  const b = await chromium.launch(LAUNCH);
  const p = await b.newPage({ viewport: { width: 956, height: 440 } });
  const errs = []; p.on('pageerror', (e) => errs.push(e.message));
  await p.route('**/index.html', async (r) => { const res = await r.fetch(); await r.fulfill({ response: res, body: (await res.text()).replace('startEngine({ onSnapshot:', 'startEngine({ newGame: { seed: 4242 }, onSnapshot:') }); });
  await p.goto(`http://127.0.0.1:${PORT}/index.html`, { timeout: 600000 });
  await p.waitForFunction(() => window.marahEngine && window.marahEngine.snapshot && document.getElementById('status').hidden, null, { timeout: 900000 });
  await p.evaluate(async () => {
    const e = window.marahEngine;
    await e.startOver({ seed: 4242 });
    for (let i = 0; i < 400 && !(e.snapshot && e.snapshot.date === '2026-10-01' && e.snapshot.herd.total === 2); i++) await new Promise((r) => setTimeout(r, 25));
    e.worker.postMessage(JSON.stringify({ op: 'pause', id: 'rv-pause' }));      // (the clock stopped: the texts hold)
    await new Promise((r) => setTimeout(r, 800));
    window.R = () => [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot;
  });
  const grab = () => p.evaluate(() => {
    const scr = R().querySelector('.scr'), o = scr.getBoundingClientRect(), q = (v) => Math.round(v * 2) / 2;
    const pathOf = (e) => { const out = []; for (let x = e; x && x !== scr; x = x.parentElement) { const i = x.parentElement ? [...x.parentElement.children].indexOf(x) : 0; out.unshift(`${x.tagName.toLowerCase()}${x.classList.length ? '.' + [...x.classList].join('.') : ''}:${i}`); } return out.join('>'); };
    const boxes = [];
    for (const e of scr.querySelectorAll('*')) {
      if (e.closest('.sbar')) continue;      // (the clock)
      const own = [...e.childNodes].filter((n) => n.nodeType === 3).map((n) => n.nodeValue).join('').trim();
      if (!own && e.children.length) continue;
      const r = e.getBoundingClientRect();
      if (!r.width && !r.height) continue;
      boxes.push([pathOf(e), q(r.x - o.x), q(r.y - o.y), q(r.width), q(r.height), own]);
    }
    const sr = R().querySelector('.sr');
    return { text: scr.innerText.replace(/[ \t]+/g, ' ').trim(), boxes, live: sr ? sr.textContent : '', title: (scr.querySelector('.title') || {}).textContent || '' };
  });
  const home = () => p.evaluate(async () => { for (let i = 0; i < 8; i++) { const b = R().querySelector('.back'); if (!b) break; b.click(); await new Promise((r) => setTimeout(r, 450)); } });
  const settle = () => p.waitForTimeout(700);
  const res = {};
  await p.evaluate(() => { window.__phone.toggle(); }); await settle();
  res['small: home'] = await grab();
  await p.evaluate(() => window.__phone.enlarge()); await settle();
  const seen = new Set(['home']), queue = [{ steps: [], name: 'home' }];
  while (queue.length) {
    const { steps, name } = queue.shift();
    await home(p); await settle();
    let ok = true;
    for (const s of steps) {
      ok = await p.evaluate((s) => { const e = R().querySelectorAll(s.sel)[s.n]; if (!e) return false; e.click(); return true; }, s);
      if (!ok) break;
      await settle();
    }
    if (!ok) { res[`big: ${name}`] = { error: 'not reached' }; continue; }
    res[`big: ${name}`] = await grab();
    const long = await p.evaluate(() => { const b = R().querySelector('.body'); if (!b || b.scrollHeight <= b.clientHeight + 4) return false; b.scrollTop = b.scrollHeight; return true; });
    if (long) { await p.waitForTimeout(250); res[`big: ${name} (end)`] = await grab(); await p.evaluate(() => { R().querySelector('.body').scrollTop = 0; }); }
    // the same screen small
    await p.evaluate(() => window.__phone.shrink()); await settle();
    res[`small: ${name}`] = await grab();
    await p.evaluate(() => window.__phone.enlarge()); await settle();
    const next = await p.evaluate(() => [...R().querySelectorAll('[data-go], [data-act="tab"]')].map((e) => {
      const sel = e.dataset.act === 'tab' ? `[data-act="tab"][data-p="${e.dataset.p}"]` : `[data-go="${e.dataset.go}"]`;
      return { key: e.dataset.act === 'tab' ? 'tab ' + e.dataset.p : e.dataset.go, sel, n: [...R().querySelectorAll(sel)].indexOf(e) };
    }));
    for (const t of next) if (!seen.has(t.key) && t.key !== 'home' && !SKIP.has(t.key)) { seen.add(t.key); queue.push({ steps: [...steps, { sel: t.sel, n: t.n }], name: t.key }); }
  }
  res.errors = errs;
  fs.writeFileSync(OUT, JSON.stringify(res));
  console.log(Object.keys(res).length - 1, 'surfaces;', errs.length, 'page errors');
  for (const [k, v] of Object.entries(res)) if (k !== 'errors') console.log(k, v.error || `${v.boxes.length} boxes · ${v.title}`);
  await b.close();
})();
