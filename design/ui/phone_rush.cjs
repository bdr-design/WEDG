// Rushing in the phone (task T15, the owner's «اي شي اسويه او ابنيه اقدر اسرعه يبني بنفس اللحظة بتكلفه اعلى»): a DESIGN
// awaiting the owner's approval (his proxy's answers, batches 4 and 4b of docs/agents/proxy_decisions.md, are
// provisional), not built, not in phone.js. Revised after the design's review. What money can hurry in the real world
// finishes now for more: a facility being built (Balance.buildDays, 3 days), a camel bought on the truck
// (Balance.camelTruckDays, 1 day), and an order of water or feed, ONLY on a day the herd went short (then the rushed
// delivery makes good today's loss and the day no longer counts dry or hungry; on other days the ordinary delivery is
// in time and the row says so). Offered on what is under way («استعجل») and at the moment of ordering («أو ابنه الحين
// بـ …»; where that line sits is the owner's eye: drawn here under the row's own line). Ten views at the owner's
// screen (956 x 440, the phone enlarged), in the phone's own screens (design/prototype3d/phone.js) with the rush drawn
// in:
//   1 build         العزبة: the second pen being built, its approved line («ينبني، يخلص بعد 3 أيام») and the rush
//   2 build_sure    the first tap: «أكّد» red, what it does on the row (two taps, as الحراج's sale)
//   3 build_order   at ordering: «أو ابنه الحين بـ …» beside «ابنه», where the money covers it
//   4 water_short   a short day (the herd went without enough water at dawn): the tanker on its way, its rush makes
//                   today good
//   5 water_ok      an ordinary day: no rush offered, the honest line
//   6 feed_short    a short day: at ordering, «أو اطلبها توصل الحين …»
//   7 feed_ok       an ordinary day: the order on its way, the honest line
//   8 truck         الحراج: a camel just bought, on the truck, «توصل الحين» priced by the part of the game's day left
//   9 short         the money does not cover the rush (cash only, never the merchant's account)
//  10 bank          البنك's October opened: «الاستعجال» its own kind
// The games (seed 4242, Qassim, وضح): A, its first day at the real clock, the second pen ordered; B, its first day, the
// cheapest camel bought, a 6 t tanker and some feed ordered, then the pen with what was left; C, a fresh first day
// (ordering); and the save short.json from tool/proto_engine/bin/t15_design_saves.dart (left alone to 1 November, the
// first day the herd went short of water and feed). Every figure is the engine's except the rush's prices, PROPOSED
// game choices (docs/proposals/rush_and_calendar.md, section 2):
//   - a facility: price x 0.5 x days left / 3, to the 500 (at ordering: the whole half);
//   - a water tanker on a short day: half its price again; a feed order on a short day: half the order again, at most
//     SAR 300;
//   - a camel on the truck: trucking x 0.5 x max(0.2, minutes of the game's day left / 1440), to the five.
// The bank's rush row is drawn (the engine has no rush); its other rows are the engine's.
// To draw again: build the prototype (THREE_DIR=<three@0.170.0 package> python3 tool/proto_app/assemble.py), serve
// tool/proto_app/assets/web on a free port (PORT, 8765 by default), write the saves (in tool/proto_engine: `dart run
// bin/t15_design_saves.dart <folder>`), and run `SAVES=<folder> NODE_PATH=$(npm root -g) node design/ui/phone_rush.cjs`
// from the repository's root; it writes mock_rush_<n>_<name>.png in OUT (default .) and design/ui/phone_rush.jpg.
// AUDIT=<audit.js> runs the layout audit on each view and writes the texts to rush_texts.txt.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const PORT = process.env.PORT || 8765;
const OUT = process.env.OUT || '.';
const SAVES = process.env.SAVES || '.';
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };

// the proposed prices (game choices)
const RULE = `window.RUSH = {
  build: (price, left) => Math.round(price * 0.5 * left / 3 / 500) * 500,
  water: (price) => Math.round(price * 0.5),
  feed: (order) => Math.min(300, Math.round(order * 0.5)),
  truck: (transport, minute) => Math.round(transport * 0.5 * Math.max(0.2, (1440 - minute) / 1440) / 5) * 5,
};`;

const CSS = `
  .row.ord2 { grid-template-columns: 36px 1fr auto; }
  .way .row.ord2 { grid-template-columns: 36px 1fr auto; }
  .row .act .btn.sm { height: 34px; padding-inline: 12px; font-size: 12.5px; }
  .row small.now, .order small.now, .note.now { color: var(--acc); font-weight: 700; }
  .row small.rush { grid-column: 2; }
  .sbar .clk { font-size: 0; } .sbar .clk::after { content: "9:41"; font-size: 14px; }
`;

async function open(b, save) {
  const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  if (save) {
    // the save made by the engine (t15_design_saves.dart), kept by the page before the engine starts
    const v = fs.readFileSync(save, 'utf8');
    await p.addInitScript(([v]) => { if (!sessionStorage.getItem('seeded')) { localStorage.clear(); localStorage.setItem('marah.proto.marah.save', v); sessionStorage.setItem('seeded', '1'); } }, [v]);
  }
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.marahEngine || window.marahEngineError, null, { timeout: 600000 });
  await p.evaluate(RULE);
  if (!save) {
    await p.evaluate(async () => {
      const e = window.marahEngine;
      await e.startOver({ seed: 4242 });
      for (let i = 0; i < 200 && !(e.snapshot && e.snapshot.date === '2026-10-01' && e.snapshot.herd.total === 2); i++) await new Promise((r) => setTimeout(r, 50));
    });
  } else {
    await p.waitForFunction(() => window.marahEngine.snapshot, null, { timeout: 600000 });
  }
  return { ctx, p };
}
const settle = (p) => p.evaluate(() => new Promise((r) => setTimeout(r, 900)));
async function phoneUp(p) {
  await p.evaluate(() => { window.requestAnimationFrame = () => 0; });
  await p.evaluate(() => {
    window.R = () => [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone')).shadowRoot;
    window.__phone.toggle(); window.__phone.enlarge();
  });
  await p.waitForTimeout(500);
  await p.evaluate(HELP);
}
// opens an app from the home screen (رجوع first if an app is open)
async function go(p, app) {
  await p.evaluate((app) => {
    const back = R().querySelector('.scr .back'); if (back) back.click();
    R().querySelector(`.scr .app[data-go="${app}"]`).click();
  }, app);
  await p.waitForTimeout(400);
  await p.evaluate(() => { R().activeElement?.blur(); });      // (a click's focus ring is not what a tap leaves)
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
  window.nb = (s) => s.replace(/(\\d) (?=[؀-ۿ])/g, '$1\\u00a0').replace(/([؀-ۿ]) (?=\\d)/g, '$1\\u00a0');
  window.DAYS = (n) => (n === 1 ? 'يوم واحد' : n === 2 ? 'يومين' : n <= 10 ? n + ' أيام' : n + ' يوم');
  window.rushBtn = (sure, can, label) => '<span class="act"><button class="btn sm ' + (!can ? '' : sure ? 'sure' : 'ghost') + '" aria-label="' + label + '"' + (can ? '' : ' disabled') + '>' + (sure ? 'أكّد' : 'استعجل') + '</button></span>';
  window.TRUCK = '<svg class="i" viewBox="0 0 24 24"><path d="M2.5 6.5h11v9h-11z"/><path d="M13.5 9.5h4l3 3.5v2.5h-7z"/><circle cx="6.5" cy="17" r="1.8"/><circle cx="16.5" cy="17" r="1.8"/></svg>';
  window.daysTo = (S, iso) => Math.round((Date.parse(iso + 'T00:00:00Z') - Date.parse(S.date + 'T00:00:00Z')) / 864e5);
  // the game's minute of the day from the save's own clock (RealTimeClock.minuteOfDay)
  window.minuteNow = () => { const s = JSON.parse(localStorage.getItem('marah.proto.marah.save') || '{}'); const L = Math.floor(864e8 / 7) / 1000; const a = (s.startedAtUtcMs || Date.now()) + (s.clockShiftMs || 0); return Math.floor((((Date.now() - a) % L) + L) % L * 1440 / L); };
`;

(async () => {
  if (process.env.AUDIT) fs.writeFileSync(path.join(OUT, 'rush_texts.txt'), '');
  const b = await chromium.launch(LAUNCH);

  // ---------------------------------------------------------------- game A: the second pen ordered
  {
    const { ctx, p } = await open(b);
    await p.evaluate(async () => { await window.marahEngine.dispatch({ type: 'buildFacility', facility: 'pen' }); });
    await settle(p);
    await phoneUp(p);
    await go(p, 'build');
    // the pen's row being built: its approved line kept, the rush after it
    const drawBuild = (sure) => p.evaluate((sure) => {
      const S = window.marahEngine.snapshot, pen = S.farm.facilities.find((x) => x.facility === 'pen');
      const left = daysTo(S, pen.doneOns[0] ?? pen.doneOn), fee = RUSH.build(pen.price, left);
      const row = [...R().querySelectorAll('.scr .row')].find((r) => /ينبني/.test(r.textContent));
      const name = row.querySelector('b').textContent;
      row.classList.add('ord2');
      row.querySelector('small').insertAdjacentHTML('afterend', `<small class="rush${sure ? ' now' : ''}">${nb(sure ? `يخلص الحين، وتدفع ${n0(fee)} ريال زيادة` : `الحين بـ ${n0(fee)} ريال زيادة`)}</small>`);
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

    // البنك: October opened, the rush its own kind (drawn), the rest the engine's
    await go(p, 'bank');
    await p.evaluate(() => { const m = R().querySelector('.scr [data-go="bankMonth"]'); if (m) m.click(); });
    await p.waitForTimeout(500);
    await p.evaluate(() => { R().activeElement?.blur(); });
    console.log('A bank', JSON.stringify(await p.evaluate(() => {
      const S = window.marahEngine.snapshot, pen = S.farm.facilities.find((x) => x.facility === 'pen');
      const fee = RUSH.build(pen.price, 3);
      const rows = [...R().querySelectorAll('.scr .row')];
      const build = rows.find((r) => /البناء/.test(r.textContent)) || rows[rows.length - 1];
      const rush = build.cloneNode(true);
      rush.querySelector('b').textContent = 'الاستعجال';
      rush.querySelector('small').innerHTML = nb('شبك ثاني، خلص بيومه');
      const amt = rush.querySelector('.amt'); if (amt) amt.textContent = `−${n0(fee)}`;
      build.after(rush);
      const top = R().querySelector('.scr .balance');
      top.innerHTML = top.innerHTML.replace(/12,000/g, n0(12000 + fee));
      return { fee, rows: rows.map((r) => r.textContent.replace(/\s+/g, ' ').trim()) };
    })));
    await shoot(p, 'bank');
    await ctx.close();
  }

  // ---------------------------------------------------------------- game C: a fresh first day, at ordering
  {
    const { ctx, p } = await open(b);
    await phoneUp(p);
    await go(p, 'build');
    console.log('C order', JSON.stringify(await p.evaluate(() => {
      const S = window.marahEngine.snapshot, out = [];
      for (const r of R().querySelectorAll('.scr .row')) {
        const btn = r.querySelector('button[data-act="build"]');
        if (!btn || btn.disabled) continue;
        const x = S.farm.facilities.find((f) => f.facility === btn.dataset.f), now = x.price + RUSH.build(x.price, 3);
        if (S.cash < now) continue;      // (only where the money covers it)
        r.querySelector('small').insertAdjacentHTML('afterend', `<small class="rush now" role="button" tabindex="0">${nb(`أو ابنه الحين بـ ${n0(now)} ريال`)}</small>`);
        out.push([x.facility, now]);
      }
      const note = [...R().querySelectorAll('.scr .note')].pop();
      note.innerHTML = nb('اللي تبنيه يخلص بعد 3 أيام ويطلع مكانه في العزبة، ولو تبيه الحين تدفع نص سعره زيادة.');
      return out;
    })));
    await shoot(p, 'build_order');
    await ctx.close();
  }

  // ---------------------------------------------------------------- the short day (the engine's save, 1 November)
  {
    const { ctx, p } = await open(b, path.join(SAVES, 'short.json'));
    console.log('short day', JSON.stringify(await p.evaluate(() => { const S = window.marahEngine.snapshot; return { date: S.date, dry: S.farm.dryDays, short: S.farm.supplies.filter((x) => x.short).map((x) => x.supply), cash: S.cash }; })));
    // a 6 t tanker ordered the ordinary way (it would come tomorrow)
    await p.evaluate(async () => { await window.marahEngine.dispatch({ type: 'orderSupply', supply: 'water', units: 1, tanker: 'small' }); });
    await settle(p);
    await phoneUp(p);
    await go(p, 'water');
    console.log('water short', JSON.stringify(await p.evaluate(() => {
      const S = window.marahEngine.snapshot, t = S.farm.tankers.find((x) => x.tanker === 'small'), fee = RUSH.water(t.price);
      const note = [...R().querySelectorAll('.scr .note')].pop();
      note.outerHTML = `<div class="sec">بالطريق</div><div class="group way"><div class="row ord2"><span class="lead">${TRUCK}</span><b>وايت ${Math.round(t.litres / 1000)} طن</b>${rushBtn(false, S.cash >= fee, 'استعجل الوايت')}<small>${nb(`يوصل بكرة · الحين بـ ${n0(fee)} ريال زيادة`)}</small></div></div>
        <div class="note">${nb(`حلالك ما شرب كفايته اليوم. لو استعجلته يوصل الحين ويشربون، وما ينحسب اليوم عطش، وحالتهم ما تنزل اليوم.`)}</div>`;
      const bd = R().querySelector('.scr .body'); bd.scrollTop = bd.scrollHeight;
      return { fee, cash: S.cash };
    })));
    await shoot(p, 'water_short');

    // العلف on the short day, at ordering: the phone's own suggested order and its line «أو اطلبها توصل الحين»
    await go(p, 'feed');
    console.log('feed short', JSON.stringify(await p.evaluate(() => {
      const S = window.marahEngine.snapshot, o = R().querySelector('.scr .order');
      if (!o) return { order: false };
      const total = Number(o.querySelector('.t').textContent.replace(/[^\d]/g, '')), fee = RUSH.feed(total);
      o.insertAdjacentHTML('afterend', `<div class="note now" role="button" tabindex="0">${nb(`أو اطلبها توصل الحين بـ ${n0(fee)} ريال زيادة: يشبعون اليوم وما تنزل حالتهم`)}</div>`);
      const bd = R().querySelector('.scr .body'); bd.scrollTop = bd.scrollHeight;
      return { total, fee, cash: S.cash };
    })));
    await shoot(p, 'feed_short');
    await ctx.close();
  }

  // ---------------------------------------------------------------- game B: an ordinary day
  {
    const { ctx, p } = await open(b);
    const B = await p.evaluate(async () => {
      const e = window.marahEngine, S0 = e.snapshot;
      const l = S0.market.slice().sort((a, b) => a.askPrice - b.askPrice)[0];
      const ok = [];
      ok.push((await e.dispatch({ type: 'buyListing', listing: l.id })).ok);
      ok.push((await e.dispatch({ type: 'orderSupply', supply: 'water', units: 1, tanker: 'small' })).ok);
      ok.push((await e.dispatch({ type: 'orderSupply', supply: 'barley', units: 4 })).ok);
      ok.push((await e.dispatch({ type: 'orderSupply', supply: 'alfalfa', units: 6 })).ok);
      return { listing: l, ok };
    });
    await settle(p);
    console.log('B', JSON.stringify(B.ok));
    await phoneUp(p);

    await go(p, 'water');
    await p.evaluate(() => {
      const S = window.marahEngine.snapshot, t = S.farm.tankers.find((x) => x.tanker === 'small');
      const note = [...R().querySelectorAll('.scr .note')].pop();
      note.outerHTML = `<div class="sec">بالطريق</div><div class="group way"><div class="row"><span class="lead">${TRUCK}</span><b>وايت ${Math.round(t.litres / 1000)} طن</b><small>${nb('الطلبة العادية توصل قبل شرب حلالك بكرة')}</small></div></div>
        <div class="note">${nb('يعبّي الخزان والباقي يرجع. الاستعجال يطلع بس لو حلالك ما شرب كفايته اليوم.')}</div>`;
    });
    await shoot(p, 'water_ok');

    await go(p, 'feed');
    await p.evaluate(() => {
      const way = R().querySelector('.scr .group.way');
      way.querySelectorAll('.row small').forEach((s) => { s.innerHTML = nb(s.innerHTML.replace('يوصل بكرة', 'توصل قبل علفة حلالك بكرة')); });
      way.insertAdjacentHTML('afterend', `<div class="note">${nb('الاستعجال يطلع بس لو حلالك ما شبع اليوم.')}</div>`);
      const bd = R().querySelector('.scr .body'); bd.scrollTop = way.offsetTop - 80;
    });
    await shoot(p, 'feed_ok');

    // الحراج: the camel just bought, on the truck; the rush by the part of the game's day left
    await go(p, 'haraj');
    console.log('truck', JSON.stringify(await p.evaluate((l) => {
      const S = window.marahEngine.snapshot, m = minuteNow(), fee = RUSH.truck(l.transport, m), c = l.camel, she = c.sex === 'female';
      const tabs = R().querySelector('.scr .seg');
      tabs.insertAdjacentHTML('afterend', `<div class="msgc good"><span class="lead"><svg class="i" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span><b>اشتريت ${c.name} بـ ${n0(l.askPrice)} ريال</b><small>${nb(`${she ? 'توصل' : 'يوصل'} عزبتك بكرة، والنقل ${n0(l.transport)} ريال.`)}</small></div>
        <div class="group way"><div class="row ord2"><span class="lead">${TRUCK}</span><b>${c.name} على اللوري</b>${rushBtn(false, S.cash >= fee, `استعجل ${c.name}`)}<small>${nb(`${she ? 'توصل' : 'يوصل'} الحين بسواق ثاني، بـ ${n0(fee)} ريال زيادة`)}</small></div></div>
        <div class="note">${nb('كل ما مضى من اليوم يرخص الاستعجال، لأن الباقي على وصولها أقل.')}</div>`);
      return { fee, minute: m, transport: l.transport, cash: S.cash, name: c.name };
    }, B.listing)));
    await shoot(p, 'truck');

    // the money does not cover it: the pen ordered with what was left, its rush off
    await p.evaluate(async () => { await window.marahEngine.dispatch({ type: 'buildFacility', facility: 'pen' }); });
    await settle(p);
    await go(p, 'build');
    console.log('short cash', JSON.stringify(await p.evaluate(() => {
      const S = window.marahEngine.snapshot, pen = S.farm.facilities.find((x) => x.facility === 'pen');
      const left = daysTo(S, pen.doneOns[0] ?? pen.doneOn), fee = RUSH.build(pen.price, left);
      const row = [...R().querySelectorAll('.scr .row')].find((r) => /ينبني/.test(r.textContent));
      const name = row.querySelector('b').textContent;
      row.classList.add('ord2');
      row.querySelector('small').insertAdjacentHTML('afterend', `<small class="rush">${nb(`الاستعجال ${n0(fee)} ريال، ورصيدك ${n0(S.cash)}`)}</small>`);
      row.querySelector('b').insertAdjacentHTML('afterend', rushBtn(false, S.cash >= fee, `استعجل ${name}، رصيدك ما يكفي`));
      R().querySelector('.scr .sec').insertAdjacentHTML('beforebegin', `<div class="note" style="margin-top:0">${nb('الاستعجال من رصيدك بس، ما ينكتب على حساب التاجر: الحساب للعلف والماء والبيطري.')}</div>`);
      return { fee, cash: S.cash };
    })));
    await shoot(p, 'short');
    await ctx.close();
  }

  await b.close();
  // in the order of the header
  const order = ['build', 'build_sure', 'build_order', 'water_short', 'water_ok', 'feed_short', 'feed_ok', 'truck', 'short', 'bank'];
  const sorted = order.map((k) => files.find((f) => new RegExp(`_\\d+_${k}\\.png$`).test(f))).filter(Boolean);
  execFileSync('convert', [...sorted, '-background', '#2a2119', '-splice', '6x0', '+append', '-chop', '6x0', '-quality', '86', path.join(__dirname, 'phone_rush.jpg')]);
})();
