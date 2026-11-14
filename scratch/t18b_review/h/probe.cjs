// T18B reviewer: opens the page on each save of falcon_states.dart and dumps what the engine gives the phone:
// snapshot.falcons, the recent events of the hunt, the catalog (worker op falconCatalog, asked here directly) and a
// trip's card (op tripCard: trapping at الحماد for 9 nights). Also searches the page for hidden values: the held
// bird's worth and skill as numbers in the snapshot JSON, the DOM and the live region, and the save in localStorage.
//   PORT=<port> SAVES=<folder> NAMES=a,b OUT=<folder> NODE_PATH=$(npm root -g) node probe.cjs
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const PORT = process.env.PORT || 8971, SAVES = process.env.SAVES, OUT = process.env.OUT || '.';
const NAMES = (process.env.NAMES || 'oct1_ready').split(',');
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };
(async () => {
  const b = await chromium.launch(LAUNCH);
  fs.mkdirSync(OUT, { recursive: true });
  for (const name of NAMES) {
    const ctx = await b.newContext({ viewport: { width: 956, height: 440 } });
    const p = await ctx.newPage();
    const errs = []; p.on('pageerror', (e) => errs.push(e.message));
    await p.addInitScript(([v]) => { if (!sessionStorage.getItem('seeded')) { localStorage.clear(); localStorage.setItem('marah.proto.marah.save', v); sessionStorage.setItem('seeded', '1'); } }, [fs.readFileSync(path.join(SAVES, name + '.json'), 'utf8')]);
    await p.goto(`http://127.0.0.1:${PORT}/index.html`, { timeout: 600000 });
    await p.waitForFunction(() => window.marahEngine && window.marahEngine.snapshot, null, { timeout: 900000 });
    const got = await p.evaluate(async () => {
      const e = window.marahEngine, w = e.worker;
      const ask = (op, extra = {}) => new Promise((res) => { const id = 'rv' + Math.random(); const f = (m) => { const x = typeof m.data === 'string' ? JSON.parse(m.data) : m.data; if (x.id === id) { w.removeEventListener('message', f); res(x); } }; w.addEventListener('message', f); w.postMessage(JSON.stringify({ op, id, ...extra })); });
      const cat = await ask('falconCatalog');
      const card = await ask('tripCard', { kind: 'trapping', ground: 'hamad', nights: 9 });
      const s = e.snapshot;
      return { date: s.date, cash: s.cash, falcons: s.falcons, hunt: (s.recentEvents || []).filter((x) => /falcon|permit|gear|trip|trap|cast/i.test(x.type)), catalog: cat.catalog, catalogChars: JSON.stringify(cat).length, card: card.card, snapshotChars: e.stats.snapshotChars, facilities: s.farm.facilities.map((f) => f.facility) };
    });
    // the hidden values of the save's birds: are they anywhere the page shows or keeps?
    const save = JSON.parse(fs.readFileSync(path.join(SAVES, name + '.json'), 'utf8'));
    const hidden = [];
    JSON.stringify(save, (k, v) => { if ((k === 'value' || k === 'skill') && typeof v === 'number') hidden.push([k, v]); return v; });
    const where = await p.evaluate((hidden) => {
      const R = [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone'))?.shadowRoot;
      const snap = JSON.stringify(window.marahEngine.snapshot), dom = R ? R.innerHTML : '', live = R ? (R.querySelector('.sr') || {}).textContent || '' : '';
      const ls = Object.keys(localStorage).map((k) => localStorage.getItem(k)).join('\n');
      const fmt = (n) => [String(n), Number(n).toLocaleString('en-US')];
      return hidden.map(([k, v]) => ({ k, v, snapshot: fmt(v).some((t) => snap.includes(t)), dom: fmt(v).some((t) => dom.includes(t)), live: fmt(v).some((t) => live.includes(t)), localStorage: fmt(v).some((t) => ls.includes(t)) }));
    }, hidden);
    fs.writeFileSync(path.join(OUT, `probe_${name}.json`), JSON.stringify({ ...got, hiddenSearch: where, errs }, null, 1));
    console.log(name, got.date, 'snapshot', got.snapshotChars, 'falcons', JSON.stringify(got.falcons).length, 'catalog', got.catalogChars, 'lots', (got.falcons.lots || []).length, 'hidden', JSON.stringify(where), errs.length ? 'ERR ' + errs.join(' | ') : '');
    await ctx.close();
  }
  await b.close();
})();
