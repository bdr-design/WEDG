// T18B worker's harness: «نادي الصقور» and «تصريح الصيد» in the real phone, on engine-made saves
// (tool/proto_engine/bin/falcon_design_saves.dart) and new games, shot at 956x440 enlarged (and small), with the layout
// audit, the type audit and the views' texts. PHASE picks a run. Env: PORT, OUT, SAVES, SCALE (2 for shots).
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const SC = '/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad';
const PORT = process.env.PORT || 8931, OUT = process.env.OUT || `${SC}/t18bw/shots`, PHASE = process.env.PHASE || 'new', SAVES = process.env.SAVES || `${SC}/t18bw/saves`;
const DSF = Number(process.env.SCALE || 2);
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };
const AUDIT = `${SC}/t4_review/h/audit.js`;
const TYPE = '/home/user/wt/t18b/tool/page_checks/type_audit.js';
fs.mkdirSync(OUT, { recursive: true });
const log = (...a) => console.log(PHASE, ...a);

async function open(b, { save = null, scale = 0, seed = null } = {}) {
  const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: DSF });
  const p = await ctx.newPage();
  p.on('pageerror', (e) => log('PAGE ERROR', e.message));
  p.on('console', (m) => { if (m.type() === 'warning' || m.type() === 'error') log('console', m.text().slice(0, 300)); });
  if (save) await p.addInitScript(([v]) => { if (!sessionStorage.getItem('seeded')) { localStorage.clear(); localStorage.setItem('marah.proto.marah.save', v); sessionStorage.setItem('seeded', '1'); } }, [save]);
  await p.route('**/index.html', async (route) => {
    const r = await route.fetch();
    route.fulfill({ response: r, body: (await r.text()).replace('startEngine({ onSnapshot:', `startEngine({ ${scale ? `timeScale: ${scale}, ` : ''}${seed ? `newGame: { seed: ${seed} }, ` : ''}onSnapshot:`) });
  });
  await p.goto(`http://127.0.0.1:${PORT}/index.html`, { timeout: 180000 });
  await p.waitForFunction(() => window.marahEngine && window.marahEngine.snapshot, null, { timeout: 600000 });
  await p.evaluate(() => {
    window.R = () => [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot;
    window.T = () => R().querySelector('.scr').innerText.replace(/\s+/g, ' ');
    window.__phone.toggle(); window.__phone.enlarge();
    // rebuilds of the screen counted (each innerHTML of .scr)
    window.__rebuilds = 0;
    new MutationObserver(() => { window.__rebuilds++; }).observe(R().querySelector('.scr'), { childList: true });
  });
  return { ctx, p };
}
const tap = async (p, sel, wait = 450) => {
  await p.waitForTimeout(wait);
  const r = await p.evaluate((s) => { const e = R().querySelector(s); if (!e) return null; e.scrollIntoView({ block: 'center' }); const b = e.getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }, sel);
  if (!r) { log('no', sel); return false; }
  await p.mouse.click(r.x, r.y); return true;
};
const home = async (p) => { for (let i = 0; i < 5; i++) { if (!(await p.evaluate(() => !!R().querySelector('.back')))) break; await tap(p, '.back'); } };
let n = 0;
async function shot(p, name, where = '') {
  await p.waitForTimeout(500);
  if (where === 'end') await p.evaluate(() => { const bd = R().querySelector('.body'); bd.scrollTop = bd.scrollHeight; });
  if (where === 'mid') await p.evaluate(() => { const bd = R().querySelector('.body'); bd.scrollTop = (bd.scrollHeight - bd.clientHeight) / 2; });
  if (where === 'top') await p.evaluate(() => { const bd = R().querySelector('.body'); bd.scrollTop = 0; });
  await p.evaluate(() => { window.__raf = window.requestAnimationFrame; window.requestAnimationFrame = () => 0; });
  const box = await p.evaluate(() => { const r = R().querySelector('.dev').getBoundingClientRect(); return { x: r.x, width: r.width }; });
  const file = path.join(OUT, `${PHASE}_${String(++n).padStart(2, '0')}_${name}.png`);
  await p.screenshot({ path: file, timeout: 600000, clip: { x: Math.max(0, box.x - 4), y: 0, width: box.width + 8, height: 440 } });
  await p.addScriptTag({ path: AUDIT }); await p.addScriptTag({ path: TYPE });
  const a = await p.evaluate(() => window.__audit()), t = await p.evaluate(() => window.__typeAudit('phone'));
  const ty = {}; for (const k of ['split', 'prepNum', 'prepEnd', 'widow', 'clipped', 'outside', 'digits', 'noSep', 'minus', 'hyphenMinus', 'parens', 'dot', 'spacing', 'proportional', 'lineHeight']) if (t[k] && t[k].length) ty[k] = t[k];
  log(name, 'layout', JSON.stringify({ clipped: a.clipped, outside: a.outside, split: a.split }), 'type', JSON.stringify(ty));
  fs.appendFileSync(path.join(OUT, `texts_${PHASE}.txt`), `## ${name}\n` + a.texts.filter((x) => !x.includes('{')).join('\n') + '\n');
  await p.evaluate(() => { window.requestAnimationFrame = window.__raf; });
  log('shot', path.basename(file), (await p.evaluate(() => T())).slice(0, 400));
}
const said = (p) => p.evaluate(() => R().querySelector('.sr').textContent);
const readSave = (f) => fs.readFileSync(path.join(SAVES, f), 'utf8');

(async () => {
  const b = await chromium.launch(LAUNCH);
  if (PHASE === 'new') {
    // a new game on 1 October (seed 4242): home, the club's three tabs, tonight's lots, a lot, the permits app
    const { p } = await open(b, { seed: 4242 });
    await shot(p, 'home');
    await tap(p, '[data-go="club"]'); await p.waitForTimeout(800); await shot(p, 'auctions');
    await tap(p, '[data-go="lots"][data-k="trapping"]'); await shot(p, 'tonight');
    await tap(p, '.it.lot[data-go="lot"]'); await shot(p, 'lot_noroom');
    await home(p);
    await tap(p, '[data-go="club"]'); await tap(p, '[data-act="fcTab"][data-p="trap"]'); await shot(p, 'trap');
    await shot(p, 'trap_end', 'end');
    await tap(p, '[data-act="fcTab"][data-p="mine"]'); await shot(p, 'mine_empty');
    await home(p);
    await tap(p, '[data-go="permit"]'); await shot(p, 'permit'); await shot(p, 'permit_mid', 'mid'); await shot(p, 'permit_end', 'end');
    await tap(p, '[data-act="permit"][data-k="trapping"]', 600); await shot(p, 'permit_sure', 'top');
    await tap(p, '[data-act="permit"][data-k="trapping"]', 600); await p.waitForTimeout(800); await shot(p, 'permit_bought', 'top');
    log('said', await said(p));
    await home(p);
    await tap(p, '[data-go="build"]'); await shot(p, 'build');
  }
  if (PHASE === 'buy') {
    // a buyer with a room (buyer.json): the ceiling, two taps, the outcomes
    const { p } = await open(b, { save: readSave('buyer.json') });
    await tap(p, '[data-go="club"]'); await p.waitForTimeout(800);
    await tap(p, '[data-go="lots"][data-k="trapping"]'); await shot(p, 'tonight');
    const lots = await p.evaluate(() => window.marahEngine.snapshot.falcons.lots.filter((l) => l.route === 'trapping').map((l) => l.lot));
    await tap(p, `.it.lot[data-id="${lots[0]}"]`); await shot(p, 'lot');
    await tap(p, '[data-act="upStep"][data-d="1"]'); await tap(p, '[data-act="upStep"][data-d="1"]'); await shot(p, 'lot_up');
    await tap(p, '[data-act="buyFalcon"]', 600); await shot(p, 'lot_sure');
    log('said', await said(p));
    await tap(p, '[data-act="buyFalcon"]', 600); await p.waitForTimeout(900); await shot(p, 'lot_outcome1');
    log('said', await said(p));
    await tap(p, '.back'); await shot(p, 'tonight_after');
    if (lots[1]) {
      await tap(p, `.it.lot[data-id="${lots[1]}"]`);
      // the ceiling raised to his balance: whichever way the hammer falls, the other outcome is shown by the first lot
      for (let i = 0; i < 40; i++) { const ok = await p.evaluate(() => { const b = R().querySelector('[data-act="upStep"][data-d="1"]'); return b && !b.disabled; }); if (!ok) break; await tap(p, '[data-act="upStep"][data-d="1"]', 120); }
      await shot(p, 'lot2_max');
      await tap(p, '[data-act="buyFalcon"]', 600); await tap(p, '[data-act="buyFalcon"]', 600); await p.waitForTimeout(900); await shot(p, 'lot2_outcome');
      await tap(p, '.back'); await shot(p, 'tonight_after2');
    }
    await home(p); await tap(p, '[data-go="club"]'); await tap(p, '[data-act="fcTab"][data-p="mine"]'); await shot(p, 'mine');
  }
  if (PHASE === 'held') {
    for (const [f, nm] of [['held.json', 'noroom'], ['held_room.json', 'room'], ['held_full.json', 'full']]) {
      const { p, ctx } = await open(b, { save: readSave(f) });
      await tap(p, '[data-go="club"]'); await p.waitForTimeout(800);
      await shot(p, `club_${nm}`);
      await tap(p, '[data-go="bird"]'); await shot(p, `bird_${nm}`); await shot(p, `bird_${nm}_end`, 'end');
      if (nm === 'room') {
        await tap(p, '[data-act="enterBird"]', 600); await shot(p, 'bird_enter_sure', 'end');
        await tap(p, '[data-act="enterBird"]', 600); await p.waitForTimeout(800); await shot(p, 'bird_entered', 'top');
        log('said', await said(p));
      }
      if (nm === 'full') { await tap(p, '.back'); await tap(p, '[data-act="fcTab"][data-p="mine"]'); await shot(p, 'mine_full'); }
      await ctx.close();
    }
    for (const [f, nm] of [['close.json', 'close'], ['closed.json', 'closed'], ['sold.json', 'sold']]) {
      const { p, ctx } = await open(b, { save: readSave(f) });
      await shot(p, `home_${nm}`);
      await tap(p, '[data-go="club"]'); await p.waitForTimeout(800); await shot(p, `club_${nm}`);
      if (nm === 'close') { await tap(p, '[data-go="bird"]'); await shot(p, 'bird_close', 'end'); }
      if (nm === 'sold') { await tap(p, '[data-go="hammer"]'); await shot(p, 'hammer'); }
      await ctx.close();
    }
  }
  if (PHASE === 'mine') {
    const { p } = await open(b, { save: readSave('mine.json') });
    await tap(p, '[data-go="club"]'); await p.waitForTimeout(800); await tap(p, '[data-act="fcTab"][data-p="mine"]'); await shot(p, 'mine'); await shot(p, 'mine_end', 'end');
    await tap(p, '[data-go="train"]'); await shot(p, 'train'); await shot(p, 'train_end', 'end');
    await tap(p, '[data-act="care"]', 600); await p.waitForTimeout(800); await shot(p, 'train_cared');
  }
  if (PHASE === 'trip') {
    const { p } = await open(b, { save: readSave('held_room.json') });
    await p.evaluate(() => window.__phone.openTrip('trapping', 'hamad', 9, () => { window.__went = true; }));
    await p.waitForTimeout(1200); await shot(p, 'trip_card'); await shot(p, 'trip_card_end', 'end');
  }
  await b.close();
})();
