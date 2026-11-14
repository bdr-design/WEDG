// The money switch in the test meter (#fps; GDD 13): a single tap does not turn it on; two taps within 3 s do; the
// money is then at 10,000,000 or more, the closed meter marks it, the bank shows «فلوس تجربة»; one tap turns it off,
// money and mark staying. Without #fps there is no meter at all. Pictures with SHOTS=<folder>.
//   PORT=<port> NODE_PATH=$(npm root -g) node tool/page_checks/money_meter.cjs
const { chromium } = require('playwright');
const path = require('path');
const PORT = process.env.PORT || 8940, SHOTS = process.env.SHOTS || '';
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };
(async () => {
  const b = await chromium.launch(LAUNCH);
  const fails = [], ok = (c, what) => { console.log(`${c ? 'ok  ' : 'FAIL'}  ${what}`); if (!c) fails.push(what); };
  const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: SHOTS ? 2 : 1, hasTouch: true });
  const p0 = await ctx.newPage();
  await p0.goto(`http://127.0.0.1:${PORT}/index.html`, { timeout: 600000, waitUntil: 'domcontentloaded' });
  await p0.waitForFunction(() => window.marahEngine?.snapshot, null, { timeout: 900000 });
  ok(await p0.evaluate(() => document.getElementById('meter').hidden), 'no #fps: no meter');
  await p0.close();
  const p = await ctx.newPage();
  p.on('pageerror', (e) => fails.push('page error: ' + e.message));
  p.on('console', (m) => { if (/meter:/.test(m.text())) console.log('console:', m.text()); });
  await p.goto(`http://127.0.0.1:${PORT}/index.html#fps`, { timeout: 600000, waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => document.getElementById('status').hidden && window.marahEngine?.snapshot, null, { timeout: 900000 });
  await p.evaluate(async () => { await window.marahEngine.startOver({ seed: 4242 }); });
  await p.waitForFunction(() => window.marahEngine.snapshot?.herd.total === 2, null, { timeout: 60000 });
  await p.evaluate(() => { window.__phone.toggle(); window.__phone.enlarge(); });
  await p.waitForFunction(() => !/يسخّن/.test(document.getElementById('meter').textContent) && document.getElementById('meter').textContent, null, { timeout: 300000 });
  // (the taps are dispatched on the elements: the enlarged phone stands over the page, and with it the scene is not
  // drawn, so the meter's frames come quickly even on a loaded test machine; its hit-testing is not what is tested)
  const tapEl = (sel) => p.evaluate((sel) => { const e = document.querySelector(sel); if (!e) return false; e.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true })); e.dispatchEvent(new MouseEvent('click', { bubbles: true, detail: 1 })); return true; }, sel);
  const setOpen = async (want) => { for (let i = 0; i < 4; i++) { if (await p.evaluate(() => document.getElementById('meter').classList.contains('open')) === want) return; await tapEl('#meter'); await p.waitForTimeout(1600); } };
  const S = () => p.evaluate(() => ({ on: window.marahEngine.snapshot.testMoney, from: window.marahEngine.snapshot.testedFrom, cash: window.marahEngine.snapshot.cash }));
  const cash0 = (await S()).cash;
  await setOpen(true); await p.waitForTimeout(1500);
  const line = async () => { const r = await p.evaluate(() => { const u = document.querySelector('#meter [data-money]'); if (!u) return null; const b = u.getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2, t: u.textContent }; }); return r; };
  await p.waitForFunction(() => document.querySelector('#meter [data-money]'), null, { timeout: 30000 }).catch(async () => console.log('meter:', await p.evaluate(() => document.getElementById('meter').className + ' | ' + document.getElementById('meter').innerHTML)));
  let l = await line();
  ok(l && /طافية/.test(l.t), 'the open meter has the line, off: ' + (l && l.t));
  if (SHOTS) await p.screenshot({ path: path.join(SHOTS, 'meter_off.png'), clip: await p.evaluate(() => { const r = document.getElementById('meter').getBoundingClientRect(); return { x: r.x - 4, y: r.y - 4, width: r.width + 8, height: r.height + 8 }; }), timeout: 600000 });
  await tapEl('#meter [data-money]');
  await p.waitForFunction(() => /مرة ثانية/.test(document.querySelector('#meter [data-money]')?.textContent || ''), null, { timeout: 20000 }).catch(() => {});
  ok(!(await S()).on, 'one tap: still off');
  l = await line();
  ok(l && /مرة ثانية/.test(l.t), 'one tap: armed, «اضغط مرة ثانية»');
  await p.waitForFunction(() => /طافية/.test(document.querySelector('#meter [data-money]')?.textContent || ''), null, { timeout: 20000 }).catch(() => {}); l = await line();
  ok(l && /طافية/.test(l.t), 'after 3 s unarmed again');
  await tapEl('#meter [data-money]'); l = await line();
  await tapEl('#meter [data-money]');
  await tapEl('#meter [data-money]');      // (a quick third tap, within the second after it turned on: ignored)
  await p.waitForFunction(() => /شغّالة/.test(document.querySelector('#meter [data-money]')?.textContent || ''), null, { timeout: 120000 }).catch(() => {});
  let s = await S();
  ok(s.on && s.cash >= 10000000 && !!s.from, `two taps (and a quick third, ignored): on, the money ${s.cash} (was ${cash0}), marked from ${s.from}`);
  ok(await p.evaluate(() => document.getElementById('meter').classList.contains('open')), 'the meter stayed open (a tap on its line does not close it)');
  if (SHOTS) await p.screenshot({ path: path.join(SHOTS, 'meter_on.png'), clip: await p.evaluate(() => { const r = document.getElementById('meter').getBoundingClientRect(); return { x: r.x - 4, y: r.y - 4, width: r.width + 8, height: r.height + 8 }; }), timeout: 600000 });
  // an order the start's money could not pay: the dearest camel on the market
  const bought = await p.evaluate(async () => { const e = window.marahEngine, l = e.snapshot.market.slice().sort((a, b) => b.askPrice - a.askPrice)[0]; const r = await e.dispatch({ type: 'buyListing', listing: l.id }); return { ok: r.ok, price: l.askPrice, err: r.error }; });
  ok(bought.ok, `the dearest listing (${bought.price}) bought: ${JSON.stringify(bought.err)}`);
  await setOpen(false);
  await p.waitForFunction(() => !document.getElementById('meter').classList.contains('open') && /فلوس تجربة/.test(document.getElementById('meter').textContent), null, { timeout: 120000 }).catch(() => {});
  ok(/فلوس تجربة/.test(await p.evaluate(() => document.getElementById('meter').textContent)), 'closed: the meter marks it');
  // the bank's row
  await p.evaluate(() => { const R = [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot; R.querySelector('[data-go="bank"]').click(); });
  await p.waitForTimeout(1500);
  const bank = await p.evaluate(() => [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot.querySelector('.scr').innerText);
  ok(/فلوس تجربة/.test(bank), 'the bank shows «فلوس تجربة»');
  ok(!/دخل اليوم 9|دخل اليوم 1\d,/.test(bank), 'today\'s net leaves the test money out');
  if (SHOTS) { const box = await p.evaluate(() => { const r = [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot.querySelector('.dev').getBoundingClientRect(); return { x: r.x - 4, y: 0, width: r.width + 8, height: 440 }; }); await p.screenshot({ path: path.join(SHOTS, 'bank_test_money.png'), clip: box, timeout: 600000 }); }
  await setOpen(true);
  await p.waitForFunction(() => document.querySelector('#meter [data-money]'), null, { timeout: 120000 }).catch(() => {});
  l = await line();
  await tapEl('#meter [data-money]');
  await p.waitForFunction(() => /طافية/.test(document.querySelector('#meter [data-money]')?.textContent || ''), null, { timeout: 120000 }).catch(() => {});
  s = await S();
  ok(!s.on && !!s.from && s.cash > 1000000, `one tap: off; money ${s.cash} and the mark (${s.from}) stay`);
  await p.waitForFunction(() => /لعبة فيها فلوس تجربة من/.test(document.getElementById('meter').textContent), null, { timeout: 60000 }).catch(() => {});
  l = await line();
  ok(l && /طافية/.test(l.t) && /لعبة فيها فلوس تجربة من/.test(await p.evaluate(() => document.getElementById('meter').textContent)), 'the open meter says the game had test money: ' + await p.evaluate(() => document.getElementById('meter').className + ' | ' + document.getElementById('meter').textContent.slice(-90)));
  await b.close();
  if (fails.length) { console.log('\nFAILED:\n' + fails.join('\n')); process.exit(1); }
  console.log('\nthe money switch: all ok');
})();
