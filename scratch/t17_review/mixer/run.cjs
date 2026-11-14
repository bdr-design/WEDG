// usage: node run.cjs PORT glbname outprefix "clip|t|view|size|cx|cy|cz" ...
const { chromium } = require('playwright'); const CONV = !!process.env.CONV;
(async () => { const [port, glb, out, ...shots] = process.argv.slice(2);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 800, height: 600 } }); p.on('console', m => console.log('page:', m.text())); p.on('pageerror', e => console.log('ERR', e.message));
  await p.goto(`http://127.0.0.1:${port}/index.html`); await p.waitForFunction('window.ready');
  console.log(JSON.stringify(await p.evaluate(u => window.load(u), glb))); await p.evaluate(c => window.useConv = c, CONV);
  let i = 0; for (const s of shots) { const [clip, t, view, size, cx, cy, cz, vis, follow] = s.split('|'); await p.evaluate(f => window.followBody = f, !!follow);
    const info = await p.evaluate(a => window.frame(...a), [clip || null, +t, view, +size, +cx, +cy, +cz, vis || null]);
    await p.locator('canvas').screenshot({ path: `${out}_${i}.png` }); console.log(s, JSON.stringify(info)); i++; }
  console.log('INFO', JSON.stringify(await p.evaluate(() => window.info2()))); await b.close(); })();
