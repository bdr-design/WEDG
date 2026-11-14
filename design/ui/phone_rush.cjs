// Rushing in the phone (task T15, the owner's «اي شي اسويه او ابنيه اقدر اسرعه يبني بنفس اللحظة بتكلفه اعلى»): a DESIGN
// awaiting the owner's approval (through his proxy), not built, not in phone.js. What the engine makes wait after the
// player decides, and money can hurry in the real world, finishes at once for a higher price: a facility being built
// (Balance.buildDays, 3 days), an order of water or feed on its way (Balance.deliveryDays, 1 day) and a camel bought
// on the truck (Balance.camelTruckDays, 1 day). Seven views at the owner's screen (956 x 440, the phone enlarged), in
// the phone's own screens (design/prototype3d/phone.js) with the rush drawn into them:
//   1 build        العزبة: the second pen being built, «استعجل» on its row with the price of finishing it now
//   2 build_sure   the same after the first tap: the button red, «أكّد», what it does said on the row (two taps: it
//                  cannot be undone, as الحراج's sale)
//   3 water        الوايت: the 6 t tanker on its way, «استعجل» (it comes now)
//   4 feed         العلف: the bags and bales on their way, one «استعجل» for the trip
//   5 truck        الحراج: a camel just bought, on the truck, «استعجل» (a second driver, she comes today)
//   6 short        العزبة when the money does not cover the rush: the button off, why on its row (a rush is no
//                  necessity: never on the merchant's account, the owner's decisions 9 and 10)
//   7 bank         البنك's October opened: the rush its own kind, «الاستعجال», each line what was hurried
// The games (seed 4242, 1 October 2026, the real clock, its first day): A, the second pen ordered (SAR 8,000 left);
// B, the cheapest camel in الحراج bought, a 6 t tanker and some feed ordered, then the pen ordered with what was left.
// Every figure is the engine's (the snapshot) except the rush's price, the PROPOSED rule, a game choice awaiting the
// proxy (docs/proposals/rush_and_calendar.md):
//   - a facility: half its price for the three days, less as it nears its end (price x 0.5 x days left / 3, to the
//     500): night work and a second crew at the overtime rate (Saudi Labour Law art. 107: the wage plus 50%);
//   - a water tanker: half its price again (a tanker sent out now, not on tomorrow's round);
//   - a feed order: SAR 150 for the trip, whatever it carries (a truck sent today; the 6 t tanker adverts' SAR 100 to
//     150 are a trip's price);
//   - a camel on the truck: half the trucking again, to the riyal's five (a second driver: a lorry driver's day is nine
//     hours, the transport authority's rule as reported in 2017, and the longest trip is about 17 hours).
// The bank's rush row is drawn (the engine has no rush); its other rows are the engine's.
// To draw again: build the prototype (THREE_DIR=<three@0.170.0 package> python3 tool/proto_app/assemble.py), serve
// tool/proto_app/assets/web on a port (PORT, 8765 by default), and run `NODE_PATH=$(npm root -g) node
// design/ui/phone_rush.cjs` from the repository's root; it writes mock_rush_<n>_<name>.png in OUT (default .) and
// design/ui/phone_rush.jpg. AUDIT=<audit.js> runs the layout audit on each view and writes the texts to rush_texts.txt.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const PORT = process.env.PORT || 8765;
const OUT = process.env.OUT || '.';
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };

// the proposed prices (a game choice, awaiting the proxy)
const RULE = `window.RUSH = {
  build: (price, left) => Math.round(price * 0.5 * left / 3 / 500) * 500,
  water: (price) => Math.round(price * 0.5),
  feed: () => 150,
  truck: (transport) => Math.round(transport * 0.5 / 5) * 5,
};`;

const CSS = `
  .row.ord2 { grid-template-columns: 36px 1fr auto; }
  .way .row.ord2 { grid-template-columns: 36px 1fr auto; }
  .row .act .btn.sm { height: 34px; padding-inline: 12px; font-size: 12.5px; }
  .sbar .clk { font-size: 0; } .sbar .clk::after { content: "9:41"; font-size: 14px; }
`;

async function open(b) {
  const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.marahEngine || window.marahEngineError, null, { timeout: 600000 });
  await p.evaluate(RULE);
  return { ctx, p };
}
// a new game on seed 4242, at its first day
const fresh = async (p) => p.evaluate(async () => {
  const e = window.marahEngine;
  await e.startOver({ seed: 4242 });
  for (let i = 0; i < 200 && !(e.snapshot && e.snapshot.date === '2026-10-01' && e.snapshot.herd.total === 2); i++) await new Promise((r) => setTimeout(r, 50));
});
const settle = (p) => p.evaluate(() => new Promise((r) => setTimeout(r, 900)));
async function phoneUp(p) {
  await p.evaluate(() => { window.requestAnimationFrame = () => 0; });
  await p.evaluate(() => {
    window.R = () => [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone')).shadowRoot;
    window.__phone.toggle(); window.__phone.enlarge();
  });
  await p.waitForTimeout(500);
}
// opens an app from the home screen (رجوع first if an app is open)
async function go(p, app) {
  await p.evaluate((app) => {
    const back = R().querySelector('.scr .back'); if (back) back.click();
    R().querySelector(`.scr .app[data-go="${app}"]`).click();
  }, app);
  await p.waitForTimeout(300);
  await p.evaluate(() => { R().activeElement?.blur(); });      // (a click's focus ring is not what a tap leaves)
  await p.waitForTimeout(500);
}

const files = [];
let n = 0;
async function shoot(p, name) {
  n++;
  await p.evaluate((css) => { const scr = R().querySelector('.scr'); const st = document.createElement('style'); st.textContent = css; scr.appendChild(st); }, CSS);
  await p.waitForTimeout(300);
  const file = path.join(OUT, `mock_rush_${n}_${name}.png`);
  const box = await p.evaluate(() => { const r = R().querySelector('.dev').getBoundingClientRect(); return { x: r.x, width: r.width }; });
  await p.screenshot({ path: file, timeout: 600000, clip: { x: Math.max(0, box.x - 4), y: 0, width: box.width + 8, height: 440 } });
  files.push(file);
  if (process.env.AUDIT) {
    await p.addScriptTag({ path: process.env.AUDIT });
    const a = await p.evaluate(() => window.__audit());
    console.log(name, 'audit', JSON.stringify({ clipped: a.clipped, ellipsis: a.ellipsis, outside: a.outside, split: a.split, scroll: a.scroll }));
    fs.appendFileSync(path.join(OUT, 'rush_texts.txt'), `== ${name}\n` + a.texts.filter((t) => !t.includes('{')).join('\n') + '\n');
  }
}

// in the page: the phone's helpers for the rush's rows
const HELP = `
  window.n0 = (v) => Math.round(v).toLocaleString('en-US');
  window.nb = (s) => s.replace(/(\\d) (?=[؀-ۿ])/g, '$1\u00a0').replace(/([؀-ۿ]) (?=\\d)/g, '$1\u00a0');
  window.DAYS = (n) => (n === 1 ? 'يوم واحد' : n === 2 ? 'يومين' : n <= 10 ? n + ' أيام' : n + ' يوم');
  window.rushBtn = (sure, can, label) => '<span class="act"><button class="btn sm ' + (!can ? '' : sure ? 'sure' : 'ghost') + '" aria-label="' + label + '"' + (can ? '' : ' disabled') + '>' + (sure ? 'أكّد' : 'استعجل') + '</button></span>';
`;

(async () => {
  if (process.env.AUDIT) fs.writeFileSync(path.join(OUT, 'rush_texts.txt'), '');
  const b = await chromium.launch(LAUNCH);

  // ---------------------------------------------------------------- game A: the second pen ordered
  {
    const { ctx, p } = await open(b);
    await fresh(p);
    await p.evaluate(async () => { await window.marahEngine.dispatch({ type: 'buildFacility', facility: 'pen' }); });
    await settle(p);
    await phoneUp(p);
    await p.evaluate(HELP);
    await go(p, 'build');
    // the pen's row being built: «استعجل» and the price of finishing it now (the engine's own row, the rush added)
    const drawBuild = (sure) => p.evaluate((sure) => {
      const S = window.marahEngine.snapshot, pen = S.farm.facilities.find((x) => x.facility === 'pen');
      const left = Math.round((Date.parse((pen.doneOns[0] ?? pen.doneOn) + 'T00:00:00Z') - Date.parse(S.date + 'T00:00:00Z')) / 864e5), fee = RUSH.build(pen.price, left);
      const row = [...R().querySelectorAll('.scr .row')].find((r) => /ينبني/.test(r.textContent));
      const name = row.querySelector('b').textContent;
      row.classList.add('ord2');
      row.querySelector('small').innerHTML = nb(sure ? `يخلص الحين، وتدفع ${n0(fee)} ريال زيادة` : `يخلص بعد ${DAYS(left)} · الحين بـ ${n0(fee)} ريال زيادة`);
      row.querySelector('b').insertAdjacentHTML('afterend', rushBtn(sure, S.cash >= fee, sure ? `أكّد استعجال ${name} بـ ${n0(fee)} ريال` : `استعجل ${name}`));
      const note = [...R().querySelectorAll('.scr .note')].pop();
      note.innerHTML = nb('اللي تبنيه يخلص بعد 3 أيام ويطلع مكانه في العزبة. ولو استعجلته يخلص الحين: تدفع نص سعره لو باقي له 3 أيام، وأقل كل ما قرب يخلص.');
      return { fee, left, cash: S.cash };
    }, sure);
    console.log('A build', JSON.stringify(await drawBuild(false)));
    await shoot(p, 'build');
    await go(p, 'build');
    await drawBuild(true);
    await shoot(p, 'build_sure');

    // ---- البنك: October opened, the rush its own kind (drawn), the rest the engine's
    await go(p, 'bank');
    await p.evaluate(() => { const m = R().querySelector('.scr [data-go="bankMonth"]'); if (m) m.click(); });
    await p.waitForTimeout(500);
    await p.evaluate(() => { R().activeElement?.blur(); });
    const bank = await p.evaluate(() => {
      const S = window.marahEngine.snapshot, pen = S.farm.facilities.find((x) => x.facility === 'pen');
      const fee = RUSH.build(pen.price, 3);
      const rows = [...R().querySelectorAll('.scr .row')];
      const build = rows.find((r) => /البناء|بناء/.test(r.textContent)) || rows[rows.length - 1];
      const rush = build.cloneNode(true);
      rush.querySelector('b').textContent = 'الاستعجال';
      rush.querySelector('small').innerHTML = nb('شبك ثاني، خلص بيومه');
      const amt = rush.querySelector('.amt'); if (amt) amt.textContent = `−${n0(fee)}`;
      build.after(rush);
      // the month's net and what went out, with the rush in them (the month had no other money: the start's milk is
      // sold from the next day)
      const top = R().querySelector('.scr .balance');
      const spent = 12000 + fee;
      top.innerHTML = top.innerHTML.replace(/12,000/g, n0(spent));
      // the month's spent and net with the rush in them
      const texts = rows.map((r) => r.textContent.replace(/\s+/g, ' ').trim());
      return { texts, fee };
    });
    console.log('A bank rows', JSON.stringify(bank));
    await shoot(p, 'bank');
    await ctx.close();
  }

  // ---------------------------------------------------------------- game B: a camel, a tanker and feed, then the pen
  {
    const { ctx, p } = await open(b);
    await fresh(p);
    const B = await p.evaluate(async () => {
      const e = window.marahEngine, S0 = e.snapshot;
      const l = S0.market.slice().sort((a, b) => a.askPrice - b.askPrice)[0];
      const buy = await e.dispatch({ type: 'buyListing', listing: l.id });
      const water = await e.dispatch({ type: 'orderSupply', supply: 'water', units: 1, tanker: 'small' });
      const barley = await e.dispatch({ type: 'orderSupply', supply: 'barley', units: 4 });
      const alfalfa = await e.dispatch({ type: 'orderSupply', supply: 'alfalfa', units: 6 });
      return { listing: l, ok: [buy.ok, water.ok, barley.ok, alfalfa.ok] };
    });
    await settle(p);
    console.log('B', JSON.stringify(B.ok), 'cash', await p.evaluate(() => window.marahEngine.snapshot.cash));
    await phoneUp(p);
    await p.evaluate(HELP);

    // ---- الوايت: the tanker on its way, the rush on its row
    await go(p, 'water');
    console.log('water', JSON.stringify(await p.evaluate(() => {
      const S = window.marahEngine.snapshot, w = S.farm.supplies.find((x) => x.supply === 'water'), t = S.farm.tankers.find((x) => x.tanker === 'small');
      const fee = RUSH.water(t.price), room = S.farm.tankL - w.amount;
      const note = [...R().querySelectorAll('.scr .note')].pop();
      const truck = R().querySelector('.scr .lead svg') ? '' : '';
      note.outerHTML = `<div class="sec">بالطريق</div><div class="group way"><div class="row ord2"><span class="lead"><svg class="i" viewBox="0 0 24 24"><path d="M2.5 6.5h11v9h-11z"/><path d="M13.5 9.5h4l3 3.5v2.5h-7z"/><circle cx="6.5" cy="17" r="1.8"/><circle cx="16.5" cy="17" r="1.8"/></svg></span><b>وايت ${Math.round(t.litres / 1000)} طن</b>${rushBtn(false, S.cash >= fee, 'استعجل الوايت')}<small>${nb(`يوصل بكرة · الحين بـ ${n0(fee)} ريال زيادة`)}</small></div></div>
        <div class="note">${nb(`يعبّي الخزان ${n0(Math.min(room, t.litres))} لتر والباقي يرجع. ولو استعجلته يطلع لك الحين بنص سعره زيادة.`)}</div>`;
      return { fee, room, cash: S.cash, w };
    })));
    await shoot(p, 'water');

    // ---- العلف: the bags and bales on their way, one rush for the trip
    await go(p, 'feed');
    console.log('feed', JSON.stringify(await p.evaluate(() => {
      const S = window.marahEngine.snapshot, fee = RUSH.feed();
      const way = R().querySelector('.scr .group.way');
      if (!way) return { way: false };
      way.insertAdjacentHTML('beforeend', `<div class="row ord2"><span class="lead"><svg class="i" viewBox="0 0 24 24"><path d="M12 3.5v4M12 16.5v4M3.5 12h4M16.5 12h4"/><circle cx="12" cy="12" r="4.5"/></svg></span><b>استعجل العلف</b>${rushBtn(false, S.cash >= fee, 'استعجل العلف')}<small>${nb(`يوصل الحين كله بـ ${n0(fee)} ريال زيادة`)}</small></div>`);
      way.querySelectorAll('.row small').forEach((s) => { s.innerHTML = nb(s.innerHTML); });
      way.insertAdjacentHTML('afterend', `<div class="note">${nb(`الاستعجال مشوار وحده بـ ${n0(fee)} ريال، يجيب اللي بالطريق كله.`)}</div>`);
      const bd = R().querySelector('.scr .body'); bd.scrollTop = bd.scrollHeight;      // (scrolled to what is on its way)
      return { fee, cash: S.cash };
    })));
    await shoot(p, 'feed');

    // ---- الحراج: the camel just bought, on the truck (the phone's own answer card after a purchase, the rush under it)
    await go(p, 'haraj');
    console.log('truck', JSON.stringify(await p.evaluate((l) => {
      const S = window.marahEngine.snapshot, fee = RUSH.truck(l.transport), c = l.camel, she = c.sex === 'female';
      const tabs = R().querySelector('.scr .seg');
      const card = `<div class="msgc good"><span class="lead"><svg class="i" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span><b>اشتريت ${c.name} بـ ${n0(l.askPrice)} ريال</b><small>${nb(`${she ? 'توصل' : 'يوصل'} عزبتك بكرة، والنقل ${n0(l.transport)} ريال.`)}</small></div>
        <div class="group way"><div class="row ord2"><span class="lead"><svg class="i" viewBox="0 0 24 24"><path d="M2.5 6.5h11v9h-11z"/><path d="M13.5 9.5h4l3 3.5v2.5h-7z"/><circle cx="6.5" cy="17" r="1.8"/><circle cx="16.5" cy="17" r="1.8"/></svg></span><b>${c.name} على اللوري</b>${rushBtn(false, S.cash >= fee, `استعجل ${c.name}`)}<small>${nb(`${she ? 'توصل' : 'يوصل'} اليوم بسواق ثاني، بـ ${n0(fee)} ريال زيادة`)}</small></div></div>`;
      tabs.insertAdjacentHTML('afterend', card);
      // the market's list stays under it as the phone has it; trimmed to what the screen shows
      return { fee, transport: l.transport, cash: S.cash, name: c.name };
    }, B.listing)));
    await shoot(p, 'truck');

    // ---- the money does not cover it: the pen ordered with what was left (B), its rush off
    await p.evaluate(async () => { await window.marahEngine.dispatch({ type: 'buildFacility', facility: 'pen' }); });
    await settle(p);
    await go(p, 'build');
    console.log('short', JSON.stringify(await p.evaluate(() => {
      const S = window.marahEngine.snapshot, pen = S.farm.facilities.find((x) => x.facility === 'pen');
      const left = Math.round((Date.parse((pen.doneOns[0] ?? pen.doneOn) + 'T00:00:00Z') - Date.parse(S.date + 'T00:00:00Z')) / 864e5), fee = RUSH.build(pen.price, left);
      const row = [...R().querySelectorAll('.scr .row')].find((r) => /ينبني/.test(r.textContent));
      const name = row.querySelector('b').textContent;
      row.classList.add('ord2');
      row.querySelector('small').innerHTML = nb(`يخلص بعد ${DAYS(left)} · الاستعجال ${n0(fee)} ريال، ورصيدك ${n0(S.cash)}`);
      row.querySelector('b').insertAdjacentHTML('afterend', rushBtn(false, S.cash >= fee, `استعجل ${name}، رصيدك ما يكفي`));
      R().querySelector('.scr .sec').insertAdjacentHTML('beforebegin', `<div class="note" style="margin-top:0">${nb('الاستعجال من رصيدك بس، ما ينكتب على حساب التاجر: الحساب للعلف والماء والبيطري.')}</div>`);
      return { fee, cash: S.cash };
    })));
    await shoot(p, 'short');
    await ctx.close();
  }

  await b.close();
  execFileSync('convert', [...files, '-background', '#2a2119', '-splice', '6x0', '+append', '-chop', '6x0', '-quality', '86', path.join(__dirname, 'phone_rush.jpg')]);
})();
