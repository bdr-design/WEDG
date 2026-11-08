const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 64, height: 64 } });
  const errs = []; p.on('pageerror', (e) => errs.push(String(e))); p.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.text()); });
  await p.goto('http://127.0.0.1:' + process.argv[2] + '/export.html', { waitUntil: 'load' });
  try { await p.waitForFunction(() => window.__ready, null, { timeout: 180000 }); } catch (e) { console.log('ERRS', errs); throw e; }
  const s = await p.evaluate(() => window.__export);
  fs.writeFileSync(process.argv[3], s);
  console.log('wrote', s.length, 'chars', errs.slice(0, 5));
  await b.close();
})();
