// The hunting outing (الطلعة) as storyboard frames: a DESIGN for the owner's approval (13 Nov 2026), nothing built.
// Each frame is a real screenshot of the game page (design/prototype3d, the yard in Qassim on its real terrain, the
// black LC300, the play HUD exactly as play.js draws it), with the NEW things drawn on top inside the page, in the
// page's own pieces where they exist:
//   - pins and cards: the page's own pin (.lbl) and place card (renderCard: the Sadu card), fed a place this script
//     makes up (the hunting ground, the licensed estate, the falcon after its flight, the warning); the card is shown
//     in play, where today it is hidden (body.playing #pop);
//   - the falcon's icon buttons: the play HUD's own button (.pl-ib), one more in the car's row and one at the right
//     edge on foot, as the car's buttons are (GDD 9.1);
//   - the falcon, the hooded falcon on the glove, and the stone-curlew: plain flat STAND-INS drawn here in SVG, until
//     the birds of task T11 exist (design/birds/); the player is first person on foot (no body: the owner, 11 Nov), so
//     the glove is seen from the eyes;
//   - frame 9: the phone, small, as play opens it, showing the permit app's violation screen (phone_falcon.cjs view 12).
// What each frame shows, what is real and what is drawn: design/ui/README.md and design/hunt/outing_board.jpg (the frames
// with their captions under them, outside the game's picture).
// Figures on the frames (each a game choice unless a source is named):
//   14 km to the hunting ground, 22 km to the estate: game choices (the estate's real places are not in the research;
//     the open ground is the real Nafud edge west of the yard, design/prototype3d/README.md, but its exact place and
//     that no village or farm is near it must be checked at build against a map);
//   5,000 riyals, hunting in a banned place or time: real [136] (search summaries, the 2021 table);
//   the farms and their surroundings banned: real [127][134][135]; by day only: real [135], one source;
//   الكروان in open land with a falcon: real [140] (an earlier list; this season's list not read); الحبارى only in the
//     licensed estates: real [142] (open land not confirmed, so the game keeps it to the estate: game choice);
//   the flight's 40 seconds and 350 m on the result card: game choices (no source read for a stone-curlew flight).
// Draws and triangles: every frame's base (the real page, before anything is drawn) is counted from the WebGL calls
// (main pass and shadow pass apart, as $SC/review_de2/draws.js does) and written to outing_draws.txt; the new
// models' cost comes from task T11's measured models (/home/user/wt/t11, design/birds/): the hooded saker close 6,752
// triangles with hood and jesses in 3 draws, alert 6,188, in flight 6,364; the stone-curlew 5,084 / 5,420; the houbara
// 4,996 / 6,052; the far models under 1,500 each; the perch 1,424; the cuff 864 (each draw casts a shadow too: the
// saker's 1 m span is over the 30 cm rule). Frames 5 and 8 show T11's own render of the hooded saker, cut out by
// cut_bird.py (t11_saker_hooded.png), on a drawn glove; the other birds are flat stand-ins. The driver's seat is
// counted without a picture (the hooded falcon on its perch in the cabin would be seen from there).
// Two things drawn here are the OWNER'S to decide, asked in the design note: the place card shown in play (the
// approved HUD hides it there) and whether the player may cast in a banned place anyway (the warning card offers only
// «طيب»).
// To draw again: build the prototype (THREE_DIR=<three@0.170.0 package> python3 tool/proto_app/assemble.py), serve
// tool/proto_app/assets/web on a port (PORT, 8765 by default), and run `NODE_PATH=$(npm root -g) node
// design/hunt/outing.cjs` from the repository's root; it writes outing_<n>_<name>.jpg and outing_board.jpg in
// design/hunt/ (or OUT=<folder>). It takes about fifteen minutes on SwiftShader.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const PORT = process.env.PORT || 8765;
const OUT = process.env.OUT || __dirname;
const DSF = +(process.env.DSF || 1);      // (the owner's screen at 1x: at 2x SwiftShader draws too slowly for the car to move or the door's animation to end)

// the page's hooks this script needs, added to the served copy only (nothing in the page changes)
const HOOK = `window.__phone = phone;
window.__open = openPlace; window.__close = closePop; window.__camera = camera; window.__controls = controls; window.__ICONS = ICONS;
window.__addPlace = (pl) => { PLACES.push(pl); const el = document.createElement('button'); el.type = 'button'; labelLayer.appendChild(el); pl.el = el; labels.push(pl); order.push(pl); refreshLabels(); return pl; };`;
// the WebGL calls a frame, main pass and shadow map apart (from $SC/review_de2/draws.js)
const COUNTER = () => {
  const s = { draws: 0, tris: 0, sd: 0, st: 0 }; let fb = null;
  const P = WebGL2RenderingContext.prototype;
  const ob = P.bindFramebuffer; P.bindFramebuffer = function (t, f) { if (t === 0x8D40 || t === 0x8CA9) fb = f; return ob.call(this, t, f); };
  const tri = (mode, count, inst = 1) => (mode === 4 ? count / 3 : mode === 5 || mode === 6 ? Math.max(0, count - 2) : 0) * inst;
  const wrap = (name, f) => { const o = P[name]; P[name] = function (...a) { const t = f(a); if (fb) { s.sd++; s.st += t; } else { s.draws++; s.tris += t; } return o.apply(this, a); }; };
  wrap('drawElements', (a) => tri(a[0], a[1])); wrap('drawArrays', (a) => tri(a[0], a[2]));
  wrap('drawElementsInstanced', (a) => tri(a[0], a[1], a[4])); wrap('drawArraysInstanced', (a) => tri(a[0], a[2], a[3]));
  window.__frames = [];
  const loop = () => { window.__frames.push([s.draws, Math.round(s.tris), s.sd, Math.round(s.st)]); if (window.__frames.length > 60) window.__frames.shift(); s.draws = s.tris = s.sd = s.st = 0; requestAnimationFrame(loop); };
  requestAnimationFrame(loop);
};

// ---- the stand-ins (flat SVG, marked as stand-ins in the captions): a hooded saker on the glove seen from the eyes,
// the saker in flight from behind, the saker down on a stone-curlew, a stone-curlew flushing
const SV = {
  fist: `<svg viewBox="0 0 300 300" width="300" height="300">
    <path d="M60 300 C70 250 95 222 140 214 L205 210 C240 212 262 236 268 300 Z" fill="#b48a5a"/>
    <path d="M60 300 C70 250 95 222 140 214 L205 210 C240 212 262 236 268 300" fill="none" stroke="#7a5532" stroke-width="5"/>
    <path d="M120 236 h110 M118 258 h120" stroke="#8e6a42" stroke-width="4"/>
    <path d="M150 214 C140 170 142 120 160 92 C176 70 214 70 228 96 C246 126 244 176 232 214 Z" fill="#9a7b5c"/>
    <path d="M160 120 C176 136 200 140 226 124 M156 150 C178 166 204 168 236 152 M158 180 C180 194 206 194 234 182" stroke="#6e5238" stroke-width="5" fill="none"/>
    <path d="M168 104 C164 70 176 44 196 40 C220 38 232 62 228 100 Z" fill="#5b3a22"/>
    <path d="M190 40 C192 26 198 20 206 18 C204 28 202 34 200 40 Z" fill="#c44a2c"/>
    <path d="M170 92 C186 98 210 98 228 90" stroke="#d9b36a" stroke-width="4" fill="none"/>
    <path d="M196 214 C196 236 192 252 186 264 M216 214 C218 236 222 250 228 262" stroke="#e8dcc4" stroke-width="5" fill="none"/>
    <path d="M200 214 l-4 10 M222 214 l4 10" stroke="#e9c84a" stroke-width="7"/>
  </svg>`,
  fly: `<svg viewBox="0 0 120 50" width="120" height="50"><path d="M2 20 C24 14 44 16 56 26 L60 22 L64 26 C76 16 96 14 118 20 C96 24 80 30 68 34 L64 44 L56 44 L52 34 C40 30 24 24 2 20 Z" fill="#4a3826"/><path d="M57 30 h6" stroke="#d8c3a0" stroke-width="2"/></svg>`,
  curlewUp: `<svg viewBox="0 0 70 40" width="70" height="40"><path d="M4 10 C16 6 28 10 34 18 C40 10 52 6 66 10 C54 14 44 20 40 24 L44 30 L34 28 L26 30 L30 24 C24 20 14 14 4 10 Z" fill="#a08460"/><path d="M8 11 C18 10 26 13 32 18 M62 11 C52 10 44 13 38 18" stroke="#3b2c1e" stroke-width="2" fill="none"/><path d="M44 30 l6 2" stroke="#3b2c1e" stroke-width="2"/></svg>`,
  down: `<svg viewBox="0 0 120 70" width="120" height="70"><ellipse cx="62" cy="60" rx="50" ry="7" fill="rgba(60,40,20,.35)"/>
    <path d="M30 56 C40 46 60 44 80 50 C86 52 92 56 94 58 Z" fill="#a08460"/><path d="M84 52 l14 -6 M88 56 l12 0" stroke="#3b2c1e" stroke-width="2"/>
    <path d="M10 40 C24 30 40 26 52 30 L58 22 C62 14 72 12 76 20 C80 28 78 36 70 42 C86 38 100 40 112 46 C96 48 80 50 64 52 L46 52 C34 50 20 46 10 40 Z" fill="#4a3826"/>
    <circle cx="70" cy="20" r="2" fill="#111"/><path d="M76 20 l5 2 l-5 2" fill="#e9c84a"/></svg>`,
};
SV.glove = `<svg viewBox="0 0 300 300" width="300" height="300" style="position:absolute;left:0;top:30px">
    <path d="M60 300 C70 250 95 222 140 214 L205 210 C240 212 262 236 268 300 Z" fill="#6b6a3e"/>
    <path d="M60 300 C70 250 95 222 140 214 L205 210 C240 212 262 236 268 300" fill="none" stroke="#4a4a2a" stroke-width="5"/>
    <path d="M120 236 h110 M118 258 h120" stroke="#55552f" stroke-width="4"/></svg>`;
const FALCON_ICON = '<svg viewBox="0 0 24 24"><path d="M2.5 10c3 0 5.5 1 7.5 3l2-3 2 3c2-2 4.5-3 7.5-3-2.8 1.8-4.8 3.6-6.6 4.6L14 19h-4l-.9-4.4C7.3 13.6 5.3 11.8 2.5 10z"/></svg>';
const CAST_ICON = '<svg viewBox="0 0 24 24"><path d="M4 18c3-1 5-3 6-6"/><path d="M8 8c3 0 5.5 1 7.5 3l1.7-2.5 1.7 2.5c1-1 2-1.5 3.1-1.7"/><path d="M13 5l3-2.5M17 6l3.5-1"/></svg>';
const LURE_ICON = '<svg viewBox="0 0 24 24"><path d="M4 4c5 2 8 6 9 10"/><circle cx="15" cy="17" r="3.2"/><path d="M13 15.5l-2-1.5M17 15.5l2-1.5"/></svg>';
const PIN_ICONS = {
  falcon: '<path d="M2.5 10c3 0 5.5 1 7.5 3l2-3 2 3c2-2 4.5-3 7.5-3-2.8 1.8-4.8 3.6-6.6 4.6L14 19h-4l-.9-4.4C7.3 13.6 5.3 11.8 2.5 10z"/>',
  estate: '<path d="M5 21V4"/><path d="M5 4h12l-2.5 4L17 12H5"/>',      // (a flag: the farm's pens already use a fence)
  ban: '<circle cx="12" cy="12" r="8.5"/><path d="M6 6l12 12"/>',
};

(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const p = await b.newPage({ viewport: { width: 956, height: 440 }, deviceScaleFactor: DSF });
  p.on('pageerror', (e) => console.log('pageerror', e.message));
  await p.addInitScript(COUNTER);
  await p.route('**/index.html', async (r) => {
    const res = await r.fetch();
    const t = (await res.text()).replace('startEngine({ onSnapshot:', 'startEngine({ newGame: { seed: 4242 }, onSnapshot:').replace('window.__phone = phone;', HOOK);
    await r.fulfill({ response: res, body: t });
  });
  await p.goto(`http://127.0.0.1:${PORT}/index.html`);
  await p.waitForFunction(() => window.__play && window.marahEngine && window.marahEngine.snapshot, null, { timeout: 600000 });
  await p.waitForTimeout(4000);
  // the drawn layer over the canvas (under the HUD), and the card shown in play
  await p.evaluate(([PIN_ICONS]) => {
    Object.assign(window.__ICONS, PIN_ICONS);
    const st = document.createElement('style');
    st.textContent = `body.playing #pop:not([hidden]) { display: flex !important; } body.playing .pop { top: calc(var(--edge-t) + 4px); }
      #drawn { position: fixed; inset: 0; pointer-events: none; z-index: 15; } #drawn > * { position: absolute; }
      #drawn .lbl { display: inline-flex; } .pl-ib.warn .dot { background: #f2b54c; }`;
    document.head.appendChild(st);
    const d = document.createElement('div'); d.id = 'drawn'; document.body.appendChild(d);
  }, [PIN_ICONS]);
  const draw = (html) => p.evaluate((h) => { document.getElementById('drawn').innerHTML = h; }, html);
  const at = (x, y, html) => `<div style="left:${x}px;top:${y}px">${html}</div>`;
  const pin = (x, y, icon) => `<div class="lbl on" style="left:${x}px;top:${y}px;transform:translate(-50%,-100%)"><svg class="i ic" viewBox="0 0 24 24">${PIN_ICONS[icon]}</svg></div>`;
  // a few steps out from the driver's door (by it, the get-in and lock buttons show at the same edge)
  const stepAway = async () => { await p.evaluate(() => { const m = window.__play.debug.man; m.pos.x += 5 * Math.sin(m.heading); m.pos.z += 5 * Math.cos(m.heading); }); await p.waitForTimeout(2500); };
  const counts = [];
  const count = async (name, note) => {
    await p.waitForTimeout(1200);
    const f = await p.evaluate(() => window.__frames.slice(-6, -1));
    const best = f.reduce((m, x) => (x[0] + x[2] > m[0] + m[2] ? x : m), [0, 0, 0, 0]);
    counts.push(`${name}: main ${best[0]} draws / ${best[1]} triangles, shadow ${best[2]} / ${best[3]}, total ${best[0] + best[2]} / ${best[1] + best[3]}  (${note})`);
    console.log(counts[counts.length - 1]);
  };
  // the hooded saker on the glove: task T11's render (cut out by cut_bird.py: design/hunt/t11_saker_hooded.png) over a
  // flat glove drawn here; still drawn in, not the game's model
  const BIRD = 'data:image/png;base64,' + fs.readFileSync(path.join(__dirname, 't11_saker_hooded.png')).toString('base64');
  const FIST = `<div style="left:250px;top:110px;width:300px;height:330px"><img src="${BIRD}" style="position:absolute;left:78px;top:32px;width:150px">${SV.glove}</div>`;
  const files = [];
  const shot = async (name, note) => {
    await p.waitForTimeout(1200);
    const f = await p.evaluate(() => window.__frames.slice(-6, -1));
    const best = f.reduce((m, x) => (x[0] + x[2] > m[0] + m[2] ? x : m), [0, 0, 0, 0]);
    counts.push(`${name}: main ${best[0]} draws / ${best[1]} triangles, shadow ${best[2]} / ${best[3]}, total ${best[0] + best[2]} / ${best[1] + best[3]}  (${note})`);
    await p.evaluate(() => { window.__q = []; window.__raf = window.requestAnimationFrame; window.requestAnimationFrame = (fn) => { window.__q.push(fn); return 1; }; });
    await p.waitForTimeout(300);
    const png = path.join(OUT, `${name}.png`);
    await p.screenshot({ path: png, timeout: 600000 });
    await p.evaluate(() => { window.requestAnimationFrame = window.__raf; const q = window.__q; window.__q = []; for (const fn of q) window.requestAnimationFrame(fn); });
    files.push(png); console.log('shot', name, counts[counts.length - 1]);
  };
  
  // ---------------------------------------------------------------- 1, 2 the map: the two new places, far pins
  await p.evaluate(() => { const c = window.__controls, cam = window.__camera; c.target.set(-300, 0, 40); cam.position.set(140, 70, 10); c.update(); });
  await p.evaluate(() => {
    const THREEV = window.__camera.position.constructor;
    const ground = window.__addPlace({ key: 'hunt', name: 'طرف النفود', icon: 'falcon', p: new THREEV(-14000, 80, 1500), min: 900, cls: 'far', edge: true, text: () => 'طرف النفود',
      open() { return { sub: 'مقناص · غرب العزبة', stats: [['المسافة', '14', 'كم'], ['الطريدة', 'الكروان'], ['الموسم', 'مفتوح', '', 'good']],
        html: '<div class="note">بر مفتوح بعيد عن المزارع والقرى. والصيد بالنهار بس.</div>', actions: [{ label: 'روح بالجيب', primary: true, run() {} }] }; } });
    window.__addPlace({ key: 'estate', name: 'المحازة', icon: 'estate', p: new THREEV(-16000, 80, -5000), min: 900, cls: 'far', edge: true, text: () => 'المحازة',
      open() { return { sub: 'محازة صيد مرخصة · غرب العزبة', stats: [['المسافة', '22', 'كم'], ['الطريدة', 'الحبارى'], ['الدخول', 'بحجز']], actions: [{ label: 'روح بالجيب', primary: true, run() {} }] }; } });
    window.__ground = ground;
  });
  await p.waitForTimeout(2500);
  await shot('outing_1_map', 'the map looking west from over the yard; the two far pins drawn');
  await p.evaluate(() => window.__open(window.__ground, true));
  await shot('outing_2_card', 'the hunting ground\'s card opened (the page\'s card, drawn content)');
  await p.evaluate(() => window.__close());

  // ---------------------------------------------------------------- 3, 4 driving out, parked in the open
  await p.evaluate(() => window.__play.start());
  await p.waitForFunction(() => window.__play.model && window.__play.model.interior, null, { timeout: 300000 });
  await p.evaluate(() => window.__play.debug.enter());
  await p.waitForTimeout(2000);
  await p.evaluate(() => { const d = window.__play.debug; d.carState.pos.set(-3000, d.carState.pos.y, 600); d.carState.yaw = -1.9; d.toggleView(); d.snap(); });
  await p.waitForTimeout(6000);
  await p.keyboard.down('KeyW');
  await p.waitForFunction(() => Math.abs(window.__play.debug.carState.v) > 6, null, { timeout: 120000 }).catch(() => console.log('slow to speed'));
  console.log('speed m/s', await p.evaluate(() => window.__play.debug.carState.v));
  await shot('outing_3_drive', 'driving out, from behind; only the gear shows while moving (real HUD); nothing drawn');
  await p.keyboard.up('KeyW');
  await p.keyboard.down('KeyS');
  await p.waitForFunction(() => Math.abs(window.__play.debug.carState.v) < 0.3, null, { timeout: 120000 }).catch(() => {});
  await p.keyboard.up('KeyS');
  await p.waitForTimeout(2500);
  // the falcon's button joins the car's row while it stands outside (the car's own buttons, GDD 9.1)
  await p.evaluate((ic) => { const row = document.querySelector('.pl-car'); const bt = document.createElement('button'); bt.className = 'pl-ib'; bt.id = 'falconBtn'; bt.setAttribute('aria-label', 'الصقر'); bt.innerHTML = ic; row.insertBefore(bt, row.querySelector('[data-c="more"]')); }, FALCON_ICON);
  await shot('outing_4_parked', 'parked in the open, from behind; the falcon\'s button drawn in the car\'s row');
  // the driver's seat, counted only (no picture): the hooded falcon on its perch in the cabin would be seen from here
  await p.evaluate(() => window.__play.debug.toggleView());
  await p.waitForTimeout(4000);
  await count('seat (count only)', 'parked, from the driver\'s seat: the cabin drawn');
  await p.evaluate(() => window.__play.debug.toggleView());
  await p.waitForTimeout(2000);

  // ---------------------------------------------------------------- 5, 6, 7 on foot: the falcon on the glove, the cast, the result
  await p.evaluate(() => { document.getElementById('falconBtn')?.remove(); window.__play.debug.exit(); });
  await p.waitForFunction(() => window.__play.debug.state.mode === 'walk', null, { timeout: 120000 });
  await p.waitForTimeout(1500);
  await stepAway();
  const castBtn = (ic, label) => `<div class="play" style="position:fixed;inset:0;z-index:21;pointer-events:none"><div class="pl-door"><button class="pl-ib big" aria-label="${label}">${ic}</button></div></div>`;
  await draw(FIST + castBtn(CAST_ICON, 'شيل البرقع وأرسله'));
  await shot('outing_5_fist', 'on foot by the car, first person; the hooded falcon on the glove (stand-in) and the cast-off button drawn');
  await draw(at(470, 168, SV.fly) + at(380, 200, SV.curlewUp.replace('width="70" height="40"', 'width="44" height="25"')) + castBtn(LURE_ICON, 'ارجعه بالملواح'));
  await shot('outing_6_flight', 'the falcon cast off (stand-in) and a stone-curlew flushing (stand-in); the lure button to call it back drawn');
  await draw(at(380, 224, SV.down) + pin(440, 222, 'falcon'));
  await p.evaluate(() => window.__open({ el: document.createElement('button'), key: 'result', name: 'غيث', icon: 'falcon', p: window.__camera.position.clone(), max: 1e9, text: () => 'غيث',
    open() { return { sub: 'حر · فرخ · صاد كروان', stats: [['الطيران', '40', 'ثانية'], ['المسافة', '350', 'م'], ['الطلعة', 'صاد', '', 'good']],
      html: '<div class="note">نزل على الكروان عند الطعس. أكّله من صيده وارجعه للدس.</div>', actions: [{ label: 'ارجعه للدس', primary: true, run() {} }] }; } }, true));
  await shot('outing_7_result', 'the falcon down on its quarry (stand-in) with its pin, and the result card the pin opened (drawn content)');
  await p.evaluate(() => window.__close());
  await draw('');

  // ---------------------------------------------------------------- 8 by the farm: the warning before
  await p.evaluate(() => { const d = window.__play.debug; d.enter(); });
  await p.waitForTimeout(2500);
  await p.evaluate(() => { const d = window.__play.debug; d.carState.pos.set(20, d.carState.pos.y, 78); d.carState.yaw = 0; d.snap(); });
  await p.waitForTimeout(4000);
  await p.evaluate(() => window.__play.debug.exit());
  await p.waitForFunction(() => window.__play.debug.state.mode === 'walk', null, { timeout: 120000 });
  await p.waitForTimeout(1500);
  await stepAway();
  await draw(FIST + `<div class="play" style="position:fixed;inset:0;z-index:21;pointer-events:none"><div class="pl-door"><button class="pl-ib big warn" style="background:rgba(28,20,12,.5);color:#f2b54c" aria-label="هنا ممنوع الصيد">${CAST_ICON}<i class="dot"></i></button></div></div>`);
  await p.evaluate(() => window.__open({ el: document.createElement('button'), key: 'ban', name: 'هنا ممنوع الصيد', icon: 'ban', cls: 'warn', p: window.__camera.position.clone(), max: 1e9, text: () => '',
    open() { return { sub: 'قريب من المزارع والعزب', html: '<div class="note warn">الصيد بالمزارع وحولها ممنوع، وغرامته 5,000 ريال لو انمسكت. ابعد عن العزب والقرى وأرسله.</div>',
      actions: [{ label: 'طيب', primary: true, run() {} }] }; } }, true));      // (whether he may cast anyway is the owner's question)
  await shot('outing_8_banned', 'on foot near the yard: the cast-off button in its warning state and the warning card it opened (drawn)');
  await p.evaluate(() => window.__close());
  await draw('');

  // ---------------------------------------------------------------- 9 the fine after: the phone, small, on the permit app's violation
  await p.evaluate(() => window.__phone.toggle());
  await p.waitForTimeout(800);
  await p.evaluate(() => {
    const R = [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone')).shadowRoot;
    const scr = R.querySelector('.scr'), sb = scr.querySelector('.sbar').outerHTML;
    scr.classList.remove('home');
    const svg = (d) => `<svg class="i" viewBox="0 0 24 24">${d}</svg>`;
    scr.innerHTML = `<span class="pill"></span>${sb}<div class="body"><div class="nav"><button class="back">${svg('<path d="M9 6l6 6-6 6"/>')}رجوع</button></div><div class="title">مخالفة</div>
      <div class="warn"><span class="lead">${svg('<path d="M12 4 2.5 20h19z"/><path d="M12 10v4.5M12 17.5v.01"/>')}</span><b>صيد بمكان ممنوع</b><small>قريب من المزارع، جنوب عزبتك</small></div>
      <div class="tank"><small>الغرامة</small><div class="v">5,000<span>ريال</span></div><div class="ln">انخصمت من رصيدك</div></div>
      <div class="note">وقفتك الدورية وانت ترسل الصقر جنب العزب. تصريحك باقي، بس المرة الجاية بعيد عن المزارع والقرى.</div></div><div class="hb"></div>`;
  });
  await p.waitForTimeout(800);
  await shot('outing_9_fine', 'the fine after: the phone opened small in play (the real phone), on the permit app\'s violation screen (drawn content)');
  // the board: the frames with their captions under them (outside the game's picture), for reading in order
  await p.close();
  await makeStrips(b, files);
  await makeBoard(b, files);
  for (const f of files) fs.unlinkSync(f);
  await b.close();
  fs.writeFileSync(path.join(OUT, 'outing_draws.txt'), counts.join('\n') + '\n');
  console.log(counts.join('\n'));
})();

const CAP = [
  'الخريطة من فوق العزبة للغرب. مرسوم: دبوس «طرف النفود» (المقناص) ودبوس «المحازة» (علم) بعيد على الأفق.',
  'تضغط الدبوس فتنفتح بطاقته جنبه. مرسوم: محتوى البطاقة (بطاقة اللعبة نفسها). «روح بالجيب» يوديك هناك والوقت يمشي (سؤال للمالك).',
  'السواقة بالبر من ورا. كله حقيقي: وهي تمشي يبقى القير بس فوق. الصقر مبرقع على وكره بالسيارة وما يبين من ورا.',
  'السيارة واقفة برا. مرسوم: زر الصقر جنب أزرار السيارة، يطلع بس والسيارة واقفة (الصيد من سيارة تمشي ممنوع بالنظام).',
  'نزلت، من عيونك. مرسوم: الصقر المبرقع (صورة مجسم الصقر من مهمة الطيور، مركّبة) على دس مرسوم، وزر «شيل البرقع وأرسله» على الطرف.',
  'أرسلته. مرسوم: الصقر طاير والكروان قام (بدائل مسطحة)، وزر الملواح يرجعه لو تبي.',
  'نزل على الكروان. مرسوم: الصقر على صيده (بديل) ودبوس عليه، وتضغطه فتطلع بطاقة النتيجة. البطاقة وقت اللعب جديدة: سؤال للمالك.',
  'جنب العزبة. مرسوم: الصقر على الدس، وزر الإرسال بلون التحذير، وبطاقة «هنا ممنوع الصيد» والغرامة 5,000 ريال [136]. هل يقدر يرسل رغم المنع؟ سؤال للمالك.',
  'بعدها لو انمسكت: الجوال الصغير (الحقيقي) على المخالفة بتطبيق «تصريح الصيد». مرسوم: محتوى الشاشة.',
];
// each frame with its strip under it (outside the game's picture): what is real and what is drawn
async function makeStrips(b, files) {
  const pg = await b.newPage({ viewport: { width: 956, height: 470 } });
  for (const [i, f] of files.entries()) {
    await pg.setContent(`<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@500;700&display=swap"><style>
      body { margin: 0; width: 956px; background: #2a2119; direction: rtl; font-family: "IBM Plex Sans Arabic", sans-serif; } img { display: block; width: 956px; height: 440px; }
      p { margin: 0; padding: 7px 12px 9px; color: #f6f1e7; font-size: 13px; line-height: 1.45; } b { background: #e8b46c; color: #1b130a; border-radius: 5px; padding: 0 6px; margin-left: 6px; }</style>
      <img src="data:image/png;base64,${fs.readFileSync(f).toString('base64')}"><p><b>${i + 1} · تصميم</b>${CAP[i] || ''}</p>`, { waitUntil: 'networkidle' });
    await pg.evaluate(() => document.fonts.ready);
    const png = f.replace(/\.png$/, '_s.png');
    await pg.screenshot({ path: png, fullPage: true, timeout: 600000 });
    execFileSync('convert', [png, '-quality', '88', f.replace(/\.png$/, '.jpg')]); fs.unlinkSync(png);
  }
  await pg.close();
}
async function makeBoard(b, files) {
  const board = await b.newPage({ viewport: { width: 1500, height: 900 } });
  const cells = files.map((f, i) => `<figure><img src="data:image/png;base64,${fs.readFileSync(f).toString('base64')}"><figcaption><b>${i + 1}</b> ${CAP[i] || ''}</figcaption></figure>`).join('');
  await board.setContent(`<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@500;700&display=swap"><style>
    body { margin: 0; padding: 14px; background: #2a2119; direction: rtl; font-family: "IBM Plex Sans Arabic", sans-serif; display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; width: 1500px; box-sizing: border-box; }
    figure { margin: 0; } img { width: 100%; display: block; border-radius: 6px; } figcaption { color: #f6f1e7; font-size: 13.5px; line-height: 1.5; padding: 6px 2px 0; }
    figcaption b { display: inline-block; min-width: 22px; text-align: center; background: #e8b46c; color: #1b130a; border-radius: 6px; margin-left: 4px; }</style>${cells}`, { waitUntil: 'networkidle' });
  await board.evaluate(() => document.fonts.ready);
  await board.screenshot({ path: path.join(OUT, 'outing_board.png'), fullPage: true, timeout: 600000 });
  execFileSync('convert', [path.join(OUT, 'outing_board.png'), '-quality', '85', path.join(OUT, 'outing_board.jpg')]); fs.unlinkSync(path.join(OUT, 'outing_board.png'));
  await board.close();
}
