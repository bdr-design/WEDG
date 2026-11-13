// المزاين in the phone: a DESIGN for the owner's approval (not built yet, not in phone.js). Seven screens in nine
// views, as the phone draws them at the owner's screen (956 x 440, the phone enlarged), in the phone's own CSS and
// pieces (design/prototype3d/phone.js) plus the approved chat's (design/ui/phone.html):
//   1 fests       the festivals: the one open for registration, the player's entry (withdraw), what is coming and when
//   2 fest        a festival opened (two views: its top, and scrolled to its end): its individual rounds (الفردي دق وجل
//   3 fest_end    لكل لون، مفاريد ودق القعدان والبكار، الفحل وإنتاجه; the group rounds only as coming later, the owner
//                 13 Nov), each kind's first prize, each colour's day, the free and late registration, the rules
//   4 enter       registering: each of the player's camels with its round, or the engine's reason it cannot enter
//   5 cheat       the secret treatment (GDD 7.1) offered in a chat: the seven kinds
//   6 strength    one kind picked: light, middle or strong, each with its price, fine and how often it is found
//   7 day         the round's day: the six stages, told one by one (here the third under way)
//   8 result      the results: the player's camel's outcome, the placings and prizes, her worth and the name's
//   9 caught      the day a treatment is found (a state this seed does not reach: see below)
// Every figure the engine has comes from it, so the drawing follows the engine when it changes:
//  - the snapshot (SnapshotJson): the festivals' cards, the herd, the market, festivalRules (late fee, 72 hours, ban,
//    the seven treatments' prices, fines, features, how long they last, the chance a festival finds each), reputation;
//  - the worker's festival page (op 'festival', SnapshotJson.festivalDetail): the rounds, their days, last entry days,
//    prizes, rivals, the camels that may enter, the entry fee, the transport, and after the day the field after each
//    stage and the places;
//  - the engine's own refusals (enterRound for each camel's round: wrongAgeClass, ownershipTooRecent...);
//  - the save, for the owners' names in the places (the snapshot gives an owner's id only).
// Two games on seed 4242 (1 October 2026, مزاين حائل open): one played forward on a fast clock to the round's results
// (the market's نمر bought, نورة entered in الفردي جل الوضح), then one at the real clock on its first day, where the
// screens are drawn. What the engine does not give is a placeholder, marked PLACEHOLDER below.
// The caught view: on this seed نورة, treated or not, is cut at the preliminary judging (13 of 26 go on), and the
// engine checks for tampering only after it, so no game here reaches it; it is drawn from the engine's rules
// (Botox at light strength: its fine; the ban; the balance it leaves below zero) with the stages before it as they would pass.
// To draw again: build the prototype (THREE_DIR=<three@0.170.0 package> python3 tool/proto_app/assemble.py), serve
// tool/proto_app/assets/web on a port (8765 by default, or PORT=<port>), and run
// `NODE_PATH=$(npm root -g) node design/ui/phone_mazayen.cjs` from the repository's root; it writes
// mock_mazayen_<n>_<name>.png in the current folder (or OUT=<folder>) and design/ui/phone_mazayen.jpg (the nine side
// by side). AUDIT=<audit.js> runs a layout audit on each view and writes the views' texts to mazayen_texts.txt.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const PORT = process.env.PORT || 8765;
const OUT = process.env.OUT || '.';
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };

// screens beyond phone.js: a stage's state on the day, a rank, the camel that cannot enter, and the approved chat's
// header, strip and bubbles (design/ui/phone.html)
const CSS = `
  .row .qty.ok { color: var(--acc); font: 600 12.5px/1 "IBM Plex Sans Arabic", sans-serif; }
  .row .qty.now { color: var(--amber); font: 700 12.5px/1 "IBM Plex Sans Arabic", sans-serif; }
  .row .qty.bad { color: var(--red); font: 700 12.5px/1 "IBM Plex Sans Arabic", sans-serif; }
  .row .qty.wait { color: var(--ink2); font: 500 12px/1 "IBM Plex Sans Arabic", sans-serif; }
  .row.now .lead { background: #fdf1dc; color: var(--amber); }
  .row.next .lead { background: #eeeef1; color: #a5a5ab; }
  .row.next b { color: var(--ink2); font-weight: 500; }
  .row.bad .lead { background: #fde6e4; color: var(--red); }
  .row .lead.rk { font: 700 15px/1 "Alexandria", sans-serif; }
  .row .lead.rk.g1 { background: #fbefd2; color: #a8730c; }
  .row.later .lead { background: #eeeef1; color: #8e8e93; }
  .row.two { grid-template-columns: 36px 1fr; }
  .it small.bad, .row small.bad { color: var(--red); font-weight: 600; }
  .it.no .ph, .it.no b { opacity: .55; }
  .it.sel { box-shadow: inset 0 0 0 2px var(--acc); }
  .open { background: var(--card); border-radius: 18px; padding: 12px 14px; display: flex; flex-direction: column; gap: 3px; box-shadow: inset 0 0 0 1.5px #bfe3d2; }
  .open .tag { align-self: flex-start; font-size: 11px; font-weight: 700; color: var(--acc); background: var(--acc-soft); border-radius: 8px; padding: 2px 8px; }
  .open b { font: 700 17px/1.3 "Alexandria", sans-serif; }
  .open small { font-size: 12px; color: var(--ink2); }
  .chathd { display: flex; align-items: center; gap: 9px; }
  .chathd .av { width: 34px; height: 34px; border-radius: 50%; background: #d9cbb4; display: grid; place-items: center; font: 700 15px/1 "Alexandria", sans-serif; color: #4a3720; }
  .chathd b { font-size: 14.5px; display: block; line-height: 1.2; }
  .chathd small { font-size: 11px; color: var(--ink2); }
  .strip { display: flex; align-items: center; gap: 10px; padding: 7px; border-radius: 14px; background: var(--card); }
  .strip .ph { width: 42px; height: 42px; border-radius: 10px; background: linear-gradient(180deg, #f3eadc, #e2cfae); overflow: hidden; flex: none; }
  .strip .ph img { width: 100%; height: 100%; object-fit: contain; }
  .strip b { font-size: 13px; display: block; }
  .strip small { font-size: 11px; color: var(--ink2); }
  .strip .lim { margin-inline-start: auto; text-align: end; font-size: 11px; color: var(--ink2); }
  .strip .lim span { display: block; font: 700 14px/1.1 "Alexandria", sans-serif; color: var(--ink); }
  .chat { display: flex; flex-direction: column; gap: 6px; }
  .msg { max-width: 82%; padding: 7px 11px; border-radius: 17px; font-size: 13px; line-height: 1.4; }
  .msg.them { align-self: flex-start; background: #e9e9eb; border-end-start-radius: 5px; }
  .msg.me { align-self: flex-end; background: var(--acc); color: #fff; border-end-end-radius: 5px; }
  .row .act .btn.pr { padding-inline: 10px; font-size: 12.5px; }
  .sbar .clk { font-size: 0; } .sbar .clk::after { content: "9:41"; font-size: 14px; }
`;

// in the page: the worker's other calls (engine.js gives dispatch only), answered by their id
const OP = `window.__op = (o) => new Promise((res) => { const w = window.marahEngine.worker; const id = 900000 + Math.floor(Math.random() * 99999);
  const h = (ev) => { const m = typeof ev.data === 'string' ? JSON.parse(ev.data) : ev.data; if (m.id === id) { w.removeEventListener('message', h); res(m); } };
  w.addEventListener('message', h); w.postMessage(JSON.stringify({ ...o, id })); });`;

async function open(b, fast) {
  const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  if (fast) {
    // the same page on a fast clock (a game day in about 0.6 s)
    await p.route('**/index.html', async (route) => {
      const r = await route.fetch();
      route.fulfill({ response: r, body: (await r.text()).replace('startEngine({ onSnapshot:', 'startEngine({ timeScale: 20000, onSnapshot:') });
    });
  }
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.marahEngine || window.marahEngineError, null, { timeout: 600000 });
  await p.evaluate(OP);
  return { ctx, p };
}

(async () => {
  const b = await chromium.launch(LAUNCH);

  // ---- game 1, fast: نمر bought and نورة entered on the first day, played to her round's places
  const g1 = await open(b, true);
  const after = await g1.p.evaluate(async () => {
    const e = window.marahEngine;
    await e.startOver({ seed: 4242 });
    const S0 = e.snapshot;
    const fest = S0.festivals.find((f) => !f.done && S0.today >= f.opensOn && S0.today <= f.closesOn);
    const d0 = (await window.__op({ op: 'festival', festival: fest.id })).festival;
    const noura = S0.yard.find((c) => c.sex === 'female');
    const rd = d0.rounds.find((r) => r.enterable && r.eligible.some((c) => c.id === noura.id) && r.kind === 'fardiJil');
    const nimr = S0.market.find((l) => l.camel.name === 'نمر' && l.camel.category === 'shoqh');
    await e.dispatch({ type: 'buyListing', listing: nimr.id });
    await e.dispatch({ type: 'enterRound', festival: fest.id, round: rd.id, camels: [noura.id] });
    let r = null;
    for (let i = 0; i < 4000; i++) {
      await new Promise((res) => setTimeout(res, 300));
      if (e.snapshot.today < rd.day) continue;
      r = (await window.__op({ op: 'festival', festival: fest.id })).festival.rounds.find((x) => x.id === rd.id);
      if (r.announced) break;
    }
    const S = e.snapshot;
    await e.flush();
    // the owners' names: the save's world (the snapshot gives the places an owner's id only)
    const save = JSON.parse(localStorage.getItem('marah.proto.marah.save'));
    const owners = {};
    const walk = (o, d = 0) => { if (!o || typeof o !== 'object' || d > 6) return; if (Array.isArray(o.owners)) for (const w of o.owners) if (w && w.id && w.name) owners[w.id] = w.name; for (const v of Object.values(o)) walk(v, d + 1); };
    walk(save);
    const names = {};
    for (const row of r.results || []) names[row.owner] = owners[row.owner] || null;
    const mine = S.yard.find((c) => c.id === noura.id);
    // (the player's own row carries her score and marks: never shown; only the place, the stage and the reason)
    return {
      date: S.date, field: r.field, prizes: r.prizes, rivals: r.rivals, cash: S.cash,
      places: (r.results || []).filter((x) => x.rank != null).map((x) => ({ rank: x.rank, name: x.name, owner: names[x.owner], prize: x.prize })),
      mine: (r.results || []).filter((x) => x.camel === noura.id).map((x) => ({ rank: x.rank, prize: x.prize, removedAt: x.removedAt, reason: x.reason })),
      estimate: [mine.estimateLow, mine.estimateHigh], reputation: S.reputation[noura.category],
    };
  });
  console.log('played to', after.date, 'field', JSON.stringify(after.field), 'نورة', JSON.stringify(after.mine));
  await g1.ctx.close();

  // ---- game 2, the real clock, on its first day: the screens drawn here
  const { p } = await open(b, false);
  const game = await p.evaluate(async () => {
    const e = window.marahEngine;
    await e.startOver({ seed: 4242 });
    await new Promise((r) => setTimeout(r, 800));
    const S0 = e.snapshot;
    const fest = S0.festivals.find((f) => !f.done && S0.today >= f.opensOn && S0.today <= f.closesOn);
    const before = (await window.__op({ op: 'festival', festival: fest.id })).festival;
    const nimrL = S0.market.find((l) => l.camel.name === 'نمر' && l.camel.category === 'shoqh');
    const buy = await e.dispatch({ type: 'buyListing', listing: nimrL.id });
    const nimr = { ...nimrL.camel, id: buy.events.find((x) => x.camel).camel, onTheWay: true };
    const noura = S0.yard.find((c) => c.sex === 'female'), calf = S0.yard.find((c) => c !== noura);
    // each camel's own round (its colour, its sex, its age's kind), and the engine's answer to entering it
    const roundFor = (c, kinds) => before.rounds.find((r) => r.enterable && r.cat === c.category && r.sex === c.sex && kinds.includes(r.kind));
    const ask = async (c, r) => (await e.dispatch({ type: 'enterRound', festival: fest.id, round: r.id, camels: [c.id] })).error;
    const rNimr = roundFor(nimr, ['diq']), rCalf = roundFor(calf, ['mafareed']), rNoura = roundFor(noura, ['fardiJil']);
    const refusals = { nimr: await ask(nimr, rNimr), calf: await ask(calf, rCalf) };
    const entered = await ask(noura, rNoura);
    await new Promise((r) => setTimeout(r, 800));
    const detail = (await window.__op({ op: 'festival', festival: fest.id })).festival;
    return { before, detail, nimr, refusals, entered, rNoura: rNoura.id, rNimr: rNimr.kind, rCalf: rCalf.kind };
  });
  console.log('entered نورة:', game.entered === null, 'refusals', JSON.stringify(game.refusals));
  await p.evaluate(() => { window.requestAnimationFrame = () => 0; });
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone')).shadowRoot; window.__phone.toggle(); window.__phone.enlarge(); });
  await p.waitForTimeout(400);

  const screens = await p.evaluate(([G, A]) => {
    const S = window.marahEngine.snapshot, FR = S.festivalRules;
    // ---- the phone's own helpers (phone.js), as they are there
    const I = {
      back: '<path d="M9 6l6 6-6 6"/>', plus: '<path d="M12 5v14M5 12h14"/>',
      alert: '<path d="M12 4 2.5 20h19z"/><path d="M12 10v4.5M12 17.5v.01"/>',
      check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>', x: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
      dot: '<circle cx="12" cy="12" r="4.2" fill="currentColor"/>',
      cup: '<path d="M7.5 4h9v5.5a4.5 4.5 0 0 1-9 0z"/><path d="M7.5 6H4.8c0 2.4 1.2 3.8 3.2 4.2M16.5 6h2.7c0 2.4-1.2 3.8-3.2 4.2"/><path d="M12 14v3.5M9.5 17.5h5v3h-5z"/>',
      camel: '<path d="M3 8.5c0-1 .8-1.6 1.7-1.6h.9c.9 0 1.5.7 1.4 1.6l-.2 1.2c-.1.8.2 1.5.8 2 .5.4 1.1.4 1.6 0 .5-.5.9-1 1.1-1.6.9-1.7 2.5-2.8 4.4-2.7 1.1.1 2.1.8 2.7 1.8.5.8 1.1 1.3 2 1.6 1.1.4 1.9 1.5 1.9 2.8V15c0 .6-.4 1.2-.9 1.5V20"/><path d="M6.4 12.2V20M9.5 15.5V20M15 15.5V20"/>',
      herd: '<path d="M2.5 10.5c0-.8.6-1.3 1.3-1.3h.7c.7 0 1.2.6 1.1 1.3l-.2 1c0 .6.2 1.2.6 1.6.4.3.9.3 1.3 0 .4-.4.7-.8.9-1.3.7-1.4 2-2.3 3.5-2.2.9.1 1.7.7 2.2 1.5.4.6.9 1 1.6 1.3.9.3 1.5 1.2 1.5 2.2v1.2"/><path d="M5.6 13.4v5M8 15.9v2.5M12.5 15.9v2.5"/><path d="M14 6.5c.5-1.2 1.6-1.9 2.9-1.8.9.1 1.6.6 2.1 1.4.3.5.7.8 1.2 1 .7.3 1.2 1 1.2 1.8"/>',
      rule: '<rect x="5" y="3.5" width="14" height="17" rx="2"/><path d="M8.5 8h7M8.5 12h7M8.5 16h4"/>',
      chip: '<rect x="6.5" y="6.5" width="11" height="11" rx="2"/><path d="M9.5 3v3.5M14.5 3v3.5M9.5 17.5V21M14.5 17.5V21M3 9.5h3.5M3 14.5h3.5M17.5 9.5H21M17.5 14.5H21"/>',
      eye: '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z"/><circle cx="12" cy="12" r="2.6"/>',
      scope: '<path d="M6 3.5v6a4 4 0 0 0 8 0v-6"/><path d="M10 13.5v2a4.5 4.5 0 0 0 9 0v-2"/><circle cx="19" cy="11.5" r="2"/>',
      star: '<path d="M12 3.8l2.5 5.2 5.7.8-4.1 4 1 5.6-5.1-2.7-5.1 2.7 1-5.6-4.1-4 5.7-.8z"/>',
      chev: '<path d="M15 6l-6 6 6 6"/>',
    };
    const svg = (k) => `<svg class="i" viewBox="0 0 24 24">${I[k]}</svg>`;
    const nav = () => `<div class="nav"><button class="back">${svg('back')}رجوع</button></div>`;
    const n0 = (v) => Math.round(v).toLocaleString('en-US');
    const NOUN = {
      day: ['يوم واحد', 'يومين', 'أيام', 'يوم'], camel: ['ناقة وحدة', 'ناقتين', 'نياق', 'ناقة'],
      edition: ['دورة وحدة', 'دورتين', 'دورات', 'دورة'], fest: ['مهرجان واحد', 'مهرجانين', 'مهرجانات', 'مهرجان'],
      month: ['شهر واحد', 'شهرين', 'شهور', 'شهر'],
    };
    const count = (n, k) => { const [one, two, few, many] = NOUN[k]; return n === 1 ? one : n === 2 ? two : n >= 3 && n <= 10 ? `${n} ${few}` : `${n} ${many}`; };
    const days = (n) => count(n, 'day');
    const WEEKDAY = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'];
    const MONTH = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'];
    const REGION = { riyadh: 'الرياض', qassim: 'القصيم', hail: 'حائل', jouf: 'الجوف', northern: 'الحدود الشمالية', sharqiya: 'الشرقية', tabuk: 'تبوك', najran: 'نجران' };
    const COAT = { wodh: ['وضحاء', 'وضح'], shoqh: ['شقحاء', 'شقح'], shoal: ['شعلاء', 'شعل'], sofr: ['صفراء', 'صفر'], homr: ['حمراء', 'حمر'], majaheem: ['مجهمية', 'مجاهيم'] };
    const FAMILY = { wodh: 'الوضح', shoqh: 'الشقح', shoal: 'الشعل', sofr: 'الصفر', homr: 'الحمر', majaheem: 'المجاهيم' };
    const PHOTO = { wodh: 'camel_side_wodh.png', shoqh: 'thumb_shaqh.png', shoal: 'thumb_shaal.png', sofr: 'thumb_safra.png', majaheem: 'thumb_majaheem.png', homr: 'thumb_shaal.png' };
    const fem = (c) => c.sex === 'female';
    const her = (c, f, m) => (fem(c) ? f : m);
    const titleOf = (c) => `${c.ageName} ${COAT[c.category][fem(c) ? 0 : 1]}`;
    const photo = (c) => `<img src="phone/${PHOTO[c.category]}" alt=""${c.category === 'homr' ? ' class="homr"' : ''}>`;
    const rng = (lo, hi) => `<bdi dir="ltr">${n0(lo)}–${n0(hi)}</bdi>`;
    const alertCard = (title, line) => `<div class="warn"><span class="lead">${svg('alert')}</span><b>${title}</b><small>${line}</small></div>`;
    // ---- dates: the engine's game days as the phone says them
    const t0 = Date.parse(S.date + 'T00:00:00Z');
    const dateOf = (day) => new Date(t0 + (day - S.today) * 864e5);
    const dd = (day) => { const d = dateOf(day); return `${WEEKDAY[d.getUTCDay()]} ${d.getUTCDate()} ${MONTH[d.getUTCMonth()]}`; };
    const dShort = (day) => { const d = dateOf(day); return `${d.getUTCDate()} ${MONTH[d.getUTCMonth()]}`; };
    // a festival's days: «من 18 لين 21 أكتوبر», «من 1 ديسمبر لين 3 يناير»
    const span = (f) => { const a = dateOf(f.startsOn), z = dateOf(f.endsOn); if (f.startsOn === f.endsOn) return dShort(f.startsOn); return a.getUTCMonth() === z.getUTCMonth() ? `من ${a.getUTCDate()} لين ${dShort(f.endsOn)}` : `من ${dShort(f.startsOn)} لين ${dShort(f.endsOn)}`; };
    const inDays = (day) => { const n = day - S.today; return n <= 0 ? 'اليوم' : n === 1 ? 'بكرة' : `بعد ${days(n)}`; };

    // ---- the festival open for registration, and its page (the engine's)
    const D = G.detail, F = D.festival;
    const coming = S.festivals.filter((f) => !f.done && f.id !== F.id).sort((a, b) => a.startsOn - b.startsOn);
    const rounds = D.rounds;
    const cats = [...new Set(rounds.filter((r) => r.cat).map((r) => r.cat))];
    const missing = Object.keys(FAMILY).filter((k) => !cats.includes(k));
    const kindRound = (k) => rounds.find((r) => r.kind === k);
    const myR = rounds.find((r) => r.id === G.rNoura);
    const noura = myR.myEntries.flat()[0] || S.yard.find((c) => c.sex === 'female');
    const calf = S.yard.find((c) => c.id !== noura.id), nimr = G.nimr;
    const KIND = { fardiJil: 'الفردي جل', fardiDiq: 'الفردي دق', mafareed: 'مفاريد القعدان والبكار', diq: 'دق القعدان والبكار', fahal: 'الفحل وإنتاجه', jamal: 'الجمل' };
    const myRound = `${KIND[myR.kind]} · ${FAMILY[myR.cat]}`;
    const late = FR.lateEntryFee, hours = FR.lateEntryHoursBefore;
    const bar = (c, line, end = '') => `<div class="strip"><span class="ph">${photo(c)}</span><span><b>${c.name} · ${titleOf(c)}</b><small>${line}</small></span>${end}</div>`;
    const free = myR.entryFee === 0 ? 'ببلاش' : `بـ ${n0(myR.entryFee)} ريال`;      // PLACEHOLDER: free until the closing (no real figure found)

    // ---------------------------------------------------------------- 1 the festivals
    const rest = coming.length - 3;
    const comingRow = (f) => `<div class="row"><span class="lead">${svg('cup')}</span><b>${f.name}</b><span class="qty">${n0(f.topPrize)}</span><small>${span(f)} · التسجيل ${f.opensOn > S.today ? `من ${dShort(f.opensOn)}` : `لين ${dShort(f.closesOn)}`}</small></div>`;
    const fests = `<div class="body">${nav()}<div class="title">المزاين</div>
      <div class="open"><span class="tag">التسجيل مفتوح</span><b>${F.name}</b><small>${REGION[F.region]} · ${span(F)}</small>
        <small>التسجيل ${free} لين ${dd(F.closesOn)}، وبعده بـ ${n0(late)} ريال لين قبل كل شوط بـ ${hours} ساعة</small>
        <small>جايزة الأول لين ${n0(F.topPrize)} ريال</small></div>
      <div class="sec">مشاركاتك</div>
      <div class="group"><div class="row"><span class="lead">${svg('camel')}</span><b>${noura.name} · ${myRound}</b><span class="act"><button class="btn ghost" aria-label="اسحب ${noura.name} من الشوط">اسحبها</button></span><small>شوطها ${dd(myR.day)} (${inDays(myR.day)})</small></div></div>
      <div class="sec">الجاية · جايزة الأول بالريال</div>
      <div class="group">${coming.slice(0, 3).map(comingRow).join('')}</div>
      ${rest > 0 ? `<div class="note">وبعدها ${count(rest, 'fest')} لين ${MONTH[dateOf(coming[coming.length - 1].endsOn).getUTCMonth()]}.</div>` : ''}</div>`;

    // ---------------------------------------------------------------- 2 and 3 a festival opened
    const rnd = (icon, name, line, prize) => `<div class="row"><span class="lead">${svg(icon)}</span><b>${name}</b><span class="qty">${prize}</span><small>${line}</small></div>`;
    const dayOf = (k) => rounds.find((r) => r.cat === k && r.kind === 'fardiJil').day;
    const fahal = kindRound('fahal');
    const later = ['الجمل', 'المنقية', 'البداوة', 'الهجيج', 'الطبع'];
    const fest = `<div class="body">${nav()}<div class="title">${F.name}</div>
      <div class="tank"><small>${REGION[F.region]} · ${span(F)}</small>
        <div class="kind"><span>التسجيل ${free}</span><span class="d">لين ${dd(F.closesOn)}</span></div>
        <div class="kind"><span>وبعده بـ ${n0(late)} ريال تأخير</span><span class="d">لين قبل الشوط بـ ${hours} ساعة</span></div></div>
      <div class="sec">الأشواط · جايزة الأول بالريال</div>
      <div class="group">
        ${rnd('camel', KIND.fardiJil, 'النياق من ثاني ولادة وفوق', n0(kindRound('fardiJil').prizes[0]))}
        ${rnd('camel', KIND.fardiDiq, 'النياق من بعد المفرودة لين الجذعة', n0(kindRound('fardiDiq').prizes[0]))}
        ${rnd('camel', KIND.mafareed, 'من سنة لين سنتين', n0(kindRound('mafareed').prizes[0]))}
        ${rnd('camel', KIND.diq, 'من بعد المفرود لين الجذع', n0(kindRound('diq').prizes[0]))}
        ${rnd('star', KIND.fahal, `الفحل ومعه ${fahal.size - 1} من إنتاجه · النتيجة بعد فحص الحمض النووي`, n0(fahal.prizes[0]))}</div>
      <div class="sec">كل لون بيومه</div>
      <div class="group">${[...new Set(cats.map(dayOf))].sort((a, b) => a - b).map((d) => `<div class="row two"><span class="lead">${svg('camel')}</span><b>${dd(d)}</b><small>${cats.filter((k) => dayOf(k) === d).map((k) => FAMILY[k]).join('، ')}</small></div>`).join('')}</div>
      ${missing.length ? `<div class="note">وما فيه ${missing.map((k) => FAMILY[k]).join(' ولا ')} بهالمهرجان.</div>` : ''}
      <div class="group"><div class="row two later"><span class="lead">${svg('herd')}</span><b>الأشواط الجماعية تجي بعدين</b><small>${later.join('، ')}</small></div></div>
      <div class="sec">الشروط</div>
      <div class="group">
        <div class="row two"><span class="lead">${svg('rule')}</span><b>ناقة وحدة بشوط فردي واحد</b><small>بكل مهرجان. والمفاريد والدق والفحل وإنتاجه غيره</small></div>
        <div class="row two"><span class="lead">${svg('chip')}</span><b>الشريحة باسمك</b><small>هي وثيقة الملكية الوحيدة، والتسجيل من هنا</small></div>
        <div class="row two"><span class="lead">${svg('eye')}</span><b>العمر يُفحص بالأسنان يوم الشوط</b><small>واللون والشوط ما يتغيرون بعد الإغلاق</small></div></div>
      <button class="sell" style="position:static;box-shadow:none;margin-bottom:6px">${svg('plus')}سجّل ناقة</button></div>`;

    // ---------------------------------------------------------------- 4 registering
    // the engine's refusals in the phone's words
    const REASON = {
      ownershipTooRecent: (c, p) => `${her(c, 'اشتريتها', 'اشتريته')} اليوم، ولازم ${her(c, 'تكون', 'يكون')} باسمك ${days(p.days)} قبل الشوط`,
      wrongAgeClass: (c) => `${her(c, 'صغيرة', 'صغير')}، وأصغر شوط للمفاريد من سنة`,
      wrongCategory: (c) => `ما فيه شوط ل${FAMILY[c.category]} بهالمهرجان`,
      sick: (c) => her(c, 'مريضة، ما تدخل لين تطيب', 'مريض، ما يدخل لين يطيب'),
      listedForSale: (c) => her(c, 'معروضة بالحراج، شيل الإعلان أول', 'معروض بالحراج، شيل الإعلان أول'),
    };
    const why = (c, err) => (REASON[err.code] ? REASON[err.code](c, err.params || {}) : err.code);
    const camelIt = (c, round, line, reason, sel) => `<div class="it${sel ? ' sel' : ''}${reason ? ' no' : ''}"><span class="ph">${photo(c)}</span><b>${c.name} · ${titleOf(c)}</b><small>${round}</small><small${reason ? ' class="bad"' : ''}>${reason || line}</small></div>`;
    const t1 = D.transportPerHead;
    const enter = `<div class="body">${nav()}<div class="title">سجّل ناقة</div>
      <div class="note" style="margin-top:-4px">${F.name} · كل ناقة وشوطها من لونها وعمرها</div>
      <div class="lst flat">
        ${camelIt(noura, `شوطها ${myRound} · ${dShort(myR.day)}`, `مرضع وعشار · ${noura.health === 'healthy' ? 'صحتها زينة' : 'مريضة'}`, '', true)}
        ${camelIt(nimr, `شوطه ${KIND[G.rNimr]} · ${FAMILY[nimr.category]}`, '', why(nimr, G.refusals.nimr))}
        ${calf ? camelIt(calf, `${her(calf, 'ترضع من أمها', 'يرضع من أمه')} ${noura.name}`, '', why(calf, G.refusals.calf)) : ''}</div>
      <div class="tank"><small>اللي تدفعه عن ${noura.name}</small>
        <div class="kind"><span>التسجيل</span><span class="d">${free} لين ${dShort(F.closesOn)}، وبعده ${n0(late)} ريال لين ${dShort(myR.lastEntryDay)}</span></div>
        <div class="kind"><span>نقلها لـ${REGION[F.region]} ورجعتها</span><span class="d">${n0(t1)} ريال يوم الشوط</span></div></div>
      <button class="btn pri" style="width:100%">سجّل ${noura.name} بشوط الجل</button>
      <div class="note">تقدر تسحبها لين يوم شوطها، وبعد ما يقفل التسجيل ما ترجع تسجّلها بهالمهرجان. وما تقدر تبيعها وهي مسجلة.</div></div>`;

    // ---------------------------------------------------------------- 5 and 6 the secret treatment
    // the kinds' names (TamperKind.label) and the features (Trait) in the phone's words; the figures are the engine's
    const TK = { botox: 'بوتوكس', filler: 'فيلر', hormones: 'هرمونات', lipStretch: 'شد الشفة', teethFiling: 'برد الأسنان', tailCut: 'قص الذيل', dye: 'الصبغ' };
    const TRAIT = { lips: 'الشفايف', nose: 'الخشم', head: 'الراس', hump: 'السنام', hind: 'المؤخرة', coat: 'الوبر', neck: 'الرقبة', ears: 'الأذان', back: 'الظهر', fore: 'المقدمة', stance: 'الوقفة' };
    const raises = (k) => `يرفع ${k.traits.map((t) => TRAIT[t]).join(' و')}`;
    // how often a festival finds it, in a word, from the engine's chance (the chance itself is not shown)
    const often = (p) => (p < 0.45 ? 'ينكشف أحيان' : p < 0.7 ? 'ينكشف كثير' : 'ينكشف أغلب المرات');
    const chatTop = `<div class="nav"><button class="back" aria-label="رجوع">${svg('back')}</button><div class="chathd"><span class="av">س</span><span><b>أبو سند</b><small>يجمّل الحلال بالسر</small></span></div></div>`;
    const chatHead = `${chatTop}
      ${bar(noura, `${myRound} · ${F.name}`, `<span class="lim">الشوط<span>${dShort(myR.day)}</span></span>`)}`;
    const kindRow = (k) => `<div class="row"><span class="lead">${svg('scope')}</span><b>${TK[k.kind]}</b><span class="qty" aria-hidden="true">${svg('chev')}</span><small>${raises(k)} · من ${n0(k.price[0])} ريال · الغرامة لين ${n0(k.fineCap)}</small></div>`;
    const cheat = `<div class="body">${chatTop}
      <div class="chat">
        <div class="msg them">أقدر أزيّن ${noura.name} قبل الشوط. بيني وبينك. وش تبي؟</div></div>
      <div class="group">${FR.tamperKinds.map(kindRow).join('')}</div></div>`;
    const K = FR.tamperKinds.find((k) => k.kind === 'botox');
    const STR = ['خفيف', 'وسط', 'قوي'];
    const strRow = (i) => `<div class="row"><span class="lead">${svg('scope')}</span><b>${STR[i]}</b><span class="act"><button class="btn ghost pr" aria-label="${TK[K.kind]} ${STR[i]} بـ ${n0(K.price[i])} ريال">${n0(K.price[i])} ريال</button></span><small>${often(K.festivalCatch[i])} · الغرامة ${n0(K.fine[i])} ريال</small></div>`;
    const strength = `<div class="body">${chatHead}
      <div class="chat"><div class="msg me">${TK[K.kind]}.</div>
        <div class="msg them">${raises(K)} يوم التحكيم ويغلّي سعرها، ويبقى فيها ${days(K.lastsDays)}. خفيف ولا وسط ولا قوي؟</div></div>
      <div class="group">${[0, 1, 2].map(strRow).join('')}</div>
      <div class="note">كل ما قوي يبيّن أكثر، وينكشف أكثر، وغرامته أكبر.</div>
      ${alertCard('لو انكشف', `بالمهرجان تطلع ${noura.name} من الشوط على طول وتنكتب عليك الغرامة، وتنحرم أنت وحلالك من كل المهرجانات، هالدورة و${count(FR.banEditionsAfter, 'edition')} جاية، والخبر يطلع. وممكن ينكشف بالحراج أو عند البيطري وتنغرم، وصيتك ينزل. ولو بعتها يروح معها.`)}</div>`;

    // ---------------------------------------------------------------- 7 the day: the six stages (GDD 7)
    // the field after each stage is the engine's (game 1); the day tells the stages one by one: the engine judges the
    // round at once, so the hour each is told is the screen's (PLACEHOLDER words: الظهر، العصر، المغرب)
    const fld = A.field, entered = myR.rivals + 1;
    const lost = (i) => (i === 0 ? entered : fld[i - 1]) - fld[i];
    const stage = (cls, icon, name, line, right) => `<div class="row ${cls}"><span class="lead">${svg(icon)}</span><b>${name}</b><span class="qty ${right[0]}">${right[1]}</span><small>${line}</small></div>`;
    const outLine = (i) => (lost(i) ? ` · طلعت ${count(lost(i), 'camel')}` : '');
    const head = `${nav()}<div class="title">يوم الشوط</div>
      <div class="note" style="margin-top:-4px">${F.name} · ${myRound} · ${dd(myR.day)}</div>`;
    const day = `<div class="body">${head}
      ${bar(noura, `بالشوط ${count(entered, 'camel')} · باقي ${count(fld[1], 'camel')}`)}
      <div class="group">
        ${stage('', 'check', 'الشريحة والشاهد', `شريحتها باسمك${outLine(0)}`, ['ok', 'عدّت'])}
        ${stage('', 'check', 'فحص الهجين واللون والعمر', `${COAT[noura.category][0]} صافية، و${noura.ageName} بأسنانها${outLine(1)}`, ['ok', 'عدّت'])}
        ${stage('now', 'dot', 'التحكيم الأولي', `اللجنة تختار النص للتحكيم النهائي`, ['now', 'الحين'])}
        ${stage('next', 'eye', 'خبراء التلاعب', 'فحص الشفايف والخشم والوبر', ['wait', 'الظهر'])}
        ${stage('next', 'scope', 'اللجنة الطبية', 'سونار وأشعة وتحاليل', ['wait', 'العصر'])}
        ${stage('next', 'star', 'التحكيم النهائي', 'المراكز والجوايز', ['wait', 'المغرب'])}</div>
      <div class="note">يجيك خبر مع كل مرحلة، ولو قفلت الجوال يكمل الشوط بدونك.</div></div>`;

    // ---------------------------------------------------------------- 8 the results (game 1, played to the day)
    const m = A.mine[0] || {};
    const STAGE_OUT = { preliminary: 'ما تأهلت للتحكيم النهائي', chipWitness: 'طلعت عند الشريحة والشاهد', breedColourAge: 'طلعت بفحص الهجين واللون والعمر', tamperingExperts: 'انكشفت عند خبراء التلاعب', medical: 'انكشفت عند اللجنة الطبية' };
    const outcome = m.rank ? `المركز ${m.rank} من ${count(entered, 'camel')}` : (STAGE_OUT[m.removedAt] || '');
    const place = (r) => `<div class="row"><span class="lead rk${r.rank === 1 ? ' g1' : ''}">${r.rank}</span><b>${r.name}</b><span class="qty">${n0(r.prize)}</span><small>${r.owner || ''}</small></div>`;
    const repWord = A.reputation > 10 ? 'كبر' : A.reputation < 10 ? 'نزل' : 'ما تغير';
    const result = `<div class="body">${nav()}<div class="title">النتيجة</div>
      <div class="note" style="margin-top:-4px">${F.name} · ${myRound} · ${count(entered, 'camel')}</div>
      <div class="it big"><span class="ph">${photo(noura)}</span><b>${noura.name}</b><small class="${m.rank && m.rank <= 10 ? '' : 'bad'}">${outcome}</small><small>${m.removedAt === 'preliminary' ? `اللجنة اختارت ${fld[2]} من ${fld[1]}` : m.prize ? `جايزتها ${n0(m.prize)} ريال نزلت برصيدك` : ''}</small><small>الشوط ما زاد قيمتها شي</small><small>يقدّرونها ${rng(A.estimate[0], A.estimate[1])}</small></div>
      <div class="sec">المراكز · الجايزة بالريال</div>
      <div class="group">${A.places.slice(0, 5).map(place).join('')}</div>
      <div class="note">والجوايز لين العاشر (${n0(A.prizes[9])} ريال). اللي يجي بالعشرة الأوائل تزيد قيمته ويكبر صيته بلونه، وصيتك ب${FAMILY[noura.category]} ${repWord}. والدرجات ما تنعلن. ونقلها ${n0(t1)} ريال انخصم.</div></div>`;

    // ---------------------------------------------------------------- 9 caught (not reached on this seed: see the header)
    // Botox at light strength (with نمر bought, the middle one is past the cash): the engine's fine for it; the balance
    // after it is the engine's cash on the day (game 1) less the treatment's price and the fine
    const fine = K.fine[0], left = A.cash - K.price[0] - fine;
    const money = (v) => `<bdi dir="ltr">${v < 0 ? '−' : ''}${n0(Math.abs(v))}</bdi>`;
    const caught = `<div class="body">${head}
      ${bar(noura, `<span style="color:var(--red);font-weight:600">طلعت من الشوط</span>`)}
      <div class="group">
        ${stage('', 'check', 'الشريحة والشاهد', 'شريحتها باسمك', ['ok', 'عدّت'])}
        ${stage('', 'check', 'فحص الهجين واللون والعمر', `${COAT[noura.category][0]} صافية، و${noura.ageName} بأسنانها`, ['ok', 'عدّت'])}
        ${stage('', 'check', 'التحكيم الأولي', `اختاروها مع ${fld[2] - 1} للنهائي`, ['ok', 'عدّت'])}
        ${stage('bad', 'x', 'خبراء التلاعب', 'لقوا بوتوكس بشفايفها', ['bad', 'انكشفت'])}</div>
      ${alertCard('انكشف البوتوكس', `طلعت ${noura.name} من الشوط، وانكتبت عليك غرامة ${n0(fine)} ريال. وانحرمت أنت وحلالك من كل المهرجانات، هالدورة و${count(FR.banEditionsAfter, 'edition')} جاية، والخبر طلع للملاك.`)}
      ${left < 0 ? alertCard(`رصيدك صار ${money(left)} ريال`, 'ما تقدر تشتري حلال ولا تبني لين تسدد، والعلف والماء يمشون. بيع من حلالك.') : ''}
      <div class="note">وصيتك ب${FAMILY[noura.category]} نزل.</div></div>`;

    return { fests, fest, fest_end: fest, enter, cheat, strength, day, result, caught };
  }, [game, after]);

  const files = [];
  let i = 0;
  if (process.env.AUDIT) fs.writeFileSync(path.join(OUT, 'mazayen_texts.txt'), '');
  for (const [k, html] of Object.entries(screens)) {
    i++;
    await p.evaluate(([html, css]) => {
      const scr = R().querySelector('.scr'), sb = scr.querySelector('.sbar').outerHTML;
      scr.classList.remove('home');
      // a number kept with its word on either side (a no-break space), as الحراج's design does
      scr.innerHTML = `<span class="pill"></span>${sb}${html.replace(/(\d) (?=[؀-ۿ])/g, '$1 ').replace(/([؀-ۿ]) (?=\d)/g, '$1 ')}<div class="hb"></div>`;
      const st = document.createElement('style'); st.textContent = css; scr.appendChild(st);
    }, [html, CSS]);
    if (k.endsWith('_end')) await p.evaluate(() => { const bd = R().querySelector('.body'); bd.scrollTop = bd.scrollHeight; });
    await p.waitForTimeout(400);
    const file = path.join(OUT, `mock_mazayen_${i}_${k}.png`);
    const box = await p.evaluate(() => { const r = R().querySelector('.dev').getBoundingClientRect(); return { x: r.x, width: r.width }; });
    await p.screenshot({ path: file, timeout: 600000, clip: { x: Math.max(0, box.x - 4), y: 0, width: box.width + 8, height: 440 } });
    files.push(file);
    if (process.env.AUDIT) {
      // the layout audit (clipped text, a number split from its word), and the view's texts for a words check
      await p.addScriptTag({ path: process.env.AUDIT });
      const a = await p.evaluate(() => window.__audit());
      console.log(k, 'audit', JSON.stringify({ clipped: a.clipped, ellipsis: a.ellipsis, outside: a.outside, split: a.split, scroll: a.scroll }));
      fs.appendFileSync(path.join(OUT, 'mazayen_texts.txt'), a.texts.filter((t) => !t.includes('{')).join('\n') + '\n');
    }
  }
  await b.close();
  // the nine side by side, a gap between them as in phone_haraj.jpg
  execFileSync('convert', [...files, '-background', '#2a2119', '-splice', '6x0', '+append', '-chop', '6x0', '-quality', '86', path.join(__dirname, 'phone_mazayen.jpg')]);
})();
