const { chromium } = require('playwright');
(async () => {
  const [port, out, ...qs] = process.argv.slice(2);
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 1200, height: 900 }, deviceScaleFactor: +(process.env.DSF || 1) });
  p.on('console', (m) => console.log('console:', m.text()));
  for (let i = 0; i < qs.length; i++) {
    await p.goto(`http://127.0.0.1:${port}/index.html?${qs[i]}`); await p.waitForFunction(() => document.title === 'done', null, { timeout: 60000 });
    await p.screenshot({ path: `${out}_${i}.png` });
  }
  await b.close();
})();
