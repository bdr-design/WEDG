// الصقور in the phone: a DESIGN for the owner's approval (13 Nov 2026), not built (nothing in phone.js or the engine).
// Two apps, «نادي الصقور» and «تصريح الصيد» (the owner's generic names, 13 Nov), in thirteen views as the phone draws
// them at the owner's screen (956 x 440, the phone enlarged), in the phone's own CSS and pieces
// (design/prototype3d/phone.js) and the approved المزاين pieces (phone_mazayen.cjs):
//   1 home          the home screen: the six apps there now, the two approved and being built (المزاين, المحادثات:
//                   task T10) and the two new ones: ten, in three rows of four
//   2 auction       نادي الصقور, the auction: the falcons on sale this autumn (wild-caught passage birds, the national
//                   auction's season), each by species, age, origin, last bid and the days left
//   3 falcon        a falcon's page for a buyer: what he sees (species, age, origin, the span, the scale), what stays
//                   hidden (how it hunts and races: only its results tell), and the bid
//   4 mine          صقوري: the player's falcon after a season: its passport, age, species, the scale, its outings and
//                   its contest results
//   5 train         الدعو: the short care, once each time the game opens, for the days since; what changes, in words
//   6 fest          مهرجان الصقور: its days, the registration, الملواح's classes and المزاين's classes and prizes, rules
//   7 race          the ملواح round's day: the times as they come in, the player's falcon still to fly
//   8 race_result   the round's result: the falcon's time and place, the places with times and prizes
//   9 beauty_result مزاين الصقور's result: places and prizes, no scores
//  10 permit_new    تصريح الصيد before it is taken: what it needs and its fee
//  11 permit        the permit held: its season and halves, the means, the quarry, by day only, personal
//  12 permit_end    the same, scrolled: where hunting is banned, what is never hunted, the fines in words
//  13 fine          a violation told (the fine after; the storyboard's frame 9 shows it in play)
// No hunting engine exists yet, so no figure here is the game's own. Each is REAL (research-realism.md section 8, its
// source number; every figure there rests on search-result text only, no official page was opened) or a GAME CHOICE:
//  REAL: the season 1 Sep 2026 – 31 Jan 2027, autumn to 30 Nov, winter from 1 Dec [127][128][129][167]; by day only,
//    an hour after sunrise to an hour before sunset [135] (one source); age 21 and over [135] (one source); the
//    permit for a falconer registered with the club, the falcon with a passport or ownership certificate [128][131];
//    personal, not transferable [164]; carried and shown [131]; the stone-curlew in open land with a falcon [140] (an
//    earlier list: this season's list of 30 species was not found, so no list is shown); the houbara in the licensed
//    estates [142] (open land not confirmed: the game keeps it to the estate, a game choice); the banned places
//    [127][129][134][135]; the never-hunted animals [134][139][141]; fines: no permit 10,000, banned place or time
//    5,000 [136], hunting from a moving vehicle 100,000 [136], any firearm 80,000 [136] (the 2021 table, search
//    summaries); the national auction of locally trapped falcons 1 Oct – 30 Nov [157]; the breeders' auction at Malham
//    in August [158]; trapping without a permit banned [156]; الملواح a 400 m race from the release to the lure
//    [169][171] (300 m in an older edition, 200 m also reported [183]: the distance changes by edition); its classes
//    الملاك، الهواة، المحترفين، النخبة [169][171]; ages فرخ (under a year) and قرناس (over a year) [169]; a saker's span at
//    least 16 inches [169]; المزاين's classes [172] (الحر and الجير بيور, each فرخ and قرناس; شاهين بحري قرناس; حر فرخ إنتاج
//    محلي); proof of ownership and at most five falcons a round [175] (one source; whether five a round or five a
//    falconer is not clear); المزاين's prizes 300,000, 175,000 and 100,000 for the first three [177] (one source); the
//    owners' round's first two times, 17.905 s and 18.061 s [182] (2025, a search summary); doping tests [179]; the
//    2025 festival 25 Dec – 10 Jan at Malham [169][157].
//  DISAGREEING, shown as such: the 2026 festival: 17–30 Nov 2026 [157] or 25 Dec 2026 – 10 Jan 2027 [181]; the views
//    draw the 2025 dates (the last edition the sources agree on) until the owner picks or the club's page is read.
//    Entries a falconer: 8 an age class, 6 for professionals, or 12 in all [169][174]: the game's 8 an age class is a
//    game choice among them. المزاين's 4th and 5th prizes (the round is 625,000 [177], the three add to 575,000, so
//    about 50,000 is left, uncertain): split 30,000 and 20,000, a game choice.
//  GAME CHOICES: every price on the auction and the falcons' bids (the real range: a farm-bred saker about 19,000 to a
//    top bird over a million [158]; no price found for wild-caught birds at the national auction); the span and the
//    weight of each falcon shown; the permit's fee 100 riyals (no official fee found; a weak source gives 100 a season
//    for falconry [160]); the passport's and the club's fees (none found: shown as nothing to pay); the entry fee
//    (not found: free); الدعو's steps and their words, once each time the game opens, and that a new falcon needs four
//    weeks of it before its first outing (real: الدعو in September and early October [155]); the race times past the
//    first two (the game band about 16.5–19 s, inside the real 16.549 s reported as a record in 2022 [183] and the 2025
//    winners 17.653–18.061 s [182]); the ملواح prizes by place (the real split is not known: [169] and [176] disagree)
//    and paying down to the 7th place (1,012 prizes over 139 rounds in 2025 [170][176], about seven a round); the field
//    of 31 falcons (5,200 falcons [157] over 139 rounds is about 37 a round: an estimate from two sources); the
//    falcons' and owners' names; the season's outings and catches; resale gain (none shown as a number).
// Words: الدعو، البرقع، الوكر، الدس، الميزان، الملواح، الطرح، المقناص as research [155][156][169]; القرموشة and الجير تبع are not
// drawn as species (they are likely sex or size classes: unresolved); a falcon's grammar is masculine (الصقر، الطير).
// The falcon pictures are STAND-INS (a flat SVG) until task T11's birds exist (design/birds/).
// To draw again: build the prototype (THREE_DIR=<three@0.170.0 package> python3 tool/proto_app/assemble.py), serve
// tool/proto_app/assets/web on a port (PORT, 8765 by default), and run `NODE_PATH=$(npm root -g) node
// design/ui/phone_falcon.cjs` from the repository's root; it writes mock_falcon_<n>_<name>.png in the current folder
// (or OUT=<folder>) and design/ui/phone_falcon.jpg (the thirteen side by side). AUDIT=<audit.js> runs the layout audit
// on each view and writes the views' texts to falcon_texts.txt.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const PORT = process.env.PORT || 8765;
const OUT = process.env.OUT || '.';

// screens beyond phone.js: the approved المزاين pieces (phone_mazayen.cjs) and a few for the falcon's pages
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
  .apps .app .ic.new { box-shadow: 0 0 0 2px #e8b46c, 0 3px 8px rgba(70,50,20,.14); }
`;
// the falcon stand-in (a flat profile, until T11's birds exist)
const PHOTO = `<svg viewBox="0 0 60 60"><path d="M22 58 C18 44 20 30 28 22 C32 16 40 15 44 20 C48 26 47 40 42 58 Z" fill="#8f7357"/>
  <path d="M26 34 C32 38 38 38 44 34 M24 42 C31 46 38 46 45 42 M24 50 C31 54 38 54 45 50" stroke="#5f4630" stroke-width="2" fill="none"/>
  <path d="M29 22 C28 12 34 7 40 8 C46 9 48 15 45 22 Z" fill="#7a5f45"/><path d="M45 14 l6 2 -5 3" fill="#e9c84a"/><circle cx="41" cy="14" r="2.2" fill="#111"/>
  <path d="M38 17 c1 3 0 6 -2 8" stroke="#3b2c1e" stroke-width="1.6" fill="none"/></svg>`;

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  await p.route('**/index.html', async (r) => { const res = await r.fetch(); await r.fulfill({ response: res, body: (await res.text()).replace('startEngine({ onSnapshot:', 'startEngine({ newGame: { seed: 4242 }, onSnapshot:') }); });
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.marahEngine && window.marahEngine.snapshot, null, { timeout: 600000 });
  await p.waitForTimeout(2500);
  await p.evaluate(() => { window.requestAnimationFrame = () => 0; });
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone')).shadowRoot; window.__phone.toggle(); window.__phone.enlarge(); });
  await p.waitForTimeout(600);

  const screens = await p.evaluate(([PHOTO]) => {
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
    };
    const svg = (k) => `<svg class="i" viewBox="0 0 24 24">${I[k]}</svg>`;
    const nav = () => `<div class="nav"><button class="back">${svg('back')}رجوع</button></div>`;
    const ph = `<span class="ph">${PHOTO}</span>`;
    const row = (icon, name, line, right = '', cls = '') => `<div class="row${cls ? ' ' + cls : ''}"><span class="lead">${svg(icon)}</span><b>${name}</b>${right ? `<span class="qty">${right}</span>` : ''}<small>${line}</small></div>`;
    const row2 = (icon, name, line, cls = '') => `<div class="row two${cls ? ' ' + cls : ''}"><span class="lead">${svg(icon)}</span><b>${name}</b><small>${line}</small></div>`;
    const alertCard = (title, line) => `<div class="warn"><span class="lead">${svg('alert')}</span><b>${title}</b><small>${line}</small></div>`;
    const seg = (on) => `<div class="seg">${['المزاد', 'صقوري', 'المهرجان'].map((t, i) => `<span${i === on ? ' class="on"' : ''}>${t}</span>`).join('')}</div>`;

    // ------------------------------------------------ 1 home: the real home (phone.js), the approved two and the new two
    const home = R().querySelector('.scr').innerHTML;
    const appEl = (k, n, badge, isNew) => `<div class="app">${badge ? `<span class="bd">${badge}</span>` : ''}<span class="ic${isNew ? ' new' : ''}">${svg(k)}</span><span>${n}</span></div>`;
    const homeHtml = home.replace(/(<div class="apps">[\s\S]*?)(<\/div><\/div><\/div>)\s*$/, (m, a, z) => m)
      .replace('</div></div></div><div class="hb">', `${appEl('cup', 'المزاين')}${appEl('talk', 'المحادثات')}${appEl('falcon', 'نادي الصقور', 1, true)}${appEl('permit', 'تصريح الصيد', 0, true)}</div></div></div><div class="hb">`);

    // ------------------------------------------------ 2 the auction (national auction season: wild-caught passage birds)
    const lot = (name, line, bid, left) => `<div class="it">${ph}<b>${name}</b><small>${line}</small><span class="pr"><span class="price num">${bid}</span><small>آخر سوم</small></span><small>${left}</small></div>`;
    const auction = `<div class="body">${nav()}<div class="title">نادي الصقور</div>${seg(0)}
      <div class="note" style="margin-top:-4px">مزاد الطرح مفتوح لين 30 نوفمبر · صقور انطرحت بتصريح هالخريف</div>
      <div class="lst">
        ${lot('حر · قرناس', 'طرح · العرض 17 إنش', '42,000', 'يقفل بعد 3 أيام')}
        ${lot('حر · فرخ', 'طرح · العرض 16 إنش', '26,500', 'يقفل بعد 5 أيام')}
        ${lot('شاهين · فرخ', 'طرح · العرض 14 إنش', '18,000', 'يقفل بكرة')}
        ${lot('حر · فرخ', 'طرح · العرض 16 إنش', '23,000', 'يقفل بعد 8 أيام')}</div>
      <div class="note">ومزاد صقور المزارع بملهم يرجع بأغسطس.</div></div>`;

    // ------------------------------------------------ 3 a falcon's page for a buyer
    const falcon = `<div class="body">${nav()}<div class="title" style="font-size:22px">حر · قرناس</div>
      <div class="it big">${ph}<b>طرح هالخريف</b><small>انطرح بتصريح بالحماد وجا للمزاد</small><small>العرض 17 إنش · الميزان 1,120 غرام</small><small>عمره فوق سنة</small></div>
      <div class="group">${row2('eye', 'وش يسوي بالصيد والسباق ما ينعرف', 'يبين بس من طلعاته ونتايجه بعد ما تدعيه')}${row2('chip', 'الجواز يطلع باسمك بعد البيعة', 'ويتسجل بالنادي، وبعدها تطلّع تصريح الصيد')}</div>
      <div class="tank"><small>المزاد</small>
        <div class="kind"><span>آخر سوم</span><span class="d">42,000 ريال · 6 مزايدين</span></div>
        <div class="kind"><span>يقفل</span><span class="d">بعد 3 أيام</span></div></div>
      <div class="group"><div class="row ord"><span class="lead">${svg('falcon')}</span><b>سومك</b><span class="stp"><button>${svg('minus')}</button><span class="n"><b>43,000</b> <span>ريال</span></span><button>${svg('plus')}</button></span><small>لو أحد زاد عليك يجيك خبر</small></div></div>
      <button class="btn pri" style="width:100%">زايد بـ 43,000</button>
      <div class="note">الصقر الجديد يبي له الدعو قبل أول طلعة.</div></div>`;

    // ------------------------------------------------ 4 the player's falcon after a season
    const mine = `<div class="body">${nav()}<div class="title">نادي الصقور</div>${seg(1)}
      <div class="it big">${ph}<b>غيث · حر قرناس</b><small>جوازه باسمك · مسجل بالنادي</small><small>طرح، اشتريته 14 أكتوبر بـ 42,000</small><small>الميزان اليوم 1,105 غرام</small></div>
      <div class="sec">طلعاته · هالموسم</div>
      <div class="group">${row('map', '6 طلعات', 'صاد 3 كراوين، وفلت منه الباقي')}${row('flag', 'آخر طلعة', 'طرف النفود · صاد كروان', '12 ديسمبر')}</div>
      <div class="sec">مسابقاته</div>
      <div class="group">${row('lure', 'الملواح · الملاك', 'حر قرناس · المركز 12 من 31', '18.906')}${row('star', 'المزاين · الحر', 'قرناس · المركز الثالث', '100,000')}</div>
      <div style="display:flex;gap:8px"><button class="btn pri" style="flex:1">دعّه اليوم</button><button class="btn ghost" style="flex:1">اعرضه بالمزاد</button></div></div>`;

    // ------------------------------------------------ 5 الدعو: the care, once each time the game opens
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
      <button class="btn pri" style="width:100%">دعّه اليوم</button>
      <div class="note">مرة وحدة كل ما تفتح اللعبة، وتنحسب لك الأيام اللي فاتت. ولو تركته أسبوعين يرجع خطوة. وبالمقيض بالصيف ما فيه دعو.</div></div>`;

    // ------------------------------------------------ 6 the festival (the 2025 dates: the 2026 ones disagree)
    const cls = (name, line, right, act) => `<div class="row"><span class="lead">${svg('lure')}</span><b>${name}</b>${act ? `<span class="act"><button class="btn ghost pr">${act}</button></span>` : `<span class="qty wait">${right}</span>`}<small>${line}</small></div>`;
    const fest = `<div class="body">${nav()}<div class="title">نادي الصقور</div>${seg(2)}
      <div class="open"><span class="tag amb">التسجيل يفتح 25 ديسمبر</span><b>مهرجان الصقور</b><small>ملهم · من 25 ديسمبر لين 10 يناير</small><small>التسجيل أسبوع من أول يوم، ببلاش</small></div>
      <div class="sec">الملواح · سباق 400 متر للملواح</div>
      <div class="group">${cls('الملاك', 'لكل نوع وعمر: فرخ وقرناس', '', 'سجّل')}${cls('الهواة', 'لين تفوز بالملاك', 'بعدين')}${cls('المحترفين والنخبة', 'للصقارين الكبار', 'بعدين')}</div>
      <div class="sec">المزاين · جايزة الأول بالريال</div>
      <div class="group">${row('star', 'الحر', 'فرخ وقرناس', '300,000')}${row('star', 'الجير بيور', 'فرخ وقرناس', '300,000')}${row('star', 'شاهين بحري', 'قرناس', '300,000')}${row('star', 'حر إنتاج محلي', 'فرخ', '300,000')}</div>
      <div class="sec">الشروط</div>
      <div class="group">${row2('chip', 'جوازه باسمك', 'هو إثبات الملكية')}${row2('rule', 'لين 8 صقور لك بكل عمر بالملواح', 'ولين 5 صقور بشوط المزاين')}${row2('eye', 'الحر عرضه 16 إنش وفوق', 'وفيه فحص منشطات')}</div></div>`;

    // ------------------------------------------------ 7 the ملواح round's day: the times come in
    const run = (rk, name, owner, t, cls = '') => `<div class="row${cls ? ' ' + cls : ''}"><span class="lead rk${rk === 1 ? ' g1' : ''}">${rk}</span><b>${name}</b><span class="qty">${t}</span><small>${owner}</small></div>`;
    const race = `<div class="body">${nav()}<div class="title">يوم الملواح</div>
      <div class="note" style="margin-top:-4px">الملاك · حر قرناس · 400 متر · 31 صقر</div>
      <div class="sec">الأسرع لين الحين · بالثواني</div>
      <div class="group">${run(1, 'سهم', 'بو فهد', '17.905')}${run(2, 'ريح', 'بو ناصر', '18.061')}${run(3, 'برق', 'بو سعد', '18.112')}</div>
      <div class="group">${row('falcon', 'غيث يطير بعد 3 صقور', 'من السناح للملواح', 'الحين', 'now')}</div>
      <div class="note">يجيك خبر لما يطير ويطلع وقته، ولو قفلت الجوال يكمل الشوط بدونك.</div></div>`;

    // ------------------------------------------------ 8 the round's result
    const prize = (rk, name, owner, t, pr) => `<div class="row"><span class="lead rk${rk === 1 ? ' g1' : ''}">${rk}</span><b>${name} · ${t}</b><span class="qty">${pr}</span><small>${owner}</small></div>`;
    const race_result = `<div class="body">${nav()}<div class="title">النتيجة</div>
      <div class="note" style="margin-top:-4px">الملواح · الملاك · حر قرناس · 31 صقر</div>
      <div class="it big">${ph}<b>غيث</b><small>وقته 18.906 ثانية</small><small>المركز 12، والجوايز لين السابع</small><small>وقته ينكتب بسجله، ويبين لمن يبي يشتريه</small></div>
      <div class="sec">المراكز · الجايزة بالريال</div>
      <div class="group">${prize(1, 'سهم', 'بو فهد', '17.905', '100,000')}${prize(2, 'ريح', 'بو ناصر', '18.061', '60,000')}${prize(3, 'برق', 'بو سعد', '18.112', '40,000')}${prize(4, 'مزن', 'بو خالد', '18.240', '25,000')}</div>
      <div class="note">والأوقات تنقاس من السناح لين الملواح.</div></div>`;

    // ------------------------------------------------ 9 المزاين's result: places and prizes, no scores
    const beauty_result = `<div class="body">${nav()}<div class="title">النتيجة</div>
      <div class="note" style="margin-top:-4px">مزاين الصقور · الحر · قرناس</div>
      <div class="it big">${ph}<b>غيث</b><small>المركز الثالث</small><small>جايزته 100,000 ريال نزلت برصيدك</small><small>واللي يجي بالمراكز يغلى سعره</small></div>
      <div class="sec">المراكز · الجايزة بالريال</div>
      <div class="group">${prize(1, 'الشاهي', 'بو سلطان', 'حر قرناس', '300,000')}${prize(2, 'الريم', 'بو عبدالله', 'حر قرناس', '175,000')}${prize(3, 'غيث', 'أنت', 'حر قرناس', '100,000')}${prize(4, 'زعزوع', 'بو فيصل', 'حر قرناس', '30,000')}${prize(5, 'هدّاج', 'بو مشعل', 'حر قرناس', '20,000')}</div>
      <div class="note">ثلاث حكام، والدرجات ما تنعلن. وجماله من خلقته، والدعو ما يغيّره.</div></div>`;

    // ------------------------------------------------ 10 the permit before it is taken
    const need = (ok, name, line) => `<div class="row"><span class="lead">${svg(ok ? 'check' : 'dot')}</span><b>${name}</b><span class="qty ${ok ? 'ok' : 'wait'}">${ok ? 'عندك' : 'ناقص'}</span><small>${line}</small></div>`;
    const permit_new = `<div class="body">${nav()}<div class="title">تصريح الصيد</div>
      <div class="note" style="margin-top:-4px">موسم الصيد مفتوح من 1 سبتمبر لين 31 يناير</div>
      <div class="sec">اللي يبيه التصريح</div>
      <div class="group">${need(true, 'عمرك 21 وفوق', 'التصريح باسمك')}${need(true, 'صقر جوازه باسمك', 'غيث · حر قرناس')}${need(true, 'مسجل بنادي الصقور', 'صقار')}</div>
      <div class="tank"><small>تصريح صقار لهالموسم</small>
        <div class="kind"><span>الرسوم</span><span class="d">100 ريال</span></div>
        <div class="kind"><span>ينفع لين</span><span class="d">31 يناير</span></div></div>
      <button class="btn pri" style="width:100%">طلّع التصريح بـ 100 ريال</button>
      <div class="note">التصريح شخصي، ما ينعطى لغيرك، وتشيله معك بالجوال وانت تصيد.</div></div>`;

    // ------------------------------------------------ 11, 12 the permit held (top, and scrolled to its end)
    const permit = `<div class="body">${nav()}<div class="title">تصريح الصيد</div>
      <div class="tank"><small>تصريح صقار · غيث</small><div class="v">ساري</div><div class="ln" style="margin-top:4px">من 1 سبتمبر لين 31 يناير</div>
        <div class="kind"><span>فترة الخريف</span><span class="d">لين 30 نوفمبر</span></div>
        <div class="kind"><span>فترة الشتاء</span><span class="d">من 1 ديسمبر</span></div></div>
      <div class="group">${row2('falcon', 'بالصقر بس', 'غيث، جوازه باسمك')}${row2('map', 'الكروان بالبر', 'والحبارى بالمحازة المرخصة بس')}${row2('sun', 'بالنهار بس', 'من بعد الشروق بساعة لين قبل الغروب بساعة')}${row2('user', 'شخصي', 'ما ينعطى لغيرك، وتشيله معك')}</div>
      <div class="sec">ممنوع الصيد فيه</div>
      <div class="group">${row2('ban', 'المدن والقرى والمزارع', 'يعني عزبتك وحولها، والاستراحات')}${row2('ban', 'المحميات والمشاريع الكبرى', 'والمحميات الملكية كلها')}${row2('ban', 'الساحل', 'على طوله، لين 20 كيلو داخل البر')}</div>
      <div class="sec">ما ينصاد أبد</div>
      <div class="group">${row2('ban', 'الحيوانات المهددة', 'الذيب والنمر والمها والغزلان والوعول والضبع')}${row2('ban', 'الطيور الجارحة كلها', 'والقميري')}</div>
      <div class="sec">الغرامات</div>
      <div class="group">${row2('alert', 'صيد بدون تصريح', 'غرامته 10,000 ريال')}${row2('alert', 'صيد بمكان أو وقت ممنوع', 'غرامته 5,000 ريال')}${row2('alert', 'الصيد من سيارة تمشي', 'غرامته 100,000 ريال، فوقّف قبل ترسل')}${row2('alert', 'الصيد بسلاح ناري', 'غرامته 80,000 ريال')}</div>
      <div class="note">والطلعة ما تجيب فلوس: بيع الصيد ممنوع.</div></div>`;

    // ------------------------------------------------ 13 the fine after (told in the permit app; frame 9 shows it in play)
    const fine = `<div class="body">${nav()}<div class="title">مخالفة</div>
      ${alertCard('صيد بمكان ممنوع', 'قريب من المزارع، جنوب عزبتك')}
      <div class="tank"><small>الغرامة</small><div class="v">5,000<span>ريال</span></div><div class="ln">انخصمت من رصيدك</div></div>
      <div class="note">وقفتك الدورية وانت ترسل الصقر جنب العزب. تصريحك باقي، بس المرة الجاية بعيد عن المزارع والقرى.</div>
      <div class="group">${row2('rule', 'الصيد بالنهار بس، وبعيد عن المزارع والقرى', 'والصقر ما ينرسل إلا والسيارة واقفة')}</div></div>`;

    return { home: homeHtml, auction, falcon, mine, train, fest, race, race_result, beauty_result, permit_new, permit, permit_end: permit, fine };
  }, [PHOTO]);

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
    await p.waitForTimeout(400);
    const file = path.join(OUT, `mock_falcon_${i}_${k}.png`);
    const box = await p.evaluate(() => { const r = R().querySelector('.dev').getBoundingClientRect(); return { x: r.x, width: r.width }; });
    await p.screenshot({ path: file, timeout: 600000, clip: { x: Math.max(0, box.x - 4), y: 0, width: box.width + 8, height: 440 } });
    files.push(file);
    if (process.env.AUDIT) {
      await p.addScriptTag({ path: process.env.AUDIT });
      const a = await p.evaluate(() => window.__audit());
      console.log(k, 'audit', JSON.stringify({ clipped: a.clipped, ellipsis: a.ellipsis, outside: a.outside, split: a.split, scroll: a.scroll }));
      fs.appendFileSync(path.join(OUT, 'falcon_texts.txt'), `## ${k}\n` + a.texts.filter((t) => !t.includes('{')).join('\n') + '\n');
    }
  }
  await b.close();
  execFileSync('convert', [...files, '-background', '#2a2119', '-splice', '6x0', '+append', '-chop', '6x0', '-quality', '86', path.join(__dirname, 'phone_falcon.jpg')]);
})();
