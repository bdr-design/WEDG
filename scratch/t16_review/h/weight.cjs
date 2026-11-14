// T16 reviewer: weight baselines in one page load each. (1) start: ms to the engine's first snapshot and to the first
// frame; (2) draws and triangles a frame (main pass and shadow) with the phone closed, and open on الحراج's listing;
// (3) the fast clock (timeScale 20000, SAVE seeded): for الحراج's list, a listing, the pick list and a sell page,
// held SECS seconds each: snapshots, rebuilds, days. Env: PORT, SAVE, SECS (6), OUT (json).
const { chromium } = require('playwright');
const fs = require('fs');
const PORT = process.env.PORT || 8961, SECS = +(process.env.SECS || 6), SAVE = process.env.SAVE;
const LAUNCH = { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] };
const COUNTER = () => {
  const s = { draws: 0, tris: 0, sd: 0, st: 0 }; let fb = null;
  const P = WebGL2RenderingContext.prototype;
  const ob = P.bindFramebuffer; P.bindFramebuffer = function (t, f) { if (t === 0x8D40 || t === 0x8CA9) fb = f; return ob.call(this, t, f); };
  const tri = (mode, count, inst = 1) => (mode === 4 ? count / 3 : mode === 5 || mode === 6 ? Math.max(0, count - 2) : 0) * inst;
  const wrap = (name, f) => { const o = P[name]; P[name] = function (...a) { const t = f(a); if (fb) { s.sd++; s.st += t; } else { s.draws++; s.tris += t; } return o.apply(this, a); }; };
  wrap('drawElements', (a) => tri(a[0], a[1])); wrap('drawArrays', (a) => tri(a[0], a[2]));
  wrap('drawElementsInstanced', (a) => tri(a[0], a[1], a[4])); wrap('drawArraysInstanced', (a) => tri(a[0], a[2], a[3]));
  window.__frames = [];
  const loop = () => { window.__frames.push([s.draws, Math.round(s.tris), s.sd, Math.round(s.st)]); s.draws = s.tris = s.sd = s.st = 0; requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
  window.__t0 = performance.now();
};
async function open(b, scale) {
  const p = await b.newPage({ viewport: { width: 956, height: 440 } });
  const errs = []; p.on('pageerror', (e) => errs.push(e.message)); p.__errs = errs;
  await p.addInitScript(COUNTER);
  if (SAVE) await p.addInitScript((s) => { if (!sessionStorage.getItem('seeded')) { localStorage.clear(); localStorage.setItem('marah.proto.marah.save', s); sessionStorage.setItem('seeded', '1'); } }, fs.readFileSync(SAVE, 'utf8'));
  await p.route('**/index.html', async (r) => { const res = await r.fetch(); await r.fulfill({ response: res, body: (await res.text()).replace('startEngine({ onSnapshot:', `startEngine({ ${scale ? `timeScale: ${scale}, ` : ''}newGame: { seed: 4242 }, onSnapshot:`) }); });
  const t = Date.now();
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.marahEngine && window.marahEngine.snapshot, null, { timeout: 600000, polling: 50 });
  const snapMs = Date.now() - t;
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot; });
  return { p, snapMs };
}
const frames = async (p, n = 30) => { await p.evaluate(() => { window.__frames.length = 0; }); await p.waitForTimeout(2500); return p.evaluate((n) => { const f = window.__frames.slice(-n); const med = (i) => f.map((x) => x[i]).sort((a, b) => a - b)[Math.floor(f.length / 2)]; return { frames: f.length, draws: med(0), tris: med(1), shadowDraws: med(2), shadowTris: med(3) }; }, n); };
(async () => {
  const b = await chromium.launch(LAUNCH);
  const out = {};
  // 1, 2: the normal clock
  { const { p, snapMs } = await open(b, 0);
    out.start = { snapMs };
    await p.waitForTimeout(1500);
    out.drawsClosed = await frames(p);
    await p.evaluate(() => { window.__phone.openApp('haraj'); });
    await p.waitForTimeout(600);
    await p.evaluate(() => R().querySelector('[data-go="listing"]')?.click());
    await p.waitForTimeout(600);
    out.drawsListing = await frames(p);
    out.errs1 = p.__errs; await p.close(); }
  // 3: the fast clock
  { const { p } = await open(b, 20000);
    await p.evaluate(() => {
      window.__n = { rebuild: 0 };
      new MutationObserver((ms) => { for (const m of ms) if (m.type === 'childList' && m.target.classList.contains('scr')) { window.__n.rebuild++; break; } }).observe(R().querySelector('.scr'), { childList: true });
    });
    const steps = [['haraj', () => window.__phone.openApp('haraj')],
      ['listing', () => { window.__phone.openApp('haraj'); setTimeout(() => R().querySelector('[data-go="listing"]')?.click(), 450); }],
      ['pick', () => { window.__phone.openApp('haraj'); setTimeout(() => R().querySelector('[data-go="pick"]')?.click(), 450); }],
      ['sell', () => { window.__phone.openApp('haraj'); setTimeout(() => { R().querySelector('[data-go="pick"]')?.click(); setTimeout(() => R().querySelector('[data-go="sell"]')?.click(), 450); }, 450); }]];
    out.rate = {};
    for (const [k, f] of steps) {
      await p.evaluate(`(${f.toString()})()`);
      await p.waitForTimeout(1500);
      const a = await p.evaluate(() => ({ r: window.__n.rebuild, d: window.marahEngine.snapshot.today, rev: window.marahEngine.snapshot.revision, title: (R().querySelector('.title') || {}).textContent }));
      await p.waitForTimeout(SECS * 1000);
      const z = await p.evaluate(() => ({ r: window.__n.rebuild, d: window.marahEngine.snapshot.today, rev: window.marahEngine.snapshot.revision }));
      out.rate[k] = { title: a.title, days: z.d - a.d, snapshots: z.rev - a.rev, rebuilds: z.r - a.r };
    }
    out.errs3 = p.__errs; await p.close(); }
  console.log(JSON.stringify(out, null, 1));
  if (process.env.OUT) fs.writeFileSync(process.env.OUT, JSON.stringify(out, null, 1));
  await b.close();
})();
