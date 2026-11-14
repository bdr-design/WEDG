// T16 reviewer: every vet-view state with a real male and a real female (the save from states_save.dart), each page
// shot (dsf 1) with the layout audit, t14's typography audit and its texts. Then the look itself on a never-looked
// listing: tap, answer, a second tap the same day. Env: PORT, SAVE, IDS, OUT, AUDIT (layout), TYPE (type audit).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { PORT = 8961, SAVE, IDS, OUT, AUDIT, TYPE } = process.env;
const ids = JSON.parse(fs.readFileSync(IDS, 'utf8'));
fs.mkdirSync(OUT, { recursive: true });
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 1 });
  const p = await ctx.newPage();
  const errs = []; p.on('pageerror', (e) => errs.push(e.message));
  await p.addInitScript((s) => { if (!sessionStorage.getItem('seeded')) { localStorage.clear(); localStorage.setItem('marah.proto.marah.save', s); sessionStorage.setItem('seeded', '1'); } }, fs.readFileSync(SAVE, 'utf8'));
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.marahEngine && window.marahEngine.snapshot, null, { timeout: 600000 });
  await p.waitForTimeout(1000);
  await p.addScriptTag({ path: AUDIT }); await p.addScriptTag({ path: TYPE });
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot; window.T = () => R().querySelector('.scr').innerText.replace(/\s+/g, ' '); window.__phone.toggle(); window.__phone.enlarge(); });
  const sleep = (ms) => p.waitForTimeout(ms);
  const tap = async (sel) => { await sleep(450); const r = await p.evaluate((s) => { const e = R().querySelector(s); if (!e) return null; e.scrollIntoView({ block: 'nearest' }); const b = e.getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }, sel); if (!r) return false; await p.mouse.click(r.x, r.y); return true; };
  const keys = ['split', 'prepNum', 'prepEnd', 'widow', 'clipped', 'ellipsis', 'outside', 'lineHeight', 'digits', 'noSep', 'minus', 'hyphenMinus', 'parens', 'dot', 'spacing', 'proportional', 'contrast'];
  const shot = async (name) => {
    await sleep(500);
    const box = await p.evaluate(() => { const r = R().querySelector('.dev').getBoundingClientRect(); return { x: r.x, width: r.width }; });
    await p.screenshot({ path: path.join(OUT, name + '.png'), clip: { x: Math.max(0, box.x - 4), y: 0, width: box.width + 8, height: 440 }, timeout: 600000 });
    const a = await p.evaluate(() => window.__audit()), ty = await p.evaluate(() => window.__typeAudit('phone'));
    fs.writeFileSync(path.join(OUT, 'words_' + name + '.txt'), a.texts.filter((t) => !t.includes('{')).join('\n') + '\n');
    const bad = Object.fromEntries(keys.filter((k) => ty[k] && ty[k].length).map((k) => [k, ty[k]]));
    console.log('VIEW', name, '| layout', JSON.stringify({ c: a.clipped, o: a.outside, s: a.split, below: a.scroll && a.scroll.below }), '| type', JSON.stringify(bad));
    console.log('TEXT', name, (await p.evaluate(() => T())).slice(0, 700));
  };
  const home = async () => { for (let i = 0; i < 5; i++) { if (!(await p.evaluate(() => !!R().querySelector('.back')))) break; await tap('.back'); } };
  // the market's states
  for (const k of ['mk_never_m', 'mk_never_f', 'mk_clean_m', 'mk_clean_f', 'mk_found_m', 'mk_found_f']) {
    await home(); await tap('[data-go="haraj"]');
    const ok = await tap(`[data-go="listing"][data-id="${ids[k]}"]`);
    if (!ok) { console.log('VIEW', k, 'listing not in the list'); continue; }
    await shot(k);
  }
  // his own camels' sell pages
  for (const k of ['herd_told_m', 'herd_told_f', 'herd_knew_m', 'herd_knew_f', 'herd_own_m', 'herd_own_f']) {
    await home(); await tap('[data-go="haraj"]'); await tap('[data-go="pick"]');
    const ok = await tap(`[data-go="sell"][data-id="${ids[k]}"]`);
    if (!ok) { console.log('VIEW', k, 'not in the pick list:', (await p.evaluate(() => T())).slice(0, 200)); continue; }
    await shot(k);
  }
  // the look itself, on the never-looked male: tap, answer; tap again the same day; sr
  await home(); await tap('[data-go="haraj"]'); await tap(`[data-go="listing"][data-id="${ids.mk_never_m}"]`);
  const cash0 = await p.evaluate(() => window.marahEngine.snapshot.cash);
  await tap('[data-act="vet"]'); await sleep(1200);
  console.log('LOOK sr', JSON.stringify(await p.evaluate(() => R().querySelector('.sr').textContent)), 'cash', cash0, '->', await p.evaluate(() => window.marahEngine.snapshot.cash));
  await shot('look_answer_m');
  const again = await p.evaluate(() => { const e = R().querySelector('[data-act="vet"]'); return e ? { disabled: e.disabled, text: e.textContent, label: e.getAttribute('aria-label') } : null; });
  console.log('LOOK again button', JSON.stringify(again));
  // the female's look answer too
  await home(); await tap('[data-go="haraj"]'); await tap(`[data-go="listing"][data-id="${ids.mk_never_f}"]`);
  await tap('[data-act="vet"]'); await sleep(1200);
  console.log('LOOK f sr', JSON.stringify(await p.evaluate(() => R().querySelector('.sr').textContent)));
  await shot('look_answer_f');
  console.log('ERRORS', JSON.stringify(errs));
  await b.close();
})();
