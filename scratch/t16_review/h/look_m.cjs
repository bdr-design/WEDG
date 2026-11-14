const { chromium } = require('playwright');
const fs = require('fs');
const { PORT = 8961, SAVE, IDS, TYPE } = process.env;
const ids = JSON.parse(fs.readFileSync(IDS, 'utf8'));
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 956, height: 440 } });
  await p.addInitScript((s) => { if (!sessionStorage.getItem('seeded')) { localStorage.clear(); localStorage.setItem('marah.proto.marah.save', s); sessionStorage.setItem('seeded', '1'); } }, fs.readFileSync(SAVE, 'utf8'));
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.marahEngine && window.marahEngine.snapshot, null, { timeout: 600000 });
  await p.addScriptTag({ path: TYPE });
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot; window.T = () => R().querySelector('.scr').innerText.replace(/\s+/g, ' '); window.__phone.openApp('haraj'); });
  for (const k of ['mk_never_m', 'mk_never_f']) {
    await p.waitForTimeout(600);
    await p.evaluate(() => { const b = R().querySelector('.back'); if (b && R().querySelector('.title').textContent !== 'الحراج') b.click(); });
    await p.waitForTimeout(600);
    await p.evaluate((id) => R().querySelector(`[data-go="listing"][data-id="${id}"]`).click(), ids[k]);
    await p.waitForTimeout(700);
    const ty = await p.evaluate(() => window.__typeAudit('phone'));
    console.log(k, 'BEFORE:', (await p.evaluate(() => T())).slice(0, 330), '| split', JSON.stringify(ty.split), 'prepEnd', JSON.stringify(ty.prepEnd), 'widow', JSON.stringify(ty.widow));
    console.log('  button label', await p.evaluate(() => R().querySelector('[data-act="vet"]').getAttribute('aria-label')));
    await p.evaluate(() => R().querySelector('[data-act="vet"]').click());
    await p.waitForTimeout(1500);
    console.log('  after look sr:', JSON.stringify(await p.evaluate(() => R().querySelector('.sr').textContent)), '| button', JSON.stringify(await p.evaluate(() => { const e = R().querySelector('[data-act="vet"]'); return e && [e.disabled, e.textContent, e.getAttribute('aria-label')]; })), '| row', (await p.evaluate(() => T())).match(/البيطري[^ا]*?(مرة|لقى)[^.]*/)?.[0]);
  }
  await b.close();
})();
