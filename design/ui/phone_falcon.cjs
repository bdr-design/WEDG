// الصقور in the phone, ROUND 2 (14 Nov 2026): a DESIGN for the owner's approval, not built (nothing in phone.js or the
// engine). Redrawn for his seven answers on round 1 (docs/agents/hunting_owner_decisions.md), his choice of falcons as
// a second business by trapping (الطرح), the trapping research (docs/proposals/hunting.md section 9, research section
// 8 "Trapping wild passage falcons", sources 184-223) and the proxy's provisional answers (docs/agents/
// proxy_decisions.md, batch 3: marked "proxy" below; his to overturn). Two apps, «نادي الصقور» and «تصريح الصيد» (his
// generic names), eighteen views at the owner's screen (956 x 440, the phone enlarged), in the phone's own CSS and pieces:
//   1 home          the home screen: the six apps, المزاين and المحادثات (being built), and the two new ones: ten
//   2 auctions      the auctions told apart: the trapping auction (1 Oct - 30 Nov, only the passage peregrine of the
//                   year, where the player SELLS his trapped bird or buys one), the falcons exhibition (1-10 Oct,
//                   imported sakers) and the breeders' auction (August, farm-bred sakers): the three routes to the
//                   player's own falcon, each in its month (proxy, batch 3 item 5)
//   3 tonight       the trapping auction's lots: what the bidders see (length, width, weight, where it was trapped)
//   4 trap          الطرح: the trapping permit, the gear he has and lacks with its prices (bought here: the owner's
//                   question, recommended), what gear does in words
//   5 sell          entering his trapped bird: the club's check and trapping document, no fees, travel paid, the
//                   opening bid, alone (partners are the next step: proxy, item 2)
//   6 hammer        the hammer price, the money in full in his balance, the ring and passport to the buyer; marked
//                   as an example (most seasons trap nothing)
//   7 mine          his falcons in the falcons' room (the owner's decision 5): each with its passport and how it came
//                   (trapped and kept: proxy item 6, resale not offered; bought at the breeders' auction), results
//   8 train         الدعو, once each time the game opens, its change in words
//   9 fest, 10 fest_end   مهرجان الصقور (the 2025 dates as an interim choice), الملواح's classes, المزاين's classes
//                   (the peregrine قرناس class dropped in 2024 [188]: شاهين بحري فرخ), the rules
//  11 race_result, 12 beauty_result   the sample falcon: 12th of 31 in the race; out of the prizes in المزاين
//  13 permit, 14 permit_mid, 15 permit_end   the hunting permit and the trapping permit (top, middle, end): seasons, where each is banned, what is
//                   released, the fines in words
//  16 away_card, 17 away_card_end   the card before leaving for a camp: the calendar's own card (task T15,
//                   /home/user/wt/t15 design/ui/phone_calendar.cjs and docs/proposals/rush_and_calendar.md section 5: the
//                   days «تقريبًا», what falls due on the way, the standing order and the vet's contract, its stops, «يمشي
//                   لقدام بس») with the trip's own lines (distance, gear, camp supplies) and the camp's own stops added
//  18 away_summary  the calendar's summary view with the trip's lines above its own; the bird marked «مثال»; the
//                   camp's two stops on their days, by the card's own figures: feed for 7 days -> the 3-day store stop on
//                   day 4; مزاين حائل's registration closing 11 October -> the registration stop on day 8 (8 October)
// (Round 2's view of a fine is dropped: the owner's decision 4 makes the falcon's and the net's buttons warn and not act,
// so no fine for hunting or trapping in a banned place can follow; the fines stay listed on the permit. None is shown.)
// No hunting or trapping engine exists, so no figure here is the game's own. REAL figures (research section 8; all of
// it search-result text or pages read on spa.gov.sa, no regulation text): the hunting season 1 Sep - 31 Jan, autumn to
// 30 Nov, winter from 1 Dec [127][128][167]; by day only [135] (one source); the trapping season and the trapping
// auction 1 Oct - 30 Nov, nightly at Malham [184][185][186] (to 15 Nov in 2020, 2022, 2024 [187][191][188]); only the
// passage peregrine juvenile (فرخ شاهين بحري) trapped in the Kingdom is accepted, not the saker nor the قرناس
// [184][189][185][188]; resident mountain peregrine and lanner banned [194]; the club's team checks the bird and
// documents the trapping, the trapping registration document leads to the passport [190][191][192]; no fees on buying
// or selling [191][190]; transport and lodging to Malham paid [184][189]; the electronic ring and papers after the sale
// [191]; opening bids 30,000-150,000 [217] (the lots' openings 50,000, 70,000 and 150,000 sit inside it); "from about
// 50,000": 2022 sales down to 50,000 [200]; sizes like 15 x 15½ in and 1,010 g as the sale pages give them [187][216]
// (what the width measures is not known); 112,000 on the hammer view: about the median of the 18 sales of 2025 read
// [185][209][211][216][217][219] (an example, not an expectation); the exhibition's two sakers 700,000 and 100,000
// [184] (the year of that exhibition not confirmed: the view says «بالمعرض» only); a farm-bred saker about 19,000 [158]; the 2026 exhibition 1-10 Oct [157]; the الملواح race 400 m [169][171];
// its classes [169][171]; فرخ / قرناس [169]; «الحر عرضه 16 إنش وفوق» [169] (the club's words, what it measures unknown);
// المزاين's classes [172][188]; at most five falcons a round [175] (one source); the first prizes 300,000 [177] (one
// round's split extended to the four classes: game choice); three judges [173]; the owners' round's first two times
// 17.905 and 18.061 s [182]; the fines 10,000 / 5,000 / 100,000 (nets; a moving vehicle) [136]; the 20 km coast [195];
// game is never sold [166]; night and lights banned in the hunting rules [135][136].
// DISAGREEING: the 2026 falcon festival 17-30 Nov [157] or 25 Dec - 10 Jan [181]: drawn with the 2025 dates (interim);
// entries 8 / 6 / 12 [169][174]: 8 a game choice.
// THE GAME'S CHOICE, NOT A RULE: «إلا أرض طرح بموسمها» on the coast line: the hunting rules close the coast to 20 km
// [195], yet the auction takes birds trapped on the coast [197][217]; the research leaves the clash unresolved, and the
// game lets a trapping ground on the coast stand in its season (a game choice, told in the note as a gap).
// PROXY (provisional), its lines word for word: «طلقته: الشاهين الجبلي طير مقيم، وطرحه ممنوع» (item 3); «طلقته: الوكري طير مقيم، وطرحه ممنوع» (item 3); «طلقته: الحر
// مهدد، والمزاد ما يقبل إلا فرخ الشاهين البحري» and «طلقته: المزاد ما يقبل إلا الفرخ» (item 4); the saker and the قرناس released (item 4: the قرناس's release a game choice, no ban found); the
// three routes (item 5); keeping a trapped bird, resale not offered (item 6); trapping lawful only on a trapping ground,
// in its season, with a trapping permit (item 9: the issuer and terms NOT found; its 500-riyal fee a game choice); a net
// off the ground is the hunting fine of 100,000, the button warns and does not act (item 9).
// GAME CHOICES: سهيل bought at the trapping auction for 71,000 (the lowest 2025 sale read [217]); the card before
// leaving's water 14 and feed 7 days, the milk's 450 riyals, 7 hours' drive, 9 days (on a built game: the engine's, as
// the calendar's card reads them; its fill of 2 bags and 12 bales at 452 riyals for 48 days and the vet's contract at
// 1,000 a month and 20 a head are T15's); the summary's lines (the one bird across the sample is براق, marked «مثال»);
// the gear's prices (pigeon 50, the second net 1,200, binoculars 900, the mobile tent 6,500, supplies 150
// a day: no source prices any of it) and that gear is bought in the club's app (the owner's question); the lots, their
// places and sizes (inside the real ranges); the bidders and their bids; the falcons' room holding 4; the falcons' names,
// dates and results; الدعو's steps; the race times past the first two; the ملواح prizes by place, paid to 7th (1,012
// prizes over 139 rounds [170][176]); the fields of 31 and 23; «تصريحك باقي» after a fine; the houbara for the kept
// peregrine (in an estate). The home screen's date, balance and herd are the engine's (seed 4242, 1 October).
// Words: الطرح، الطاروح، الدربيل، الحمام، الشبك as research [204][222][223]; القرموشة and الجير تبع not drawn as species.
// The saker's picture is task T11's render (awaiting the owner's approval); the peregrine is a flat stand-in (not built).
// To draw again: build the prototype (THREE_DIR=<three@0.170.0 package> python3 tool/proto_app/assemble.py), serve
// tool/proto_app/assets/web on a port (PORT, 8765 by default), run `python3 -I design/hunt/cut_bird.py` once (the bird
// cut-outs), and `NODE_PATH=$(npm root -g) node design/ui/phone_falcon.cjs` from the repository's root; it writes
// mock_falcon_<n>_<name>.png in the current folder (or OUT=<folder>) and design/ui/phone_falcon.jpg. AUDIT=<audit.js>
// runs the layout audit on each view and writes the views' texts to falcon_texts.txt.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const PORT = process.env.PORT || 8765;
const OUT = process.env.OUT || '.';

const CSS = `
  .row .qty.ok { color: var(--acc); font: 600 12.5px/1 "IBM Plex Sans Arabic", sans-serif; }
  .row .qty.now { color: var(--amber); font: 700 12.5px/1 "IBM Plex Sans Arabic", sans-serif; }
  .row .qty.wait { color: var(--ink2); font: 500 12px/1 "IBM Plex Sans Arabic", sans-serif; }
  .row.now .lead { background: #fdf1dc; color: var(--amber); }
  .row.next .lead { background: #eeeef1; color: #a5a5ab; }
  .row.next b { color: var(--ink2); font-weight: 500; }
  .row.later .lead { background: #eeeef1; color: #8e8e93; }
  .row .lead.rk { font: 700 15px/1 "Alexandria", sans-serif; }
  .row .lead.rk.g1 { background: #fbefd2; color: #a8730c; }
  .row.me { background: #f3faf6; }
  .row.two { grid-template-columns: 36px 1fr; }
  .open { background: var(--card); border-radius: 18px; padding: 12px 14px; display: flex; flex-direction: column; gap: 3px; box-shadow: inset 0 0 0 1.5px #bfe3d2; }
  .open .tag { align-self: flex-start; font-size: 11px; font-weight: 700; color: var(--acc); background: var(--acc-soft); border-radius: 8px; padding: 2px 8px; }
  .open .tag.amb { color: var(--amber); background: #fdf1dc; }
  .open b { font: 700 17px/1.3 "Alexandria", sans-serif; }
  .open small { font-size: 12px; color: var(--ink2); }
  .row .act .btn.pr { padding-inline: 10px; font-size: 12.5px; }
  .lst { display: flex; flex-direction: column; gap: 8px; }
  .it { display: grid; grid-template-columns: 58px 1fr auto; column-gap: 10px; align-items: center; background: var(--card); border-radius: 16px; padding: 8px 10px; }
  .it .ph { grid-row: span 3; width: 58px; height: 58px; border-radius: 12px; background: linear-gradient(180deg, #eef2f6, #dfe6ec); overflow: hidden; display: grid; place-items: center; }
  .it .ph svg { width: 100%; height: 100%; }
  .it b { font-size: 13.5px; font-weight: 600; } .it small { font-size: 11.5px; color: var(--ink2); }
  .it .pr { grid-row: span 3; text-align: end; } .it .pr .price { font: 700 15px/1.1 "Alexandria", sans-serif; display: block; } .it .pr small { display: block; }
  .it.big { grid-template-columns: 84px 1fr; } .it.big .ph { width: 84px; height: 84px; grid-row: span 4; }
  .sbar .clk { font-size: 0; } .sbar .clk::after { content: "9:41"; font-size: 14px; }
  .it .ph img { height: 56px; width: auto; display: block; } .it.big .ph img { height: 82px; }
  .it.two { grid-template-columns: 58px 1fr; }
  .it.lot { grid-template-columns: 58px 1fr 76px; } .it.lot b, .it.lot small { grid-column: 2; } .it.lot .pr { grid-column: 3; grid-row: 1 / span 3; display: flex; flex-direction: column; align-items: flex-end; gap: 2px; }
  /* the calendar's card and summary (task T15, design/ui/phone_calendar.cjs in /home/user/wt/t15), copied as they are */
  .row .lead.fest { background: #fbefd2; color: #a8730c; } .row .lead.me { background: #fde6e4; color: var(--red); }
  .row .lead.milk { background: #e6eef8; color: #2f7fcf; } .row .lead.brd { background: var(--acc-soft); color: var(--acc); }
  .span { background: var(--card); border-radius: 16px; padding: 10px 12px; display: flex; flex-direction: column; gap: 2px; }
  .span b { font: 700 15px/1.3 "Alexandria", sans-serif; } .span small { font-size: 12px; color: var(--ink2); }
  .stops { font-size: 12px; line-height: 1.55; background: var(--card); border-radius: 16px; padding: 10px 12px; color: var(--ink); }
  .row .act .btn.sm { height: 34px; padding-inline: 12px; font-size: 12.5px; } .row.two2 { grid-template-columns: 36px 1fr auto; } .btn.wide { width: 100%; }
  .apps .app .ic.new { box-shadow: 0 0 0 2px #e8b46c, 0 3px 8px rgba(70,50,20,.14); }
`;
// the saker's picture: task T11's render (awaiting the owner's approval), cut out by design/hunt/cut_bird.py; the
// peregrine is not built yet: a flat STAND-IN (dark helmet and moustache, barred breast)
const SAKER = `<img src="data:image/png;base64,${fs.readFileSync(path.join(__dirname, '../hunt/birds/saker_alert_side.png')).toString('base64')}" alt="">`;
const PERE = `<svg viewBox="0 0 60 60"><path d="M22 58 C18 44 20 30 28 22 C32 16 40 15 44 20 C48 26 47 40 42 58 Z" fill="#5d6670"/>
  <path d="M28 30 C33 34 39 34 44 30 L44 56 L24 56 Z" fill="#e9e1d2"/><path d="M27 38 h16 M26 44 h18 M25 50 h19" stroke="#59606a" stroke-width="1.6" stroke-dasharray="2 2"/>
  <path d="M29 22 C28 12 34 7 40 8 C46 9 48 15 45 22 Z" fill="#2f3338"/><path d="M45 14 l6 2 -5 3" fill="#e9c84a"/><circle cx="41" cy="14" r="2.2" fill="#111"/>
  <path d="M38 16 c1 4 0 7 -2 9" stroke="#1d2024" stroke-width="3" fill="none"/></svg>`;

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  await p.route('**/index.html', async (r) => { const res = await r.fetch(); await r.fulfill({ response: res, body: (await res.text()).replace('startEngine({ onSnapshot:', 'startEngine({ newGame: { seed: 4242 }, onSnapshot:') }); });
  await p.goto(`http://127.0.0.1:${PORT}/index.html`, { timeout: 600000 });
  await p.waitForFunction(() => window.marahEngine && window.marahEngine.snapshot, null, { timeout: 600000 });
  await p.waitForTimeout(2500);
  await p.evaluate(() => { window.requestAnimationFrame = () => 0; });
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone')).shadowRoot; window.__phone.toggle(); window.__phone.enlarge(); });
  await p.waitForTimeout(600);

  const screens = await p.evaluate(([SAKER, PERE]) => {
    const I = {
      back: '<path d="M9 6l6 6-6 6"/>', plus: '<path d="M12 5v14M5 12h14"/>', minus: '<path d="M5 12h14"/>',
      alert: '<path d="M12 4 2.5 20h19z"/><path d="M12 10v4.5M12 17.5v.01"/>',
      check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>', dot: '<circle cx="12" cy="12" r="4.2" fill="currentColor"/>',
      cup: '<path d="M7.5 4h9v5.5a4.5 4.5 0 0 1-9 0z"/><path d="M7.5 6H4.8c0 2.4 1.2 3.8 3.2 4.2M16.5 6h2.7c0 2.4-1.2 3.8-3.2 4.2"/><path d="M12 14v3.5M9.5 17.5h5v3h-5z"/>',
      talk: '<path d="M4 5.5h16v10H9l-5 4z"/>',
      falcon: '<path d="M2.5 10c3 0 5.5 1 7.5 3l2-3 2 3c2-2 4.5-3 7.5-3-2.8 1.8-4.8 3.6-6.6 4.6L14 19h-4l-.9-4.4C7.3 13.6 5.3 11.8 2.5 10z"/>',
      permit: '<rect x="4" y="3.5" width="16" height="17" rx="2"/><path d="M8 8h8M8 12h5"/><path d="M13.5 17.5l1.8 1.6 3.2-3.6"/>',
      rule: '<rect x="5" y="3.5" width="14" height="17" rx="2"/><path d="M8.5 8h7M8.5 12h7M8.5 16h4"/>',
      clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
      sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M5.3 5.3l1.8 1.8M16.9 16.9l1.8 1.8M5.3 18.7l1.8-1.8M16.9 7.1l1.8-1.8"/>',
      user: '<circle cx="12" cy="8" r="3.2"/><path d="M5.5 19.5c.6-3.3 3-5 6.5-5s5.9 1.7 6.5 5"/>',
      ban: '<circle cx="12" cy="12" r="8.5"/><path d="M6 6l12 12"/>',
      map: '<path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2z"/><path d="M9 4v14M15 6v14"/>',
      scale: '<path d="M12 4v16M6 20h12"/><path d="M5 8h14"/><path d="M5 8l-2.5 6h5zM19 8l-2.5 6h5z"/>',
      lure: '<path d="M4 4c5 2 8 6 9 10"/><circle cx="15" cy="17" r="3.2"/>',
      flag: '<path d="M5 21V4M5 4h11l-2 4 2 4H5"/>',
      eye: '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z"/><circle cx="12" cy="12" r="2.6"/>',
      star: '<path d="M12 3.8l2.5 5.2 5.7.8-4.1 4 1 5.6-5.1-2.7-5.1 2.7 1-5.6-4.1-4 5.7-.8z"/>',
      chip: '<rect x="6.5" y="6.5" width="11" height="11" rx="2"/><path d="M9.5 3v3.5M14.5 3v3.5M9.5 17.5V21M14.5 17.5V21M3 9.5h3.5M3 14.5h3.5M17.5 9.5H21M17.5 14.5H21"/>',
      pigeon: '<path d="M4 14c2-4 6-6 10-5l3-3 1 3c1.5 1 2.5 2.5 2 4-2 3-6 5-10 4-2.5-.5-4.5-1.5-6-3z"/><path d="M9 18l-1 3M12 18.5l.5 2.5"/>',
      net: '<path d="M4 4l16 16M20 4L4 20M12 3v18M3 12h18"/><rect x="3" y="3" width="18" height="18" rx="3"/>',
      tent: '<path d="M2 19h20M4 19l8-14 8 14"/><path d="M12 5v14M9 19l3-5 3 5"/>',
      binoc: '<circle cx="7" cy="15" r="3.5"/><circle cx="17" cy="15" r="3.5"/><path d="M7 11.5V6h3v5M17 11.5V6h-3v5M10 13h4"/>',
      box: '<path d="M3.5 7.5L12 3l8.5 4.5v9L12 21l-8.5-4.5z"/><path d="M3.5 7.5L12 12l8.5-4.5M12 12v9"/>',
      gavel: '<path d="M14 4l6 6M11 7l6 6M12.5 5.5l-5 5M18.5 11.5l-5 5M8.5 9.5L3 15l3 3 5.5-5.5"/>',
      room: '<path d="M3 20h18M5 20V9l7-5 7 5v11"/><path d="M9 20v-6h6v6"/>',
    };
    const svg = (k) => `<svg class="i" viewBox="0 0 24 24">${I[k]}</svg>`;
    const nav = () => `<div class="nav"><button class="back">${svg('back')}رجوع</button></div>`;
    const ph = `<span class="ph">${SAKER}</span>`, pp = `<span class="ph">${PERE}</span>`;
    const row = (icon, name, line, right = '', cls = '') => `<div class="row${cls ? ' ' + cls : ''}"><span class="lead">${svg(icon)}</span><b>${name}</b>${right ? `<span class="qty">${right}</span>` : ''}<small>${line}</small></div>`;
    const row2 = (icon, name, line, cls = '') => `<div class="row two${cls ? ' ' + cls : ''}"><span class="lead">${svg(icon)}</span><b>${name}</b><small>${line}</small></div>`;
    const alertCard = (title, line) => `<div class="warn"><span class="lead">${svg('alert')}</span><b>${title}</b><small>${line}</small></div>`;
    const seg = (on) => `<div class="seg" style="grid-template-columns:repeat(4,1fr)">${['المزاد', 'صقوري', 'الطرح', 'المهرجان'].map((t, i) => `<span${i === on ? ' class="on"' : ''}>${t}</span>`).join('')}</div>`;

    // ------------------------------------------------ 1 home: the real home (phone.js), the approved two and the new two
    const home = R().querySelector('.scr').innerHTML;
    const appEl = (k, n, badge, isNew) => `<div class="app">${badge ? `<span class="bd">${badge}</span>` : ''}<span class="ic${isNew ? ' new' : ''}">${svg(k)}</span><span>${n}</span></div>`;
    const homeHtml = home.replace('</div></div></div><div class="hb">', `${appEl('cup', 'المزاين')}${appEl('talk', 'المحادثات')}${appEl('falcon', 'نادي الصقور', 1, true)}${appEl('permit', 'تصريح الصيد', 0, true)}</div></div></div><div class="hb">`);

    // ------------------------------------------------ 2 the auctions told apart, and the three routes to a falcon
    const auctions = `<div class="body">${nav()}<div class="title">نادي الصقور</div>${seg(0)}
      <div class="open"><span class="tag">مفتوح الحين</span><b>مزاد الطرح</b><small>ملهم · من 1 أكتوبر لين 30 نوفمبر، كل ليلة</small><small>فروخ الشاهين البحري المطروحة بالمملكة بس</small><small>تبيع فيه طيرك اللي طرحته، أو تشتري</small></div>
      <div class="sec">وصقرك له ثلاث طرق، كل وحدة بشهرها</div>
      <div class="group">${row('gavel', 'مزاد الطرح', 'فرخ شاهين بحري · من حوالي 50,000', 'الحين')}${row('star', 'معرض الصقور', 'حر مستورد، وأسعاره عالية', 'لين 10 أكتوبر')}${row('falcon', 'مزاد صقور المزارع', 'ملهم · حر فرخ إنتاج مزارع', 'أغسطس')}</div>
      <div class="tank"><small>مزاد الطرح ما يقبل الحر ولا القرناس</small><div class="kind"><span>حرين مستوردة بالمعرض</span><span class="d">700,000 و100,000 ريال</span></div><div class="kind"><span>حر المزارع</span><span class="d">حوالي 19,000 ريال</span></div></div></div>`;

    // ------------------------------------------------ 3 the trapping auction tonight: what the bidders see
    const lot = (name, line, bid, left) => `<div class="it lot">${pp}<b>${name}</b><small>${line}</small><span class="pr"><span class="price num">${bid}</span><small>الافتتاح</small></span><small>${left}</small></div>`;
    const tonight = `<div class="body">${nav()}<div class="title">مزاد الليلة</div>
      <div class="note" style="margin-top:-4px">مزاد الطرح · ملهم · كل طير بطوله وعرضه ووزنه ومكان طرحه</div>
      <div class="lst">
        ${lot('فرخ شاهين', 'الحماد · 15 × 15½ إنش · 1,010 غرام', '70,000', 'شاهين بحري · طرح قبل يومين')}
        ${lot('فرخ شاهين', 'الخفجي · 15¼ × 15¼ إنش · 960 غرام', '50,000', 'شاهين بحري · طرح أمس')}
        ${lot('فرخ شاهين', 'الليث · 15½ × 15½ إنش · 1,040 غرام', '150,000', 'شاهين بحري · طرح أمس')}</div>
      <div class="group">${row2('eye', 'وش يسوي بالصيد ما ينعرف', 'ولا قيمته قبل المزاد: المزاد يقولها')}${row2('rule', 'ما فيه رسوم', 'لا على البايع ولا على المشتري')}</div></div>`;

    // ------------------------------------------------ 4 الطرح: the permit, the gear (bought here: a question), the grounds
    const gear = (icon, name, line, have) => `<div class="row"><span class="lead">${svg(icon)}</span><b>${name}</b><span class="qty ${have ? 'ok' : 'wait'}">${have}</span><small>${line}</small></div>`;
    const trap = `<div class="body">${nav()}<div class="title">نادي الصقور</div>${seg(2)}
      <div class="group">${row('permit', 'تصريح الطرح', 'ساري لين 30 نوفمبر · بأراضي الطرح بس', 'عندك')}</div>
      <div class="sec">عدة الطاروح · السعر بالريال</div>
      <div class="group">
        ${gear('pigeon', 'الحمام', 'عندك 6 حمامات · الحمامة 50', 'عندك')}
        ${gear('net', 'شبك الحمام', 'الشبك على ظهر الحمامة', 'عندك')}
        ${gear('net', 'شبك الطيور والجربوع', 'لو الصقر ما يبي الحمام · 1,200', '')}
        ${gear('binoc', 'الدربيل', 'تشوف الصقر من بعيد · 900', '')}
        ${gear('tent', 'الخيمة المتنقلة', 'تلحق الصقور لأرض ثانية · 6,500', '')}
        ${gear('box', 'مؤونة المخيم', 'ماء وأكل وبنزين · 150 لليوم', 'تكفي 10 أيام')}</div>
      <button class="btn pri" style="width:100%">اشتر الناقص بـ 8,600</button>
      <div class="note">العدة تقرّبك من الطير وما تضمنه: أغلب المواسم تخلص بدون طير.</div></div>`;

    // ------------------------------------------------ 5 entering a trapped bird
    const sell = `<div class="body">${nav()}<div class="title" style="font-size:22px">اعرض طيرك</div>
      <div class="it big">${pp}<b>براق · فرخ شاهين بحري</b><small>طرحته بالحماد 12 أكتوبر</small><small>15 × 15½ إنش · 1,010 غرام</small><small>بالبرقع بغرفة الصقور</small></div>
      <div class="group">${row2('check', 'فريق النادي يفحصه ويوثّق الطرح', 'ويعطيك وثيقة تسجيل طرح')}${row2('box', 'النقل والسكن لملهم عليهم', 'وما فيه رسوم على البيع')}</div>
      <div class="tank"><small>يدخل مزاد الليلة</small>
        <div class="kind"><span>سوم الافتتاح</span><span class="d">70,000 ريال</span></div>
        <div class="kind"><span>تشاركه</span><span class="d">لحالك: السعر كله لك</span></div></div>
      <button class="btn pri" style="width:100%">اعرضه الليلة</button>
      <div class="note">المزايدين يشوفون طوله وعرضه ووزنه ومكان طرحه، وقيمته ما تنعرف إلا بالمزاد. وتقدر تخليه لك بدل ما تبيعه.</div></div>`;

    // ------------------------------------------------ 6 the hammer
    const bid = (who, amt, top) => `<div class="row${top ? ' me' : ''}"><span class="lead">${svg('user')}</span><b>${who}</b><span class="qty">${amt}</span><small>${top ? 'رسى عليه' : 'سام'}</small></div>`;
    const hammer = `<div class="body">${nav()}<div class="title">رسى المزاد</div>
      <div class="it big">${pp}<b>براق</b><small>رسى بـ 112,000 ريال</small><small>نزلت برصيدك كاملة، بدون رسوم</small><small>الحجل الإلكتروني والجواز للمشتري</small></div>
      <div class="sec">آخر الأسوام · بالريال</div>
      <div class="group">${bid('بو فهد', '112,000', true)}${bid('بو ناصر', '110,000')}${bid('بو سعد', '95,000')}</div>
      <div class="note">هذا مثال: أغلب المواسم ما ينطرح فيها طير، وسعر الطير يختلف كثير من ليلة لليلة.</div></div>`;

    // ------------------------------------------------ 7 the player's falcons: each with its passport and how it came
    const mine = `<div class="body">${nav()}<div class="title">نادي الصقور</div>${seg(1)}
      <div class="note" style="margin-top:-4px">بغرفة الصقور · صقرين من 4</div>
      <div class="lst">
        <div class="it two">${pp}<b>سهيل · شاهين بحري فرخ</b><small>اشتريته من مزاد الطرح 20 أكتوبر بـ 71,000</small><small>جوازه باسمك · الطلعات: صاد حبارى بالمحازة مرة</small></div>
        <div class="it two">${ph}<b>غيث · حر فرخ</b><small>اشتريته من مزاد المزارع بأغسطس</small><small>جوازه باسمك · الملواح 18.906 ثانية</small></div></div>
      <div class="group">${row2('rule', 'الطير اللي تطرحه وتخليه لك ما ينعرض للبيع بعدين', 'ما لقينا له طريق نظامي')}</div>
      <button class="btn pri" style="width:100%">ادعهم اليوم</button></div>`;

    // ------------------------------------------------ 8 الدعو
    const step = (cls, icon, name, line, right) => `<div class="row ${cls}"><span class="lead">${svg(icon)}</span><b>${name}</b><span class="qty ${right[0]}">${right[1]}</span><small>${line}</small></div>`;
    const train = `<div class="body">${nav()}<div class="title">الدعو · غيث</div>
      <div class="note" style="margin-top:-4px">صقر جديد يبي 4 أسابيع دعو قبل أول طلعة</div>
      <div class="group">
        ${step('', 'check', 'يرضى بالبرقع والدس', 'الأسبوع الأول', ['ok', 'تم'])}
        ${step('', 'check', 'ياكل على يدك', 'الأسبوع الثاني', ['ok', 'تم'])}
        ${step('now', 'dot', 'يجي للملواح من قريب', 'الأسبوع الثالث', ['now', 'الحين'])}
        ${step('next', 'lure', 'يجي للملواح من بعيد', 'الأسبوع الرابع', ['wait', 'بعدين'])}
        ${step('next', 'falcon', 'جاهز للمقناص', 'بعد الدعو', ['wait', 'بعدين'])}</div>
      <div class="group">${row('scale', 'الميزان', 'تزنه كل يوم قبل أكله', '1,120 غرام')}</div>
      <button class="btn pri" style="width:100%">ادعه اليوم</button>
      <div class="note">مرة وحدة كل ما تفتح اللعبة، وتنحسب لك الأيام اللي فاتت. ولو تركته أسبوعين يرجع خطوة. وبالمقيض بالصيف ما فيه دعو.</div></div>`;

    // ------------------------------------------------ 9, 10 the festival (the 2025 dates, interim) and its rules
    const cls = (name, line, right, act) => `<div class="row"><span class="lead">${svg('lure')}</span><b>${name}</b>${act ? `<span class="act"><button class="btn ghost pr">${act}</button></span>` : `<span class="qty wait">${right}</span>`}<small>${line}</small></div>`;
    const fest = `<div class="body">${nav()}<div class="title">نادي الصقور</div>${seg(3)}
      <div class="open"><span class="tag amb">التسجيل يفتح 25 ديسمبر</span><b>مهرجان الصقور</b><small>ملهم · من 25 ديسمبر لين 10 يناير</small><small>التسجيل أسبوع من أول يوم، ببلاش</small></div>
      <div class="sec">الملواح · سباق 400 متر للملواح</div>
      <div class="group">${cls('الملاك', 'لكل نوع وعمر: فرخ وقرناس', '', 'سجّل')}${cls('الهواة', 'لين تفوز بالملاك', 'بعدين')}${cls('المحترفين والنخبة', 'للصقارين الكبار', 'بعدين')}</div>
      <div class="sec">المزاين · جايزة الأول بالريال</div>
      <div class="group">${row('star', 'الحر', 'فرخ وقرناس', '300,000')}${row('star', 'الجير بيور', 'فرخ وقرناس', '300,000')}${row('star', 'شاهين بحري', 'فرخ', '300,000')}${row('star', 'حر إنتاج محلي', 'فرخ', '300,000')}</div>
      <div class="sec">الشروط</div>
      <div class="group">${row2('chip', 'جوازه باسمك', 'هو إثبات الملكية')}${row2('rule', 'لين 8 صقور لك بكل عمر بالملواح', 'ولين 5 صقور بشوط المزاين')}${row2('eye', 'الحر عرضه 16 إنش وفوق', 'وفيه فحص منشطات')}</div></div>`;

    // ------------------------------------------------ 11, 12 results
    const prize = (rk, name, owner, t, pr) => `<div class="row"><span class="lead rk${rk === 1 ? ' g1' : ''}">${rk}</span><b>${name} · ${t}</b><span class="qty">${pr}</span><small>${owner}</small></div>`;
    const race_result = `<div class="body">${nav()}<div class="title">النتيجة</div>
      <div class="note" style="margin-top:-4px">الملواح · الملاك · حر فرخ · 31 صقر</div>
      <div class="it big">${ph}<b>غيث</b><small>وقته 18.906 ثانية</small><small>المركز 12، والجوايز لين السابع</small><small>وقته ينكتب بسجله</small></div>
      <div class="sec">المراكز · الجايزة بالريال</div>
      <div class="group">${prize(1, 'سهم', 'بو فهد', '17.905', '100,000')}${prize(2, 'ريح', 'بو ناصر', '18.061', '60,000')}${prize(3, 'برق', 'بو سعد', '18.112', '40,000')}${prize(4, 'مزن', 'بو خالد', '18.240', '25,000')}</div>
      <div class="note">والأوقات تنقاس من السناح لين الملواح.</div></div>`;
    const beauty_result = `<div class="body">${nav()}<div class="title">النتيجة</div>
      <div class="note" style="margin-top:-4px">مزاين الصقور · الحر · فرخ · 23 صقر</div>
      <div class="it big">${ph}<b>غيث</b><small>ما جا بالمراكز</small><small>الجوايز للخمسة الأوائل</small><small>يقدر يدخل السنة الجاية قرناس</small></div>
      <div class="sec">المراكز · الجايزة بالريال</div>
      <div class="group">${prize(1, 'الشاهي', 'بو سلطان', 'حر فرخ', '300,000')}${prize(2, 'الريم', 'بو عبدالله', 'حر فرخ', '175,000')}${prize(3, 'سلطانة', 'بو نايف', 'حر فرخ', '100,000')}${prize(4, 'زعزوع', 'بو فيصل', 'حر فرخ', '30,000')}${prize(5, 'هدّاج', 'بو مشعل', 'حر فرخ', '20,000')}</div>
      <div class="note">ثلاث حكام، والدرجات ما تنعلن. وجماله من خلقته، والدعو ما يغيّره.</div></div>`;

    // ------------------------------------------------ 13, 14 تصريح الصيد: the two permits (top, then scrolled)
    const permit = `<div class="body">${nav()}<div class="title">تصريح الصيد</div>
      <div class="tank"><small>تصريح صقار</small><div class="v">ساري</div><div class="ln" style="margin-top:4px">من 1 سبتمبر لين 31 يناير، بالنهار بس</div>
        <div class="kind"><span>فترة الخريف</span><span class="d">لين 30 نوفمبر</span></div>
        <div class="kind"><span>فترة الشتاء</span><span class="d">من 1 ديسمبر</span></div></div>
      <div class="tank"><small>تصريح الطرح</small><div class="v">ساري</div><div class="ln" style="margin-top:4px">من 1 أكتوبر لين 30 نوفمبر، بأراضي الطرح بس</div>
        <div class="kind"><span>الرسوم</span><span class="d">500 ريال</span></div></div>
      <div class="group">${row2('falcon', 'المقناص بالصقر', 'الكروان بالبر، والحبارى بالمحازة المرخصة بس')}${row2('net', 'الطرح', 'فرخ الشاهين البحري، بأرض طرح، بشبك على الحمام')}${row2('user', 'شخصي', 'ما ينعطى لغيرك، وتشيله معك')}</div>
      <div class="sec">ممنوع الصيد فيه</div>
      <div class="group">${row2('ban', 'المدن والقرى والمزارع', 'يعني عزبتك وحولها، والاستراحات')}${row2('ban', 'المحميات والمشاريع الكبرى', 'والمحميات الملكية كلها')}${row2('ban', 'الساحل', 'لين 20 كيلو داخل البر، إلا أرض طرح بموسمها')}</div>
      <div class="sec">بالطرح: لو جا بالشبك</div>
      <div class="group">${row2('ban', 'الشاهين الجبلي', 'طلقته: الشاهين الجبلي طير مقيم، وطرحه ممنوع')}${row2('ban', 'الوكري', 'طلقته: الوكري طير مقيم، وطرحه ممنوع')}${row2('falcon', 'الحر', 'طلقته: الحر مهدد، والمزاد ما يقبل إلا فرخ الشاهين البحري')}${row2('falcon', 'القرناس', 'طلقته: المزاد ما يقبل إلا الفرخ')}${row2('ban', 'بالليل وبالضو', 'ما فيه طرح')}</div>
      <div class="sec">الغرامات</div>
      <div class="group">${row2('alert', 'صيد بدون تصريح', 'غرامته 10,000 ريال')}${row2('alert', 'صيد بمكان أو وقت ممنوع', 'غرامته 5,000 ريال')}${row2('alert', 'الشبك برا أرض الطرح', 'غرامته 100,000 ريال')}${row2('alert', 'الصيد من سيارة تمشي', 'غرامته 100,000 ريال')}</div>
      <div class="note">والصيد نفسه ما ينباع: بيع الصيد ممنوع. اللي ينباع فرخ الشاهين البحري المطروح، بمزاد الطرح بس.</div></div>`;

    // ------------------------------------------------ 16, 17 the card before leaving: the calendar's card (task T15, its words and
    // layout as phone_calendar.cjs draws them), with the trip's own lines added under its own (gear, camp supplies, distance)
    const away_card = `<div class="body">${nav()}<div class="title">قبل ما تمشي</div>
      <div class="span"><b>مخيم طرح بالحماد · لين 10 أكتوبر</b><small>9 أيام · من الخميس 1 أكتوبر · 600 كم، حوالي 7 ساعات سواقة</small></div>
      <div class="sec">يكفي 9 أيام؟</div>
      <div class="group">
        <div class="row two2"><span class="lead">${svg('scale')}</span><b>الماء · يكفي 14 يوم</b><span class="act"><button class="btn sm ghost">عبّه</button></span><small>يكفي الأيام كلها تقريبًا: <span class="pos">يكفي</span></small></div>
        <div class="row two2"><span class="lead me">${svg('box')}</span><b>العلف · يكفي 7 أيام</b><span class="act"><button class="btn sm ghost">عبّه</button></span><small>كيسين و12 ربطة بـ 452 ريال، يصير يكفي 48 يوم تقريبًا</small></div></div>
      <div class="sec">اللي يجي بالطريق</div>
      <div class="group">
        <div class="row two"><span class="lead fest">${svg('cup')}</span><b>مزاين حائل · التسجيل يقفل 11 أكتوبر</b><small>ما سجلت بشي</small></div>
        <div class="row two"><span class="lead milk">${svg('user')}</span><b>ما عليك رواتب</b><small>ما عندك رعاة</small></div></div>
      <div class="sec">مخيمك</div>
      <div class="group">
        <div class="row two"><span class="lead">${svg('pigeon')}</span><b>عدتك: 6 حمامات وشبك الحمام</b><small>ناقصك: الدربيل، الخيمة المتنقلة، شبك الطيور</small></div>
        <div class="row two"><span class="lead">${svg('box')}</span><b>مؤونة المخيم · تكفي 10 أيام</b><small>ماء وأكل وبنزين</small></div></div></div>`;
    const away_card_end = `<div class="body">${nav()}<div class="title">قبل ما تمشي</div>
      <div class="sec">تقدر تجهّز قبل</div>
      <div class="group">
        <div class="row two2"><span class="lead">${svg('box')}</span><b>طلب ثابت للماء والعلف</b><span class="act"><button class="btn sm ghost">شغّله</button></span><small>لما يبقى 3 أيام يجيك الطلب بنفسه، وتدفعه مثل أي طلب</small></div>
        <div class="row two2"><span class="lead">${svg('user')}</span><b>عقد البيطري</b><span class="act"><button class="btn sm ghost">اتعاقد</button></span><small>1,040 ريال بالشهر لحلالك، ويعالج اللي يمرض بيومه</small></div></div>
      <div class="sec">يوقف ويرجع لك لو</div>
      <div class="stops">مرض شي من حلالك، أو مات من مرض أو عطش · قرب العلف أو الماء يخلص (باقي 3 أيام) · نزل رصيدك تحت الصفر، أو وصل حساب التاجر حده · انكتبت عليك غرامة · جاك سوم على إعلان · جا يوم شوطك · باقي 3 أيام على قفل تسجيل مهرجان تقدر تدخله · بدا وقت الضراب وعندك ناقة تنلقح · ضاقت الشبوك على حلالك · خلصت مؤونة المخيم · خلص موسم الطرح</div>
      <div class="note">وكل يوم بالمخيم يرجع لك من الفجر لين الساعة 10، وبالمسا ساعة: الشغل بيدك. وتقدر تفك المخيم وترجع أي وقت.</div>
      <button class="btn pri wide">اطلع للمخيم</button>
      <div class="note">التقويم يمشي لقدام بس: الأيام اللي تمضي ما ترجع.</div></div>`;
    // ------------------------------------------------ 18 the summary: the calendar's summary view with the trip's lines above its own
    const away_summary = `<div class="body">${nav()}<div class="title">اللي صار</div>
      <div class="span"><b>9 أيام · مخيم الحماد</b><small>من الخميس 1 أكتوبر لين السبت 10 أكتوبر</small></div>
      <div class="group">
        <div class="row two"><span class="lead">${svg('net')}</span><b>طرحت فرخ شاهين بحري (مثال)</b><small>اليوم السابع · بغرفة الصقور</small></div>
        <div class="row two"><span class="lead">${svg('falcon')}</span><b>طلقت حر</b><small>اليوم الثالث: المزاد ما يقبله</small></div>
        <div class="row two"><span class="lead">${svg('box')}</span><b>المؤونة والبنزين</b><small>صرفت 1,350 ريال</small></div></div>
      <div class="group">
        <div class="row two"><span class="lead milk">${svg('scale')}</span><b>الحليب دخلك 450 ريال</b><small>ينباع كل يوم</small></div>
        <div class="row two"><span class="lead me">${svg('alert')}</span><b>قرب العلف يخلص</b><small>اليوم الرابع: وقف لك، وطلبته من الجوال ووصل</small></div>
        <div class="row two"><span class="lead fest">${svg('cup')}</span><b>باقي 3 أيام على قفل تسجيل مزاين حائل</b><small>اليوم الثامن: وقف لك، وما سجلت</small></div>
        <div class="row two"><span class="lead brd">${svg('check')}</span><b>ما مرض شي</b><small>وما مات شي</small></div></div>
      <div class="note">هذا مثال: أغلب المواسم ما ينطرح فيها طير. والتفاصيل بالبنك والعزبة.</div></div>`;

    return { home: homeHtml, auctions, tonight, trap, sell, hammer, mine, train, fest, fest_end: fest, race_result, beauty_result, permit, permit_mid: permit, permit_end: permit, away_card, away_card_end, away_summary };
  }, [SAKER, PERE]);


  const files = [];
  let i = 0;
  if (process.env.AUDIT) fs.writeFileSync(path.join(OUT, 'falcon_texts.txt'), '');
  for (const [k, html] of Object.entries(screens)) {
    i++;
    await p.evaluate(([html, css, k]) => {
      const scr = R().querySelector('.scr');
      if (k === 'home') { scr.classList.add('home'); scr.innerHTML = html; }
      else {
        const sb = scr.querySelector('.sbar').outerHTML;
        scr.classList.remove('home');
        // a number kept with its word on either side (a no-break space), as الحراج's design does
        scr.innerHTML = `<span class="pill"></span>${sb}${html.replace(/(\d) (?=[؀-ۿ])/g, '$1 ').replace(/([؀-ۿ]) (?=\d)/g, '$1 ')}<div class="hb"></div>`;
      }
      const st = document.createElement('style'); st.textContent = css; scr.appendChild(st);
    }, [html, CSS, k]);
    if (k.endsWith('_end')) await p.evaluate(() => { const bd = R().querySelector('.body'); bd.scrollTop = bd.scrollHeight; });
    if (k.endsWith('_mid')) await p.evaluate(() => { const bd = R().querySelector('.body'); bd.scrollTop = (bd.scrollHeight - bd.clientHeight) / 2; });
    await p.waitForTimeout(400);
    const file = path.join(OUT, `mock_falcon_${i}_${k}.png`);
    const box = await p.evaluate(() => { const r = R().querySelector('.dev').getBoundingClientRect(); return { x: r.x, width: r.width }; });
    await p.screenshot({ path: file, timeout: 600000, clip: { x: Math.max(0, box.x - 4), y: 0, width: box.width + 8, height: 440 } });
    files.push(file);
    if (process.env.AUDIT) {
      await p.addScriptTag({ path: process.env.AUDIT });
      const a = await p.evaluate(() => window.__audit());
      console.log(k, 'audit', JSON.stringify({ clipped: a.clipped, ellipsis: a.ellipsis, outside: a.outside, split: a.split, scroll: a.scroll }));
      // (the audit's own pattern misses a size such as «15 × 15½ إنش»: this one keeps a whole size with its unit)
      const half = await p.evaluate(() => { const scr = R().querySelector('.scr'), out = []; const w = document.createTreeWalker(scr, NodeFilter.SHOW_TEXT); const re = /\d[\d,.]*[½¼]?(?:[\u00a0 ]×[\u00a0 ]\d[\d,.]*[½¼]?)?[\u00a0 ][\u0600-\u06ff]+/g;
        for (let n; (n = w.nextNode());) { let m; re.lastIndex = 0; while ((m = re.exec(n.nodeValue))) { const r = document.createRange(); r.setStart(n, m.index); r.setEnd(n, m.index + m[0].length); if (new Set([...r.getClientRects()].filter((q) => q.width > 0.5).map((q) => Math.round(q.top))).size > 1) out.push(m[0]); } }
        return out; });
      if (half.length) console.log(k, 'sizes split from their unit', JSON.stringify(half));
      fs.appendFileSync(path.join(OUT, 'falcon_texts.txt'), `## ${k}\n` + a.texts.filter((t) => !t.includes('{')).join('\n') + '\n');
    }
  }
  await b.close();
  execFileSync('convert', [...files, '-background', '#2a2119', '-splice', '6x0', '+append', '-chop', '6x0', '-quality', '86', path.join(__dirname, 'phone_falcon.jpg')]);
})();
