// The typography audit's table: one row per surface (type_audit.cjs's audit.json), each check's count, the smallest
// text as drawn (CSS px, and its em in millimetres on a 6.1 inch iPhone: 460 pixels an inch at 3 to the CSS pixel,
// 0.166 mm a CSS px; the owner's 6.9 inch phone has the same density) and the type scale's size.
//   node tool/page_checks/type_table.cjs <before>/audit.json [<after>/audit.json]
const fs = require('fs');
const MM = 25.4 / 460 * 3;      // (mm a CSS px)
const CHECKS = ['split', 'prepNum', 'prepEnd', 'widow', 'clipped', 'ellipsis', 'outside', 'lineHeight', 'digits', 'noSep', 'minus', 'hyphenMinus', 'parens', 'dot', 'spacing', 'proportional', 'contrast'];
const SHORT = { split: 'split', prepNum: 'prep|n', prepEnd: 'prep|', widow: 'widow', clipped: 'clip', ellipsis: '…', outside: 'out', lineHeight: 'lh', digits: '٣', noSep: 'nosep', minus: 'minus', hyphenMinus: 'hyph', parens: '()', dot: '·', spacing: 'track', proportional: 'prop', contrast: 'contr' };
const surfaces = (res) => Object.entries(res).filter(([, v]) => v && !Array.isArray(v) && !v.error);
function row(v) { return CHECKS.map((k) => (v[k] || []).length); }
function table(res, after) {
  const head = ['surface', ...CHECKS.map((k) => SHORT[k]), 'min px', 'mm', 'sizes'];
  const lines = [head.join('\t')];
  const tot = CHECKS.map(() => 0), totA = CHECKS.map(() => 0);
  for (const [k, v] of surfaces(res)) {
    const a = after && after[k];
    const r = row(v), ra = a && !a.error ? row(a) : null;
    r.forEach((x, i) => (tot[i] += x)); if (ra) ra.forEach((x, i) => (totA[i] += x));
    const cell = (i) => (ra ? (r[i] === ra[i] ? String(r[i]) : `${r[i]}→${ra[i]}`) : String(r[i]));
    const px = v.smallest ? v.smallest.px : '', pa = a && a.smallest ? a.smallest.px : px;
    lines.push([k, ...CHECKS.map((_, i) => cell(i)), px === pa ? px : `${px}→${pa}`, px ? (pa * MM).toFixed(2) : '', Object.keys(v.sizes || {}).length + (a && a.sizes && Object.keys(a.sizes).length !== Object.keys(v.sizes || {}).length ? '→' + Object.keys(a.sizes).length : '')].join('\t'));
  }
  lines.push(['TOTAL', ...CHECKS.map((_, i) => (after ? (tot[i] === totA[i] ? String(tot[i]) : `${tot[i]}→${totA[i]}`) : String(tot[i]))), '', '', ''].join('\t'));
  return lines.join('\n');
}
// every finding, by surface and check (for the report's detail)
function details(res) {
  const out = [];
  for (const [k, v] of surfaces(res)) {
    const f = CHECKS.filter((c) => (v[c] || []).length);
    if (!f.length && !v.smallest) continue;
    out.push(`## ${k} (scale ${v.scale}; smallest ${v.smallest ? `${v.smallest.px}px = ${v.smallest.css}px x scale, ${v.smallest.text}` : '-'})`);
    out.push('   sizes: ' + Object.entries(v.sizes || {}).map(([s, n]) => `${s} x${n}`).join(', '));
    for (const c of f) out.push(`   ${c}: ${v[c].join(' ‖ ')}`);
  }
  return out.join('\n');
}
module.exports = { table, details };
if (require.main === module) {
  const files = process.argv.slice(2).filter((x) => !x.startsWith('--'));
  const a = JSON.parse(fs.readFileSync(files[0], 'utf8')), b = files[1] ? JSON.parse(fs.readFileSync(files[1], 'utf8')) : null;
  console.log(table(a, b));
  if (process.argv.includes('--details')) console.log('\n' + details(b || a));
}
