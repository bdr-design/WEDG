// التقويم, the calendar app (task T15, the owner's «بخطه مدروسه ومحكمه خليني اقدر انتقل بين المواسم بنفسي يعني تقويم وهكذا
// موجود اختياري»): a DESIGN awaiting the owner's approval (through his proxy), not built, not in phone.js. The year at a
// glance from the engine's own calendar, and the game moved forward to a day or a season the player picks, with a
// card that says what the stretch needs before he goes, stops that hand the game back when something needs him, and
// what happened at the end. Nine views at the owner's screen (956 x 440, the phone enlarged), in the phone's CSS and
// pieces (design/prototype3d/phone.js):
//   1 home      the home screen with the apps approved or being built (the six, المزاين and المحادثات from wt/t10)
//               and التقويم, the ninth
//   2 year      the year: twelve months as strips, from this month (past days pale, today marked), with the breeding
//               season, each festival's registration and its days, the player's own dated things (a calving, the end
//               of a milking)
//   3 year_end  the year scrolled: what is coming, by its day, each a row to pick
//   4 picked    a season picked (المربعانية, 7 December): its month, the day ringed, what is on it, «امشِ لين»
//   5 card      before going: will the water and the feed last the stretch (the days each lasts against the days
//               asked), filled before leaving with the phone's own orders, and what falls due on the way
//   6 card_end  the card scrolled: what stops the jump, the go button (two taps), forward only
//   7 going     the jump under way: the day it has reached, the days of the stretch, what has come in, «وقّف هنا»
//   8 stopped   the jump handed back early: why (the first stop the engine's events gave), what to do, «كمّل»
//   9 summary   what happened over the stretch, by the engine's events and ledger
// The games (seed 4242, 1 October 2026): one at the real clock, its first day, where the screens are drawn; and one
// on a fast clock (a game day in about 0.6 s) that does what the card offers (fills the tank and the feed shade on
// the first day) and then runs on untouched to the target, held at the first day that one of the design's stops
// comes in its events: that day's snapshot gives the going (half-way), stopped and summary views. Every figure is the
// engine's (snapshot, events, ledger) except: the Najdi seasons' days (phone.js's table, copied), the year's own dated
// things the engine has (a calving's due day, a milking's end) worked out from the snapshot as phone.js does, and the
// days the stores last, reckoned from today's need (the card says «تقريبًا»: the herd's need moves with the season
// and its calves, and the card never runs the future to tell it: that would tell an illness before it came).
// What is a proposal (the calendar is not built): the stops, the card's words, the app. The hunting season is left
// out on purpose (not built; the year's strips have room for its band).
// To draw again: build the prototype (THREE_DIR=<three@0.170.0 package> python3 tool/proto_app/assemble.py), serve
// tool/proto_app/assets/web on a port (PORT, 8765 by default), and run `NODE_PATH=$(npm root -g) node
// design/ui/phone_calendar.cjs` from the repository's root; it writes mock_calendar_<n>_<name>.png in OUT (default .)
// and design/ui/phone_calendar.jpg. AUDIT=<audit.js> runs the layout audit on each view and writes the texts to
// calendar_texts.txt.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const PORT = process.env.PORT || 8765;
const OUT = process.env.OUT || '.';
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };
const TARGET = '2026-12-07';      // the season picked in the views: المربعانية's first day

const CSS = `
  .sbar .clk { font-size: 0; } .sbar .clk::after { content: "9:41"; font-size: 14px; }
  .yr { background: var(--card); border-radius: 16px; padding: 10px 12px 8px; display: flex; flex-direction: column; gap: 5px; }
  .yr .m { display: grid; grid-template-columns: 50px 1fr; align-items: center; column-gap: 8px; height: 17px; }
  .yr .m > span { font-size: 11px; font-weight: 600; color: var(--ink2); }
  .yr .m > span.now { color: var(--ink); font-weight: 700; }
  .yr .t { position: relative; height: 12px; border-radius: 3px; background: #ececf0; overflow: hidden; }
  .yr .t i { position: absolute; top: 0; bottom: 0; }
  .yr .t i.past { background: #f7f7f9; }
  .yr .t i.brd { top: auto; height: 3px; background: #57b88a; }
  .yr .t i.reg { background: #f6e3b8; }
  .yr .t i.fest { background: #d9a033; top: 2px; bottom: 2px; border-radius: 2px; }
  .yr .t i.me { width: 6px; height: 6px; top: 3px; border-radius: 3px; background: var(--red); margin-right: -3px; }
  .yr .t i.milk { background: #2f7fcf; }
  .yr .t i.today { width: 2px; background: var(--ink); margin-right: -1px; top: -1px; bottom: -1px; }
  .key { display: flex; flex-wrap: wrap; gap: 4px 12px; font-size: 11px; color: var(--ink2); padding-inline: 4px; margin-top: -4px; }
  .key span { display: inline-flex; align-items: center; gap: 4px; white-space: nowrap; }
  .key i { display: inline-block; width: 12px; height: 8px; border-radius: 2px; }
  .row.pick { grid-template-columns: 36px 1fr auto; }
  .row .chev { grid-row: span 2; color: #c4c4c9; }
  .row .chev svg { width: 16px; height: 16px; }
  .row .lead.fest { background: #fbefd2; color: #a8730c; }
  .row .lead.me { background: #fde6e4; color: var(--red); }
  .row .lead.milk { background: #e6eef8; color: #2f7fcf; }
  .row .lead.brd { background: var(--acc-soft); color: var(--acc); }
  .row .lead.sea { background: #f1f1f4; color: #55555b; }
  .row .qty.bad { color: var(--red); font: 700 12.5px/1 "IBM Plex Sans Arabic", sans-serif; }
  .row .qty.ok { color: var(--acc); font: 600 12.5px/1 "IBM Plex Sans Arabic", sans-serif; }
  .cal { background: var(--card); border-radius: 16px; padding: 10px 10px 8px; display: grid; grid-template-columns: repeat(7, 1fr); row-gap: 4px; text-align: center; }
  .cal .wd { font-size: 10.5px; font-weight: 600; color: var(--ink2); }
  .cal .d { height: 30px; display: grid; place-items: center; font: 600 13px/1 "Alexandria", sans-serif; border-radius: 9px; position: relative; }
  .cal .d.fest { background: #fbefd2; color: #7a530a; }
  .cal .d.sel { background: var(--acc); color: #fff; }
  .cal .d.brd::after { content: ""; position: absolute; bottom: 3px; left: 50%; width: 4px; height: 4px; margin-left: -2px; border-radius: 2px; background: #57b88a; }
  .cal .d.sel::after { background: #fff; }
  .span { background: var(--card); border-radius: 16px; padding: 10px 12px; display: flex; flex-direction: column; gap: 2px; }
  .span b { font: 700 15px/1.3 "Alexandria", sans-serif; }
  .span small { font-size: 12px; color: var(--ink2); }
  .stops { font-size: 12px; line-height: 1.55; background: var(--card); border-radius: 16px; padding: 10px 12px; color: var(--ink); }
  .row .act .btn.sm { height: 34px; padding-inline: 12px; font-size: 12.5px; }
  .row.two2 { grid-template-columns: 36px 1fr auto; }
  .row.two { grid-template-columns: 36px 1fr; }
`;

async function open(b, fast) {
  const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  if (fast) {
    await p.route('**/index.html', async (route) => {
      const r = await route.fetch();
      route.fulfill({ response: r, body: (await r.text()).replace('startEngine({ onSnapshot:', 'startEngine({ timeScale: 20000, onSnapshot:') });
    });
  }
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.marahEngine || window.marahEngineError, null, { timeout: 600000 });
  await p.evaluate(async () => {
    const e = window.marahEngine;
    await e.startOver({ seed: 4242 });
    for (let i = 0; i < 200 && !(e.snapshot && e.snapshot.date === '2026-10-01' && e.snapshot.herd.total === 2); i++) await new Promise((r) => setTimeout(r, 50));
  });
  return { ctx, p };
}

// the orders that fill the tank and the feed shade (what the card's «عبّه» buttons send): the tanker that fits, and
// bags and bales in the ration's own mix up to the shade's room (the engine refuses what does not fit)
const FILL = `window.__fill = (S) => {
  const f = S.farm, sup = (k) => f.supplies.find((x) => x.supply === k);
  const w = sup('water'), b = sup('barley'), a = sup('alfalfa');
  const tanker = f.tankers.filter((t) => t.room > 0).sort((x, y) => y.litres - x.litres)[0] || null;
  const room = f.storeKg - b.amount - a.amount, share = b.need / (b.need + a.need);
  const wantB = Math.max(0, f.storeKg * share - b.amount), wantA = Math.max(0, f.storeKg * (1 - share) - a.amount);
  let bags = Math.floor(wantB / b.unitSize), bales = Math.floor(wantA / a.unitSize);
  while (bags * b.unitSize + bales * a.unitSize > room && bales > 0) bales--;
  const litres = tanker ? Math.min(f.tankL, w.amount + tanker.litres) : w.amount;
  return {
    tanker, bags, bales,
    cost: (tanker ? tanker.price : 0) + bags * b.unitPrice + bales * a.unitPrice,
    feedCost: bags * b.unitPrice + bales * a.unitPrice,
    water: Math.floor(litres / w.need),
    barley: Math.floor((b.amount + bags * b.unitSize) / b.need),
    alfalfa: Math.floor((a.amount + bales * a.unitSize) / a.need),
  };
};`;

(async () => {
  const b = await chromium.launch(LAUNCH);

  // ---------------------------------------------------------------- the fast game: filled on day one, then untouched
  // (CACHE=<file>: the fast game's result kept between drawings, as it takes minutes)
  const CACHE = process.env.CACHE;
  const run = CACHE && fs.existsSync(CACHE) ? JSON.parse(fs.readFileSync(CACHE, 'utf8')) : await (async () => {
    const { ctx, p } = await open(b, true);
    await p.evaluate(FILL);
    const out = await p.evaluate(async (TARGET) => {
      const e = window.marahEngine, S0 = e.snapshot, fill = window.__fill(S0);
      const sent = [];
      if (fill.tanker) sent.push((await e.dispatch({ type: 'orderSupply', supply: 'water', units: 1, tanker: fill.tanker.tanker })).ok);
      if (fill.bags) sent.push((await e.dispatch({ type: 'orderSupply', supply: 'barley', units: fill.bags })).ok);
      if (fill.bales) sent.push((await e.dispatch({ type: 'orderSupply', supply: 'alfalfa', units: fill.bales })).ok);
      const target = S0.today + Math.round((Date.parse(TARGET + 'T00:00:00Z') - Date.parse(S0.date + 'T00:00:00Z')) / 864e5);
      const me = S0.playerId, seen = new Map();
      // the design's stops: an illness, a death, a store down to its last days, money below zero, an offer, his
      // round's day, a treatment found
      const STOP = (x) => ['fellSick', 'died', 'supplyLow', 'cashNegative', 'offerReceived', 'placed', 'entryRemoved', 'disqualifiedSick', 'resultsPending', 'tamperingFound', 'saleRefused'].includes(x.type) && x.owner === me && x.day > S0.today;
      let mid = null, stop = null, S = S0;
      for (let i = 0; i < 6000; i++) {
        await new Promise((r) => setTimeout(r, 120));
        S = e.snapshot;
        for (const x of S.recentEvents) seen.set(`${x.day}|${x.type}|${x.camel || ''}|${x.supply || ''}|${x.festival || ''}`, x);
        if (!mid && S.today >= S0.today + 24) mid = JSON.parse(JSON.stringify(S));
        stop = [...seen.values()].filter(STOP).sort((x, y) => x.day - y.day)[0] || null;
        if (stop || S.today >= target) break;
      }
      // the snapshot of the stop's day itself (the poll can land a day later on the fast clock)
      const events = [...seen.values()].filter((x) => x.day > S0.today && (!stop || x.day <= stop.day)).sort((x, y) => x.day - y.day);
      // the milk's money from the ledger: to the half-way day (its month so far) and over the whole stretch
      let milkEnd = 0;
      const shapes = [];
      for (const m of S.bank.months) {
        const r = await e.bankMonth(m.month), mm = r.month || r;
        shapes.push(Object.keys(r));
        for (const l of (mm.lines || [])) if (l.kind === 'milk') milkEnd += l.amount;
      }
      return { S0, fill, sent, target, mid, stop, S, events, milkEnd, milkMid: mid ? mid.farm.milk.thisMonth : 0, shapes };
    }, TARGET);
    await ctx.close();
    return out;
  })();
  if (CACHE && !fs.existsSync(CACHE)) fs.writeFileSync(CACHE, JSON.stringify(run));
  console.log('fill', JSON.stringify(run.fill), 'sent', JSON.stringify(run.sent));
  console.log('ledger shapes', JSON.stringify(run.shapes), 'milk', run.milkMid, run.milkEnd, 'snapshot day', run.S.today, 'stop day', run.stop && run.stop.day);
  console.log('stopped', run.stop ? JSON.stringify(run.stop) : 'no stop', 'at', run.S.date, 'events', run.events.map((x) => `${x.day}:${x.type}`).join(' '));

  // ---------------------------------------------------------------- the real clock's game: the screens drawn
  const { p } = await open(b, false);
  await p.evaluate(FILL);
  await p.evaluate(() => { window.requestAnimationFrame = () => 0; });
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone')).shadowRoot; window.__phone.toggle(); window.__phone.enlarge(); });
  await p.waitForTimeout(600);

  const screens = await p.evaluate((A) => {
    const S = window.marahEngine.snapshot;
    const I = {
      back: '<path d="M9 6l6 6-6 6"/>', chev: '<path d="M15 6l-6 6 6 6"/>',
      cal: '<rect x="4" y="5.5" width="16" height="14.5" rx="2.5"/><path d="M4 10h16M8.5 3.5v4M15.5 3.5v4"/><path d="M8 14h2M14 14h2M8 17h2"/>',
      cup: '<path d="M7.5 4h9v5.5a4.5 4.5 0 0 1-9 0z"/><path d="M7.5 6H4.8c0 2.4 1.2 3.8 3.2 4.2M16.5 6h2.7c0 2.4-1.2 3.8-3.2 4.2"/><path d="M12 14v3.5M9.5 17.5h5v3h-5z"/>',
      talk: '<path d="M4 5.5h16v10H9l-5 4z"/>',
      water: '<path d="M12 3.5c3.2 4 5.5 7.1 5.5 10a5.5 5.5 0 0 1-11 0c0-2.9 2.3-6 5.5-10z"/>',
      feed: '<path d="M12 20V9M12 9c0-3 2-5 5-5 0 3-2 5-5 5zM12 13c0-3-2-5-5-5 0 3 2 5 5 5zM12 17c0-3 2-5 5-5 0 3-2 5-5 5z"/>',
      alert: '<path d="M12 4 2.5 20h19z"/><path d="M12 10v4.5M12 17.5v.01"/>',
      milk: '<path d="M9 3.5h6M9.5 3.5v3L7 10v9.5h10V10l-2.5-3.5v-3"/>',
      heart: '<path d="M12 19.5s-7-4.3-7-9.5a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.2-7 9.5-7 9.5z"/>',
      sun: '<circle cx="12" cy="12" r="3.8"/><path d="M12 3v2.5M12 18.5V21M3 12h2.5M18.5 12H21M5.6 5.6l1.8 1.8M16.6 16.6l1.8 1.8M5.6 18.4l1.8-1.8M16.6 7.4l1.8-1.8"/>',
      truck: '<path d="M2.5 6.5h11v9h-11z"/><path d="M13.5 9.5h4l3 3.5v2.5h-7z"/><circle cx="6.5" cy="17" r="1.8"/><circle cx="16.5" cy="17" r="1.8"/>',
      money: '<rect x="3" y="6.5" width="18" height="11" rx="2"/><circle cx="12" cy="12" r="2.6"/>',
      flag: '<path d="M5.5 21V4M5.5 4.5h11l-2 3.5 2 3.5h-11"/>',
      stop: '<rect x="7" y="7" width="10" height="10" rx="2"/>',
      check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    };
    const svg = (k) => `<svg class="i" viewBox="0 0 24 24">${I[k]}</svg>`;
    const nav = () => `<div class="nav"><button class="back">${svg('back')}رجوع</button></div>`;
    const n0 = (v) => Math.round(v).toLocaleString('en-US');
    const NOUN = { day: ['يوم واحد', 'يومين', 'أيام', 'يوم'], bag: ['كيس واحد', 'كيسين', 'أكياس', 'كيس'], bale: ['بالة وحدة', 'بالتين', 'بالات', 'بالة'], camel: ['ناقة وحدة', 'ناقتين', 'نياق', 'ناقة'], fest: ['مهرجان واحد', 'مهرجانين', 'مهرجانات', 'مهرجان'], order: ['طلب واحد', 'طلبين', 'طلبات', 'طلب'], tanker: ['وايت واحد', 'وايتين', 'وايتات', 'وايت'] };
    const count = (n, k) => { const [one, two, few, many] = NOUN[k]; return n === 1 ? one : n === 2 ? two : n >= 3 && n <= 10 ? `${n} ${few}` : `${n} ${many}`; };
    const days = (n) => count(n, 'day');
    const WEEKDAY = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'];
    const MONTH = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'];
    // phone.js's seasons, as they are there
    const SEASONS = [[1, 15, 'الشبط'], [2, 10, 'العقارب'], [3, 21, 'الربيع'], [6, 1, 'القيظ'], [8, 24, 'سهيل'], [10, 16, 'الوسم'], [12, 7, 'المربعانية']];
    const season = (d) => { const m = d.getUTCMonth() + 1, x = d.getUTCDate(); let nm = 'المربعانية'; for (const [sm, sd, s] of SEASONS) if (m > sm || (m === sm && x >= sd)) nm = s; return nm; };
    const BREED = [11, 12, 1, 2, 3, 4];
    const t0 = Date.parse(S.date + 'T00:00:00Z');
    const dateOf = (day) => new Date(t0 + (day - S.today) * 864e5);
    const dayOf = (iso) => S.today + Math.round((Date.parse(iso + 'T00:00:00Z') - t0) / 864e5);
    const dd = (day) => { const d = dateOf(day); return `${WEEKDAY[d.getUTCDay()]} ${d.getUTCDate()} ${MONTH[d.getUTCMonth()]}`; };
    const dShort = (day) => { const d = dateOf(day); return `${d.getUTCDate()} ${MONTH[d.getUTCMonth()]}`; };
    const span = (a, z) => { const x = dateOf(a), y = dateOf(z); if (a === z) return dShort(a); return x.getUTCMonth() === y.getUTCMonth() ? `من ${x.getUTCDate()} لين ${dShort(z)}` : `من ${dShort(a)} لين ${dShort(z)}`; };
    const inDays = (day) => { const n = day - S.today; return n <= 0 ? 'اليوم' : n === 1 ? 'بكرة' : `بعد ${days(n)}`; };
    const her = (c, f, m) => (c.sex === 'female' ? f : m);

    // ---- the year's dated things: the engine's festivals, the breeding months, the seasons, the herd's own
    const fests = S.festivals.filter((f) => !f.done).sort((a, b) => a.startsOn - b.startsOn);
    const yearEnd = S.today + 364;
    const items = [];
    for (const f of fests) {
      if (f.startsOn > yearEnd) continue;
      items.push({ day: f.closesOn, icon: 'flag', cls: 'fest', b: `تسجيل ${f.name} يقفل`, s: `${dd(f.closesOn)} · وبعده متأخر لين 72 ساعة قبل الشوط` });
      items.push({ day: f.startsOn, icon: 'cup', cls: 'fest', b: f.name, s: `${span(f.startsOn, f.endsOn)} · ${inDays(f.startsOn)}` });
    }
    // the breeding season's next start (Nov) and end (Apr)
    const y = dateOf(S.today).getUTCFullYear();
    const bStart = dayOf(`${y}-11-01`), bEnd = dayOf(`${y + 1}-04-30`);
    items.push({ day: bStart, icon: 'heart', cls: 'brd', b: 'يبدأ وقت الضراب', s: `${dd(bStart)} لين آخر أبريل` });
    // the seasons' starts
    for (let k = 0; k < 2; k++) for (const [m, d, nm] of SEASONS) {
      const day = dayOf(`${y + k}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`);
      if (day > S.today && day <= yearEnd) items.push({ day, icon: 'sun', cls: 'sea', b: nm, s: `يبدأ ${dd(day)}`, season: true });
    }
    // the herd's own: a calving's due day, a milking's end (a year from calving)
    for (const c of S.yard) if (c.pregnant && c.dueOn) items.push({ day: c.dueOn, icon: 'heart', cls: 'me', b: `${c.name} تولد`, s: `متوقع ${dd(c.dueOn)} · ${inDays(c.dueOn)}` });
    for (const m of S.farm.milk.camels) { const end = S.today + (365 - m.days); items.push({ day: end, icon: 'milk', cls: 'milk', b: `حليب ${m.name} يخلص`, s: `${dd(end)} · يكمل ${m.calfName} سنة`, milkEnd: true }); }
    items.sort((a, b) => a.day - b.day);
    const pickRow = (x) => `<div class="row pick"><span class="lead ${x.cls}">${svg(x.icon)}</span><b>${x.b}</b><span class="chev">${svg('chev')}</span><small>${x.s}</small></div>`;

    // ---------------------------------------------------------------- 1 home: the nine apps
    const home = (() => {
      const scr = R().querySelector('.scr');
      const apps = scr.querySelector('.apps');
      const app = (k, n) => `<div class="app"><span class="ic">${svg(k)}</span><span>${n}</span></div>`;
      apps.insertAdjacentHTML('beforeend', app('cup', 'المزاين') + app('talk', 'المحادثات') + app('cal', 'التقويم'));
      return null;
    })();

    // ---------------------------------------------------------------- 2 the year: twelve months as strips
    const months = [];
    const d0 = dateOf(S.today);
    for (let k = 0; k < 12; k++) {
      const ym = new Date(Date.UTC(d0.getUTCFullYear(), d0.getUTCMonth() + k, 1));
      const first = dayOf(ym.toISOString().slice(0, 10)), len = new Date(Date.UTC(ym.getUTCFullYear(), ym.getUTCMonth() + 1, 0)).getUTCDate();
      const last = first + len - 1, pos = (day) => ((day - first) / len) * 100, w = (a, z) => ((z - a + 1) / len) * 100;
      const segs = [];
      const clip = (a, z) => [Math.max(a, first), Math.min(z, last)];
      if (S.today > first) { const [a, z] = clip(first, S.today - 1); segs.push(`<i class="past" style="right:${pos(a)}%;width:${w(a, z)}%"></i>`); }
      if (BREED.includes(ym.getUTCMonth() + 1)) segs.push(`<i class="brd" style="right:0;width:100%"></i>`);
      for (const f of fests) {
        const [ra, rz] = clip(f.opensOn, f.closesOn); if (ra <= rz) segs.push(`<i class="reg" style="right:${pos(ra)}%;width:${w(ra, rz)}%"></i>`);
      }
      for (const f of fests) { const [a, z] = clip(f.startsOn, f.endsOn); if (a <= z) segs.push(`<i class="fest" style="right:${pos(a)}%;width:${w(a, z)}%"></i>`); }
      for (const x of items) if ((x.cls === 'me' || x.cls === 'milk') && x.day >= first && x.day <= last) segs.push(`<i class="me${x.cls === 'milk' ? ' milk' : ''}" style="right:${pos(x.day) + 50 / len}%"></i>`);
      if (S.today >= first && S.today <= last) segs.push(`<i class="today" style="right:${pos(S.today) + 50 / len}%"></i>`);
      const now = S.today >= first && S.today <= last;
      months.push(`<div class="m"><span${now ? ' class="now"' : ''}>${MONTH[ym.getUTCMonth()]}${ym.getUTCMonth() === 0 || k === 0 ? ` ${ym.getUTCFullYear()}` : ''}</span><div class="t">${segs.join('')}</div></div>`);
    }
    const key = `<div class="key"><span><i style="background:#57b88a;height:3px"></i>الضراب</span><span><i style="background:#f6e3b8"></i>التسجيل</span><span><i style="background:#d9a033"></i>المزاين</span><span><i style="background:var(--red);width:8px;border-radius:4px"></i>ولادة</span><span><i style="background:#2f7fcf;width:8px;border-radius:4px"></i>يخلص الحليب</span></div>`;
    const todayLine = `اليوم ${dd(S.today)} · ${season(dateOf(S.today))}${S.breedingSeason ? ' · وقت الضراب' : ''}`;
    const year = `<div class="body">${nav()}<div class="title">التقويم</div>
      <div class="note" style="margin-top:-4px">${todayLine}</div>
      <div class="yr">${months.join('')}</div>${key}
      <div class="sec">اللي جاي</div>
      <div class="group">${items.slice(0, 6).map(pickRow).join('')}</div>
      <div class="note">اختار أي يوم أو أي شي جاي، وتمشي له. التقويم يمشي لقدام بس، واللي يمضي ما يرجع.</div></div>`;

    // ---------------------------------------------------------------- 3 the year scrolled (same screen)
    const yearEnd_ = `<div class="body">${nav()}<div class="title">التقويم</div>
      <div class="note" style="margin-top:-4px">${todayLine}</div>
      <div class="sec">اللي جاي</div>
      <div class="group">${items.slice(0, 16).map(pickRow).join('')}</div>
      <div class="note">اختار أي يوم أو أي شي جاي، وتمشي له. التقويم يمشي لقدام بس، واللي يمضي ما يرجع.</div></div>`;

    // ---------------------------------------------------------------- 4 a season picked: its month, the day ringed
    const tgt = dayOf(A.target), td = dateOf(tgt), N = tgt - S.today;
    const mFirst = dayOf(`${td.getUTCFullYear()}-${String(td.getUTCMonth() + 1).padStart(2, '0')}-01`);
    const mLen = new Date(Date.UTC(td.getUTCFullYear(), td.getUTCMonth() + 1, 0)).getUTCDate();
    const cells = ['ح', 'ن', 'ث', 'ر', 'خ', 'ج', 'س'].map((x) => `<span class="wd">${x}</span>`);
    for (let k = 0; k < dateOf(mFirst).getUTCDay(); k++) cells.push('<span></span>');
    for (let k = 0; k < mLen; k++) {
      const day = mFirst + k, fest = fests.some((f) => day >= f.startsOn && day <= f.endsOn), brd = BREED.includes(td.getUTCMonth() + 1);
      cells.push(`<span class="d${day === tgt ? ' sel' : fest ? ' fest' : ''}${brd ? ' brd' : ''}">${k + 1}</span>`);
    }
    const onIt = fests.filter((f) => tgt >= f.startsOn && tgt <= f.endsOn);
    const picked = `<div class="body">${nav()}<div class="title">${MONTH[td.getUTCMonth()]} ${td.getUTCFullYear()}</div>
      <div class="cal">${cells.join('')}</div>
      <div class="span"><b>${dd(tgt)}</b><small>أول ${season(td)} · ${inDays(tgt)}</small></div>
      <div class="group">
        ${onIt.map((f) => `<div class="row two"><span class="lead fest">${svg('cup')}</span><b>${f.name}</b><small>${span(f.startsOn, f.endsOn)} · ما سجلت فيه</small></div>`).join('')}
        <div class="row two"><span class="lead brd">${svg('heart')}</span><b>وقت الضراب</b><small>من 1 نوفمبر لين آخر أبريل</small></div></div>
      <button class="btn pri wide">امشِ لين ${dd(tgt)}</button>
      <div class="note">قبلها يوريك وش تحتاج للأيام هذي.</div></div>`;

    // ---------------------------------------------------------------- 5 the card before the jump
    const F = window.__fill(S), sup = (k) => S.farm.supplies.find((x) => x.supply === k);
    const w = sup('water'), bb = sup('barley'), aa = sup('alfalfa');
    const lastW = Math.floor(w.amount / w.need), lastB = Math.floor(bb.amount / bb.need), lastA = Math.floor(aa.amount / aa.need);
    const lastFeed = Math.min(lastB, lastA), feedFilled = Math.min(F.barley, F.alfalfa);
    const verdict = (n) => (n >= N ? ['ok', 'يكفي'] : ['bad', 'ما يكفي']);
    const stopAt = Math.min(F.water, feedFilled) - 3;      // the stop comes with the warning, three days before a store is out
    const supRow = (icon, name, last, filled, fillWhat, fillCost) => {
      const [cls, word] = verdict(filled);
      return `<div class="row two2"><span class="lead${last < N ? ' me' : ''}">${svg(icon)}</span><b>${name} · يكفي ${days(last)}</b><span class="act"><button class="btn sm ghost" aria-label="عبّ ${name}">عبّه</button></span><small>${fillWhat} بـ ${n0(fillCost)} ريال، ويصير يكفي ${days(filled)} تقريبًا: <span class="${cls === 'ok' ? 'pos' : ''}" style="${cls === 'bad' ? 'color:var(--red);font-weight:700' : ''}">${word}</span></small></div>`;
    };
    const milkDay = S.farm.milk.sold * S.farm.milk.price;
    const between = fests.filter((f) => f.startsOn > S.today && f.startsOn <= tgt);
    const card = `<div class="body">${nav()}<div class="title">قبل ما تمشي</div>
      <div class="span"><b>لين ${dd(tgt)}</b><small>${days(N)} · من ${dd(S.today)}</small></div>
      <div class="sec">يكفي ${days(N)}؟</div>
      <div class="group">
        ${supRow('water', 'الماء', lastW, F.water, `وايت ${Math.round(F.tanker.litres / 1000)} طن`, F.tanker.price)}
        ${supRow('feed', 'العلف', lastFeed, feedFilled, `${count(F.bags, 'bag')} و${count(F.bales, 'bale')}`, F.feedCost)}</div>
      <div class="note">${feedFilled < N ? `حتى لو عبّيت، العلف ما يكفي الأيام كلها: يوقف التقويم حوالي ${dShort(S.today + stopAt)} عشان تطلب، وبعدها تكمل.` : 'لو عبّيت يكفي الأيام كلها.'}</div>
      <div class="sec">اللي يجي بالطريق</div>
      <div class="group">
        <div class="row two"><span class="lead brd">${svg('heart')}</span><b>وقت الضراب يبدأ ${dShort(bStart)}</b><small>${S.yard.filter((c) => c.sex === 'female' && !c.pregnant && c.ageDays >= 1209).length ? 'عندك نياق تنلقح' : 'نورة عشار، وما عندك غيرها تنلقح'}</small></div>
        <div class="row two"><span class="lead fest">${svg('cup')}</span><b>${count(between.length, 'fest')}</b><small>${between.map((f) => f.name.replace('مهرجان ', '').replace('مزاين ', '')).join('، ')} · ما سجلت بشي</small></div>
        <div class="row two"><span class="lead milk">${svg('milk')}</span><b>الحليب يدخلك ${n0(milkDay)} ريال باليوم</b><small>وما عليك رواتب: ما عندك رعاة</small></div></div></div>`;

    // ---------------------------------------------------------------- 6 the card scrolled: the stops, the go button
    const cardEnd = `<div class="body">${nav()}<div class="title">قبل ما تمشي</div>
      <div class="sec">يوقف ويرجع لك لو</div>
      <div class="stops">مرضت ناقة أو ماتت · قرب العلف أو الماء يخلص (باقي 3 أيام) · نزل رصيدك تحت الصفر · جاك سوم على إعلان · جا يوم شوطك · انكشف تجميل بحلالك</div>
      <div class="note">وكل شي ثاني يمشي بنفسه: الحليب ينباع، والرواتب تنخصم، والولادات تصير، وتلقاها كلها بالآخر.</div>
      <button class="btn pri wide">امشِ لين ${dd(tgt)}</button>
      <div class="note">التقويم يمشي لقدام بس: الأيام اللي تمضي ما ترجع. وتقدر توقفه بنص الطريق.</div></div>`;

    // ---------------------------------------------------------------- 7 the jump under way (the fast game, 24 days in)
    const M = A.mid, mDay = M ? M.today : S.today + 24;
    const mw = M ? M.farm.supplies.find((x) => x.supply === 'water') : w, mb = M ? M.farm.supplies.find((x) => x.supply === 'barley') : bb, ma = M ? M.farm.supplies.find((x) => x.supply === 'alfalfa') : aa;
    const done = mDay - S.today, pct = Math.round(done / N * 100);
    const midMilk = A.milkMid;
    const going = `<div class="body"><div class="nav"></div><div class="title">يمشي الوقت</div>
      <div class="tank"><small>وصل</small><div class="v"><b class="fit">${dd(mDay)}</b></div>
        <div class="bar"><i style="width:${pct}%;background:linear-gradient(90deg,#0b8a5c,#3fb487)"></i></div>
        <div class="ln">${days(done)} من ${days(N)} · لين ${dShort(tgt)}</div></div>
      <div class="group">
        <div class="row two"><span class="lead milk">${svg('milk')}</span><b>الحليب دخلك ${n0(midMilk)} ريال</b><small>من ${dShort(S.today)}</small></div>
        <div class="row two"><span class="lead">${svg('water')}</span><b>الماء يكفي ${days(mw.daysLeft)}</b><small>والشعير ${days(mb.daysLeft)} والبرسيم ${days(ma.daysLeft)}</small></div></div>
      <button class="btn ghost wide">${svg('stop')}وقّف هنا</button>
      <div class="note">الأيام تنحسب يوم يوم، ويوقف بنفسه لو صار شي يبيك.</div></div>`;

    // ---------------------------------------------------------------- 8 the early stop (the fast game's first stop)
    const st = A.stop, sDay = st ? st.day : tgt;
    const SUP = { barley: 'الشعير', alfalfa: 'البرسيم', water: 'الماء' };
    let why = '', what = '', act = '';
    if (st && st.type === 'supplyLow') {
      why = st.days > 0 ? `${SUP[st.supply]} يخلص ${st.days === 1 ? 'بكرة' : `بعد ${days(st.days)}`}` : `${SUP[st.supply]} خلص`;
      what = 'اطلب اليوم يوصل بكرة، وبعدها كمّل.';
      act = st.supply === 'water' ? 'اطلب وايت' : 'اطلب علف';
    } else if (st && st.type === 'fellSick') {
      why = `${st.name} ${'مرضت'}`; what = 'عالجها اليوم: لو تركتها بعد 10 أيام ممكن تموت. البيطري على حساب التاجر لو رصيدك ما كفى.'; act = 'عالجها';
    } else if (st && st.type === 'died') {
      why = `ماتت ${st.name}`; what = 'شوف وش تحتاج بقية الحلال قبل ما تكمل.'; act = 'شوف الحلال';
    } else if (st) { why = st.type; what = ''; act = 'شوف'; }
    const leftDays = tgt - sDay;
    const stopped = `<div class="body">${nav()}<div class="title">وقف التقويم</div>
      <div class="warn"><span class="lead">${svg('alert')}</span><b>${why}</b><small>وقف ${dd(sDay)}، وباقي ${days(leftDays)} لين ${dShort(tgt)}. ${what}</small></div>
      <button class="btn pri wide">${act}</button>
      <button class="btn ghost wide">كمّل لين ${dd(tgt)}</button>
      <div class="group"><div class="row pick"><span class="lead sea">${svg('flag')}</span><b>اللي صار لين هنا</b><span class="chev">${svg('chev')}</span><small>${days(sDay - S.today)}، من ${dShort(S.today)}</small></div></div></div>`;

    // ---------------------------------------------------------------- 9 the summary (the engine's events and ledger)
    const ev = A.events, by = (t) => ev.filter((x) => x.type === t);
    const rows = [];
    const milkAll = A.milkEnd;
    rows.push(`<div class="row two"><span class="lead milk">${svg('milk')}</span><b>الحليب دخلك ${n0(milkAll)} ريال</b><small>ينباع كل يوم</small></div>`);
    const deliv = by('supplyDelivered');
    if (deliv.length) rows.push(`<div class="row two"><span class="lead">${svg('truck')}</span><b>وصل ${count(deliv.length, 'order')}</b><small>${deliv.map((x) => x.supply === 'water' ? `وايت ${Math.round(x.size / 1000)} طن` : x.supply === 'barley' ? count(x.units, 'bag') + ' شعير' : count(x.units, 'bale') + ' برسيم').join('، ')}</small></div>`);
    const sick = by('fellSick'), died = by('died'), born = by('calfBorn');
    rows.push(`<div class="row two"><span class="lead ${sick.length || died.length ? 'me' : 'brd'}">${svg('heart')}</span><b>${sick.length ? `مرض ${count(sick.length, 'camel')}` : 'ما مرض شي'}</b><small>${died.length ? `ماتت ${died.map((x) => x.name).join('، ')}` : 'وما مات شي'}${born.length ? ` · ولد ${born.length}` : ''}</small></div>`);
    const regs = by('registrationOpened');
    if (regs.length) rows.push(`<div class="row two"><span class="lead fest">${svg('cup')}</span><b>انفتح تسجيل ${count(regs.length, 'fest')}</b><small>${regs.map((x) => x.name.replace('مهرجان ', '').replace('مزاين ', '')).join('، ')}</small></div>`);
    const lows = by('supplyLow');
    if (lows.length) rows.push(`<div class="row two"><span class="lead me">${svg('alert')}</span><b>${why}</b><small>هذا اللي وقّف التقويم</small></div>`);
    const summary = `<div class="body">${nav()}<div class="title">اللي صار</div>
      <div class="span"><b>${days(sDay - S.today)}</b><small>من ${dd(S.today)} لين ${dd(sDay)}</small></div>
      <div class="group">${rows.join('')}</div>
      <div class="note">والتفاصيل بالبنك والعزبة.</div></div>`;

    return { home: null, year, year_end: yearEnd_, picked, card, card_end: cardEnd, going, stopped, summary };
  }, { target: TARGET, mid: run.mid, stop: run.stop, events: run.events, milkEnd: run.milkEnd, milkMid: run.milkMid });

  const files = [];
  let i = 0;
  if (process.env.AUDIT) fs.writeFileSync(path.join(OUT, 'calendar_texts.txt'), '');
  for (const [k, html] of Object.entries(screens)) {
    i++;
    if (html) {
      await p.evaluate(([html, css]) => {
        const scr = R().querySelector('.scr'), sb = scr.querySelector('.sbar').outerHTML;
        scr.classList.remove('home');
        scr.innerHTML = `<span class="pill"></span>${sb}${html.replace(/(\d) (?=[؀-ۿ])/g, '$1\u00a0').replace(/([؀-ۿ]) (?=\d)/g, '$1\u00a0')}<div class="hb"></div>`;
      }, [html, CSS]);
    }
    await p.evaluate((css) => { const st = document.createElement('style'); st.textContent = css; R().querySelector('.scr').appendChild(st); }, CSS);
    if (k.endsWith('_end')) await p.evaluate(() => { const bd = R().querySelector('.body'); bd.scrollTop = bd.scrollHeight; });
    await p.waitForTimeout(400);
    const file = path.join(OUT, `mock_calendar_${i}_${k}.png`);
    const box = await p.evaluate(() => { const r = R().querySelector('.dev').getBoundingClientRect(); return { x: r.x, width: r.width }; });
    await p.screenshot({ path: file, timeout: 600000, clip: { x: Math.max(0, box.x - 4), y: 0, width: box.width + 8, height: 440 } });
    files.push(file);
    if (process.env.AUDIT) {
      await p.addScriptTag({ path: process.env.AUDIT });
      const a = await p.evaluate(() => window.__audit());
      console.log(k, 'audit', JSON.stringify({ clipped: a.clipped, ellipsis: a.ellipsis, outside: a.outside, split: a.split, scroll: a.scroll }));
      fs.appendFileSync(path.join(OUT, 'calendar_texts.txt'), `== ${k}\n` + a.texts.filter((t) => !t.includes('{')).join('\n') + '\n');
    }
  }
  await b.close();
  execFileSync('convert', [...files, '-background', '#2a2119', '-splice', '6x0', '+append', '-chop', '6x0', '-quality', '86', path.join(__dirname, 'phone_calendar.jpg')]);
})();
