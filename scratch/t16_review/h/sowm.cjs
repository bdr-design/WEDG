// After a سوم on a listing (seller answers): the page's scroll, shot, audits.
const { chromium } = require('playwright');
const fs = require('fs'); const path = require('path');
const { PORT = 8961, SAVE, IDS, OUT, AUDIT, TYPE } = process.env;
const ids = JSON.parse(fs.readFileSync(IDS, 'utf8'));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 956, height: 440 }, timeout: 300000 });
  await p.addInitScript((s) => { if (!sessionStorage.getItem('seeded')) { localStorage.clear(); localStorage.setItem('marah.proto.marah.save', s); sessionStorage.setItem('seeded', '1'); } }, fs.readFileSync(SAVE, 'utf8'));
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.marahEngine && window.marahEngine.snapshot, null, { timeout: 600000 });
  await p.addScriptTag({ path: AUDIT }); await p.addScriptTag({ path: TYPE });
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot; window.T = () => R().querySelector('.scr').innerText.replace(/\s+/g, ' '); window.__phone.openApp('haraj'); });
  for (const k of ['mk_never_m', 'mk_never_f', 'mk_found_m', 'mk_clean_f']) {
    await p.waitForTimeout(600);
    await p.evaluate(() => { if (R().querySelector('.title').textContent !== 'الحراج') R().querySelector('.back').click(); });
    await p.waitForTimeout(600);
    await p.evaluate((id) => R().querySelector(`[data-go="listing"][data-id="${id}"]`).click(), ids[k]);
    await p.waitForTimeout(700);
    { const a0 = await p.evaluate(() => window.__audit()); console.log(k, 'listing page before: below', a0.scroll && a0.scroll.below, (await p.evaluate(() => T())).slice(0, 80)); }
    for (let i = 0; i < 40; i++) await p.evaluate(() => R().querySelector('[data-act="bidStep"][data-d="-1"]:not([disabled])')?.click());
    await p.waitForTimeout(500);
    await p.evaluate(() => R().querySelector('[data-act="bid"]').click());
    await p.waitForTimeout(1500);
    const a = await p.evaluate(() => window.__audit()), ty = await p.evaluate(() => window.__typeAudit('phone'));
    const box = await p.evaluate(() => { const r = R().querySelector('.dev').getBoundingClientRect(); return { x: r.x, width: r.width }; });
    await p.screenshot({ path: path.join(OUT, 'sowm_' + k + '.png'), clip: { x: Math.max(0, box.x - 4), y: 0, width: box.width + 8, height: 440 }, timeout: 300000 });
    console.log(k, 'after سوم: below', a.scroll && a.scroll.below, '| layout', JSON.stringify({ c: a.clipped, o: a.outside, s: a.split }), '| type split/prep/widow', JSON.stringify([ty.split, ty.prepNum, ty.prepEnd, ty.widow]), '|', (await p.evaluate(() => T())).slice(0, 260));
  }
  await b.close();
})();
