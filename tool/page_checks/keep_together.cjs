// phone.js keepTogether(): the words a line must not split, on the audit's cases (the three the review found among
// them: a preposition right after another). Reads the function out of phone.js and runs it in node.
//   node tool/page_checks/keep_together.cjs
const fs = require('fs');
const path = require('path');
const src = fs.readFileSync(path.join(__dirname, '..', '..', 'design', 'prototype3d', 'phone.js'), 'utf8');
const m = src.match(/export function keepTogether\(html, mazayen = false\) \{[\s\S]*?\n\}\n/);
if (!m) { console.log('FAIL: keepTogether not found in phone.js'); process.exit(1); }
const keepTogether = new Function(m[0].replace('export ', '') + '\nreturn keepTogether;')();
const NB = ' ';
// [text, mazayen screen, the pairs that must be joined]
const cases = [
  ['المرشح من بعد المفرودة', false, ['من' + NB + 'بعد', 'بعد' + NB + 'المفرودة']],
  ['التسجيل لين قبل كل شوط', false, ['لين' + NB + 'قبل', 'قبل' + NB + 'كل', 'كل' + NB + 'شوط']],
  ['تشارك من كل المهرجانات', false, ['من' + NB + 'كل', 'كل' + NB + 'المهرجانات']],
  ['ابنِ خزان أكبر من العزبة', false, ['من' + NB + 'العزبة']],
  ['خصوصًا قبل 3 شهور.', false, ['قبل' + NB + '3', '3' + NB + 'شهور.']],
  ['الكيس 50 كجم بـ 64 ريال', false, ['50' + NB + 'كجم', 'بـ' + NB + '64', '64' + NB + 'ريال']],
  ['<b>من</b> <span>بعد</span>', false, []],      // (a tag between: left as it is)
  ['سقف السعر لين 100,000', true, ['لين' + NB + '100,000']],
];
let fails = 0;
for (const [t, mz, want] of cases) {
  const out = keepTogether(t, mz);
  const missing = want.filter((w) => !out.includes(w));
  // (no line may end on a lone preposition: none followed by a plain space)
  const lone = out.match(/(^|[\s>])(من|في|على|عن|مع|إلى|الى|لين|قبل|بعد|كل|و) (?=[^\s<])/);
  const ok = !missing.length && !lone;
  if (!ok) fails++;
  console.log(`${ok ? 'ok  ' : 'FAIL'}  ${t}${missing.length ? '  missing: ' + missing.join(' ‖ ') : ''}${lone ? '  lone: ' + lone[0] : ''}`);
}
if (fails) process.exit(1);
console.log('\nkeepTogether: all cases joined');
