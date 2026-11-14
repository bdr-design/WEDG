// T16 worker's harness: الحراج's approved vet views in the real phone, on engine-made saves (tool/proto_engine/bin/
// vet_design_save.dart: played forward; one state staged, see its header) and new games, shot at 956x440 enlarged,
// with the layout audit, the typography audit (t14's tool/page_checks/type_audit.js) and the views' texts.
// PHASE: v (vet_before.json: a clean listing's look, a second the same day, the treated listing's look), d (vet.json:
// the declared sale, listed and its offer, the broker's price, the refusal), s (short.json: cash short for the look),
// w (a new game on the fast clock: the listing's page open while it leaves the market). Env: PORT, OUT, SAVES.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const PORT = process.env.PORT || 8962, OUT = process.env.OUT || '.', PHASE = process.env.PHASE || 'v', SAVES = process.env.SAVES;
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };
const AUDIT = '/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/t4_review/h/audit.js';
const TYPE = path.join(__dirname, 'type_audit.js');
fs.mkdirSync(OUT, { recursive: true });
const log = (...a) => console.log(PHASE, ...a);

async function open(b, { save = null, scale = 0, seed = null } = {}) {
  const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  p.on('pageerror', (e) => log('PAGE ERROR', e.message));
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
  });
  return { ctx, p };
}
const tap = async (p, sel) => {
  await p.waitForTimeout(450);
  const r = await p.evaluate((s) => { const e = R().querySelector(s); if (!e) return null; e.scrollIntoView({ block: 'center' }); const b = e.getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }, sel);
  if (!r) { log('no', sel); return false; }
  await p.mouse.click(r.x, r.y); return true;
};
const home = async (p) => { for (let i = 0; i < 4; i++) { if (!(await p.evaluate(() => !!R().querySelector('.back')))) break; await tap(p, '.back'); } };
let n = 0;
async function shot(p, name, end) {
  await p.waitForTimeout(500);
  if (end) await p.evaluate(() => { const bd = R().querySelector('.body'); bd.scrollTop = bd.scrollHeight; });
  await p.evaluate(() => { window.__raf = window.requestAnimationFrame; window.requestAnimationFrame = () => 0; });
  const box = await p.evaluate(() => { const r = R().querySelector('.dev').getBoundingClientRect(); return { x: r.x, width: r.width }; });
  const file = path.join(OUT, `t16_${PHASE}${++n}_${name}.png`);
  await p.screenshot({ path: file, timeout: 600000, clip: { x: Math.max(0, box.x - 4), y: 0, width: box.width + 8, height: 440 } });
  await p.addScriptTag({ path: AUDIT }); await p.addScriptTag({ path: TYPE });
  const a = await p.evaluate(() => window.__audit()), t = await p.evaluate(() => window.__typeAudit('phone'));
  const ty = {}; for (const k of ['split', 'prepNum', 'prepEnd', 'widow', 'clipped', 'outside', 'digits', 'noSep', 'minus', 'hyphenMinus', 'parens', 'dot', 'spacing', 'proportional', 'lineHeight']) if (t[k] && t[k].length) ty[k] = t[k];
  log(name, 'layout', JSON.stringify({ clipped: a.clipped, outside: a.outside, split: a.split }), 'type', JSON.stringify(ty));
  fs.appendFileSync(path.join(OUT, 'texts.txt'), a.texts.filter((x) => !x.includes('{')).join('\n') + '\n');
  await p.evaluate(() => { window.requestAnimationFrame = window.__raf; });
  log('shot', file, (await p.evaluate(() => T())).slice(0, 500));
}

// every page module parsed as a module first (a plain `node --check` of a .js file passed one that did not load)
const WEB = process.env.WEB || '/home/user/wt/t16/tool/proto_app/assets/web';
for (const f of ['phone.js', 'play.js', 'world.js', 'engine.js', 'terrain.js', 'car_physics.js']) {
  const tmp = path.join(__dirname, `check_${f}.mjs`);
  fs.copyFileSync(path.join(WEB, f), tmp);
  try { require('child_process').execFileSync(process.execPath, ['--check', tmp], { stdio: 'pipe' }); } catch (e) { console.log(PHASE, 'MODULE DOES NOT PARSE', f, String(e.stderr).slice(0, 300)); process.exit(1); }
  fs.unlinkSync(tmp);
}
(async () => {
  const b = await chromium.launch(LAUNCH);
  if (PHASE === 'v') {
    const text = fs.readFileSync(path.join(SAVES, 'vet_before.json'), 'utf8');
    // the treated listing, from the save (the phone is never told it before a look)
    const data = JSON.parse(text).data, W = data.world;
    const cam = Object.fromEntries((W.camels || []).map((c) => [c.id, c]));
    const treated = (W.listings || []).filter((l) => (cam[l.camel] || {}).treatments && cam[l.camel].treatments.length).sort((a, b) => a.ask - b.ask)[0];
    log('treated listing', treated && treated.id);
    const { p } = await open(b, { save: text });
    await tap(p, '[data-go="haraj"]');
    const clean = await p.evaluate((tid) => window.marahEngine.snapshot.market.filter((l) => l.id !== tid).sort((a, b) => a.askPrice - b.askPrice)[0].id, treated.id);
    await tap(p, `[data-go="listing"][data-id="${clean}"]`); await shot(p, 'before_look');
    await tap(p, '[data-act="vet"]'); await p.waitForTimeout(800); await shot(p, 'nothing_found');
    log('second look today', JSON.stringify(await p.evaluate(async (id) => (await window.marahEngine.dispatch({ type: 'checkListing', listing: id })).error, clean)));
    log('button', await p.evaluate(() => { const x = R().querySelector('[data-act="vet"]'); return x && [x.textContent, x.disabled]; }));
    await tap(p, '.back'); await tap(p, `[data-go="listing"][data-id="${treated.id}"]`); await shot(p, 'treated_before');
    await tap(p, '[data-act="vet"]'); await p.waitForTimeout(800); await shot(p, 'found');
    log('sr', await p.evaluate(() => R().querySelector('.sr').textContent));
    // nothing of a seller's treatment before a look: the other listings carry none
    log('leak', await p.evaluate(() => window.marahEngine.snapshot.market.filter((l) => l.treatments && !l.checked && !l.declared).length));
  }
  if (PHASE === 'd') {
    const { p } = await open(b, { save: fs.readFileSync(path.join(SAVES, 'vet.json'), 'utf8'), scale: 1500 });
    const g = await p.evaluate(() => { const S = window.marahEngine.snapshot; const d = S.yard.find((c) => c.declaredSale != null), o = S.yard.find((c) => c.declareRefused); return { d: d && d.id, o: o && o.id }; });
    log('camels', JSON.stringify(g));
    // the refusal first (the dye lasts 30 days: the fast clock's wait for an offer outlives it)
    await tap(p, '[data-go="haraj"]'); await tap(p, '[data-go="pick"]');
    await tap(p, `[data-go="sell"][data-id="${g.o}"]`); await shot(p, 'refused'); await shot(p, 'refused_end', true);
    await home(p); await tap(p, '[data-go="haraj"]'); await tap(p, '[data-go="pick"]');
    await tap(p, `[data-go="sell"][data-id="${g.d}"]`); await shot(p, 'declare');
    await tap(p, '[data-act="list"]'); await p.waitForTimeout(800); await shot(p, 'declared_listed');
    await p.waitForFunction(() => window.marahEngine.snapshot.myListings.some((l) => l.offers.length), null, { timeout: 300000, polling: 300 });
    await p.waitForTimeout(600); await shot(p, 'declared_offer');
    log('offers', JSON.stringify(await p.evaluate(() => window.marahEngine.snapshot.myListings.map((l) => [l.declared, l.askPrice, l.offers.map((o) => o.amount), l.camel.declaredSale]))));
  }
  if (PHASE === 's') {
    const { p } = await open(b, { save: fs.readFileSync(path.join(SAVES, 'short.json'), 'utf8') });
    await tap(p, '[data-go="haraj"]'); await tap(p, '[data-go="listing"]'); await shot(p, 'cash_short');
    log('cash', await p.evaluate(() => window.marahEngine.snapshot.cash));
  }
  if (PHASE === 'w') {
    const { p } = await open(b, { scale: 20000, seed: 4242 });
    await p.evaluate(async () => { const e = window.marahEngine; await e.startOver({ seed: 4242 }); for (let i = 0; i < 400 && !(e.snapshot && e.snapshot.date === '2026-10-01'); i++) await new Promise((r) => setTimeout(r, 25)); });
    await tap(p, '[data-go="haraj"]');
    const id = await p.evaluate(() => window.marahEngine.snapshot.market.slice().sort((a, b) => a.expiresOn - b.expiresOn)[0].id);
    await tap(p, `[data-go="listing"][data-id="${id}"]`);
    await p.waitForFunction((id) => !window.marahEngine.snapshot.market.some((l) => l.id === id), id, { timeout: 120000, polling: 100 });
    await p.waitForTimeout(800); await shot(p, 'gone');
  }
  if (PHASE === 'k') {
    // bought knowing (his vet found it, he bought it): the declared sale refused, the three ways out
    const { p } = await open(b, { save: fs.readFileSync(path.join(SAVES, 'vet_knew.json'), 'utf8') });
    const id = await p.evaluate(() => (window.marahEngine.snapshot.yard.find((c) => c.declareRefused === 'knewWhenBought') || {}).id);
    log('knew camel', id);
    await tap(p, '[data-go="haraj"]'); await tap(p, '[data-go="pick"]');
    await tap(p, `[data-go="sell"][data-id="${id}"]`); await shot(p, 'knew'); await shot(p, 'knew_end', true);
    log('declared refused', JSON.stringify(await p.evaluate(async (id) => (await window.marahEngine.dispatch({ type: 'quickSale', camel: id, declared: true })).error, id)));
  }
  if (PHASE === 'x') {
    // every view in the other sex: the screen reached in the real game, then the same snapshot with the camel's sex
    // turned given to the phone (window.__phone.setGame), shot and audited (the templates' words, not the engine's)
    const flipped = (S, id) => {
      const f = (c) => (c && c.id === id ? { ...c, sex: c.sex === 'male' ? 'female' : 'male' } : c);
      return { ...S, revision: S.revision + 1000, yard: S.yard.map(f), market: S.market.map((l) => ({ ...l, camel: f(l.camel) })) };
    };
    const flip = (p, id) => p.evaluate(([id, src]) => { const fl = eval(src); window.__phone.setGame(fl(window.marahEngine.snapshot, id)); }, [id, flipped.toString()]);
    let { ctx, p } = await open(b, { save: fs.readFileSync(path.join(SAVES, 'vet_before.json'), 'utf8') });
    const text = fs.readFileSync(path.join(SAVES, 'vet_before.json'), 'utf8'), W = JSON.parse(text).data.world;
    const cam = Object.fromEntries(W.camels.map((c) => [c.id, c]));
    const treated = W.listings.filter((l) => (cam[l.camel] || {}).treatments && cam[l.camel].treatments.length).sort((a, b) => a.ask - b.ask)[0];
    await tap(p, '[data-go="haraj"]');
    const clean = await p.evaluate((tid) => window.marahEngine.snapshot.market.filter((l) => l.id !== tid).sort((a, b) => a.askPrice - b.askPrice)[0], treated.id);
    await tap(p, `[data-go="listing"][data-id="${clean.id}"]`); await flip(p, clean.camel.id); await shot(p, 'x_before_look');
    await tap(p, '[data-act="vet"]'); await p.waitForTimeout(800); await flip(p, clean.camel.id); await shot(p, 'x_nothing_found');
    await tap(p, '.back'); await tap(p, `[data-go="listing"][data-id="${treated.id}"]`);
    await tap(p, '[data-act="vet"]'); await p.waitForTimeout(800); await flip(p, treated.camel); await shot(p, 'x_found');
    await ctx.close();
    for (const [save, pickIt, name] of [['vet.json', (S) => S.yard.find((c) => c.declaredSale != null), 'x_declare'], ['vet.json', (S) => S.yard.find((c) => c.declareRefused === 'ownTreatment'), 'x_own'], ['vet_knew.json', (S) => S.yard.find((c) => c.declareRefused === 'knewWhenBought'), 'x_knew']]) {
      ({ ctx, p } = await open(b, { save: fs.readFileSync(path.join(SAVES, save), 'utf8') }));
      const id = await p.evaluate((src) => (eval(src)(window.marahEngine.snapshot) || {}).id, pickIt.toString());
      await tap(p, '[data-go="haraj"]'); await tap(p, '[data-go="pick"]'); await tap(p, `[data-go="sell"][data-id="${id}"]`);
      await flip(p, id); await shot(p, name);
      await ctx.close();
    }
  }
  if (PHASE === 'p') {
    // the two views that scroll, for the owner: (a) as built, (b) the most compact honest arrangement (every approved
    // block and word kept; tighter spacing within the phone's own scale; no smaller text), each its first screen and
    // its end
    const text = fs.readFileSync(path.join(SAVES, 'vet_before.json'), 'utf8'), W = JSON.parse(text).data.world;
    const cam = Object.fromEntries(W.camels.map((c) => [c.id, c]));
    const treated = W.listings.filter((l) => (cam[l.camel] || {}).treatments && cam[l.camel].treatments.length).sort((a, b) => a.ask - b.ask)[0];
    const { p } = await open(b, { save: text });
    const COMPACT = `.body { gap: 8px !important; } .tank { padding: 10px 14px !important; gap: 2px !important; } .kind { margin-top: 2px !important; }
      .row { min-height: 46px !important; padding-block: 6px !important; } .it.big { grid-template-columns: 84px 1fr !important; } .it.big .ph { width: 84px !important; height: 84px !important; }
      .btn { height: 40px !important; } .warn { padding-block: 8px !important; } .sec { margin-bottom: -4px !important; }`;
    const overflow = () => p.evaluate(() => { const bd = R().querySelector('.body'); return bd.scrollHeight - bd.clientHeight; });
    const both = async (name) => {
      for (const [k, css] of [['a_built', ''], ['b_compact', COMPACT]]) {
        await p.evaluate((css) => { let st = R().querySelector('#cmp'); if (!st) { st = document.createElement('style'); st.id = 'cmp'; R().appendChild(st); } st.textContent = css; R().querySelector('.body').scrollTop = 0; }, css);
        await p.waitForTimeout(400);
        const o = await overflow();
        log(name, k, 'scrolls', o, 'px');
        await shot(p, `${name}_${k}_top`); await shot(p, `${name}_${k}_end`, true);
        await p.evaluate(() => { R().querySelector('.body').scrollTop = 0; });
      }
      await p.evaluate(() => { const st = R().querySelector('#cmp'); if (st) st.textContent = ''; });
    };
    await tap(p, '[data-go="haraj"]');
    const clean = await p.evaluate((tid) => window.marahEngine.snapshot.market.filter((l) => l.id !== tid).sort((a, b) => a.askPrice - b.askPrice)[0].id, treated.id);
    await tap(p, `[data-go="listing"][data-id="${clean}"]`); await tap(p, '[data-act="vet"]'); await p.waitForTimeout(800);
    await both('check');
    await tap(p, '.back'); await tap(p, `[data-go="listing"][data-id="${treated.id}"]`); await tap(p, '[data-act="vet"]'); await p.waitForTimeout(800);
    await both('found');
  }
  if (PHASE === 'f') {
    // the camel's page in every state, compact (the owner's item 21): how far each scrolls, and the audits. States
    // the game reached are shot as they are; the rest are the same snapshot with one field changed, given to the phone
    // (window.__phone.setGame): the other sex, a long name, two kinds found, no سوم left
    const text = fs.readFileSync(path.join(SAVES, 'vet_before.json'), 'utf8'), W = JSON.parse(text).data.world;
    const cam = Object.fromEntries(W.camels.map((c) => [c.id, c]));
    const treated = W.listings.filter((l) => (cam[l.camel] || {}).treatments && cam[l.camel].treatments.length).sort((a, b) => a.ask - b.ask)[0];
    let { ctx, p } = await open(b, { save: text });
    const over = () => p.evaluate(() => { const bd = R().querySelector('.body'); return bd.scrollHeight - bd.clientHeight; });
    const mod = (id, src) => p.evaluate(([id, src]) => { const fn = eval(src); const S = window.marahEngine.snapshot; window.__phone.setGame({ ...S, revision: S.revision + 1000, market: S.market.map((l) => (l.id === id ? fn(JSON.parse(JSON.stringify(l))) : l)) }); }, [id, src]);
    const state = async (name) => { const o = await over(); const now = await p.evaluate(() => !!R().querySelector('[data-act="buyNow"]')); log('FIT', name, o, 'px', now ? 'buyNow' : 'no buyNow'); await shot(p, name); };
    await tap(p, '[data-go="haraj"]');
    const clean = await p.evaluate((tid) => window.marahEngine.snapshot.market.filter((l) => l.id !== tid).sort((a, b) => a.askPrice - b.askPrice)[0].id, treated.id);
    await tap(p, `[data-go="listing"][data-id="${clean}"]`); await state('f_before_look');
    await mod(clean, ((l) => { l.camel.sex = l.camel.sex === 'male' ? 'female' : 'male'; return l; }).toString()); await state('f_before_look_other_sex');
    await mod(clean, ((l) => { l.camel.name = 'الغالية بنت الشيخة المزيونة'; l.sellerName = 'أبو عبدالرحمن بن سلطان'; return l; }).toString()); await state('f_long_name');
    await tap(p, '[data-act="vet"]'); await p.waitForTimeout(800); await state('f_after_look');
    await mod(clean, ((l) => { l.camel.sex = l.camel.sex === 'male' ? 'female' : 'male'; return l; }).toString()); await state('f_after_look_other_sex');
    await mod(clean, ((l) => { l.bargainsLeft = 0; return l; }).toString()); await state('f_no_bids_left');
    await mod(clean, ((l) => { l.checked = 11; return l; }).toString()); await state('f_eleven_looks');
    // a سوم answered: the seller's card at the top (a real bid)
    await p.evaluate(() => window.__phone.setGame(window.marahEngine.snapshot));
    await tap(p, '[data-act="bid"]'); await p.waitForTimeout(900); await state('f_after_bid');
    await tap(p, '.back'); await tap(p, `[data-go="listing"][data-id="${treated.id}"]`);
    await tap(p, '[data-act="vet"]'); await p.waitForTimeout(800); await state('f_found');
    await mod(treated.id, ((l) => { l.treatments = ['botox', 'filler']; return l; }).toString()); await state('f_two_kinds');
    await mod(treated.id, ((l) => { l.treatments = ['botox', 'filler']; l.camel.sex = l.camel.sex === 'male' ? 'female' : 'male'; l.camel.name = 'الغالية بنت الشيخة المزيونة'; return l; }).toString()); await state('f_two_kinds_other_sex_long');
    await mod(treated.id, ((l) => { l.askPrice = 10000000; return l; }).toString()); await state('f_cannot_pay');
    await ctx.close();
    ({ ctx, p } = await open(b, { save: fs.readFileSync(path.join(SAVES, 'short.json'), 'utf8') }));
    await tap(p, '[data-go="haraj"]'); await tap(p, '[data-go="listing"]'); await state('f_cash_short');
    await ctx.close();
    ({ ctx, p } = await open(b, { scale: 20000, seed: 4242 }));
    await p.evaluate(async () => { const e = window.marahEngine; await e.startOver({ seed: 4242 }); for (let i = 0; i < 400 && !(e.snapshot && e.snapshot.date === '2026-10-01'); i++) await new Promise((r) => setTimeout(r, 25)); });
    await tap(p, '[data-go="haraj"]');
    const id = await p.evaluate(() => window.marahEngine.snapshot.market.slice().sort((a, b) => a.expiresOn - b.expiresOn)[0].id);
    await tap(p, `[data-go="listing"][data-id="${id}"]`);
    await p.waitForFunction((id) => !window.marahEngine.snapshot.market.some((l) => l.id === id), id, { timeout: 180000, polling: 100 });
    await p.waitForTimeout(800); await state('f_gone');
  }
  if (PHASE === 't') {
    // T15's additions beside the camel's page: a purchase on the truck (its rush row in الحراج), then the next
    // camel's page with the buy-now link, each measured for scroll
    const { ctx, p } = await open(b, { seed: 4242 });
    await p.evaluate(async () => { const e = window.marahEngine; await e.startOver({ seed: 4242 }); for (let i = 0; i < 400 && !(e.snapshot && e.snapshot.date === '2026-10-01'); i++) await new Promise((r) => setTimeout(r, 25)); });
    const over = () => p.evaluate(() => { const bd = R().querySelector('.body'); return bd.scrollHeight - bd.clientHeight; });
    const st = async (name) => { const o = await over(); const f = await p.evaluate(() => ({ now: !!R().querySelector('[data-act="buyNow"]'), truck: !!R().querySelector('[data-act="rushTruck"]'), hjl: !!R().querySelector('.body.hjl') })); log('FIT', name, o, 'px', JSON.stringify(f)); await shot(p, name); };
    await tap(p, '[data-go="haraj"]');
    const ids = await p.evaluate(() => window.marahEngine.snapshot.market.slice().sort((a, b) => a.askPrice - b.askPrice).map((l) => l.id));
    await tap(p, `[data-go="listing"][data-id="${ids[1]}"]`); await st('t_listing_fresh');
    await tap(p, '.back');
    await p.evaluate(async (id) => { await window.marahEngine.dispatch({ type: 'buyListing', listing: id }); await new Promise((r) => setTimeout(r, 1200)); }, ids[0]);
    await p.waitForTimeout(800); await st('t_haraj_truck');
    await tap(p, `[data-go="listing"][data-id="${ids[1]}"]`); await st('t_listing_after_buy');
    await tap(p, '[data-act="vet"]'); await p.waitForTimeout(800); await st('t_listing_after_buy_looked');
    await ctx.close();
  }
  if (PHASE === 'q') {
    // the owner's items 26 and 27 on the reviewer's real save (both sexes): the seller's answer in the سوم's block, every
    // kind (real, then each kind given by the engine's own error shapes), and the sell pages with a suckling calf
    const RS = process.env.RSAVE, ids = JSON.parse(fs.readFileSync(RS + '.ids.json', 'utf8'));
    let { ctx, p } = await open(b, { save: fs.readFileSync(RS, 'utf8') });
    const over = () => p.evaluate(() => { const bd = R().querySelector('.body'); return bd.scrollHeight - bd.clientHeight; });
    const said = () => p.evaluate(() => (R().querySelector('.sr') || {}).textContent || '');
    const st = async (name) => { if (process.env.QCSS) for (const [i, css] of JSON.parse(process.env.QCSS).entries()) log('CAND', name, i, await p.evaluate((css) => { const R0 = R(); let t = R0.getElementById('cand'); if (!t) { t = document.createElement('style'); t.id = 'cand'; R0.appendChild(t); } t.textContent = css; const bd = R0.querySelector('.body'); const o = bd.scrollHeight - bd.clientHeight; t.textContent = ''; return o; }, css)); const o = await over(); const f = await p.evaluate(() => ({ top: !!R().querySelector('.body > .msgc'), ans: (R().querySelector('.note.ans') || {}).textContent || null })); log('FIT', name, o, 'px', JSON.stringify(f), 'said', await said()); await shot(p, name); };
    const mod = (id, src) => p.evaluate(([id, src]) => { const fn = eval(src); const S = window.marahEngine.snapshot; window.__phone.setGame({ ...S, revision: S.revision + 1000, market: S.market.map((l) => (l.id === id ? fn(JSON.parse(JSON.stringify(l))) : l)) }); }, [id, src]);
    const fake = (kind) => p.evaluate((kind) => {
      const e = window.marahEngine; if (!e.__d) e.__d = e.dispatch.bind(e);
      e.dispatch = async (c) => {
        if (c.type !== 'bargain' || kind === 'real') return e.__d(c);
        if (kind === 'accept') return e.__d({ type: 'buyListing', listing: c.listing });
        const l = window.marahEngine.snapshot.market.find((x) => x.id === c.listing);
        if (kind === 'counter') return { ok: false, error: { code: 'bargainCountered', params: { ask: l.askPrice - 500 } }, events: [] };
        if (kind === 'counterPoor') return { ok: false, error: { code: 'bargainCountered', params: { ask: 9000000 } }, events: [] };
        return { ok: false, error: { code: 'bargainRejected', params: { ask: kind === 'rejectPoor' ? 9000000 : l.askPrice } }, events: [] };
      };
    }, kind);
    await tap(p, '[data-go="haraj"]');
    const QK = process.env.QONLY ? process.env.QONLY.split(',') : null;
    for (const k of ['mk_never_m', 'mk_never_f', 'mk_clean_m', 'mk_clean_f', 'mk_found_m', 'mk_found_f'].filter((k) => !QK || QK.includes(k))) {
      const id = ids[k];
      if (!(await p.evaluate((id) => window.marahEngine.snapshot.market.some((l) => l.id === id), id))) { log('gone', k); continue; }
      for (const kind of ['real', 'counter', 'reject', 'counterPoor', 'rejectPoor', 'lastCounter', 'lastReject'].filter((k) => !process.env.QKINDS || process.env.QKINDS.split(',').includes(k))) {
        await home(p); await tap(p, '[data-go="haraj"]'); await p.evaluate(() => window.__phone.setGame(window.marahEngine.snapshot));
        if (!(await tap(p, `[data-go="listing"][data-id="${id}"]`))) continue;
        if (kind.startsWith('last')) await mod(id, ((l) => { l.bargainsLeft = 1; return l; }).toString());
        await fake(kind === 'lastCounter' ? 'counter' : kind === 'lastReject' ? 'reject' : kind);
        if (!(await tap(p, '[data-act="bid"]'))) { log('no bid', k, kind); continue; }
        await p.waitForTimeout(900); await st(`q_${k}_${kind}`);
        if (kind === 'real') { await tap(p, '[data-act="bidStep"]'); await p.waitForTimeout(500); await st(`q_${k}_real_step`); }
      }
    }
    // an accepted سوم: bought, back to the list with its word (on the list's card, as before)
    await home(p); await tap(p, '[data-go="haraj"]'); await fake('accept');
    const cheap = await p.evaluate(() => window.marahEngine.snapshot.market.slice().sort((a, b) => a.askPrice - b.askPrice)[0].id);
    await tap(p, `[data-go="listing"][data-id="${cheap}"]`); await tap(p, '[data-act="bid"]'); await p.waitForTimeout(1200); await st('q_accept');
    await ctx.close();
    if (process.env.QSKIPSELL) { await b.close(); return; }
    // the sell pages (item 27): the refusal with the suckling line, and every herd state on the same save
    ({ ctx, p } = await open(b, { save: fs.readFileSync(RS, 'utf8') }));
    for (const k of ['herd_own_f', 'herd_own_m', 'herd_knew_f', 'herd_knew_m', 'herd_told_f', 'herd_told_m']) {
      await home(p); await tap(p, '[data-go="haraj"]'); await tap(p, '[data-go="pick"]');
      if (!(await tap(p, `[data-go="sell"][data-id="${ids[k]}"]`))) continue;
      const o = await over(); const f = await p.evaluate(() => ({ cards: [...R().querySelectorAll('.body > .warn')].map((w) => w.querySelector('b').textContent), also: (R().querySelector('.warn small.also') || {}).textContent || null }));
      log('FIT', `s_${k}`, o, 'px', JSON.stringify(f)); await shot(p, `s_${k}`);
    }
    // every nursing mother on the farm without a refusal: her sell page unchanged (the card of its own)
    const mothers = await p.evaluate(() => window.marahEngine.snapshot.farm.milk.camels.filter((m) => m.calfName).map((m) => m.id));
    for (const id of mothers.slice(0, 4)) {
      await home(p); await tap(p, '[data-go="haraj"]'); await tap(p, '[data-go="pick"]');
      if (!(await tap(p, `[data-go="sell"][data-id="${id}"]`))) continue;
      const o = await over(); const f = await p.evaluate(() => ({ cards: [...R().querySelectorAll('.body > .warn')].map((w) => w.querySelector('b').textContent), also: !!R().querySelector('.warn small.also') }));
      log('FIT', `m_${id}`, o, 'px', JSON.stringify(f)); await shot(p, `m_${id}`);
    }
    await ctx.close();
  }
  if (PHASE === 'm') {
    // nursing mothers' sell pages on other saves (no refusal): their suckling card unchanged
    for (const f of process.env.MSAVES.split(',')) {
      const { ctx, p } = await open(b, { save: fs.readFileSync(f, 'utf8') });
      const over = () => p.evaluate(() => { const bd = R().querySelector('.body'); return bd.scrollHeight - bd.clientHeight; });
      const mothers = await p.evaluate(() => window.marahEngine.snapshot.farm.milk.camels.filter((m) => m.calfName).map((m) => m.id));
      log('mothers', path.basename(f), mothers.length);
      for (const id of mothers.slice(0, 3)) {
        await home(p); await tap(p, '[data-go="haraj"]'); await tap(p, '[data-go="pick"]');
        if (!(await tap(p, `[data-go="sell"][data-id="${id}"]`))) continue;
        const o = await over(); const fx = await p.evaluate(() => ({ cards: [...R().querySelectorAll('.body > .warn')].map((w) => w.querySelector('b').textContent), also: !!R().querySelector('.warn small.also'), html: R().querySelector('.body').innerHTML.length }));
        log('FIT', `m_${path.basename(f)}_${id}`, o, 'px', JSON.stringify(fx)); await shot(p, `m_${id}`);
      }
      await ctx.close();
    }
  }
  await b.close();
})();
