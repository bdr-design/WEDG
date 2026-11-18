// The hunting season's phone shot from real games on the engine, for the owner (task T18 part B, design first): the
// four things built past the approved design (design/ui/phone_falcon.cjs), each in the phone as it is now, so the
// owner sees them before they are adopted:
//   1. the ceiling of a lot (his choice of 18 Nov: ready amounts, then + and −),
//   2. his trapped bird's three ways: no room, a free place, the room full,
//   3. the card before leaving for الحماد (843 km from القصيم),
//   4. every refusal line the engine gives, with where the phone shows it (written to a text file beside the sheet).
// The saves are the engine's own, played by its commands (tool/proto_engine/bin/falcon_design_saves.dart).
//
//   cd tool/proto_engine && dart run bin/falcon_design_saves.dart <saves>
//   python3 tool/proto_app/assemble.py, then serve tool/proto_app/assets/web on PORT
//   PORT=<p> SAVES=<saves> OUT=<dir> node design/ui/phone_falcon_engine.cjs
// Writes OUT/falcon_engine_*.png (2x), OUT/phone_falcon_engine.jpg (the sheet) and OUT/phone_falcon_refusals.txt.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const PORT = process.env.PORT || 8961, SAVES = process.env.SAVES, OUT = process.env.OUT || __dirname;
if (!SAVES) throw new Error('SAVES: the folder falcon_design_saves.dart wrote');
fs.mkdirSync(OUT, { recursive: true });
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };

async function open(b, save) {
  const ctx = await b.newContext({ viewport: { width: 956, height: 440 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  p.on('pageerror', (e) => console.log('PAGE ERROR', e.message));
  const text = fs.readFileSync(path.join(SAVES, save), 'utf8');
  await p.addInitScript(([v]) => { if (!sessionStorage.getItem('fe')) { localStorage.clear(); localStorage.setItem('marah.proto.marah.save', v); sessionStorage.setItem('fe', '1'); } }, [text]);
  await p.goto(`http://127.0.0.1:${PORT}/index.html`, { timeout: 600000 });
  await p.waitForFunction(() => window.marahEngine && window.marahEngine.snapshot && document.getElementById('status').hidden, null, { timeout: 900000 });
  await p.evaluate(() => {
    window.R = () => [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot;
    window.__phone.toggle(); window.__phone.enlarge();
  });
  await p.waitForTimeout(800);
  return { ctx, p };
}
async function tap(p, sel, n = 0) {
  await p.waitForTimeout(500);
  const r = await p.evaluate(([s, n]) => { const e = R().querySelectorAll(s)[n]; if (!e) return null; e.scrollIntoView({ block: 'center' }); const b = e.getBoundingClientRect(); return { x: b.x + b.width / 2, y: b.y + b.height / 2 }; }, [sel, n]);
  if (!r) throw new Error(`no ${sel}[${n}]`);
  await p.mouse.click(r.x, r.y);
  await p.waitForTimeout(450);
}
const home = (p) => p.evaluate(() => window.__phone.show('home'));
const SHOTS = [];
async function shot(p, name, label, where = 'top') {
  await p.waitForTimeout(400);
  await p.evaluate((w) => { const bd = R().querySelector('.body'); if (bd) bd.scrollTop = w === 'end' ? bd.scrollHeight : 0; }, where);
  await p.waitForTimeout(150);
  const box = await p.evaluate(() => { const r = R().querySelector('.dev').getBoundingClientRect(); return { x: r.x, width: r.width }; });
  const file = path.join(OUT, `falcon_engine_${name}.png`);
  await p.screenshot({ path: file, timeout: 600000, clip: { x: Math.max(0, box.x - 4), y: 0, width: box.width + 8, height: 440 } });
  SHOTS.push({ file, label });
}

(async () => {
  const b = await chromium.launch(LAUNCH);
  // 1. the ceiling: 400,000 granted, the room built (buyer.json)
  {
    const { ctx, p } = await open(b, 'buyer.json');
    await tap(p, '[data-go="club"]'); await tap(p, '.open[data-go="lots"]'); await tap(p, '.it.lot[data-go="lot"]');
    await shot(p, 'ceiling', '١ · سقف المزايدة: أرقام جاهزة ثم + و−');
    await tap(p, '[data-act="upSet"]', 2);
    await shot(p, 'ceiling_twice', '١ · بعد ما اخترت «الضعف»');
    await ctx.close();
  }
  // 2. his trapped bird: no room, a free place, the room full
  for (const [save, name, label] of [['held.json', 'bird_noroom', '٢ · طيرك المطروح، وما عندك غرفة'], ['held_room.json', 'bird_room', '٢ · طيرك المطروح، وفي مكان'], ['held_full.json', 'bird_full', '٢ · طيرك المطروح، والغرفة مليانة']]) {
    const { ctx, p } = await open(b, save);
    await tap(p, '[data-go="club"]'); await tap(p, '.row[data-go="bird"]');
    await shot(p, name, label, 'end');
    await ctx.close();
  }
  // 3. the card before leaving for الحماد, nine nights (mine.json: back from the trapping camp, its permit and gear)
  {
    const { ctx, p } = await open(b, 'mine.json');
    await p.evaluate(() => window.__phone.openTrip('trapping', 'hamad', 9, () => {}));
    await p.waitForTimeout(1200);
    await shot(p, 'card_hamad', '٣ · قبل ما تمشي: الحماد، 9 ليالي');
    await shot(p, 'card_hamad_end', '٣ · نفس البطاقة، آخرها', 'end');
    // 4. the refusals: the engine's lines (the catalog), and the phone's own words for money
    const cat = (await p.evaluate(() => window.marahEngine.falconCatalog())).catalog;
    const lines = Object.entries(cat.lines.refusals).map(([k, v]) => `${k}\t${v}`);
    fs.writeFileSync(path.join(OUT, 'phone_falcon_refusals.txt'), lines.join('\n') + '\n');
    await ctx.close();
  }
  await b.close();
  // the sheet: the shots in a row of four, each with its label
  const b2 = await chromium.launch(LAUNCH);
  const pg = await (await b2.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 })).newPage();
  const cells = SHOTS.map((s) => `<figure><img src="data:image/png;base64,${fs.readFileSync(s.file).toString('base64')}"><figcaption>${s.label}</figcaption></figure>`).join('');
  await pg.setContent(`<html dir="rtl"><body style="margin:0;background:#f3efe8;font:600 15px system-ui"><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;padding:16px">${cells}</div><style>figure{margin:0;text-align:center}img{width:100%;border-radius:12px}figcaption{margin-top:6px}</style></body></html>`);
  await pg.waitForTimeout(500);
  await pg.screenshot({ path: path.join(OUT, 'phone_falcon_engine.jpg'), fullPage: true, type: 'jpeg', quality: 86 });
  await b2.close();
  console.log('wrote', SHOTS.length, 'shots and the sheet to', OUT);
})();
