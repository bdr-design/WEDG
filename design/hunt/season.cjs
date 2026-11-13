// The hunting season against the camel year, and what a season costs and brings: two DESIGN pictures for the owner
// (13 Nov 2026), nothing built. Drawn as plain pages in the phone's fonts (no game page needed):
//   season_calendar.jpg  a year from August 2026 to July 2027, the falcons' lane above the camels' lane; the new game's
//                        start (1 October) and what its first season can still do; the falcon festival's two date
//                        ranges, each with the camel festival it collides with
//   season_money.jpg     one season's costs against what it can bring, for a pastime and for a contest falcon
// Figures: REAL (research-realism.md section 8, by source number; all of it search-result text, no page opened) or
// GAME CHOICE, as marked on the pictures themselves:
//   Malham breeders' auction 5–25 Aug 2026 [158]; الدعو in September and early October [155]; the national auction of
//   wild-caught falcons 1 Oct – 30 Nov [157]; the season 1 Sep – 31 Jan, autumn to 30 Nov and winter from 1 Dec
//   [127][128][167]; the falcons and hunting exhibition 1–10 Oct and a ملواح race 4–9 Oct 2026 [157]; the falcon
//   festival 2026: 17–30 Nov [157] or 25 Dec – 10 Jan [181] (the sources disagree; 2025 was 25 Dec – 10 Jan
//   [169][157]); the moult (المقيض) in spring and summer: NOT in our research (the reviewer's search only), so drawn
//   hatched and marked as needing a source.
//   The camels' lane is the engine's (seed 4242's festivals: S.festivals, the same as the reviewer's calendar.txt):
//   mating 1 Nov – 30 Apr (GDD 4), الوسم from 16 Oct (GDD 4, real [114][115]), the festivals with their registration.
//   Money: a farm-bred saker about 19,000 and top birds over a million [158]; المزاين's first three 300,000, 175,000,
//   100,000 [177] (one source); 1,012 prizes [170][176] for more than 5,200 falcons [157] in 2025, so about one falcon
//   in five wins anything (an estimate from two sources); selling game is an offence [166]. Everything else is a game
//   choice and marked so: the wild-caught falcon's price 42,000, feed 20 riyals a day, the kit 2,500, the permit 100
//   (a weak source gives 100 [160]), passport and club nothing (no fee found), each outing's fuel 60, the trip to Malham
//   1,500, the entry fee nothing (not found), the ملواح prizes by place, the resale prices.
// To draw again: `NODE_PATH=$(npm root -g) node design/hunt/season.cjs` from the repository's root (no server needed:
// the fonts come from Google Fonts); it writes both JPEGs here (or OUT=<folder>).
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const OUT = process.env.OUT || __dirname;
const FONT = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Alexandria:wght@500;600;700&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap">';

// ---------------------------------------------------------------- the calendar
const D0 = Date.UTC(2026, 7, 1), D1 = Date.UTC(2027, 7, 1);      // 1 Aug 2026 .. 1 Aug 2027
const W = 1500, LEFT = 40, RIGHT = 200, SPAN = W - LEFT - RIGHT;
const x = (y, m, d) => W - RIGHT - (Date.UTC(y, m - 1, d) - D0) / (D1 - D0) * SPAN;      // from the right edge: the year runs right to left
const MONTHS = ['أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر', 'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو'];
// [label, from [y,m,d], to [y,m,d] (inclusive), class, source]
const FALCON = [
  ['المقيض', [2026, 8, 1], [2026, 8, 31], 'moult', ''],
  ['مزاد صقور المزارع · ملهم', [2026, 8, 5], [2026, 8, 25], 'auc', '[158]'],
  ['الدعو', [2026, 9, 1], [2026, 10, 10], 'train', '[155]'],
  ['مزاد الطرح', [2026, 10, 1], [2026, 11, 30], 'auc', '[157]'],
  ['معرض الصقور', [2026, 10, 1], [2026, 10, 10], 'ev', '[157]'],
  ['سباق ملواح', [2026, 10, 4], [2026, 10, 9], 'ev', '[157]'],
  ['المقيض (يبي مصدر)', [2027, 3, 1], [2027, 7, 31], 'moult', ''],
];
const SEASON = [['فترة الخريف', [2026, 9, 1], [2026, 11, 30], 'hunt', '[127][167]'], ['فترة الشتاء', [2026, 12, 1], [2027, 1, 31], 'hunt2', '[127][167]']];
const FEST = [['مهرجان الصقور؟ 17–30 نوفمبر', [2026, 11, 17], [2026, 11, 30], 'fa', '[157]'], ['مهرجان الصقور؟ 25 ديسمبر–10 يناير', [2026, 12, 25], [2027, 1, 10], 'fb', '[181]']];
// the engine's festivals on seed 4242: [name, starts, ends, registration opens, closes]
const CAMEL_F = [
  ['حائل', [2026, 10, 18], [2026, 10, 21], [2026, 10, 1], [2026, 10, 11]],
  ['القصيم', [2026, 11, 8], [2026, 11, 9], [2026, 10, 9], [2026, 11, 1]],
  ['الجوف', [2026, 11, 29], [2026, 12, 2], [2026, 10, 30], [2026, 11, 22]],
  ['المهرجان الكبير', [2026, 12, 1], [2027, 1, 3], [2026, 10, 17], [2026, 11, 24]],
  ['الأحساء', [2027, 2, 7], [2027, 2, 10], [2027, 1, 8], [2027, 1, 31]],
  ['الشمال', [2027, 2, 28], [2027, 3, 1], [2027, 1, 29], [2027, 2, 21]],
  ['نجران', [2027, 3, 28], [2027, 3, 31], [2027, 2, 26], [2027, 3, 21]],
  ['تبوك', [2027, 6, 14], [2027, 6, 15], [2027, 5, 15], [2027, 6, 7]],
];
const bar = (top, h, [lbl, a, z, cls, src]) => {
  const x0 = x(...z) - SPAN / 365, x1 = x(...a);      // (right to left: the end is the left edge; inclusive of the last day)
  const out = x1 - x0 < 30 + lbl.length * 6.5;          // a short bar: its label beside it, to its left
  return `<div class="bar ${cls}${out ? ' out' : ''}" style="top:${top}px;height:${h}px;left:${x0}px;width:${x1 - x0}px"><span>${lbl}${src ? ` <i>${src}</i>` : ''}</span></div>`;
};
const calendar = () => {
  let h = '';
  MONTHS.forEach((m, i) => { const a = x(2026 + (i >= 5 ? 1 : 0), ((7 + i) % 12) + 1, 1), b = x(2026 + (i >= 4 ? 1 : 0), ((8 + i) % 12) + 1, 1); h += `<div class="mon" style="left:${b}px;width:${a - b}px">${m}</div>`; });
  for (let i = 0; i <= 12; i++) { const yy = 2026 + ((7 + i) >= 12 ? 1 : 0), mm = ((7 + i) % 12) + 1; h += `<div class="grid" style="left:${x(yy, mm, 1)}px"></div>`; }
  h += `<div class="lane" style="top:84px">الصقور</div>`;
  h += bar(80, 28, FALCON[0]) + bar(80, 28, FALCON[6]) + bar(80, 28, FALCON[2]) + bar(112, 28, FALCON[1]) + bar(112, 28, FALCON[3]) + bar(144, 24, FALCON[4]) + bar(172, 24, FALCON[5]);
  h += `<div class="lane" style="top:218px">موسم الصيد</div>`;
  h += bar(212, 34, SEASON[0]) + bar(212, 34, SEASON[1]);
  h += `<div class="lane" style="top:270px">مهرجان الصقور</div>`;
  h += bar(264, 28, FEST[0]) + bar(298, 28, FEST[1]);
  h += `<div class="note" style="top:266px;left:${x(2027, 6, 30)}px;width:${x(2027, 2, 1) - x(2027, 6, 30)}px">المصادر مختلفة على نسخة 2026 ([157] أو [181])، ونسخة 2025 كانت 25 ديسمبر–10 يناير [169][157]</div>`;
  h += `<div class="lane" style="top:352px">الإبل</div>`;
  h += bar(346, 26, ['الضراب', [2026, 11, 1], [2027, 4, 30], 'mate', 'GDD 4']);
  h += `<div class="tick" style="left:${x(2026, 10, 16)}px;top:378px">الوسم من 16 أكتوبر</div>`;
  const row0 = 404, rh = 30;
  CAMEL_F.forEach(([n, a, z, ra, rz], i) => { const t = row0 + i * rh; h += bar(t, 24, ['', ra, rz, 'reg', '']) + bar(t, 24, [n, a, z, n === 'المهرجان الكبير' ? 'big' : 'cf', '']); });
  h += `<div class="lane small" style="top:${row0 + 2}px">مزاين اللعبة<br><span>الفاتح: التسجيل</span></div>`;
  // collisions: a band from the festival's option down to the camel festival it meets
  const clash = (a, z, top, bottom, t) => { const x0 = x(...z) - SPAN / 365, x1 = x(...a); return `<div class="clash" style="left:${x0 - 2}px;width:${x1 - x0 + 4}px;top:${top}px;height:${bottom - top}px"></div><div class="ct" style="left:${x0 - 236}px;top:${bottom - 22}px">${t}</div>`; };
  h += clash([2026, 11, 29], [2026, 11, 30], 262, row0 + 2 * rh + 26, 'لو بنوفمبر: آخره يصادف الجوف');
  h += clash([2026, 12, 25], [2027, 1, 3], 296, row0 + 3 * rh + 26, 'لو بديسمبر: داخل المهرجان الكبير');
  h += `<div class="start" style="left:${x(2026, 10, 1)}px"></div><div class="startt" style="left:${x(2026, 10, 1) - 1}px">بداية اللعبة · 1 أكتوبر</div>`;
  return `<!doctype html><meta charset="utf-8">${FONT}<style>
    body { margin: 0; width: ${W}px; height: 820px; background: #f6f1e7; font-family: "IBM Plex Sans Arabic", sans-serif; direction: rtl; color: #1c1712; position: relative; overflow: hidden; }
    h1 { font: 700 24px/1 Alexandria, sans-serif; margin: 0; position: absolute; right: 24px; top: 12px; } h1 small { font: 500 14px "IBM Plex Sans Arabic"; color: #6e6457; margin-right: 10px; }
    .mon { position: absolute; top: 46px; text-align: center; font: 600 13px Alexandria; color: #6e6457; }
    .grid { position: absolute; top: 64px; height: 600px; width: 1px; background: #e2d8c6; }
    .lane { position: absolute; right: 18px; width: 170px; font: 700 15px Alexandria; color: #4a3f33; } .lane.small span { font: 500 12px "IBM Plex Sans Arabic"; color: #6e6457; }
    .bar { position: absolute; border-radius: 7px; display: flex; align-items: center; justify-content: center; overflow: hidden; font-size: 12px; font-weight: 600; white-space: nowrap; }
    .bar span { padding: 0 6px; } .bar.out { overflow: visible; justify-content: flex-start; } .bar.out span { position: absolute; right: calc(100% + 2px); color: #1c1712; padding: 0 2px; } .bar i { font-style: normal; font-weight: 500; opacity: .75; font-size: 11px; }
    .auc { background: #f2d7a6; color: #5a3d0f; } .train { background: #cfe6d6; color: #1f5a37; } .ev { background: #e7e0f2; color: #45366b; }
    .moult { background: repeating-linear-gradient(-45deg, #e9e2d6 0 6px, #ddd3c2 6px 12px); color: #6e6457; }
    .hunt { background: #0b8a5c; color: #fff; } .hunt2 { background: #2f7fcf; color: #fff; }
    .fa, .fb { background: #fff; border: 2px dashed #c27a12; color: #8a560b; }
    .mate { background: #f3d5cf; color: #7a2a1d; } .reg { background: #e9e5dc; color: #6e6457; font-size: 10.5px; } .cf { background: #c8402f; color: #fff; } .big { background: #8e2b1f; color: #fff; }
    .clash { position: absolute; border: 2.5px solid #e5372b; border-radius: 8px; background: rgba(229,55,43,.07); }
    .ct { position: absolute; width: 230px; font: 700 12px "IBM Plex Sans Arabic"; color: #e5372b; text-align: left; }
    .note { position: absolute; font-size: 12px; color: #8a560b; line-height: 1.4; }
    .tick { position: absolute; font-size: 11.5px; font-weight: 600; color: #2f6e9e; border-right: 2px solid #2f6e9e; padding-right: 4px; }
    .start { position: absolute; top: 64px; height: 600px; width: 0; border-left: 3px solid #111; }
    .startt { position: absolute; top: 664px; transform: translateX(-100%); font: 700 13px Alexandria; background: #111; color: #fff; padding: 3px 8px; border-radius: 6px; white-space: nowrap; }
    .box { position: absolute; bottom: 14px; right: 24px; left: 24px; display: grid; grid-template-columns: 1fr 1fr; gap: 18px; font-size: 13px; line-height: 1.55; }
    .box div { background: #fff; border-radius: 12px; padding: 10px 14px; } .box b { font-family: Alexandria; }
  </style><h1>موسم القنيص وسنة الإبل<small>من أغسطس 2026 لين يوليو 2027 · الأرقام بين [ ] مصادر البحث، والباقي اختيار لعب</small></h1>${h}
  <div class="box"><div><b>أول موسم بلعبة جديدة (تبدأ 1 أكتوبر):</b> الموسم صار له شهر، ومزاد ملهم راح، ومزاد الطرح مفتوح لين 30 نوفمبر. تشتري صقر طرح، تطلع جوازه وتصريحك، وتدعيه 4 أسابيع (اختيار لعب)، فأول طلعة حوالي آخر أكتوبر أو أول نوفمبر، والمهرجان الكبير للإبل يطلب تسجيل حلالك بنفس الوقت.</div>
  <div><b>وين يتصادم:</b> لو مهرجان الصقور 17–30 نوفمبر يصادف آخره مزاين الجوف (29 نوفمبر–2 ديسمبر) وآخر أيام تسجيل المهرجان الكبير. ولو 25 ديسمبر–10 يناير يصير داخل المهرجان الكبير للإبل (لين 3 يناير): يختار اللاعب وش يحضر، والراعي يمسك الحلال.</div></div>`;
};

// ---------------------------------------------------------------- the money
const money = () => {
  const r = (a, b, c, d, cls = '') => `<tr class="${cls}"><td>${a}</td><td>${b}</td><td>${c}</td><td class="src">${d}</td></tr>`;
  return `<!doctype html><meta charset="utf-8">${FONT}<style>
    body { margin: 0; width: 1300px; background: #f6f1e7; font-family: "IBM Plex Sans Arabic", sans-serif; direction: rtl; color: #1c1712; padding: 18px 24px 20px; box-sizing: border-box; }
    h1 { font: 700 24px/1.2 Alexandria, sans-serif; margin: 0 0 4px; } p.s { margin: 0 0 12px; color: #6e6457; font-size: 13.5px; }
    table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; font-size: 14px; }
    th { background: #2a2119; color: #f6f1e7; font: 600 14px Alexandria; padding: 9px 12px; text-align: right; }
    td { padding: 7px 12px; border-top: 1px solid #eee5d6; } td:nth-child(2), td:nth-child(3) { font-family: Alexandria; font-weight: 600; white-space: nowrap; }
    td.src { font-size: 12px; color: #6e6457; } tr.h td { background: #f1ebe0; font: 700 13px Alexandria; color: #4a3f33; }
    tr.tot td { background: #fbf6ec; font-weight: 700; } .neg { color: #c4362b; } .pos { color: #0b8a5c; }
    .q { margin-top: 12px; background: #fff; border-radius: 12px; padding: 12px 16px; font-size: 14px; line-height: 1.6; box-shadow: inset 0 0 0 2px #e8b46c; }
  </style><h1>موسم واحد: وش يكلّف ووش يجيب (بالريال)</h1>
  <p class="s">صقر طرح واحد من مزاد الطرح، موسم كامل. الأرقام بين [ ] من البحث (كله من نصوص نتايج البحث، ما فتحنا صفحة رسمية)، والباقي اختيار لعب.</p>
  <table><tr><th></th><th>هواية: طلعات بس</th><th>مسابقات بعد</th><th>من وين الرقم</th></tr>
  ${r('اللي تصرفه', '', '', '', 'h')}
  ${r('الصقر: حر طرح من المزاد', '42,000', '42,000', 'اختيار لعب. صقر المزارع حوالي 19,000 والكبار فوق المليون [158]')}
  ${r('أكله 5 شهور', '3,060', '3,060', 'اختيار لعب: 20 ريال باليوم')}
  ${r('عدته: البرقع والدس والوكر والميزان وجهاز التتبع', '2,500', '2,500', 'اختيار لعب')}
  ${r('الجواز والتسجيل بالنادي', '0', '0', 'ما لقينا رسوم')}
  ${r('تصريح الصيد', '100', '100', 'اختيار لعب (مصدر ضعيف يقول 100 [160])')}
  ${r('10 طلعات: بنزين', '600', '600', 'اختيار لعب: 60 للطلعة')}
  ${r('رسوم التسجيل والنقل لملهم', '', '1,500', 'التسجيل ما لقيناه (ببلاش)، والنقل اختيار لعب')}
  ${r('اللي يجيك', '', '', '', 'h')}
  ${r('بيع الصيد', '0', '0', 'ممنوع: بيع الصيد مخالفة [166]')}
  ${r('جوايز، اللي يصير أغلب المرات', '', '0', 'تقريبًا صقر من كل خمسة يفوز بشي: 1,012 جايزة [170][176] لأكثر من 5,200 صقر [157]')}
  ${r('جوايز، لو جا بالمراكز', '', '25,000 – 300,000', 'المزاين: 300,000 و175,000 و100,000 للثلاثة الأوائل [177] (مصدر واحد)؛ الملواح بالمراكز اختيار لعب')}
  ${r('بيعه آخر الموسم', '45,000', '45,000 – 80,000', 'اختيار لعب: يغلى بالدعو والنتايج')}
  ${r('آخر الموسم لو بعته', '<span class="neg">−3,260</span>', '<span class="neg">−4,760</span> لين <span class="pos">+130,240</span> (ثالث بالمزاين)', 'الهواية تكلف شوي لو بعته، وأكثر لو خليته. والمسابقات: أغلبها خسارة بسيطة، ومرة بالكثير ربح كبير', 'tot')}
  </table>
  <div class="q"><b>قرارك:</b> الصقور تبقى هواية تصرف عليها ومعها فرصة نادرة بجايزة كبيرة، ولا تصير تجارة ثانية؟ <b>نقترح الأولى:</b> الجوايز حقيقية وكبيرة بس نادرة مثل الواقع (صقر من خمسة يفوز بشي، والأوائل أقل بكثير)، فما تصير الصقور طريق مضمون للفلوس، والإبل تبقى الأساس.</div>`;
};

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1500, height: 820 }, deviceScaleFactor: 1.5 });
  for (const [name, html, w] of [['season_calendar', calendar(), 1500], ['season_money', money(), 1300]]) {
    await p.setViewportSize({ width: w, height: 820 });
    await p.setContent(html, { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    const png = path.join(OUT, name + '.png');
    await p.screenshot({ path: png, fullPage: true });
    execFileSync('convert', [png, '-quality', '88', png.replace(/png$/, 'jpg')]); fs.unlinkSync(png);
    console.log('wrote', name);
  }
  await b.close();
})();
