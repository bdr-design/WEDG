// Compares two boxes.cjs outputs: per surface, texts that differ and boxes that moved (more than 0.5 px) or changed.
//   node cmp_boxes.cjs base.json build.json [surfaces to ignore, comma separated substrings]
const fs = require('fs');
const [A, B] = [process.argv[2], process.argv[3]].map((f) => JSON.parse(fs.readFileSync(f, 'utf8')));
const IGN = (process.argv[4] || '').split(',').filter(Boolean);
let same = 0, diff = 0;
for (const k of new Set([...Object.keys(A), ...Object.keys(B)])) {
  if (k === 'errors' || IGN.some((s) => k.includes(s))) continue;
  const a = A[k], b = B[k];
  if (!a || !b) { console.log(`${k}: ${a ? 'GONE in the build' : 'NEW in the build'}`); diff++; continue; }
  if (a.error || b.error) { console.log(`${k}: ${a.error || 'ok'} / ${b.error || 'ok'}`); continue; }
  const out = [];
  if (a.text !== b.text) out.push(`  text differs:\n    base:  ${a.text.replace(/\n/g, ' | ')}\n    build: ${b.text.replace(/\n/g, ' | ')}`);
  const mb = new Map(b.boxes.map((x) => [x[0], x]));
  let moved = 0;
  for (const x of a.boxes) {
    const y = mb.get(x[0]);
    if (!y) { if (moved++ < 8) out.push(`  box gone: ${x[0]} «${x[5]}»`); continue; }
    if ([1, 2, 3, 4].some((i) => Math.abs(x[i] - y[i]) > 0.5) || x[5] !== y[5]) { if (moved++ < 8) out.push(`  box ${x[0]} «${x[5]}» ${x.slice(1, 5)} -> ${y.slice(1, 5)} «${y[5]}»`); }
  }
  if (b.boxes.length !== a.boxes.length) out.push(`  boxes ${a.boxes.length} -> ${b.boxes.length}`);
  if (moved > 8) out.push(`  … ${moved} boxes changed in all`);
  if (out.length) { diff++; console.log(`${k}:\n${out.join('\n')}`); } else same++;
}
console.log(`\n${same} surfaces the same, ${diff} differ`);
console.log('page errors:', A.errors?.length || 0, '->', B.errors?.length || 0);
