const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await (await b.newContext({ viewport: { width: 956, height: 440 } })).newPage();
  p.on('pageerror', (e) => console.log('ERR', e.message));
  await p.route('**/index.html', async (r) => { const res = await r.fetch(); await r.fulfill({ response: res, body: (await res.text()).replace('startEngine({ onSnapshot:', 'startEngine({ newGame: { seed: 4242 }, onSnapshot:') }); });
  await p.goto('http://127.0.0.1:8931/index.html', { timeout: 600000 });
  await p.waitForFunction(() => window.marahEngine && window.marahEngine.snapshot, null, { timeout: 600000 });
  const out = await p.evaluate(async () => {
    const E = window.marahEngine, S = E.snapshot;
    const cat = await new Promise((res) => { const w = E.worker; const id = 99991; const h = (e) => { const m = typeof e.data === 'string' ? JSON.parse(e.data) : e.data; if (m.id === id) { w.removeEventListener('message', h); res(m); } }; w.addEventListener('message', h); w.postMessage(JSON.stringify({ op: 'falconCatalog', id })); });
    return { date: S.date, cash: S.cash, falcons: S.falcons, catLen: JSON.stringify(cat).length, cat, keys: Object.keys(S) };
  });
  console.log(JSON.stringify(out, null, 1).slice(0, 14000));
  await b.close();
})();
