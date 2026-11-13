// البنك on the engine, approved by the owner on 13 Nov 2026 (the month rows by their biggest movement, option B; السعي
// folded into its sale), built in design/prototype3d/phone.js. Drawn as phone_haraj.cjs drew الحراج: the
// real phone's CSS and pieces (design/prototype3d/phone.js) plus the approved design's bank styles (phone_bank.css,
// from design/ui/phone.html), at the owner's screen (956 x 440, the phone enlarged), every figure the engine's own.
// The figures: phone_bank_data.dart plays a new game (seed 4242, القصيم, وضح: the prototype's fixed game) forward
// with the rules engine and dumps its ledger at three moments (day one; 27 October, a month of milk, feed and one
// tanker; 15 April 2027, six and a half months in, a camel bought and the calf sold); it is written to
// phone_bank.json here. The snapshot JSON carries no ledger yet (the build comes after the owner approves), so the
// screens read that dump, grouped as the presenter would group it.
// To draw again, from the repository's root (dart on the PATH, the workspace's .dart_tool present):
//   build and serve the prototype (THREE_DIR=... python3 tool/proto_app/assemble.py, then
//   python3 -m http.server 8765 --bind 127.0.0.1 -d tool/proto_app/assets/web), and run
//   `NODE_PATH=$(npm root -g) node design/ui/phone_bank.cjs` (PORT=... for another port; DRY=1 prints each screen's
//   words without a browser). It writes
//   mock_bank_*.png in the current folder and phone_bank.jpg (the screens side by side) here.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const ROOT = path.resolve(__dirname, '../..');
const PORT = process.env.PORT || 8765;
const BANK_CSS = fs.readFileSync(__dirname + '/phone_bank.css', 'utf8');

const json = execFileSync('dart', ['--packages=.dart_tool/package_config.json', 'design/ui/phone_bank_data.dart'], { cwd: ROOT, encoding: 'utf8', maxBuffer: 1 << 24 });
fs.writeFileSync(__dirname + '/phone_bank.json', json);
const DATA = JSON.parse(json);
const M = Object.fromEntries(DATA.moments.map((m) => [m.key, m]));

// ---------------------------------------------------------------- words (phone.js's own, and its counting rule)
const MONTH = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'];
// the GDD's counting rule (9, «الكتابة»): one and two by the word, 3 to 10 the plural, 11 and up the singular; the
// first two as phone.js has them, the others new (each the thing its ledger row is one of)
const NOUN = {
  head: ['راس واحد', 'راسين', 'روس', 'راس'],
  order: ['طلب واحد', 'طلبين', 'طلبات', 'طلب'],          // a feed or water order
  trip: ['نقلة وحدة', 'نقلتين', 'نقلات', 'نقلة'],         // a truck's trip (a camel home, to a stud, to a festival)
  treat: ['علاج واحد', 'علاجين', 'علاجات', 'علاج'],        // the vet's treatment (handlers.dart _treat)
  prize: ['جائزة وحدة', 'جائزتين', 'جوائز', 'جائزة'],       // a festival's prize
  mating: ['تلقيح واحد', 'تلقيحين', 'تلقيحات', 'تلقيح'],    // a stud's fee, one a mating
  build: ['منشأة وحدة', 'منشأتين', 'منشآت', 'منشأة'],
};
const count = (n, k) => { const [one, two, few, many] = NOUN[k]; return n === 1 ? one : n === 2 ? two : n >= 3 && n <= 10 ? `${n} ${few}` : `${n} ${many}`; };
const n0 = (v) => Math.round(v).toLocaleString('en-US');
const sg = (v) => (v > 0 ? '+' : v < 0 ? '−' : '') + n0(Math.abs(v));
const mon = (ym) => MONTH[Number(ym.slice(5, 7)) - 1];
const monthName = (ym) => `${mon(ym)} ${ym.slice(0, 4)}`;
const dayName = (iso) => `${Number(iso.slice(8, 10))} ${MONTH[Number(iso.slice(5, 7)) - 1]}`;
// a facility by the name the العزبة app gives it (phone.js FAC; the pen there is «شبك ثاني», «شبك ثالث»… by count)
const FACILITY = { pen: 'شبك', tank: 'خزان 30 طن', store: 'مستودع علف', caravan: 'كرفان الراعي', tent: 'بيت الشعر', room: 'غرفة العزبة' };
const I = {
  milk: '<path d="M8.5 3.5h7M9 3.5v3l-2.2 3.3a3 3 0 0 0-.5 1.7v7.5a1.5 1.5 0 0 0 1.5 1.5h8.4a1.5 1.5 0 0 0 1.5-1.5V11.5a3 3 0 0 0-.5-1.7L15 6.5v-3"/><path d="M6.4 13h11.2"/>',
  feed: '<rect x="4" y="7" width="16" height="11" rx="2"/><path d="M9.5 7v11M14.5 7v11"/>',
  water: '<path d="M12 3.5s6 6.4 6 10.6a6 6 0 0 1-12 0C6 9.9 12 3.5 12 3.5z"/>',
  camel: '<path d="M3 8.5c0-1 .8-1.6 1.7-1.6h.9c.9 0 1.5.7 1.4 1.6l-.2 1.2c-.1.8.2 1.5.8 2 .5.4 1.1.4 1.6 0 .5-.5.9-1 1.1-1.6.9-1.7 2.5-2.8 4.4-2.7 1.1.1 2.1.8 2.7 1.8.5.8 1.1 1.3 2 1.6 1.1.4 1.9 1.5 1.9 2.8V15c0 .6-.4 1.2-.9 1.5V20"/><path d="M6.4 12.2V20M9.5 15.5V20M15 15.5V20"/>',
  truck: '<path d="M2.5 6.5h11v9.5h-11z"/><path d="M13.5 9.5h4.2l3.3 3.6V16h-7.5"/><circle cx="6.5" cy="17.5" r="1.8"/><circle cx="17" cy="17.5" r="1.8"/>',
  user: '<circle cx="12" cy="8" r="3.2"/><path d="M5.5 19.5c.6-3.3 3-5 6.5-5s5.9 1.7 6.5 5"/>',
  build: '<path d="M3.5 20.5h17"/><path d="M5.5 20.5V10l6.5-5 6.5 5v10.5"/><path d="M10 20.5v-5h4v5"/>',
  cal: '<rect x="3.5" y="5" width="17" height="15" rx="2.5"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
  back: '<path d="M9 6l6 6-6 6"/>',
};
const svg = (k) => `<svg class="i" viewBox="0 0 24 24">${I[k]}</svg>`;
const sum = (rows) => rows.reduce((n, r) => n + r.amount, 0);
const one = (rows) => (rows.length === 1 ? rows[0] : null);
const named = (r) => r.refName != null;      // (a ref the dump could name: never a raw id on the screen)
// a transport row by its reason (the dump reads it from the rows beside it: the ledger does not keep it)
const TRIP = { purchase: (r) => `نقل ${r.refName} لعزبتك`, mating: (r) => `نقل ${r.refName} للفحل`, festival: (r) => `${r.refName}، رايح جاي` };
// each kind: its name, its icon (phone.js's), and the line under it from its rows. السعي goes with the sale it was
// taken from (the kind «بيع حلال»: what reached the player, as الحراج says «يوصلك … بعد السعي»), so it is no cost row
const KIND = {
  milk: { name: 'الحليب', icon: 'milk', line: (rows, cur) => (cur ? 'ينباع كل يوم، لين اليوم' : 'ينباع كل يوم') },
  sale: { name: 'بيع حلال', icon: 'camel', line: (rows) => {
    const sold = rows.filter((r) => r.cat === 'sale'), fee = -sum(rows.filter((r) => r.cat === 'commission'));
    const what = one(sold) && named(sold[0]) ? `${sold[0].refName} بـ ${n0(sold[0].amount)}` : `${count(sold.length, 'head')} بـ ${n0(sum(sold))}`;
    return fee ? `${what} · السعي ${n0(fee)}` : `${what} · ${dayName(sold[0].date)}`;
  } },
  prize: { name: 'جوائز المزاين', icon: 'camel', line: (rows) => count(rows.length, 'prize') },
  purchase: { name: 'شراء حلال', icon: 'camel', line: (rows) => (one(rows) && named(rows[0]) ? `${rows[0].refName} · ${dayName(rows[0].date)}` : count(rows.length, 'head')) },
  transport: { name: 'النقل', icon: 'truck', line: (rows) => (one(rows) && named(rows[0]) && TRIP[rows[0].why] ? TRIP[rows[0].why](rows[0]) : count(rows.length, 'trip')) },
  feed: { name: 'العلف', icon: 'feed', line: (rows) => count(rows.length, 'order') },
  water: { name: 'الوايت', icon: 'water', line: (rows) => count(rows.length, 'order') },
  wages: { name: 'رواتب الرعاة', icon: 'user', line: () => 'تنخصم أول الشهر' },
  construction: { name: 'البناء', icon: 'build', line: (rows) => (rows.every((r) => FACILITY[r.refName]) ? rows.map((r) => FACILITY[r.refName]).join('، ') : count(rows.length, 'build')) },
  vet: { name: 'البيطري', icon: 'user', line: (rows) => count(rows.length, 'treat') },
  studFee: { name: 'أجرة الفحل', icon: 'camel', line: (rows) => count(rows.length, 'mating') },
};
const kindOf = (cat) => (cat === 'commission' ? 'sale' : cat);

// ---------------------------------------------------------------- the ledger grouped as a presenter would group it
// rows into kinds; in = the kinds that brought money, out = the kinds that cost it (a sale net of its السعي)
function kinds(rows) {
  const by = new Map();
  for (const r of rows) { const k = kindOf(r.cat); if (!by.has(k)) by.set(k, []); by.get(k).push(r); }
  const ks = [...by.entries()].map(([kind, rs]) => ({ kind, rows: rs, v: sum(rs) }));
  return { ks, inn: ks.filter((k) => k.v > 0).reduce((n, k) => n + k.v, 0), out: -ks.filter((k) => k.v < 0).reduce((n, k) => n + k.v, 0) };
}
// a row's month: a roll-up row's own (milk, wages), else its day's; the opening balance apart (not an income)
function months(m) {
  const by = new Map();
  for (const r of m.ledger) {
    if (r.cat === 'opening') continue;
    const ym = r.month || r.date.slice(0, 7);
    if (!by.has(ym)) by.set(ym, []);
    by.get(ym).push(r);
  }
  return [...by.entries()].map(([ym, rows]) => ({ ym, ...kinds(rows) })).sort((a, b) => b.ym.localeCompare(a.ym));
}
const opening = (m) => m.ledger.filter((r) => r.cat === 'opening');
// today: the day's one-off rows, and today's milk (the ledger keeps it as one row a month: GameView.todayNet's rule)
function today(m) {
  const rows = m.ledger.filter((r) => r.day === m.today && r.cat !== 'opening' && r.cat !== 'milk');
  if (m.milkIncomeToday) rows.push({ cat: 'milk', amount: m.milkIncomeToday });
  const t = kinds(rows);
  if (t.inn - t.out !== m.todayNet) throw new Error(`today ${t.inn} - ${t.out} != todayNet ${m.todayNet}`);
  return t;
}
function check(m) {      // the figures add up: the opening and every month's net make the balance (cash == the ledger's sum)
  const total = sum(opening(m)) + months(m).reduce((n, g) => n + g.inn - g.out, 0);
  if (total !== m.cash) throw new Error(`${m.key}: ${total} != cash ${m.cash}`);
}
DATA.moments.forEach(check);

const nav = () => `<div class="nav"><button class="back">${svg('back')}رجوع</button></div>`;
// what came in and what went out (a month's, a day's split): «دخل … · طلع …»; «دخل اليوم / صرفت اليوم» is the day's
// net only, as the home widget has it
const inOut = (inn, out) => [inn ? `دخل ${n0(inn)} ريال` : '', out ? `طلع ${n0(out)} ريال` : ''].filter(Boolean).join(' · ');
// today's line: the net in the home widget's own words; when money moved both ways, what came in and what went out
// on a grey line of its own under it, as each month's row has it (one line holding both read as two «دخل»); green
// only when money only came in (as the widget's «دخل اليوم»)
function todayLine(t) {
  const net = t.inn - t.out;
  const head = net > 0 ? `دخل اليوم ${n0(net)} ريال` : net < 0 ? `صرفت اليوم ${n0(-net)} ريال` : t.inn ? 'اليوم ما زاد ولا نقص' : 'ما فيه حركة اليوم';
  const both = t.inn && t.out ? `<div class="ln ink2">${inOut(t.inn, t.out)}</div>` : '';
  return `<div class="ln${t.inn && !t.out ? ' pos' : !t.inn && !t.out ? ' ink2' : ''}">${head}</div>${both}`;
}
// a month's biggest kind, named (the alternative main screen: where the money went)
function biggest(g) {
  const k = g.ks.slice().sort((a, b) => Math.abs(b.v) - Math.abs(a.v))[0];
  const r = one(k.rows.filter((x) => x.cat !== 'commission'));
  // (a sale by what reached the player: its price less السعي, said so)
  const text = k.kind === 'purchase' && r && named(r) ? `شراء ${r.refName} ${n0(-k.v)} ريال` : k.kind === 'sale' && r && named(r) ? `بيع ${r.refName}، وصلك ${n0(k.v)} ريال` : `${KIND[k.kind].name} ${n0(Math.abs(k.v))} ريال`;
  return { k, text };
}

// the bank's main screen: the balance, today's money, each month's in and out and net (this month first), and the
// opening balance in a line under them (not an income). alt: each month's second line names its biggest kind,
// and its icon is that kind's, instead of the in and out
function main(m, alt = false) {
  const t = today(m), gs = months(m), ym = m.date.slice(0, 7), op = opening(m)[0];
  const mrow = (g) => {
    const net = g.inn - g.out, isCur = g.ym === ym, top = alt ? biggest(g) : null;
    const line = alt ? `أكبرها: ${top.text}` : inOut(g.inn, g.out);
    return `<div class="row"><span class="lead${alt && top.k.v < 0 ? ' out' : ''}">${svg(alt ? KIND[top.k.kind].icon : 'cal')}</span><b>${isCur ? `${mon(g.ym)} · هالشهر` : monthName(g.ym)}</b><span class="amt${net > 0 ? ' pos' : ''}">${sg(net)}</span><small>${line}</small></div>`;
  };
  // the milk buyer's word only when the day's milking sells some (the milk app's own rule: farm.milk.sold)
  const first = op.day === m.today ? `بديت اليوم برصيد ${n0(op.amount)} ريال.${m.milkSold > 0.05 ? ' حليب ناقتك أول دخل لك: يمر المشتري بكرة وياخذه.' : ''}` : `بديت اللعبة ${dayName(op.date)} ${op.date.slice(0, 4)} برصيد ${n0(op.amount)} ريال.`;
  return `<div class="body">${nav()}<div class="title">البنك</div>
    <div class="balance"><small>رصيدك</small><div class="v">${n0(m.cash)}<span>ريال</span></div>${todayLine(t)}</div>
    ${gs.length ? `<div class="sec">الشهور</div><div class="group">${gs.map(mrow).join('')}</div>` : ''}
    <div class="note">${first}</div></div>`;
}

// a month opened: what came in and what went out, each kind with its sum, and the month's net
function month(m, ym) {
  const g = months(m).find((x) => x.ym === ym), cur = ym === m.date.slice(0, 7);
  const row = (k) => `<div class="row"><span class="lead${k.v < 0 ? ' out' : ''}">${svg(KIND[k.kind].icon)}</span><b>${KIND[k.kind].name}</b><span class="amt${k.v > 0 ? ' pos' : ''}">${sg(k.v)}</span><small>${KIND[k.kind].line(k.rows, cur)}</small></div>`;
  const ins = g.ks.filter((k) => k.v > 0).sort((a, b) => b.v - a.v), outs = g.ks.filter((k) => k.v < 0).sort((a, b) => a.v - b.v);
  // a month without milk says so (the ledger has no milk row for it: no nursing camel milked)
  const noMilk = g.ks.some((k) => k.kind === 'milk') ? '' : `<div class="row"><span class="lead out">${svg('milk')}</span><b>الحليب</b><span class="amt"></span><small>ما فيه حليب ${cur ? 'هالشهر' : `في ${mon(ym)}`}</small></div>`;
  const net = g.inn - g.out;
  return `<div class="body">${nav()}<div class="title">${monthName(ym)}</div>
    <div class="balance"><small>${cur ? 'الصافي لين اليوم' : 'الصافي'}</small><div class="v${net > 0 ? ' pos' : ''}"><bdi dir="ltr">${sg(net)}</bdi><span>ريال</span></div>
      <div class="ln ink2">${inOut(g.inn, g.out)}</div></div>
    <div class="sec">الدخل</div><div class="group">${ins.map(row).join('')}${noMilk}</div>
    ${outs.length ? `<div class="sec">المصروف</div><div class="group">${outs.map(row).join('')}</div>` : ''}</div>`;
}

const SCREENS = [
  ['day1', main(M.day1, true)],
  ['october', main(M.october, true)],
  ['october_month', month(M.october, '2026-10')],
  ['april', main(M.april, true)],      // (the owner's option B, 13 Nov 2026: each month by its biggest movement)
  ['november', month(M.april, '2026-11')],
  ['february', month(M.april, '2027-02')],
];

// DRY=1: print each screen's words and stop (no browser)
if (process.env.DRY) {
  for (const [k, html] of SCREENS) console.log(`--- ${k}\n` + html.replace(/<svg[\s\S]*?<\/svg>/g, '').replace(/<\/(div|small|b|span)>/g, '$& ').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim());
  process.exit(0);
}

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 2 });
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.marahEngine || window.marahEngineError, null, { timeout: 300000 });
  await p.waitForTimeout(2500);
  // hold the 3D scene's frames (swiftshader at 2x is slow), released for each shot
  await p.evaluate(() => { const q = []; const raf = window.requestAnimationFrame.bind(window); window.requestAnimationFrame = (f) => { q.push(f); return q.length; }; window.__release = (n = 2) => { for (let i = 0; i < n; i++) { const fs = q.splice(0); for (const f of fs) raf(f); } }; });
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone')).shadowRoot; window.__phone.toggle(); window.__phone.enlarge(); });
  await p.waitForTimeout(400);
  const shots = [];
  for (const [k, html] of SCREENS) {
    await p.evaluate(([html, css]) => {
      const scr = R().querySelector('.scr'), sb = scr.querySelector('.sbar').outerHTML;
      scr.classList.remove('home');
      // (a number kept on the line of the word after it, as phone.js's show() does)
      scr.innerHTML = `<span class="pill"></span>${sb}${html.replace(/(\d) (?=[؀-ۿ])/g, '$1 ')}<div class="hb"></div>`;
      const st = document.createElement('style'); st.textContent = css; scr.appendChild(st);
    }, [html, BANK_CSS]);
    await p.evaluate(() => window.__release(2));
    await p.waitForTimeout(400);
    const file = path.resolve(`mock_bank_${k}.png`);
    await p.screenshot({ path: file, timeout: 300000, clip: { x: (956 - 223) / 2, y: 0, width: 223, height: 440 } });
    shots.push(file);
    // what does not fit: the body's overflow, and any line of a row's label or figure that wraps
    console.log(k, await p.evaluate(() => {
      const bd = R().querySelector('.body');
      const wraps = [...bd.querySelectorAll('.row b, .row .amt, .balance .v, .title')].filter((e) => e.getClientRects().length > 1 || e.offsetHeight > parseFloat(getComputedStyle(e).lineHeight || 0) * 1.6).map((e) => e.textContent);
      return { scroll: bd.scrollHeight, fits: bd.clientHeight, wraps };
    }));
  }
  // the screens side by side, each the phone's strip of the screen (as phone_haraj.jpg)
  const imgs = shots.map((f) => 'data:image/png;base64,' + fs.readFileSync(f).toString('base64'));
  const jpg = await p.evaluate(async (imgs) => {
    const W = 446, H = 880, X = 0;
    const c = document.createElement('canvas'); c.width = W * imgs.length; c.height = H;
    const g = c.getContext('2d');
    for (let i = 0; i < imgs.length; i++) {
      const im = new Image(); im.src = imgs[i]; await im.decode();
      g.drawImage(im, X, 0, W, H, i * W, 0, W, H);
    }
    return c.toDataURL('image/jpeg', 0.86).split(',')[1];
  }, imgs);
  fs.writeFileSync(__dirname + '/phone_bank.jpg', Buffer.from(jpg, 'base64'));
  await b.close();
})();
