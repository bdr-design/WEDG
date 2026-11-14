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
//   The average prize a falcon: more than 38 million [170][176] over more than 5,200 falcons [157], about 7,300 (an
//   estimate from two sources). The third place's 100,000 is one round's split [177]. No auction runs from December to
//   August, so the falcon is sold at the next autumn's national auction, after eight months of feed through the moult.
//   The trapping lane: the trapping season 1 Oct - 30 Nov [184][185][186]; the passage from September, the peregrine's
//   peak in October, to December [198][202][205]; the three routes to a falcon (the proxy's batch 3 item 5): the
//   breeders' auction in August [158], the exhibition's imported sakers 1-10 Oct [157][184], the trapping auction
//   1 Oct - 30 Nov where the player sells or buys [184].
//   Money, round 2 (no single "expected profit" anywhere: the range only):
//   - trapping, a season alone: chance 0.08 to 0.336 (40 birds in 2025 over 119 trappers [213], or «مئات» [211]: the
//     proxy's range, a game choice inside the sources; 0.336 = 40/119), shown as about one season in 13 (1/0.08 = 12.5,
//     rounded against the player) to one in 3 (1/0.336 = 2.98); mean price 88,000 [200] to 160,000 [213]; the season's cost 20,000
//     INVENTED; expected about -13,000 (0.08 x 88,000 - 20,000 = -12,960) to about +33,760 (0.336 x 160,000 - 20,000), the
//     first rounded against the player, the second exact; a bird of 300,000 or more: one season in about 83 (1 / (0.08 x 6/40) =
//     83.3) to 20 (1 / (0.336 x 6/40) = 19.8), at least 6 of the 40 birds of 2025 that dear [213][185] (a floor);
//     partners raise the chance and divide the price, groups of 2 to 9 [184][190][200] (the next step: proxy item 2);
//     the gear's 8,600 is the phone's game-choice prices;
//   - falconry: a farm-bred saker about 19,000 [158] or a peregrine of the year from about 50,000 [200]; game choices:
//     the falcons' room 18,000 holding 4, feed 20 riyals a day (3,060), kit 2,500, permit 100 (a weak source gives 100
//     [160]), four trips of days at 1,500 each; game is never sold [166]; no lawful resale route found for a kept falcon
//     (proxy item 6); contest prizes: about one falcon in five wins anything, average about 7,300 a falcon (more than
//     38 million [170][176] over more than 5,200 falcons [157]: an estimate), a third place in المزاين 100,000 [177].
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
  ['المقيض (يبي مصدر)', [2026, 8, 1], [2026, 8, 31], 'moult tiny', ''],
  ['مزاد المزارع (طريق 1) [158]', [2026, 8, 5], [2026, 8, 25], 'auc tiny', ''],
  ['الدعو', [2026, 9, 1], [2026, 10, 10], 'train', '[155]'],
  ['مزاد الطرح (طريق 3)', [2026, 10, 1], [2026, 11, 30], 'auc2', '[184]'],
  ['معرض الصقور: حر مستورد (طريق 2)', [2026, 10, 1], [2026, 10, 10], 'ev', '[157][184]'],
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
  const out = !cls.includes('tiny') && x1 - x0 < 30 + lbl.length * 6.5;          // a short bar: its label beside it, to its left
  return `<div class="bar ${cls}${out ? ' out' : ''}" style="top:${top}px;height:${h}px;left:${x0}px;width:${x1 - x0}px"><span>${lbl}${src ? ` <i>${src}</i>` : ''}</span></div>`;
};
const calendar = () => {
  let h = '';
  MONTHS.forEach((m, i) => { const a = x(2026 + (i >= 5 ? 1 : 0), ((7 + i) % 12) + 1, 1), b = x(2026 + (i >= 4 ? 1 : 0), ((8 + i) % 12) + 1, 1); h += `<div class="mon" style="left:${b}px;width:${a - b}px">${m}</div>`; });
  for (let i = 0; i <= 12; i++) { const yy = 2026 + ((7 + i) >= 12 ? 1 : 0), mm = ((7 + i) % 12) + 1; h += `<div class="grid" style="left:${x(yy, mm, 1)}px"></div>`; }
  h += `<div class="lane" style="top:84px">الصقور</div>`;
  h += bar(80, 28, FALCON[0]) + bar(80, 28, FALCON[6]) + bar(80, 28, FALCON[2]) + bar(112, 28, FALCON[1]) + bar(112, 28, FALCON[3]) + bar(144, 24, FALCON[4]) + bar(172, 24, FALCON[5]);
  h += `<div class="lane" style="top:210px">الطرح</div>`;
  h += bar(206, 24, ['عبور الصقور: الشمال من سبتمبر، والشاهين أكثره بأكتوبر، لين ديسمبر', [2026, 9, 1], [2026, 12, 31], 'pass', '[198][202][205]']);
  h += bar(234, 30, ['موسم الطرح', [2026, 10, 1], [2026, 11, 30], 'trap', '[184][185][186]']);
  h += `<div class="lane" style="top:282px">موسم الصيد</div>`;
  h += bar(276, 34, SEASON[0]) + bar(276, 34, SEASON[1]);
  h += `<div class="lane" style="top:334px">مهرجان الصقور</div>`;
  h += bar(328, 28, FEST[0]) + bar(362, 28, FEST[1]);
  h += `<div class="note" style="top:330px;left:${x(2027, 6, 30)}px;width:${x(2027, 2, 1) - x(2027, 6, 30)}px">المصادر مختلفة على نسخة 2026 ([157] أو [181])، ونسخة 2025 كانت 25 ديسمبر–10 يناير [169][157]</div>`;
  h += `<div class="lane" style="top:416px">الإبل</div>`;
  h += bar(410, 26, ['الضراب', [2026, 11, 1], [2027, 4, 30], 'mate', 'GDD 4']);
  h += `<div class="tick" style="left:${x(2026, 10, 16)}px;top:442px">الوسم من 16 أكتوبر</div>`;
  const row0 = 468, rh = 30;
  CAMEL_F.forEach(([n, a, z, ra, rz], i) => { const t = row0 + i * rh; h += bar(t, 24, ['', ra, rz, 'reg', '']) + bar(t, 24, [n, a, z, n === 'المهرجان الكبير' ? 'big' : 'cf', '']); });
  h += `<div class="lane small" style="top:${row0 + 2}px">مزاين اللعبة<br><span>الفاتح: التسجيل</span></div>`;
  // collisions: a band from the festival's option down to the camel festival it meets
  const clash = (a, z, top, bottom, t) => { const x0 = x(...z) - SPAN / 365, x1 = x(...a); return `<div class="clash" style="left:${x0 - 2}px;width:${x1 - x0 + 4}px;top:${top}px;height:${bottom - top}px"></div><div class="ct" style="left:${x0 - 236}px;top:${bottom - 22}px">${t}</div>`; };
  h += clash([2026, 11, 29], [2026, 11, 30], 326, row0 + 2 * rh + 26, 'لو بنوفمبر: آخره يصادف الجوف');
  h += clash([2026, 12, 25], [2027, 1, 3], 360, row0 + 3 * rh + 26, 'لو بديسمبر: داخل المهرجان الكبير');
  h += `<div class="start" style="left:${x(2026, 10, 1)}px"></div><div class="startt" style="left:${x(2026, 10, 1) - 1}px">بداية اللعبة: 1 أكتوبر</div>`;
  return `<!doctype html><meta charset="utf-8">${FONT}<style>
    body { margin: 0; width: ${W}px; height: 900px; background: #f6f1e7; font-family: "IBM Plex Sans Arabic", sans-serif; direction: rtl; color: #1c1712; position: relative; overflow: hidden; }
    h1 { font: 700 24px/1 Alexandria, sans-serif; margin: 0; position: absolute; right: 24px; top: 12px; } h1 small { font: 500 14px "IBM Plex Sans Arabic"; color: #6e6457; margin-right: 10px; }
    .mon { position: absolute; top: 46px; text-align: center; font: 600 13px Alexandria; color: #6e6457; }
    .grid { position: absolute; top: 64px; height: 664px; width: 1px; background: #e2d8c6; }
    .lane { position: absolute; right: 18px; width: 170px; font: 700 15px Alexandria; color: #4a3f33; } .lane.small span { font: 500 12px "IBM Plex Sans Arabic"; color: #6e6457; }
    .bar { position: absolute; border-radius: 7px; display: flex; align-items: center; justify-content: center; overflow: hidden; font-size: 12px; font-weight: 600; white-space: nowrap; }
    .bar span { padding: 0 6px; } .bar.out { overflow: visible; justify-content: flex-start; } .bar.out span { position: absolute; right: calc(100% + 2px); color: #1c1712; padding: 0 2px; } .bar i { font-style: normal; font-weight: 500; opacity: .75; font-size: 11px; }
    .auc { background: #f2d7a6; color: #5a3d0f; } .auc2 { background: #e9c27c; color: #4a300a; } .pass { background: #e6ddf0; color: #4a3d63; font-size: 11px; } .trap { background: #6b4f9e; color: #fff; } .train { background: #cfe6d6; color: #1f5a37; } .ev { background: #e7e0f2; color: #45366b; }
    .bar.tiny span { font-size: 10.5px; white-space: normal; line-height: 1.05; text-align: center; } .moult { background: repeating-linear-gradient(-45deg, #e9e2d6 0 6px, #ddd3c2 6px 12px); color: #6e6457; }
    .hunt { background: #0b8a5c; color: #fff; } .hunt2 { background: #2f7fcf; color: #fff; }
    .fa, .fb { background: #fff; border: 2px dashed #c27a12; color: #8a560b; }
    .mate { background: #f3d5cf; color: #7a2a1d; } .reg { background: #e9e5dc; color: #6e6457; font-size: 10.5px; } .cf { background: #c8402f; color: #fff; } .big { background: #8e2b1f; color: #fff; }
    .clash { position: absolute; border: 2.5px solid #e5372b; border-radius: 8px; background: rgba(229,55,43,.07); }
    .ct { position: absolute; width: 230px; font: 700 12px "IBM Plex Sans Arabic"; color: #e5372b; text-align: left; }
    .note { position: absolute; font-size: 12px; color: #8a560b; line-height: 1.4; }
    .tick { position: absolute; font-size: 11.5px; font-weight: 600; color: #2f6e9e; border-right: 2px solid #2f6e9e; padding-right: 4px; }
    .start { position: absolute; top: 64px; height: 664px; width: 0; border-left: 3px solid #111; }
    .startt { position: absolute; top: 728px; transform: translateX(-100%); font: 700 13px "IBM Plex Sans Arabic"; background: #111; color: #fff; padding: 3px 8px; border-radius: 6px; white-space: nowrap; }
    .box { position: absolute; bottom: 14px; right: 24px; left: 24px; display: grid; grid-template-columns: 1fr 1fr; gap: 18px; font-size: 13px; line-height: 1.55; }
    .box div { background: #fff; border-radius: 12px; padding: 10px 14px; } .box b { font-family: Alexandria; }
  </style><h1>موسم القنيص وسنة الإبل<small>من أغسطس 2026 لين يوليو 2027 · الأرقام بين [ ] مصادر البحث، والباقي اختيار لعب</small></h1>${h}
  <div class="box"><div><b>أول موسم بلعبة جديدة (تبدأ 1 أكتوبر):</b> الطرح يفتح نفس اليوم، ومزاد الطرح يبدأ معه، ومعرض الصقور مفتوح لين 10 أكتوبر، ومزاد المزارع راح لين أغسطس الجاي. تطلّع تصريح الطرح وتشتري عدتك وتطلع للمخيم؛ أو تشتري صقرك من المعرض أو مزاد الطرح وتدعيه 4 أسابيع (اختيار لعب). والمهرجان الكبير للإبل يطلب تسجيل حلالك بنفس الوقت.</div>
  <div><b>وين يتصادم:</b> الطرح كله (أكتوبر ونوفمبر) فوق تسجيل المهرجان الكبير ومزاين حائل والقصيم والجوف وأول الضراب، والمخيم أيام. ولو مهرجان الصقور 17–30 نوفمبر يصادف آخره الجوف، ولو 25 ديسمبر–10 يناير يصير داخل المهرجان الكبير. والعزبة تمشي مثل كل يوم وانت غايب.</div></div>`;
};

// ---------------------------------------------------------------- the money
const money = () => {
  const r = (a, b, c, d, cls = '') => `<tr class="${cls}"><td>${a}</td><td>${b}</td><td>${c}</td><td class="src">${d}</td></tr>`;
  return `<!doctype html><meta charset="utf-8">${FONT}<style>
    body { margin: 0; width: 1300px; background: #f6f1e7; font-family: "IBM Plex Sans Arabic", sans-serif; direction: rtl; color: #1c1712; padding: 18px 24px 20px; box-sizing: border-box; }
    h1 { font: 700 24px/1.2 Alexandria, sans-serif; margin: 0 0 4px; } h2 { font: 700 18px Alexandria; margin: 16px 0 6px; } p.s { margin: 0 0 10px; color: #6e6457; font-size: 13.5px; }
    table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; font-size: 14px; }
    th { background: #2a2119; color: #f6f1e7; font: 600 14px Alexandria; padding: 9px 12px; text-align: right; }
    td { padding: 7px 12px; border-top: 1px solid #eee5d6; } td:nth-child(2), td:nth-child(3) { font-family: Alexandria; font-weight: 600; }
    td.src { font-size: 12px; color: #6e6457; } tr.tot td { background: #fbf6ec; font-weight: 700; } .neg { color: #c4362b; } .pos { color: #0b8a5c; }
    .q { margin-top: 12px; background: #fff; border-radius: 12px; padding: 12px 16px; font-size: 14px; line-height: 1.6; box-shadow: inset 0 0 0 2px #e8b46c; }
  </style><h1>الصقور تجارة ثانية: وش يكلّف ووش يجيب (بالريال)</h1>
  <p class="s">الأرقام بين [ ] من البحث (نصوص نتايج بحث وصفحات وكالة الأنباء، ما لقينا نص نظام الطرح)، و«الوكيل» جواب مؤقت لين يرد المالك، والباقي اختيار لعب. ما فيه رقم «ربح متوقع» واحد: المدى بس.</p>
  <h2>موسم طرح واحد، لحالك</h2>
  <table><tr><th></th><th>مبتدي عدته قليلة</th><th>عدته كاملة وأرضه زينة</th><th>من وين الرقم</th></tr>
  ${r('حظه بطير ينباع بالموسم', 'حوالي موسم من 13', 'حوالي موسم من 3', '40 طير بموسم 2025 على 119 طاروح [213]، أو «مئات» [211]: المدى 0.08 لين 0.336، والعدة تحركك داخله وما تطلعك فوقه (الوكيل، اختيار لعب)')}
  ${r('سعر الطير بالمتوسط', '88,000', '160,000', '2022: 7.125 مليون على 81 طير [200]؛ 2025 حوالي 160,000 [213]')}
  ${r('مصروف الموسم: المخيم والبنزين والحمام والشبك', '20,000', '20,000', 'مخترع: ما لقينا له رقم، وباللعبة يتبع العدة')}
  ${r('العدة تشتريها مرة', '0', '8,600', 'اختيار لعب: أسعار عدة الطاروح بالجوال')}
  ${r('اللي يصير أغلب المواسم', 'ما ينطرح طير', 'ما ينطرح طير', 'وتخسر مصروف المخيم')}
  ${r('المتوقع بالموسم (حظ × سعر − مصروف)', '<span class="neg">حوالي −13,000</span>', '<span class="pos">حوالي +33,760</span>', '0.08 × 88,000 − 20,000 = −12,960 (مقرّب ضد اللاعب) و0.336 × 160,000 − 20,000 = +33,760')}
  ${r('طير بـ 300,000 وفوق', 'موسم من 83 تقريبًا', 'موسم من 20 تقريبًا', 'على الأقل 6 من 40 طير بموسم 2025 [213][185]: 1 ÷ (0.08 × 6/40) و1 ÷ (0.336 × 6/40) = 83.3 و19.8، مقرّب لأقرب رقم')}
  ${r('مع شركاء (الخطوة الجاية)', '', '', 'يزيد الحظ ويتقسم السعر: أغلب الطيور طرحها ربع من 2 لين 9 [184][190][200] (الوكيل: لحالك أول)', 'tot')}
  </table>
  <h2>المقناص بصقرك (هواية تصرف عليها)</h2>
  <table><tr><th></th><th>بالموسم</th><th></th><th>من وين الرقم</th></tr>
  ${r('صقرك', '19,000 أو من 50,000', '', 'حر فرخ من مزاد المزارع حوالي 19,000 [158]؛ أو فرخ شاهين بحري من مزاد الطرح من حوالي 50,000 [200]؛ أو طير طرحته وخليته لك (الوكيل)')}
  ${r('غرفة الصقور (تبنيها مرة)', '18,000', '', 'اختيار لعب: تشيل 4 صقور')}
  ${r('أكله 5 شهور، وعدته', '3,060 + 2,500', '', 'اختيار لعب: 20 ريال باليوم')}
  ${r('تصريح الصيد', '100', '', 'اختيار لعب (مصدر ضعيف يقول 100 [160])')}
  ${r('4 رحلات مقناص، كل رحلة أيام', '6,000', '', 'اختيار لعب: 1,500 للرحلة (مخيم وبنزين)')}
  ${r('بيع الصيد، وبيع الصقر بعدين', '0', '', 'بيع الصيد ممنوع [166]؛ والصقر ما لقينا له طريق بيع نظامي بعدين (الوكيل)')}
  ${r('جوايز المسابقات', 'أغلب المرات 0', '', 'تقريبًا صقر من خمسة يفوز بشي، والمعدل حوالي 7,300 للصقر (أكثر من 38 مليون [170][176] على أكثر من 5,200 صقر [157]: تقدير)؛ الثالث بالمزاين 100,000 [177]', 'tot')}
  </table>
  <div class="q"><b>قرار المالك:</b> «تجارة ثانية»، وبكلامه «اصيده صيد وفيه طيور بس قيمتها عاليه جدًا»: يعني الطرح. والمدى فوق يوري إن التجارة حقيقية بس صعبة: أغلب المواسم ما فيها طير، والطير الغالي نادر.</div>`;
};

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1500, height: 900 }, deviceScaleFactor: 1.5 });
  for (const [name, html, w] of [['season_calendar', calendar(), 1500], ['season_money', money(), 1300]]) {
    await p.setViewportSize({ width: w, height: 900 });
    await p.setContent(html, { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    const png = path.join(OUT, name + '.png');
    await p.screenshot({ path: png, fullPage: true });
    execFileSync('convert', [png, '-quality', '88', png.replace(/png$/, 'jpg')]); fs.unlinkSync(png);
    console.log('wrote', name);
  }
  await b.close();
})();
