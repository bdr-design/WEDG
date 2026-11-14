// الحراج on the engine, in the page: open it, buy, haggle, sell and list, offers (a fast clock: TS game seconds a second)
const { chromium } = require('playwright');
const TS = Number(process.env.TS || 1);
const DPR = Number(process.env.DPR || 1);
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 956, height: 440 }, deviceScaleFactor: DPR });
  const logs = []; p.on('pageerror', (e) => logs.push('pageerror: ' + e.message)); p.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') logs.push(m.type() + ': ' + m.text()); });
  if (TS > 1) await p.route('**/index.html', async (r) => { const res = await r.fetch(); let t = await res.text(); t = t.replace("startEngine({ onSnapshot:", `startEngine({ timeScale: ${TS}, newGame: { seed: 4242 }, onSnapshot:`); await r.fulfill({ response: res, body: t }); });
  else await p.route('**/index.html', async (r) => { const res = await r.fetch(); let t = await res.text(); t = t.replace("startEngine({ onSnapshot:", `startEngine({ newGame: { seed: 4242 }, onSnapshot:`); await r.fulfill({ response: res, body: t }); });
  await p.goto('http://127.0.0.1:8765/index.html');
  await p.waitForFunction(() => window.marahEngine || window.marahEngineError, null, { timeout: 300000 });
  await p.waitForTimeout(1500);
  // hold the 3D scene's frames (swiftshader at 2x is slow), released for each shot
  await p.evaluate(() => { const q = []; const raf = window.requestAnimationFrame.bind(window); window.requestAnimationFrame = (f) => { q.push(f); return q.length; }; window.__release = (n = 2) => { for (let i = 0; i < n; i++) { const fs = q.splice(0); for (const f of fs) raf(f); } }; });
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone')).shadowRoot;
    window.T = (sel) => { const e = R().querySelector(sel); return e ? e.textContent.replace(/\s+/g, ' ').trim() : null; };
    window.C = (sel) => { const e = R().querySelector(sel); if (!e) return 'missing ' + sel; e.click(); return 'ok'; };
    window.__phone.toggle(); window.__phone.enlarge(); });
  const say = async (l, js) => console.log(l, JSON.stringify(await p.evaluate(js)));
  const shot = async (n) => { if (process.env.ONLY && !n.match(process.env.ONLY)) return; await p.evaluate(() => window.__release(3)); await p.waitForTimeout(250); if (process.env.SHOTS) await p.screenshot({ path: n + '.png', timeout: 180000 }); };
  const wait = (ms) => p.waitForTimeout(ms);
  await say('engine:', `({ status: marahEngine.status, cash: marahEngine.snapshot.cash, herd: marahEngine.snapshot.herd.total, market: marahEngine.snapshot.market.length, haraj: marahEngine.snapshot.haraj, yard: marahEngine.snapshot.yard.map((c) => [c.name, c.quickSale, c.onTheWay]) })`);
  await say('home apps:', `[...R().querySelectorAll('.app')].map((a) => a.getAttribute('aria-label') || a.textContent.trim())`);
  await shot('h_home');
  await say('open haraj', `C('[data-go="haraj"]')`); await wait(200);
  await say('list:', `T('.body').slice(0, 400)`);
  await shot('h_market');
  // the cheapest affordable
  const pickId = await p.evaluate(() => { const S = marahEngine.snapshot; const l = S.market.filter((x) => x.askPrice + x.transport <= S.cash).sort((a, b) => a.askPrice - b.askPrice)[0]; return l && l.id; });
  console.log('picking', pickId);
  await say('open listing', `C('[data-go="listing"][data-id="${pickId}"]')`); await wait(200);
  await say('detail:', `T('.body')`);
  await shot('h_detail');
  // haggle low: step down to the floor of the stepper
  for (let i = 0; i < 60; i++) await p.evaluate(() => R().querySelector('[data-act="bidStep"][data-d="-1"]:not([disabled])')?.click());
  await say('bid low:', `T('.stp .n')`);
  await say('send low bid', `C('[data-act="bid"]')`); await wait(700);
  await say('answer:', `({ msg: T('.msgc'), err: T('.warn'), left: T('.row.ord small'), state: R().querySelector('[data-act="bid"]').disabled })`);
  await shot('h_reject');
  // a bid a little under the price
  await p.evaluate(() => { for (let i = 0; i < 80; i++) R().querySelector('[data-act="bidStep"][data-d="1"]:not([disabled])')?.click(); for (let i = 0; i < 3; i++) R().querySelector('[data-act="bidStep"][data-d="-1"]:not([disabled])')?.click(); });
  await say('bid:', `T('.stp .n')`);
  await say('send bid', `C('[data-act="bid"]')`); await wait(700);
  await say('answer 2:', `({ msg: T('.msgc'), err: T('.warn'), buy: T('[data-act="buy"]'), left: T('.row.ord small'), screen: T('.title') })`);
  await shot('h_counter');
  const herd0 = await p.evaluate(() => marahEngine.snapshot.herd.total);
  if (await p.evaluate(() => !!R().querySelector('[data-act="buy"]:not([disabled])'))) { await say('buy', `C('[data-act="buy"]')`); await wait(800); }
  await say('after buy:', `({ title: T('.title'), msg: T('.msgc'), err: T('.warn'), cash: marahEngine.snapshot.cash, herd: marahEngine.snapshot.herd.total, yard: marahEngine.snapshot.yard.length, ev: marahEngine.snapshot.recentEvents.filter((e) => e.type === 'camelBought').map((e) => [e.day, e.price]) })`);
  console.log('herd before', herd0);
  await shot('h_bought');
  // sell: the picker, the dam's page
  await say('open pick', `C('.sell')`); await wait(200);
  await say('pick:', `T('.body')`);
  await shot('h_pick');
  const dam = await p.evaluate(() => marahEngine.snapshot.farm.milk.camels[0]?.id);
  await say('open dam', `C('[data-go="sell"][data-id="${dam}"]')`); await wait(200);
  await say('sell page:', `T('.body')`);
  await shot('h_sell');
  // quick sale asks twice: first tap only readies it
  await say('quick 1', `C('[data-act="quick"]')`); await wait(300);
  await say('after 1st tap:', `({ btn: T('[data-act="quick"]'), herd: marahEngine.snapshot.herd.total })`);
  await shot('h_quick_sure');
  await say('ask step up x4', `(() => { for (let i = 0; i < 4; i++) R().querySelector('[data-act="askStep"][data-d="1"]').click(); return T('.row.ord'); })()`);
  await say('quick after other tap:', `T('[data-act="quick"]')`);
  await say('list', `C('[data-act="list"]')`); await wait(800);
  await say('mine:', `({ title: T('.title'), body: T('.body'), mine: marahEngine.snapshot.myListings.map((l) => [l.camel.name, l.askPrice, l.expiresOn - marahEngine.snapshot.today]) })`);
  await shot('h_mine');
  if (TS > 1) {
    // days pass: the offers come; then the engine is paused (as when the app goes to the background; never resumed here:
    // on a fast clock it would catch up every day since) for the shots
    for (let i = 0; i < 60; i++) { await wait(500); const n = await p.evaluate(() => marahEngine.snapshot.openOffers); if (n >= 2) break; }
    await p.evaluate(() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => true }); document.dispatchEvent(new Event('visibilitychange')); });
    await wait(500);
    await p.evaluate(() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => false }); });
    await say('offers:', `({ day: marahEngine.snapshot.today, n: marahEngine.snapshot.openOffers, body: T('.body'), badge: T('.seg .dot') })`);
    await shot('h_offers');
    const off = await p.evaluate(() => marahEngine.snapshot.myListings[0]?.offers[0]?.id);
    if (off) {
      await say('accept 1', `C('[data-act="accept"][data-o="${off}"]')`); await wait(700);
      await say('btn:', `T('[data-act="accept"][data-o="${off}"]')`);
      await say('accept 2', `C('[data-act="accept"][data-o="${off}"]')`); await wait(900);
      await say('after accept:', `({ msg: T('.msgc'), err: T('.warn'), cash: marahEngine.snapshot.cash, herd: marahEngine.snapshot.herd.total, mine: marahEngine.snapshot.myListings.length })`);
      await shot('h_sold');
    }
  }
  console.log('logs', logs.filter((l) => !/GPU stall|WebGL|swiftshader/i.test(l)).slice(0, 20));
  await b.close();
})();
