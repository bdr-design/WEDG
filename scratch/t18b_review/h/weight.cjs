// T18B reviewer: weight in two page loads. (1) normal clock, a fixed new game: ms to the engine's first snapshot,
// draws and triangles a frame (main and shadow pass) with the phone closed and small and big on home; the snapshot's
// size and its `falcons` part; (2) the fast clock (timeScale 20000, a game day in about 0.6 s): each screen held SECS
// seconds, the screen's rebuilds (childList on .scr) against the snapshots and days that came. SCREENS: the
// screens to hold (each a path of data-go from home, '>' between; default: every app of the base).
//   PORT=<port> OUT=<json> [SECS=5] [SCREENS=...] NODE_PATH=$(npm root -g) node weight.cjs
const { chromium } = require('playwright');
const fs = require('fs');
const PORT = process.env.PORT || 8971, SECS = +(process.env.SECS || 5);
const SCREENS = (process.env.SCREENS || 'home,water,feed,milk,build,haraj,bank,mazayen,chats,cal').split(',');
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
  // the worker's messages counted by kind (the catalog asked: how often, how big)
  const W = window.Worker;
  window.__ops = {};
  window.Worker = class extends W { constructor(...a) { super(...a); const pm = this.postMessage.bind(this); this.postMessage = (m, ...r) => { try { const op = JSON.parse(m).op; window.__ops[op] = (window.__ops[op] || 0) + 1; } catch { /* */ } return pm(m, ...r); }; } };
};
async function open(b, scale) {
  const p = await b.newPage({ viewport: { width: 956, height: 440 } });
  const errs = []; p.on('pageerror', (e) => errs.push(e.message)); p.__errs = errs;
  await p.addInitScript(COUNTER);
  await p.route('**/index.html', async (r) => { const res = await r.fetch(); await r.fulfill({ response: res, body: (await res.text()).replace('startEngine({ onSnapshot:', `startEngine({ ${scale ? `timeScale: ${scale}, ` : ''}newGame: { seed: 4242 }, onSnapshot:`) }); });
  const t = Date.now();
  await p.goto(`http://127.0.0.1:${PORT}/index.html`, { timeout: 600000 });
  await p.waitForFunction(() => window.marahEngine && window.marahEngine.snapshot, null, { timeout: 600000, polling: 50 });
  const snapMs = Date.now() - t;
  await p.waitForFunction(() => document.getElementById('status').hidden, null, { timeout: 600000, polling: 100 });
  const readyMs = Date.now() - t;
  await p.evaluate(() => { window.R = () => [...document.querySelectorAll('*')].find((x) => x.shadowRoot && x.shadowRoot.querySelector('.phone')).shadowRoot; });
  return { p, snapMs, readyMs };
}
const frames = async (p, n = 30) => { await p.evaluate(() => { window.__frames.length = 0; }); await p.waitForTimeout(2500); return p.evaluate((n) => { const f = window.__frames.slice(-n); const med = (i) => f.map((x) => x[i]).sort((a, b) => a - b)[Math.floor(f.length / 2)]; return { frames: f.length, draws: med(0), tris: med(1), shadowDraws: med(2), shadowTris: med(3) }; }, n); };
const go = (p, path) => p.evaluate(async (path) => {
  for (let i = 0; i < 8; i++) { const b = R().querySelector('.back'); if (!b) break; b.click(); await new Promise((r) => setTimeout(r, 450)); }
  for (const g of path.split('>').filter((x) => x !== 'home')) { const e = R().querySelector(`[data-go="${g}"]`); if (!e) return 'no ' + g; e.click(); await new Promise((r) => setTimeout(r, 500)); }
  return (R().querySelector('.title') || {}).textContent || 'home';
}, path);
(async () => {
  const b = await chromium.launch(LAUNCH);
  const out = {};
  { const { p, snapMs, readyMs } = await open(b, 0);
    out.start = { snapMs, readyMs };
    await p.waitForTimeout(1500);
    out.drawsClosed = await frames(p);
    await p.evaluate(() => window.__phone.toggle()); await p.waitForTimeout(600);
    out.drawsSmall = await frames(p);
    await p.evaluate(() => window.__phone.enlarge()); await p.waitForTimeout(600);
    out.drawsBig = await frames(p);
    out.snapshot = await p.evaluate(() => { const s = window.marahEngine.snapshot, st = window.marahEngine.stats; return { chars: st.snapshotChars, falconsChars: s.falcons ? JSON.stringify(s.falcons).length : null, keys: Object.keys(s).length, today: s.date }; });
    out.ops1 = await p.evaluate(() => window.__ops);
    out.errs1 = p.__errs; await p.close(); }
  { const { p } = await open(b, 20000);
    await p.evaluate(() => {
      window.__n = { rebuild: 0 };
      new MutationObserver((ms) => { for (const m of ms) if (m.type === 'childList' && m.target.classList.contains('scr')) { window.__n.rebuild++; break; } }).observe(R().querySelector('.scr'), { childList: true });
      window.__phone.toggle(); window.__phone.enlarge();
    });
    out.rate = {};
    for (const s of SCREENS) {
      const title = await go(p, s);
      await p.waitForTimeout(800);
      const a = await p.evaluate(() => ({ r: window.__n.rebuild, d: window.marahEngine.snapshot.today, n: window.marahEngine.stats.snapshots }));
      await p.waitForTimeout(SECS * 1000);
      const z = await p.evaluate(() => ({ r: window.__n.rebuild, d: window.marahEngine.snapshot.today, n: window.marahEngine.stats.snapshots }));
      out.rate[s] = { title, days: z.d - a.d, snapshots: z.n - a.n, rebuilds: z.r - a.r };
      console.log(s, JSON.stringify(out.rate[s]));
    }
    out.ops3 = await p.evaluate(() => window.__ops);
    out.errs3 = p.__errs; await p.close(); }
  console.log(JSON.stringify(out, null, 1));
  if (process.env.OUT) fs.writeFileSync(process.env.OUT, JSON.stringify(out, null, 1));
  await b.close();
})();
