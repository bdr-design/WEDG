// المزاين in the phone: a DESIGN for the owner's approval (not built yet, not in phone.js). Seven screens in eight views, as the
// phone draws them at the owner's screen (956 x 440, the phone enlarged), in the phone's own CSS and pieces
// (design/prototype3d/phone.js) plus the approved chat's (design/ui/phone.html):
//   1 fests    the festivals: the one open for registration, the player's entries (withdraw), what is coming and when
//   2 fest     a festival opened (two views: its top, and scrolled to its end): its individual rounds (الفردي دق وجل لكل
//              لون، مفاريد ودق القعدان والبكار، الفحل وإنتاجه; the group rounds only as coming later, the owner 13 Nov),
//              each one's first prize, the closing (late fee after it, 72 hours before the round), who may enter
//   3 enter    registering: each of the player's camels with the round it fits, or why it cannot enter; the cost
//   4 cheat    the secret treatment (GDD 7.1), offered in a chat by a man who does it, with the risk said honestly
//   5 day      the round's day: the six stages of GDD 7, passed one by one (here the third under way)
//   6 result   the results: the player's camel's outcome, the placings and prizes, what it did to her worth
//   7 caught   the day when the treatment is found: out at the tampering experts, the fine, the ban
// The game is a real one: a new game on seed 4242 (1 October 2026, مزاين حائل open), in which the player buys the
// market's نمر (a حق شقح) to have a camel bought too recently. The engine has the festivals, their dates and the
// player's camels; the Saudi rounds, the fees, the six stages and the cheating are drawn to the GDD with placeholder
// figures (listed in the report that came with this file, and in design/ui/README.md).
// To draw again: build the prototype (THREE_DIR=<three@0.170.0 package> python3 tool/proto_app/assemble.py), serve
// tool/proto_app/assets/web on a port (8765 by default, or PORT=<port>), and run
// `NODE_PATH=$(npm root -g) node design/ui/phone_mazayen.cjs` from the repository's root; it writes
// mock_mazayen_<n>_<name>.png in the current folder and design/ui/phone_mazayen.jpg (the eight side by side).
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const path = require('path');
const PORT = process.env.PORT || 8765;
const OUT = process.env.OUT || '.';

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
  .row.off { opacity: .55; }
  .it small.bad, .row small.bad { color: var(--red); font-weight: 600; }
  .it.sel { box-shadow: inset 0 0 0 2px var(--acc); }
  .it .tick { grid-row: span 4; }
  .open { background: var(--card); border-radius: 18px; padding: 12px 14px; display: flex; flex-direction: column; gap: 3px; box-shadow: inset 0 0 0 1.5px #bfe3d2; }
  .open .tag { align-self: flex-start; font-size: 11px; font-weight: 700; color: var(--acc); background: var(--acc-soft); border-radius: 8px; padding: 2px 8px; }
  .open b { font: 700 17px/1.3 "Alexandria", sans-serif; }
  .open small { font-size: 12px; color: var(--ink2); }
  .open .kind { margin-top: 2px; }
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
`;

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 2 });
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.marahEngine || window.marahEngineError, null, { timeout: 300000 });
  // a new game on the fixed seed, its clock stopped on its first day; the market's نمر bought; the save read for the
  // open festival's colours (the snapshot carries a festival's count of rounds, not the rounds)
  const game = await p.evaluate(async () => {
    const e = window.marahEngine;
    await e.startOver({ seed: 4242 });
    await new Promise((r) => setTimeout(r, 800));
    const nimr = e.snapshot.market.find((l) => l.camel.name === 'نمر' && l.camel.category === 'shoqh');
    const bought = nimr ? await e.dispatch({ type: 'buyListing', listing: nimr.id }) : { ok: false };
    await new Promise((r) => setTimeout(r, 1500));
    await new Promise((r) => { e.worker.postMessage(JSON.stringify({ op: 'pause', id: 990001 })); setTimeout(r, 600); });
    await e.flush();
    const save = JSON.parse(localStorage.getItem('marah.proto.marah.save'));
    const find = (o, d = 0) => { if (!o || typeof o !== 'object' || d > 5) return null; if (o.festivals) return o.festivals; for (const v of Object.values(o)) { const r = find(v, d + 1); if (r) return r; } return null; };
    const fs = Object.values(find(save) || {});
    // the snapshot's yard leaves out a camel still on the truck: نمر as the market showed him
    return { bought: bought.ok, nimr: nimr && { ...nimr.camel, onTheWay: true }, rounds: Object.fromEntries(fs.map((f) => [f.name, f.rounds.map((r) => ({ cat: r.cat, sex: r.sex, age: r.age, rivals: r.rivals }))])) };
  });
  console.log('bought نمر:', game.bought, 'today', await p.evaluate(() => window.marahEngine.snapshot.date));
  await p.evaluate(() => { window.requestAnimationFrame = () => 0; });
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone')).shadowRoot; window.__phone.toggle(); window.__phone.enlarge(); });
  await p.waitForTimeout(400);

  const screens = await p.evaluate(([GR, NIMR]) => {
    const S = window.marahEngine.snapshot;
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
      truck: '<path d="M2.5 6.5h11v9.5h-11z"/><path d="M13.5 9.5h4.2l3.3 3.6V16h-7.5"/><circle cx="6.5" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/>',
      chip: '<rect x="6.5" y="6.5" width="11" height="11" rx="2"/><path d="M9.5 3v3.5M14.5 3v3.5M9.5 17.5V21M14.5 17.5V21M3 9.5h3.5M3 14.5h3.5M17.5 9.5H21M17.5 14.5H21"/>',
      eye: '<path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6z"/><circle cx="12" cy="12" r="2.6"/>',
      scope: '<path d="M6 3.5v6a4 4 0 0 0 8 0v-6"/><path d="M10 13.5v2a4.5 4.5 0 0 0 9 0v-2"/><circle cx="19" cy="11.5" r="2"/>',
      star: '<path d="M12 3.8l2.5 5.2 5.7.8-4.1 4 1 5.6-5.1-2.7-5.1 2.7 1-5.6-4.1-4 5.7-.8z"/>',
    };
    const svg = (k) => `<svg class="i" viewBox="0 0 24 24">${I[k]}</svg>`;
    const nav = (end = '') => `<div class="nav"><button class="back">${svg('back')}رجوع</button>${end ? `<span class="end">${end}</span>` : ''}</div>`;
    const n0 = (v) => Math.round(v).toLocaleString('en-US');
    const NOUN = {
      day: ['يوم واحد', 'يومين', 'أيام', 'يوم'], head: ['راس واحد', 'راسين', 'روس', 'راس'],
      camel: ['ناقة وحدة', 'ناقتين', 'نياق', 'ناقة'], round: ['دورة وحدة', 'دورتين', 'دورات', 'دورة'],
    };
    const count = (n, k) => { const [one, two, few, many] = NOUN[k]; return n === 1 ? one : n === 2 ? two : n >= 3 && n <= 10 ? `${n} ${few}` : `${n} ${many}`; };
    const days = (n) => count(n, 'day');
    const WEEKDAY = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'];
    const MONTH = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'];
    const REGION = { riyadh: 'الرياض', qassim: 'القصيم', hail: 'حائل', jouf: 'الجوف', northern: 'الحدود الشمالية', sharqiya: 'الشرقية', tabuk: 'تبوك', najran: 'نجران' };
    const COAT = { wodh: ['وضحاء', 'وضح'], shoqh: ['شقحاء', 'شقح'], shoal: ['شعلاء', 'شعل'], sofr: ['صفراء', 'صفر'], homr: ['حمراء', 'حمر'], majaheem: ['مجهمية', 'مجاهيم'] };
    // a colour family's name, as a round is named for it (الوضح، المجاهيم)
    const FAMILY = { wodh: 'الوضح', shoqh: 'الشقح', shoal: 'الشعل', sofr: 'الصفر', homr: 'الحمر', majaheem: 'المجاهيم' };
    const PHOTO = { wodh: 'camel_side_wodh.png', shoqh: 'thumb_shaqh.png', shoal: 'thumb_shaal.png', sofr: 'thumb_safra.png', majaheem: 'thumb_majaheem.png', homr: 'thumb_shaal.png' };
    const fem = (c) => c.sex === 'female';
    const her = (c, f, m) => (fem(c) ? f : m);
    const titleOf = (c) => `${c.ageName} ${COAT[c.category][fem(c) ? 0 : 1]}`;
    const photo = (c) => `<img src="phone/${PHOTO[c.category]}" alt=""${c.category === 'homr' ? ' class="homr"' : ''}>`;
    const est = (c) => `<bdi dir="ltr">${n0(c.estimateLow)}–${n0(c.estimateHigh)}</bdi>`;
    const alertCard = (title, line) => `<div class="warn"><span class="lead">${svg('alert')}</span><b>${title}</b><small>${line}</small></div>`;
    // ---- dates: the engine's game days as the phone says them
    const t0 = Date.parse(S.date + 'T00:00:00Z');
    const dateOf = (day) => new Date(t0 + (day - S.today) * 864e5);
    const dd = (day) => { const d = dateOf(day); return `${WEEKDAY[d.getUTCDay()]} ${d.getUTCDate()} ${MONTH[d.getUTCMonth()]}`; };
    const dShort = (day) => { const d = dateOf(day); return `${d.getUTCDate()} ${MONTH[d.getUTCMonth()]}`; };
    const inDays = (day) => { const n = day - S.today; return n <= 0 ? 'اليوم' : n === 1 ? 'بكرة' : `بعد ${days(n)}`; };

    // ---- the festival open for registration, and the engine's numbers for it
    const open = S.festivals.find((f) => !f.done && S.today >= f.opensOn && S.today <= f.closesOn);
    const coming = S.festivals.filter((f) => !f.done && f !== open).sort((a, b) => a.judgedOn - b.judgedOn);
    const cats = [...new Set(GR[open.name].map((r) => r.cat))];
    const missing = Object.keys(FAMILY).filter((k) => !cats.includes(k));
    const rivals = (cat, age) => (GR[open.name].find((r) => r.cat === cat && r.sex === 'female' && r.age === age) || { rivals: 20 }).rivals;
    // prizes as the engine's (ContestRules.prizes: the tier's first prize, a share for places 1 to 10, less for the
    // young classes), the Saudi classes mapped onto its ages: جل as the eldest, دق as لقي/جذع, المفاريد as the youngest
    const TOP = { grand: 800000, regional: 150000, local: 40000 };
    const SHARES = [1.0, 0.6, 0.42, 0.3, 0.22, 0.16, 0.12, 0.09, 0.07, 0.05];
    const mr = (v) => (v >= 1e6 ? Math.round(v / 5e4) * 5e4 : v >= 1e5 ? Math.round(v / 5e3) * 5e3 : v >= 1e4 ? Math.round(v / 500) * 500 : Math.round(v / 100) * 100);
    const prizes = (tier, cls) => SHARES.map((s) => mr(TOP[tier] * ({ jel: 1, daq: 0.8, mafareed: 0.6 })[cls] * s));
    // the late fee and the round's day: GDD 7 (late registration costs a fee and closes 72 hours before the round);
    // the engine's closesOn is taken as the end of the free registration
    const LATE_FEE = 1000;      // PLACEHOLDER: no real figure found
    const lateUntil = open.judgedOn - 3;
    // the truck to the festival and back, as the engine charges it on the day (Balance.transportCost, Region.roadKmTo)
    const LL = { riyadh: [24.71, 46.68], qassim: [26.33, 43.97], hail: [27.52, 41.69], jouf: [29.97, 40.21], northern: [29.63, 43.49], sharqiya: [25.38, 49.59], tabuk: [28.38, 36.57], najran: [17.49, 44.13] };
    const km = (a, b) => { if (a === b) return 25; const [la1, lo1] = LL[a], [la2, lo2] = LL[b], rad = (d) => d * Math.PI / 180; const h = Math.sin(rad(la2 - la1) / 2) ** 2 + Math.cos(rad(la1)) * Math.cos(rad(la2)) * Math.sin(rad(lo2 - lo1) / 2) ** 2; return Math.round(6371 * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h)) * 1.25); };
    const truck = (head) => Math.round((350 + km(S.farm.region, open.region) * 2.2) * (0.55 + 0.45 * head)) * 2;

    const yard = S.yard;
    const noura = yard.find((c) => c.sex === 'female' && c.ageDays > 2000) || yard[0];
    const nimr = yard.find((c) => c.name === 'نمر') || NIMR;
    const calf = yard.find((c) => c !== noura && c !== nimr);
    const jelPrizes = prizes(open.tier, 'jel');
    const field = rivals(noura.category, 'fater') + 1;      // the engine's field for her family's eldest round, and her
    const myRound = `الفردي جل · ${FAMILY[noura.category]}`;
    const bar = (c, line, end = '') => `<div class="strip"><span class="ph">${photo(c)}</span><span><b>${c.name} · ${titleOf(c)}</b><small>${line}</small></span>${end}</div>`;

    // ---------------------------------------------------------------- 1 the festivals
    const rest = coming.length - 3;
    const comingRow = (f) => `<div class="row"><span class="lead">${svg('cup')}</span><b>${f.name}</b><span class="qty">${n0(f.topPrize)}</span><small>${f.opensOn > S.today ? `التسجيل من ${dShort(f.opensOn)}` : `التسجيل لين ${dShort(f.closesOn)}`} · الشوط ${dShort(f.judgedOn)}</small></div>`;
    const fests = `<div class="body">${nav()}<div class="title">المزاين</div>
      <div class="open"><span class="tag">التسجيل مفتوح</span><b>${open.name}</b><small>${REGION[open.region]} · الأشواط ${dd(open.judgedOn)}</small>
        <div class="kind"><span>يقفل التسجيل</span><span class="d">${dd(open.closesOn)} (${inDays(open.closesOn)})</span></div>
        <div class="kind"><span>جايزة الأول</span><span class="d">لين ${n0(open.topPrize)} ريال</span></div></div>
      <div class="sec">مشاركاتك</div>
      <div class="group"><div class="row"><span class="lead">${svg('camel')}</span><b>${noura.name} · ${myRound}</b><span class="act"><button class="btn ghost">اسحبها</button></span><small>${open.name} · شوطها ${inDays(open.judgedOn)}</small></div></div>
      <div class="sec">الجاية · جايزة الأول بالريال</div>
      <div class="group">${coming.slice(0, 3).map(comingRow).join('')}</div>
      ${rest > 0 ? `<div class="note">وبعدها ${rest === 1 ? 'مهرجان واحد' : rest === 2 ? 'مهرجانين' : `${rest} مهرجانات`} لين ${MONTH[dateOf(coming[coming.length - 1].judgedOn).getUTCMonth()]}.</div>` : ''}</div></div>`;

    // ---------------------------------------------------------------- 2 a festival opened
    const daqP = prizes(open.tier, 'daq')[0], mafP = prizes(open.tier, 'mafareed')[0];
    const rnd = (icon, name, line, prize, off) => `<div class="row${off ? ' off' : ''}"><span class="lead">${svg(icon)}</span><b>${name}</b><span class="qty">${prize}</span><small>${line}</small></div>`;
    const fest = `<div class="body">${nav()}<div class="title">${open.name}</div>
      <div class="tank"><small>${REGION[open.region]} · الأشواط ${dd(open.judgedOn)}</small>
        <div class="kind"><span>التسجيل ببلاش</span><span class="d">لين ${dd(open.closesOn)}</span></div>
        <div class="kind"><span>وبعده بـ ${n0(LATE_FEE)} ريال تأخير</span><span class="d">لين ${dd(lateUntil)}</span></div>
        <div class="kind"><span>ويقفل</span><span class="d">قبل الشوط بـ 72 ساعة</span></div></div>
      <div class="sec">الأشواط الفردية · جايزة الأول بالريال</div>
      <div class="group">
        ${rnd('camel', 'الفردي · جل', 'النياق من ثاني ولادة وفوق', n0(jelPrizes[0]))}
        ${rnd('camel', 'الفردي · دق', 'من بعد المفرودة لين الجذعة', n0(daqP))}
        ${rnd('camel', 'مفاريد البكار والقعدان', 'من سنة لين سنتين', n0(mafP))}
        ${rnd('camel', 'دق القعدان والبكار', 'من بعد المفرود لين الجذع', n0(daqP))}
        ${rnd('star', 'الفحل وإنتاجه', 'النتيجة بعد فحص الحمض النووي', n0(jelPrizes[0]))}</div>
      <div class="note">لكل لون شوطه: ${cats.map((k) => FAMILY[k]).join('، ')}.${missing.length ? ` وما فيه ${missing.map((k) => FAMILY[k]).join(' ولا ')} ${missing.length === 1 ? 'بهالمهرجان' : ''}.` : ''}</div>
      <div class="note">والأشواط الجماعية (الجمل، المنقية، البداوة، الهجيج، الطبع) تجي بعدين.</div>
      <div class="sec">الشروط</div>
      <div class="group">
        <div class="row" style="grid-template-columns:36px 1fr"><span class="lead">${svg('rule')}</span><b>ناقة وحدة بشوط فردي واحد</b><small>بكل مهرجان. والمفاريد والدق والفحل وإنتاجه غيره</small></div>
        <div class="row" style="grid-template-columns:36px 1fr"><span class="lead">${svg('chip')}</span><b>الشريحة باسمك</b><small>هي وثيقة الملكية الوحيدة، والتسجيل من هنا</small></div>
        <div class="row" style="grid-template-columns:36px 1fr"><span class="lead">${svg('eye')}</span><b>العمر يُفحص بالأسنان يوم الشوط</b><small>واللون والشوط ما يتغيرون بعد الإغلاق</small></div></div>
      <button class="sell" style="position:static;box-shadow:none;margin-bottom:6px">${svg('plus')}سجّل ناقة</button></div>`;

    // ---------------------------------------------------------------- 3 registering
    const camelIt = (c, round, line, reason, sel) => `<div class="it${sel ? ' sel' : ''}${reason ? ' off' : ''}"><span class="ph">${photo(c)}</span><b>${c.name} · ${titleOf(c)}</b><small>${round}</small><small${reason ? ' class="bad"' : ''}>${reason || line}</small></div>`;
    const t1 = truck(1);
    const enter = `<div class="body">${nav()}<div class="title">سجّل ناقة</div>
      <div class="note" style="margin-top:-4px">${open.name} · كل ناقة وشوطها من لونها وعمرها</div>
      <div class="lst flat">
        ${camelIt(noura, `شوطها ${myRound}`, `مرضع وعشار · ${noura.health === 'healthy' ? 'صحتها زينة' : 'مريضة'}`, '', true)}
        ${nimr ? camelIt(nimr, `شوطه دق القعدان · ${FAMILY[nimr.category]}`, '', `اشتريته اليوم، ولازم يكون باسمك ${days(30)} قبل الشوط`) : ''}
        ${calf ? camelIt(calf, `${her(calf, 'ترضع من أمها', 'يرضع من أمه')} ${noura.name}`, '', `${her(calf, 'صغيرة', 'صغير')}، أصغر شوط للمفاريد من سنة`) : ''}</div>
      <div class="tank"><small>اللي تدفعه عن ${noura.name}</small>
        <div class="kind"><span>التسجيل</span><span class="d">ببلاش لين ${dShort(open.closesOn)}</span></div>
        <div class="kind"><span>نقلها لـ${REGION[open.region]} ورجعتها</span><span class="d">${n0(t1)} ريال يوم الشوط</span></div></div>
      <button class="btn pri" style="width:100%">سجّل ${noura.name} بشوط الجل</button>
      <div class="note">تقدر تسحبها ببلاش لين ${dd(lateUntil)}. وما تقدر تبيعها وهي مسجلة.</div></div>`;

    // ---------------------------------------------------------------- 4 the secret treatment
    const treat = (name, raises, risk, fine, price) => `<div class="row"><span class="lead">${svg('scope')}</span><b>${name}</b><span class="act"><button class="btn ghost">${n0(price)}</button></span><small>${raises} · ${risk}<br>الغرامة لين ${n0(fine)}</small></div>`;
    const cheat = `<div class="body"><div class="nav"><button class="back">${svg('back')}</button><div class="chathd"><span class="av">ج</span><span><b>أبو جابر</b><small>يجمّل الحلال بالسر</small></span></div></div>
      ${bar(noura, `${myRound} · ${open.name}`, `<span class="lim">الشوط<span>${dShort(open.judgedOn)}</span></span>`)}
      <div class="chat">
        <div class="msg them">سمعت إنك مسجّل ${noura.name} بحائل. أقدر أكبّر شفايفها وخشمها قبل الشوط، وما أحد يدري.</div>
        <div class="msg me">وش عندك؟</div></div>
      <div class="group">
        ${treat('بوتوكس بالشفة', 'يكبّر الشفايف', 'أكثر شي ينكشف', 100000, 4000)}
        ${treat('فيلر بالخشم', 'يرفع الخشم والراس', 'ينكشف بالسونار', 100000, 6000)}
        ${treat('شد الشفة', 'يطوّل الشفة', 'ينكشف بالفحص', 100000, 3000)}
        ${treat('صبغ الوبر', 'يصفّي اللون', 'ينكشف بالفحص', 30000, 1500)}</div>
      ${alertCard('لو انكشف', `تطلع ${noura.name} من الشوط على طول، وتنكتب عليك الغرامة، وتنحرم أنت وحلالك من كل المهرجانات، هالدورة و${count(5, 'round')} جاية، والخبر يطلع. والتجميل ممنوع حتى برا المهرجان.`)}</div>`;

    // ---------------------------------------------------------------- 5 the day: the six stages (GDD 7)
    // the field as it narrows: the engine's entries for her family's eldest round, then PLACEHOLDER cuts
    const out2 = 2, finalists = 15;
    const stage = (cls, icon, name, line, right) => `<div class="row ${cls}"><span class="lead">${svg(icon)}</span><b>${name}</b><span class="qty ${right[0]}">${right[1]}</span><small>${line}</small></div>`;
    const stagesHead = `${nav()}<div class="title">يوم الشوط</div>
      <div class="note" style="margin-top:-4px">${open.name} · ${myRound} · ${dd(open.judgedOn)}</div>`;
    const day = `<div class="body">${stagesHead}
      ${bar(noura, `بالشوط ${count(field, 'camel')} · باقي ${count(field - out2, 'camel')}`)}
      <div class="group">
        ${stage('', 'check', 'الشريحة والشاهد', 'شريحتها باسمك', ['ok', 'عدّت'])}
        ${stage('', 'check', 'فحص الهجين واللون والعمر', `${COAT[noura.category][0]} صافية، و${noura.ageName} بأسنانها · طلعت ${count(out2, 'camel')}`, ['ok', 'عدّت'])}
        ${stage('now', 'dot', 'التحكيم الأولي', `اللجنة تختار ${finalists} للتحكيم النهائي`, ['now', 'الحين'])}
        ${stage('next', 'eye', 'خبراء التلاعب', 'فحص الشفايف والخشم والوبر', ['wait', 'الظهر'])}
        ${stage('next', 'scope', 'اللجنة الطبية', 'سونار وأشعة وتحاليل', ['wait', 'العصر'])}
        ${stage('next', 'star', 'التحكيم النهائي', 'المراكز والجوايز', ['wait', 'المغرب'])}</div>
      <div class="note">يجيك خبر مع كل مرحلة، ولو قفلت الجوال يكمل الشوط بدونك.</div></div>`;

    // ---------------------------------------------------------------- 6 the results
    const names = [...new Set(S.market.filter((l) => l.camel.sex === 'female' && l.camel.name !== noura.name).map((l) => l.camel.name))];
    const owners = [...new Set(S.market.map((l) => l.sellerName))];
    const place = (i) => `<div class="row"><span class="lead rk${i === 0 ? ' g1' : ''}">${i + 1}</span><b>${names[i]}</b><span class="qty">${n0(jelPrizes[i])}</span><small>${owners[i]}</small></div>`;
    const result = `<div class="body">${nav()}<div class="title">النتيجة</div>
      <div class="note" style="margin-top:-4px">${open.name} · ${myRound} · ${count(field, 'camel')}</div>
      <div class="it big"><span class="ph">${photo(noura)}</span><b>${noura.name}</b><small class="bad">ما تأهلت للتحكيم النهائي</small><small>اللجنة اختارت ${finalists} من ${field - out2}</small><small>قيمتها ما تغيرت</small><small>يقدّرونها ${est(noura)}</small></div>
      <div class="sec">المراكز · الجايزة بالريال</div>
      <div class="group">${[0, 1, 2, 3, 4].map(place).join('')}</div>
      <div class="note">والجوايز لين العاشر (${n0(jelPrizes[9])} ريال). اللي يجي بالعشرة الأوائل تزيد قيمته ويكبر صيتك ب${FAMILY[noura.category]}. والدرجات ما تنعلن. ونقلها ${n0(t1)} ريال انخصم.</div></div>`;

    // ---------------------------------------------------------------- 7 caught
    const FINE = 60000;      // PLACEHOLDER: scaled with the treatment's strength, up to the type's cap (100,000)
    const caught = `<div class="body">${stagesHead}
      ${bar(noura, `<span style="color:var(--red);font-weight:600">طلعت من الشوط</span>`)}
      <div class="group">
        ${stage('', 'check', 'الشريحة والشاهد', 'شريحتها باسمك', ['ok', 'عدّت'])}
        ${stage('', 'check', 'فحص الهجين واللون والعمر', `${COAT[noura.category][0]} صافية، و${noura.ageName} بأسنانها`, ['ok', 'عدّت'])}
        ${stage('', 'check', 'التحكيم الأولي', `اختاروها مع ${finalists - 1} للنهائي`, ['ok', 'عدّت'])}
        ${stage('bad', 'x', 'خبراء التلاعب', 'لقوا بوتوكس بشفايفها', ['bad', 'انكشفت'])}</div>
      ${alertCard('انكشف التجميل', `طلعت ${noura.name} من الشوط، وانكتبت عليك غرامة ${n0(FINE)} ريال. وانحرمت أنت وحلالك من كل المهرجانات، هالدورة و${count(5, 'round')} جاية، والخبر طلع للملاك.`)}
      <div class="note">نقلها ${n0(t1)} ريال انخصم بعد. وصيتك ب${FAMILY[noura.category]} نزل.</div></div>`;

    return { fests, fest, fest_end: fest, enter, cheat, day, result, caught };
  }, [game.rounds, game.nimr]);

  const files = [];
  let i = 0;
  for (const [k, html] of Object.entries(screens)) {
    i++;
    await p.evaluate(([html, css]) => {
      const scr = R().querySelector('.scr'), sb = scr.querySelector('.sbar').outerHTML;
      scr.classList.remove('home');
      // a number kept with its word (a no-break space between them), as الحراج's design does
      scr.innerHTML = `<span class="pill"></span>${sb}${html.replace(/(\d) (?=[؀-ۿ])/g, '$1\u00a0').replace(/([؀-ۿ]) (?=\d)/g, '$1\u00a0')}<div class="hb"></div>`;
      const st = document.createElement('style'); st.textContent = css; scr.appendChild(st);
    }, [html, CSS]);
    if (k.endsWith('_end')) await p.evaluate(() => { const bd = R().querySelector('.body'); bd.scrollTop = bd.scrollHeight; });
    await p.waitForTimeout(400);
    // the reviewer's layout audit, when asked (AUDIT=<audit.js>): clipped text, a number split from its word
    if (process.env.AUDIT) {
      await p.addScriptTag({ path: process.env.AUDIT });
      const a = await p.evaluate(() => window.__audit());
      console.log(k, 'audit', JSON.stringify({ clipped: a.clipped, ellipsis: a.ellipsis, outside: a.outside, split: a.split, scroll: a.scroll }));
      require('fs').appendFileSync(path.join(OUT, 'mazayen_texts.txt'), a.texts.join('\n') + '\n');
    }
    const file = path.join(OUT, `mock_mazayen_${i}_${k}.png`);
    const box = await p.evaluate(() => { const r = R().querySelector('.dev').getBoundingClientRect(); return { x: r.x, y: r.y, width: r.width, height: r.height }; });
    await p.screenshot({ path: file, timeout: 600000, clip: { x: Math.max(0, box.x - 4), y: 0, width: box.width + 8, height: 440 } });
    files.push(file);
    console.log(k, 'scroll/visible', await p.evaluate(() => { const bd = R().querySelector('.body'); return [bd.scrollHeight, bd.clientHeight]; }));
  }
  await b.close();
  // the eight side by side, a gap between them as in phone_haraj.jpg
  execFileSync('convert', [...files, '-background', '#2a2119', '-splice', '6x0', '+append', '-chop', '6x0', '-quality', '86', path.join(__dirname, 'phone_mazayen.jpg')]);
})();
