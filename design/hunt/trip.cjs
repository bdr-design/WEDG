// Away for days (round 2, 14 Nov 2026): the falcon trip (المقناص) and the trapping camp (الطرح) as ONE way of being
// away, the falcons' room at the farm, as storyboard frames: a DESIGN for the owner's approval, nothing built.
// Drawn for his answers (docs/agents/hunting_owner_decisions.md): he drives and casts himself (1); a card opens in play
// only by his tap, on the right (3); in a banned place or time the button warns and does not act (4); a falcons' room
// with its pin and card (5); a falcon lost rarely, found with the tracker (6); the farm runs as on any day while he is
// away (7), and, his word of 14 Nov, «خل الطلعة ايام مافي مشكلة»: the falcon outing is days too. Trapping is his
// «تجارة ثانية» («اصيده صيد…»), a camp for days on his gear («مخيم وايام والطرح يعتمد على تجهيزاتك وحمامك…»). The
// proxy's provisional answers (docs/agents/proxy_decisions.md batch 3) are drawn and marked in the captions.
// Each frame is a real screenshot of the game page (design/prototype3d: the yard in Qassim on its real terrain, the
// black LC300, the play HUD exactly as play.js draws it) with the NEW things drawn on top inside the page:
//   - pins and cards: the page's own pin (.lbl) and place card (the Sadu card), fed places made up here; in play the
//     card opens only on a tap of a pin or a warning button (decision 3), docked on the right;
//   - icon buttons: the play HUD's own .pl-ib: the falcon's or the net's in the car's row while it stands, and one at
//     the right edge on foot; a warning state that does not act (decision 4);
//   - birds: task T11's renders (awaiting the owner's approval) cut out by cut_bird.py: the hooded saker on a drawn
//     glove and on its perch, the saker in flight and standing, the stone-curlew in flight; the PEREGRINE is not built:
//     flat STAND-INS (marked); the lure pigeon, the caught stone-curlew and the camp's things (the mobile tent, the
//     pigeon cage, the nets, the supplies) and the falcons' room are flat STAND-INS too;
//   - the small phone in play, with screens drawn in it.
// Each frame has a strip under it (outside the game's picture) saying what is real and what is drawn; trip_board.jpg
// holds them all. FIGURES on the frames (real by source number, or game choices):
//   the falconry ground 14 km west (the real Nafud edge; its exact place a game choice), the estate (game choice);
//   الحماد about 600 km north (straight line, from the yard's 25.81 N 42.90 E to Arar's 30.98 N 41.04 E; a real
//     trapping ground [198][202]); the trapping season to 30 Nov [184][185][186];
//   the farm's feed 9 days and water 8, the camp's supplies, the days at camp, the flight's 40 s and 350 m, the tracker's
//     1.8 km and 20 minutes, the camp's and trip's days: game choices (on a built game the feed and water days are the
//     engine's, as the calendar's jump card will say: task T15);
//   a trapped bird's 15 x 15½ in and 1,010 g: as the sale pages give sizes [187][216];
//   5,000 for a banned place [136]; 100,000 for a net off the ground [136] (the proxy's item 9);
//   the released saker's line: the proxy's, batch 3 item 4.
// WHAT THE NEW THINGS COST TO DRAW (estimates: none is built; T11's birds are measured): the hooded saker 6,752
// triangles in 3 draws; in flight 6,364; standing 6,188; the stone-curlew 5,084 / 5,420; far birds under 1,500; the
// perch 1,424; the cuff 864 (T11); the peregrine about the saker's (not built); a lure pigeon about 1.5k, skinned, 1 draw;
// a net a few hundred, 1 draw; the mobile tent about 1.5k, the pigeon cage about 400, the supplies about 800 (static,
// in the cached shadow map: 3 draws); the falcons' room about 2k in 2 draws, its perches instanced, 1 draw. Every
// frame's base is counted from the WebGL calls and written to trip_draws.txt.
// AWAY FOR DAYS IS THE CALENDAR'S ONE MECHANISM (task T15, /home/user/wt/t15 docs/proposals/rush_and_calendar.md section 5):
// «اطلع» opens the calendar's card before the jump (phone_falcon.cjs views 16-17) with the trip's lines added; the drive
// is the plan's travel time; each «نام لين الفجر» is one call of the engine's away() to tomorrow, landing at the working
// hour's start, with ALL the calendar's stops (an illness, a death, a store at 3 days, money below zero, the account at its
// limit, a fine or ban, an offer, his round's day, a registration closing in 3 days, the breeding season opening, the pens
// full) plus the camp's own (its supplies out, the trapping season's end, the trip's chosen end); a bird in the net is
// played live, not a stop; the summary (trip_21) is the calendar's summary view with the trip's lines above its own.
// DRAW COSTS: the driver's seat is round 1's count only (37 draws / 159k); this run's reading did not take. The binocular
// view (trip_14) narrows the view, so the far peregrine shows enlarged and needs the near model by its size on screen:
// about 6k triangles and 3 draws (+3 shadow) over the base; he leaves it by the binoculars' own button at the right edge
// (the mask hides the top-left buttons).
// To draw again: build the prototype (THREE_DIR=<three@0.170.0 package> python3 tool/proto_app/assemble.py), serve
// tool/proto_app/assets/web on a port (PORT, 8765 by default), run `python3 -I design/hunt/cut_bird.py` once, then
// `NODE_PATH=$(npm root -g) node design/hunt/trip.cjs` from the repository's root; it writes trip_<nn>_<name>.jpg,
// trip_board.jpg and trip_draws.txt in design/hunt/ (or OUT=<folder>). About twenty-five minutes on SwiftShader.
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const PORT = process.env.PORT || 8765;
const OUT = process.env.OUT || __dirname;
const DSF = 1;      // (the owner's screen at 1x: at 2x SwiftShader draws too slowly for the car to move)

// the page's hooks this script needs, added to the served copy only (nothing in the page changes)
const HOOK = `window.__phone = phone;
window.__open = openPlace; window.__close = closePop; window.__camera = camera; window.__controls = controls; window.__ICONS = ICONS;
window.__addPlace = (pl) => { PLACES.push(pl); const el = document.createElement('button'); el.type = 'button'; labelLayer.appendChild(el); pl.el = el; labels.push(pl); order.push(pl); refreshLabels(); (window.__added = window.__added || []).push(pl); return pl; };`;
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

// ---- round 2's stand-ins (flat SVG, marked in the strips) and buttons
Object.assign(SV, {
  tent: `<svg viewBox="0 0 220 130" width="220" height="130"><path d="M10 120 L60 30 L160 30 L210 120 Z" fill="#d9c7a3"/><path d="M60 30 L110 120 L160 30" fill="#c4b088"/><path d="M95 120 L110 78 L125 120 Z" fill="#3b2f22"/><path d="M10 120 h200" stroke="#7a6a4f" stroke-width="3"/><path d="M60 30 L20 120 M160 30 L200 120" stroke="#8b7a5c" stroke-width="2"/></svg>`,
  cage: `<svg viewBox="0 0 70 50" width="70" height="50"><rect x="2" y="8" width="66" height="40" rx="3" fill="rgba(90,80,60,.25)" stroke="#5a4f3b" stroke-width="2"/><path d="M14 8v40M26 8v40M38 8v40M50 8v40M62 8v40" stroke="#5a4f3b" stroke-width="1.2"/><ellipse cx="22" cy="38" rx="9" ry="6" fill="#9aa0a8"/><ellipse cx="44" cy="40" rx="9" ry="6" fill="#b9bec4"/><circle cx="28" cy="34" r="3" fill="#7d838b"/><circle cx="50" cy="36" r="3" fill="#959ba3"/></svg>`,
  nets: `<svg viewBox="0 0 70 30" width="70" height="30"><ellipse cx="35" cy="20" rx="32" ry="9" fill="#5e6b4a"/><path d="M6 18 q29 -14 58 0 M10 24 q25 -10 50 0" stroke="#3f4a30" stroke-width="1.5" fill="none"/></svg>`,
  supplies: `<svg viewBox="0 0 90 46" width="90" height="46"><rect x="2" y="12" width="22" height="32" rx="3" fill="#2f6e3a"/><rect x="28" y="12" width="22" height="32" rx="3" fill="#2f6e3a"/><rect x="54" y="20" width="34" height="24" fill="#a07a45"/><path d="M8 12v-6h10v6M34 12v-6h10v6" stroke="#244f2b" stroke-width="3" fill="none"/></svg>`,
  pigeon: `<svg viewBox="0 0 40 26" width="40" height="26"><ellipse cx="20" cy="16" rx="13" ry="7" fill="#9aa0a8"/><circle cx="31" cy="10" r="4.5" fill="#7d838b"/><path d="M35 10 l4 1 -4 1" fill="#c9a26a"/><path d="M8 13 L1 9 L4 16 Z" fill="#6b717a"/><path d="M6 6 L34 22 M10 22 L30 4" stroke="#3f4a30" stroke-width="1" opacity=".8"/></svg>`,
  pereFly: `<svg viewBox="0 0 120 46" width="120" height="46"><path d="M2 18 C24 12 44 14 56 24 L60 20 L64 24 C76 14 96 12 118 18 C96 22 80 28 68 32 L64 42 L56 42 L52 32 C40 28 24 22 2 18 Z" fill="#3e454d"/><path d="M56 24 h8 v10 h-8z" fill="#e3dccd"/></svg>`,
  pereNet: `<svg viewBox="0 0 120 70" width="120" height="70"><ellipse cx="60" cy="62" rx="50" ry="6" fill="rgba(60,40,20,.35)"/><path d="M14 48 C28 30 44 26 56 30 L60 20 C64 12 74 12 78 20 C82 28 80 36 72 42 C88 38 100 42 110 48 C94 52 78 54 62 56 L46 56 C34 54 22 52 14 48 Z" fill="#3e454d"/><path d="M60 32 C66 36 72 36 76 32 L74 52 L60 52 Z" fill="#e3dccd"/><circle cx="72" cy="20" r="2" fill="#111"/><path d="M78 20 l5 2 -5 2" fill="#e9c84a"/><path d="M8 30 L112 60 M8 60 L112 26 M30 18 L50 66 M70 14 L90 66" stroke="#2c3322" stroke-width="1.3" opacity=".85"/></svg>`,
  curlewDown: `<svg viewBox="0 0 90 30" width="90" height="30"><ellipse cx="45" cy="24" rx="40" ry="5" fill="rgba(60,40,20,.3)"/><path d="M6 20 C20 10 50 8 76 14 C82 16 86 20 86 22 Z" fill="#b59a74"/><path d="M76 14 l12 -4" stroke="#e0c35a" stroke-width="2"/></svg>`,
  room: `<svg viewBox="0 0 150 100" width="150" height="100"><path d="M6 96 L6 38 L75 10 L144 38 L144 96 Z" fill="#cdbb98"/><path d="M6 38 L75 10 L144 38" fill="none" stroke="#8a7656" stroke-width="4"/><rect x="58" y="54" width="34" height="42" fill="#5a4630"/><rect x="18" y="52" width="26" height="18" fill="#3c4a52"/><rect x="106" y="52" width="26" height="18" fill="#3c4a52"/><path d="M6 96 h138" stroke="#7a6a4f" stroke-width="3"/></svg>`,
  scope: `<svg style="position:fixed;inset:0;width:100%;height:100%" viewBox="0 0 956 440" preserveAspectRatio="none"><defs><mask id="bino"><rect width="956" height="440" fill="#fff"/><circle cx="398" cy="220" r="190" fill="#000"/><circle cx="558" cy="220" r="190" fill="#000"/></mask></defs><rect width="956" height="440" fill="#000" mask="url(#bino)"/></svg>`,
});
const NET_ICON = '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 12h18M12 3v18M3 3l18 18M21 3L3 21"/></svg>';
const PIGEON_ICON = '<svg viewBox="0 0 24 24"><path d="M4 14c2-4 6-6 10-5l3-3 1 3c1.5 1 2.5 2.5 2 4-2 3-6 5-10 4-2.5-.5-4.5-1.5-6-3z"/><path d="M15 3v3M18.5 4.5l-1.5 2"/></svg>';
const BINOC_ICON = '<svg viewBox="0 0 24 24"><circle cx="7" cy="15" r="3.5"/><circle cx="17" cy="15" r="3.5"/><path d="M7 11.5V6h3v5M17 11.5V6h-3v5M10 13h4"/></svg>';
const TRACK_ICON = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="2.5"/><path d="M7.5 7.5a6.4 6.4 0 0 0 0 9M16.5 7.5a6.4 6.4 0 0 1 0 9M4.6 4.6a10.5 10.5 0 0 0 0 14.8M19.4 4.6a10.5 10.5 0 0 1 0 14.8"/></svg>';
Object.assign(PIN_ICONS, {
  net: '<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 12h18M12 3v18M3 3l18 18M21 3L3 21"/>',
  tent: '<path d="M2 19h20M4 19l8-14 8 14"/><path d="M9 19l3-5 3 5"/>',
  room: '<path d="M3 20h18M5 20V9l7-5 7 5v11"/><path d="M9 20v-6h6v6"/>',
});
const ONLY = (process.env.ONLY || 'map,room,trip,camp').split(',');
// RESTRIP=1: no game page; the strips and the board are remade from the frames already drawn (their top 956 x 440)      // (a part alone, to redraw it: map, room, trip, camp)

(async () => {
  if (process.env.RESTRIP) {
    const bb = await chromium.launch();
    const raw = fs.readdirSync(OUT).filter((f) => /^trip_\d\d_.*\.jpg$/.test(f)).sort().map((f) => { const png = path.join(OUT, f.replace(/\.jpg$/, '.png')); execFileSync('convert', [path.join(OUT, f), '-crop', '956x440+0+0', '+repage', png]); return png; });
    await makeStrips(bb, raw); await makeBoard(bb); for (const f of raw) fs.unlinkSync(f); await bb.close(); return;
  }
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
  await p.evaluate(([PIN_ICONS]) => {
    Object.assign(window.__ICONS, PIN_ICONS);
    const st = document.createElement('style');
    st.textContent = `body.playing #pop:not([hidden]) { display: flex !important; } body.playing .pop { top: calc(var(--edge-t) + 4px); }
      #drawn { position: fixed; inset: 0; pointer-events: none; z-index: 15; } #drawn > * { position: absolute; }
      #drawn .lbl { display: inline-flex; } .pl-ib.warn .dot { background: #f2b54c; } .pl-ib .rdot { position: absolute; right: 4%; top: 4%; width: 24%; height: 24%; border-radius: 50%; background: #f06a5d; box-shadow: 0 0 0 2px #1b130a; }`;
    document.head.appendChild(st);
    const d = document.createElement('div'); d.id = 'drawn'; document.body.appendChild(d);
  }, [PIN_ICONS]);
  const draw = (html) => p.evaluate((h) => { document.getElementById('drawn').innerHTML = h; }, html);
  const at = (x, y, html) => `<div style="left:${x}px;top:${y}px">${html}</div>`;
  const img = (name, x, y, w) => `<img src="data:image/png;base64,${fs.readFileSync(path.join(__dirname, 'birds', name + '.png')).toString('base64')}" style="position:absolute;left:${x}px;top:${y}px;width:${w}px">`;
  const pin = (x, y, icon) => `<div class="lbl on" style="left:${x}px;top:${y}px;transform:translate(-50%,-100%)"><svg class="i ic" viewBox="0 0 24 24">${PIN_ICONS[icon]}</svg></div>`;
  const edge = (buttons) => `<div class="play" style="position:fixed;inset:0;z-index:21;pointer-events:none"><div class="pl-door">${buttons}</div></div>`;
  const btn = (ic, label, cls = '', extra = '') => `<button class="pl-ib ${cls}" aria-label="${label}"${cls.includes('warn') ? ' style="background:rgba(28,20,12,.5);color:#f2b54c"' : ''}>${ic}${extra}</button>`;
  const open = (pl) => p.evaluate((o) => window.__open({ el: document.createElement('button'), p: window.__camera.position.clone(), max: 1e9, text: () => '', ...o,
    open() { return o.c; } }, true), pl);
  const close = () => p.evaluate(() => window.__close());
  const stepAway = async () => { await p.evaluate(() => { const m = window.__play.debug.man; m.pos.x += 5 * Math.sin(m.heading); m.pos.z += 5 * Math.cos(m.heading); }); await p.waitForTimeout(2500); };
  const counts = [], files = [];
  const measure = async () => { await p.waitForTimeout(1200); const f = await p.evaluate(() => window.__frames.slice(-6, -1)); return f.reduce((m, x) => (x[0] + x[2] > m[0] + m[2] ? x : m), [0, 0, 0, 0]); };
  const line = (name, best, note) => `${name}: main ${best[0]} draws / ${best[1]} triangles, shadow ${best[2]} / ${best[3]}, total ${best[0] + best[2]} / ${best[1] + best[3]}  (${note})`;
  const count = async (name, note) => { counts.push(line(name, await measure(), note)); console.log(counts[counts.length - 1]); };
  const shot = async (name, note) => {
    await p.evaluate(() => document.activeElement && document.activeElement.blur && document.activeElement.blur());
    counts.push(line(name, await measure(), note));
    await p.evaluate(() => { window.__q = []; window.__raf = window.requestAnimationFrame; window.requestAnimationFrame = (fn) => { window.__q.push(fn); return 1; }; });
    await p.waitForTimeout(300);
    const png = path.join(OUT, `${name}.png`);
    await p.screenshot({ path: png, timeout: 600000 });
    await p.evaluate(() => { window.requestAnimationFrame = window.__raf; const q = window.__q; window.__q = []; for (const fn of q) window.requestAnimationFrame(fn); });
    files.push(png); console.log('shot', counts[counts.length - 1]);
  };
  const phoneScreen = (html) => p.evaluate((h) => {
    const R = [...document.querySelectorAll('*')].find((e) => e.shadowRoot && e.shadowRoot.querySelector('.phone')).shadowRoot;
    const scr = R.querySelector('.scr'), sb = scr.querySelector('.sbar').outerHTML;
    scr.classList.remove('home');
    scr.innerHTML = `<span class="pill"></span>${sb}<div class="body">${h}</div><div class="hb"></div>`;
  }, html);
  const ps = (d) => `<svg class="i" viewBox="0 0 24 24">${d}</svg>`;
  const BACK = `<div class="nav"><button class="back">${ps('<path d="M9 6l6 6-6 6"/>')}رجوع</button></div>`;
  const FIST = `<div style="left:250px;top:110px;width:300px;height:330px">${img('saker_hooded_three_quarter', 82, 18, 140)}${SV.glove}</div>`;
  // the farm's days left, as the card before leaving says them (game choices here; the engine's on a built game)
  const FARM = 'العلف يكفي 9 أيام والماء 8، والعزبة تمشي مثل كل يوم وانت غايب.';

  // ================================================================ the map: the grounds' pins and the card before leaving
  if (ONLY.includes('map')) {
    await p.evaluate(() => { const c = window.__controls, cam = window.__camera; c.target.set(-300, 0, 40); cam.position.set(140, 70, 10); c.update(); });
    await p.evaluate(() => {
      const V = window.__camera.position.constructor;
      window.__hunt = window.__addPlace({ key: 'hunt', name: 'طرف النفود', icon: 'falcon', p: new V(-14000, 80, 1500), min: 900, cls: 'far', edge: true, text: () => '',
        open() { return { sub: 'مقناص · رحلة أيام · غرب العزبة', stats: [['المسافة', '14', 'كم'], ['الطريدة', 'الكروان'], ['الأيام', 'تختارها']],
          html: '<div class="note">قبل ما تطلع يوريك الجوال بطاقة التقويم: كم يكفي العلف والماء، واللي يجي بالطريق، ومتى يرجع لك. والعزبة تمشي مثل كل يوم وانت غايب.</div>', actions: [{ label: 'اطلع للرحلة', primary: true, run() {} }] }; } });
      window.__addPlace({ key: 'estate', name: 'المحازة', icon: 'estate', p: new V(-16000, 80, -5000), min: 900, cls: 'far', edge: true, text: () => '', open() { return {}; } });
    });
    await p.waitForTimeout(2500);
    await shot('trip_01_map_west', 'the map looking west: the falconry ground and the estate as far pins (drawn)');
    await p.evaluate(() => window.__open(window.__hunt, true));
    await shot('trip_02_card_hunt', 'the falconry ground\'s card before leaving: a trip of days, the farm\'s days left (drawn content)');
    await close();
    // north: the trapping grounds (their real direction: الحماد by Arar, and Hail)
    await p.evaluate(() => { const c = window.__controls, cam = window.__camera; c.target.set(-20, 0, -320); cam.position.set(40, 70, 140); c.update(); });
    await p.evaluate(() => {
      const V = window.__camera.position.constructor, dir = (dx, dz) => { const k = 60000 / Math.hypot(dx, dz); return new V(dx * k, 200, dz * k); };
      window.__hamad = window.__addPlace({ key: 'hamad', name: 'الحماد · أرض طرح', icon: 'net', p: dir(-185, -575), min: 900, cls: 'far', edge: true, text: () => '',
        open() { return { sub: 'مخيم أيام · شمال العزبة', stats: [['المسافة', '600', 'كم'], ['الطرح', 'لين 30 نوفمبر'], ['عدتك', 'ناقصة', '', 'warn']],
          html: '<div class="note">قبل ما تطلع يوريك الجوال بطاقة التقويم مع عدتك ومؤونة المخيم: كم يكفي العلف والماء، واللي يجي بالطريق، ومتى يرجع لك.</div>',
          actions: [{ label: 'اطلع للمخيم', primary: true, run() {} }, { label: 'كمّل عدتك', run() {} }] }; } });
      window.__addPlace({ key: 'hail', name: 'حائل · أرض طرح', icon: 'net', p: dir(-120, -190), min: 900, cls: 'far', edge: true, text: () => '', open() { return {}; } });
    });
    await p.waitForTimeout(2500);
    await p.evaluate(() => window.__open(window.__hamad, true));
    await shot('trip_03_card_trap', 'the map looking north: the trapping grounds as far pins and the card before leaving for الحماد (drawn)');
    await close();
  }

  await p.evaluate(() => (window.__added || []).forEach((l) => { l.off = true; l.el.style.visibility = 'hidden'; }));      // (the grounds' pins are not on the farm's frames)
  // ================================================================ the falcons' room at the farm
  if (ONLY.includes('room')) {
    await p.evaluate(() => { const c = window.__controls, cam = window.__camera; c.target.set(-12, 0, 20); cam.position.set(-60, 34, 70); c.update(); });
    await p.waitForTimeout(2500);
    await draw(at(355, 92, SV.room.replace('width="150" height="100"', 'width="90" height="60"')) + pin(400, 94, 'room'));
    await shot('trip_04_room', 'the farm: the falcons\' room drawn (a stand-in building) with its pin');
    await open({ key: 'room', name: 'غرفة الصقور', icon: 'room', c: { sub: 'أوكار ومقيض · تشيل 4 صقور', stats: [['الصقور', '2', ''], ['تبي دعو', '1', '', 'warn'], ['المقيض', 'بالصيف']],
      html: '<div class="note">سهيل · شاهين بحري فرخ، من مزاد الطرح. غيث · حر فرخ، من مزاد المزارع: ما دعيته من أمس.</div>', actions: [{ label: 'ادعهم', primary: true }, { label: 'نادي الصقور' }] } });
    await shot('trip_05_room_card', 'the room\'s card, opened by its pin (drawn content)');
    await close(); await draw('');
  }

  // ================================================================ the trip (falconry), then the camp (trapping): in play
  if (ONLY.includes('trip') || ONLY.includes('camp')) {
    await p.evaluate(() => window.__play.start());
    await p.waitForFunction(() => window.__play.model && window.__play.model.interior, null, { timeout: 300000 });
    await p.evaluate(() => window.__play.debug.enter());
    await p.waitForTimeout(2000);
    await p.evaluate(() => { const d = window.__play.debug; d.carState.pos.set(-3000, d.carState.pos.y, 600); d.carState.yaw = -1.9; d.toggleView(); d.snap(); });
    await p.waitForTimeout(6000);
    await p.keyboard.down('KeyW');
    await p.waitForFunction(() => Math.abs(window.__play.debug.carState.v) > 2, null, { timeout: 120000 }).catch(() => console.log('slow to speed'));
    await shot('trip_06_drive', 'driving to the ground, from behind; only the gear shows while moving (real HUD); nothing drawn');
    await p.keyboard.up('KeyW'); await p.keyboard.down('KeyS');
    await p.waitForFunction(() => Math.abs(window.__play.debug.carState.v) < 0.3, null, { timeout: 120000 }).catch(() => {});
    await p.keyboard.up('KeyS');
    await p.waitForTimeout(2500);
    await p.evaluate(() => window.__play.debug.toggleView());      // (behind -> the driver's seat, counted, and back)
    await p.waitForTimeout(3000);
    await count('seat (count only)', 'parked, from the driver\'s seat: the cabin drawn (the hooded falcon on its perch in the cabin would be seen here)');
    await p.evaluate(() => window.__play.debug.toggleView());
    await p.waitForTimeout(3000);
    const carBtn = (ic, id, label) => p.evaluate(([ic, id, label]) => { document.querySelectorAll('.pl-car .added').forEach((e) => e.remove()); const row = document.querySelector('.pl-car'); const bt = document.createElement('button'); bt.className = 'pl-ib added'; bt.id = id; bt.setAttribute('aria-label', label); bt.innerHTML = ic; row.insertBefore(bt, row.querySelector('[data-c="more"]')); }, [ic, id, label]);
    const CAMP = (falcon) => at(70, 196, SV.tent) + (falcon ? `<div style="left:300px;top:205px;width:60px;height:140px">${img('saker_hooded_perch', 0, 0, 44)}</div>` : at(300, 262, SV.cage) + at(318, 300, SV.nets)) + at(36, 278, SV.supplies) + pin(180, 200, 'tent');
    if (ONLY.includes('trip')) {
      await p.evaluate(() => { const d = window.__play.debug; if (d.state.view !== 3) d.toggleView(); });
      await p.waitForTimeout(3000);
      await carBtn(FALCON_ICON, 'falconBtn', 'الصقر');
      await draw(CAMP(true));
      await shot('trip_07_camp_falcon', 'the falcon trip\'s camp, parked: the tent, the hooded saker on its perch (T11), the supplies and the tent\'s pin drawn; the falcon\'s button in the car\'s row');
      // (in the car: the card docks below the car's row, and the pedals and the steering pad step aside while it is open: a proposal)
      await p.evaluate(() => { const st = document.createElement('style'); st.id = 'incar'; st.textContent = 'body.playing .pop { top: 96px !important; } .pl-pedals, .pl-steer { visibility: hidden; }'; document.head.appendChild(st); });
      await open({ key: 'camp', name: 'المخيم · اليوم الثالث', icon: 'tent', c: { sub: 'طرف النفود · رحلة مقناص', stats: [['الأيام', '3', ''], ['المؤونة', 'يومين', '', 'warn'], ['العزبة تكفي', '6', 'أيام تقريبًا']],
        html: '<div class="note">الصبح والعصر تطلع بالصقر، والليل تنام. تقدر تفك المخيم وترجع أي وقت.</div>', actions: [{ label: 'نام لين الفجر', primary: true }, { label: 'فك المخيم وارجع' }] } });
      await shot('trip_08_camp_card', 'the camp\'s card, opened by the tent\'s pin: the day, the supplies, the farm\'s days, sleep to dawn or break camp (drawn content)');
      await close(); await draw(''); await p.evaluate(() => document.getElementById('incar')?.remove());
      await p.evaluate(() => { document.querySelectorAll('.pl-car .added').forEach((e) => e.remove()); window.__play.debug.exit(); });
      await p.waitForFunction(() => window.__play.debug.state.mode === 'walk', null, { timeout: 120000 });
      await p.waitForTimeout(1500); await stepAway();
      await draw(FIST + edge(btn(CAST_ICON, 'شيل البرقع وأرسله', 'big')));
      await shot('trip_09_fist', 'on foot, first person: the hooded saker (T11) on a drawn glove; the cast-off button at the edge (drawn)');
      await draw(`<div style="left:440px;top:150px;width:140px;height:60px">${img('saker_flight_below', 0, 0, 120)}</div><div style="left:360px;top:196px;width:80px;height:30px">${img('curlew_flight_three_quarter', 0, 0, 64)}</div>` + edge(btn(LURE_ICON, 'ارجعه بالملواح', 'big')));
      await shot('trip_10_flight', 'the cast: the saker in flight and a stone-curlew flushing (T11\'s renders), the lure button (drawn)');
      await draw(`<div style="left:392px;top:226px;width:90px;height:30px">${SV.curlewDown}</div><div style="left:410px;top:186px;width:40px;height:70px">${img('saker_alert_side', 0, 0, 30)}</div>` + pin(425, 186, 'falcon'));
      await open({ key: 'res', name: 'غيث', icon: 'falcon', c: { sub: 'حر · فرخ · صاد كروان', stats: [['الطيران', '40', 'ثانية'], ['المسافة', '350', 'م'], ['الطلعة', 'صاد', '', 'good']],
        html: '<div class="note">نزل على الكروان عند الطعس. أكّله من صيده وارجعه للدس.</div>', actions: [{ label: 'ارجعه للدس', primary: true }] } });
      await shot('trip_11_result', 'the saker down on its quarry (the saker T11; the caught curlew a stand-in) with its pin, and the result card the tap opened (drawn)');
      await close();
      await draw(edge(btn(TRACK_ICON, 'جهاز التتبع', 'big', '<i class="rdot"></i>')));
      await open({ key: 'lost', name: 'غيث ما رجع', icon: 'falcon', cls: 'warn', c: { sub: 'جهاز التتبع · شمال غرب', stats: [['المسافة', '1.8', 'كم'], ['آخر إشارة', 'قبل 20 دقيقة']],
        html: '<div class="note warn">تدوّره بالسيارة على إشارة الجهاز: غالبًا تلقاه، وأحيانًا يروح.</div>', actions: [{ label: 'روح للإشارة', primary: true }] } });
      await shot('trip_12_lost', 'the rare lost falcon: the tracker\'s button with its dot at the edge, and its card (drawn)');
      await close(); await draw('');
    }
    if (ONLY.includes('camp')) {
      // the trapping camp on the same open ground (a real trapping ground would be at الحماد: the terrain here is Qassim's)
      if (await p.evaluate(() => window.__play.debug.state.mode === 'walk')) { await p.evaluate(() => { const d = window.__play.debug, c = d.carState.pos; d.man.pos.set(c.x + 1.5, c.y, c.z + 1.5); }); await p.waitForTimeout(1500); await p.evaluate(() => window.__play.debug.enter()); await p.waitForTimeout(3000); }
      await p.evaluate(() => { const d = window.__play.debug; if (d.state.view !== 3) d.toggleView(); });
      await p.waitForTimeout(3000);
      await carBtn(NET_ICON, 'netBtn', 'الطرح');
      await draw(CAMP(false));
      await shot('trip_13_camp_trap', 'the trapping camp, parked: the mobile tent, the pigeon cage, the nets, the supplies and the tent\'s pin (stand-ins); the net\'s button in the car\'s row (drawn)');
      await p.evaluate(() => { document.querySelectorAll('.pl-car .added').forEach((e) => e.remove()); window.__play.debug.exit(); });
      await p.waitForFunction(() => window.__play.debug.state.mode === 'walk', null, { timeout: 120000 });
      await p.waitForTimeout(1500); await stepAway();
      const TRAPBTNS = (scope) => edge(btn(PIGEON_ICON, 'أطلق الحمامة بالشبك', 'big') + btn(BINOC_ICON, 'الدربيل', scope ? 'on' : ''));
      await draw(SV.scope + at(520, 150, SV.pereFly.replace('width="120" height="46"', 'width="30" height="12"')) + TRAPBTNS(true));
      await shot('trip_14_dawn', 'dawn at camp, through the binoculars: a passing peregrine far off (stand-in); the pigeon-and-net and binoculars buttons (drawn)');
      await draw(at(420, 250, SV.pigeon) + at(380, 150, SV.pereFly.replace('width="120" height="46"', 'width="80" height="31"')) + TRAPBTNS(false));
      await shot('trip_15_stoop', 'the pigeon with the net on its back released; the peregrine stooping (both stand-ins)');
      await draw(at(390, 222, SV.pereNet) + pin(450, 222, 'net'));
      await open({ key: 'catch', name: 'فرخ شاهين بحري', icon: 'net', c: { sub: 'طرحته · ينباع بمزاد الطرح', stats: [['الطول', '15', 'إنش'], ['العرض', '15½', 'إنش'], ['الوزن', '1,010', 'غرام']],
        html: '<div class="note">برقعه وحطه بالخيمة. تعرضه بمزاد الطرح بملهم خلال أيام، أو تخليه لك.</div>', actions: [{ label: 'برقعه', primary: true }] } });
      await shot('trip_16_catch', 'the peregrine in the net (stand-in) with its pin, and the card the tap opened: a sellable bird (drawn)');
      await close();
      await draw(`<div style="left:430px;top:200px;width:50px;height:80px">${img('saker_alert_side', 0, 0, 34)}</div>` + pin(447, 200, 'net'));
      await open({ key: 'rel', name: 'حر', icon: 'net', c: { sub: 'ما ينطرح · طلقته', html: '<div class="note">طلقته: الحر مهدد، والمزاد ما يقبل إلا فرخ الشاهين البحري</div>', actions: [{ label: 'طيب', primary: true }] } });
      await shot('trip_17_release', 'a saker in the net (T11\'s saker) released, with the proxy\'s line (drawn)');
      await close();
      await draw(pin(180, 200, 'tent'));
      await open({ key: 'day', name: 'المخيم · اليوم السادس', icon: 'tent', c: { sub: 'الحماد · مخيم طرح', stats: [['الطيور اليوم', 'ما جا شي'], ['المؤونة', '4', 'أيام'], ['العلف بالعزبة', 'باقي 3 أيام', '', 'warn']],
        html: '<div class="note warn">باقي 3 أيام على العلف بالعزبة: تطلبه من الجوال وانت هنا، أو تفك المخيم وترجع.</div>', actions: [{ label: 'نام لين الفجر', primary: true }, { label: 'فك المخيم وارجع' }] } });
      await shot('trip_18_empty_day', 'an empty day\'s evening: the camp\'s card, opened by the tent\'s pin, with the farm\'s warning that handed the game back (drawn)');
      await close(); await draw('');
      // off the ground: back by the yard, the net's button warns and does not act
      await p.evaluate(() => { const d = window.__play.debug; d.enter(); });
      await p.waitForTimeout(2500);
      await p.evaluate(() => { const d = window.__play.debug; d.carState.pos.set(20, d.carState.pos.y, 78); d.carState.yaw = 0; d.snap(); });
      await p.waitForTimeout(4000);
      await p.evaluate(() => window.__play.debug.exit());
      await p.waitForFunction(() => window.__play.debug.state.mode === 'walk', null, { timeout: 120000 });
      await p.waitForTimeout(1500); await stepAway();
      await draw(edge(btn(PIGEON_ICON, 'هنا ما فيه طرح', 'big warn', '<i class="dot"></i>')));
      await open({ key: 'noTrap', name: 'هنا ما فيه طرح', icon: 'ban', cls: 'warn', c: { sub: 'مو أرض طرح', html: '<div class="note warn">الطرح بأرض طرح بس وبموسمه، والشبك برا أرض الطرح غرامته 100,000 ريال.</div>', actions: [{ label: 'طيب', primary: true }] } });
      await shot('trip_19_off_ground', 'by the yard: the net\'s button in its warning state, and the warning card it opened (drawn); it does not act');
      await close();
      await draw(edge(btn(CAST_ICON, 'هنا ممنوع الصيد', 'big warn', '<i class="dot"></i>')) + FIST);
      await open({ key: 'ban', name: 'هنا ممنوع الصيد', icon: 'ban', cls: 'warn', c: { sub: 'قريب من المزارع والعزب', html: '<div class="note warn">الصيد بالمزارع وحولها ممنوع، وغرامته 5,000 ريال لو انمسكت. ابعد عن العزب والقرى وأرسله.</div>', actions: [{ label: 'طيب', primary: true }] } });
      await shot('trip_20_banned', 'by the yard with the falcon: the cast-off button warns and does not act (decision 4), and its card (drawn)');
      await close(); await draw('');
      // back home: the trip's summary in the small phone (the calendar's summary, task T15)
      await p.evaluate(() => window.__phone.toggle());
      await p.waitForTimeout(800);
      await phoneScreen(`${BACK}<div class="title">اللي صار</div>
        <div class="span" style="background:#fff;border-radius:16px;padding:10px 12px;display:flex;flex-direction:column;gap:2px"><b style="font:700 15px/1.3 Alexandria,sans-serif">9 أيام · مخيم الحماد</b><small style="font-size:12px;color:#6e6e73">من الخميس 1 أكتوبر لين السبت 10 أكتوبر</small></div>
        <div class="group">
          <div class="row"><span class="lead">${ps('<rect x="3" y="3" width="18" height="18" rx="3"/><path d="M3 12h18M12 3v18"/>')}</span><b>طرحت فرخ شاهين بحري (مثال)</b><small>اليوم الثامن · بغرفة الصقور</small></div>
          <div class="row"><span class="lead">${ps('<path d="M5 12.5l4.5 4.5L19 7.5"/>')}</span><b>طلقت حر</b><small>اليوم الرابع: المزاد ما يقبله</small></div>
          <div class="row"><span class="lead">${ps('<circle cx="12" cy="12" r="8.5"/>')}</span><b>المؤونة والبنزين</b><small>صرفت 1,350 ريال</small></div></div>
        <div class="group">
          <div class="row"><span class="lead">${ps('<path d="M12 4 2.5 20h19z"/>')}</span><b>قرب العلف يخلص</b><small>اليوم السادس: طلبته من الجوال ووصل</small></div>
          <div class="row"><span class="lead">${ps('<path d="M5 12.5l4.5 4.5L19 7.5"/>')}</span><b>ما مرض شي</b><small>وما مات شي</small></div></div>
        <div class="note">هذا مثال: أغلب المواسم ما ينطرح فيها طير.</div>`);
      await p.waitForTimeout(800);
      await shot('trip_21_back', 'back at the farm: the trip\'s summary in the small phone (drawn content)');
    }
  }
  await p.close();
  await makeStrips(b, files);
  await makeBoard(b);
  for (const f of files) fs.unlinkSync(f);
  await b.close();
  if (!process.env.ONLY) fs.writeFileSync(path.join(OUT, 'trip_draws.txt'), counts.join('\n') + '\n');
  console.log(counts.join('\n'));
})();

const CAP = {
  trip_01_map_west: 'الخريطة للغرب. مرسوم: دبوس أرض المقناص «طرف النفود» ودبوس «المحازة» بعيد على الأفق.',
  trip_02_card_hunt: 'تضغط دبوس المقناص فتنفتح بطاقته: الرحلة أيام (كلام المالك 14 نوفمبر)، و«اطلع للرحلة» يفتح بالجوال بطاقة التقويم نفسها مع سطور الرحلة. مرسوم: المحتوى.',
  trip_03_card_trap: 'الخريطة للشمال: دبابيس أراضي الطرح (الحماد وحائل) باتجاهها الحقيقي، وبطاقة الأرض بضغطتك؛ «اطلع للمخيم» يفتح بطاقة التقويم مع العدة والمؤونة. مرسوم.',
  trip_04_room: 'العزبة: غرفة الصقور (مبنى بديل مرسوم) ودبوسها (قرار المالك 5).',
  trip_05_room_card: 'بطاقة غرفة الصقور بضغطة دبوسها: الصقور والدعو والمقيض. مرسوم: المحتوى. سعرها وسعتها اختيار لعب.',
  trip_06_drive: 'السواقة للأرض من ورا. كله حقيقي: وهي تمشي يبقى القير بس فوق. نفس السواقة للمقناص وللطرح.',
  trip_07_camp_falcon: 'مخيم رحلة المقناص. مرسوم: الخيمة والمؤونة (بدائل)، والصقر المبرقع على وكره (صورة مجسم الطيور، ينتظر موافقة المالك)، ودبوس الخيمة، وزر الصقر جنب أزرار السيارة.',
  trip_08_camp_card: 'بطاقة المخيم بضغطة دبوس الخيمة: اليوم والمؤونة وأيام العزبة، «نام لين الفجر» أو «فك المخيم وارجع» أي وقت. بالسيارة تنزل البطاقة تحت أزرارها، والدواسات تختفي وهي مفتوحة (اقتراح). مرسوم.',
  trip_09_fist: 'الصبح، من عيونك: الصقر المبرقع (صورة المجسم، ينتظر الموافقة) على دس مرسوم، وزر «شيل البرقع وأرسله» على الطرف.',
  trip_10_flight: 'أرسلته: الصقر طاير والكروان قام (صور المجسمات، تنتظر الموافقة)، وزر الملواح يرجعه. النتيجة من الصقر والأرض والحظ.',
  trip_11_result: 'نزل على الكروان (الصقر صورة المجسم، والكروان المصيود بديل) ودبوس عليه؛ تضغطه فتطلع البطاقة (قرار المالك 3). الصيد ما ينباع.',
  trip_12_lost: 'نادر: الصقر ما رجع. زر جهاز التتبع بنقطة حمرا على الطرف، وبطاقته بضغطتك: غالبًا تلقاه وأحيانًا يروح (قرار المالك 6). مرسوم.',
  trip_13_camp_trap: 'مخيم الطرح، نفس المخيم: الخيمة المتنقلة وقفص الحمام والشبك والمؤونة (بدائل)، وزر الطرح جنب أزرار السيارة. الأرض هنا أرض القصيم بالصورة.',
  trip_14_dawn: 'الفجر بالدربيل (دايرتين): شاهين عابر بعيد (بديل: الشاهين ما انبنى). على الطرف: زر الحمامة بالشبك، وزر الدربيل اللي يشيله. مرسوم.',
  trip_15_stoop: 'أطلقت الحمامة والشبك على ظهرها، والشاهين ينقض (بدائل). مرسوم.',
  trip_16_catch: 'الشاهين بالشبك (بديل) ودبوسه، وبطاقته بضغطتك: فرخ شاهين بحري ينباع بمزاد الطرح، طوله وعرضه ووزنه. مرسوم.',
  trip_17_release: 'حر بالشبك (صورة مجسم الحر) ودبوسه؛ بضغطتك على الدبوس تنفتح البطاقة: ينطلق، بسطر الوكيل (جواب مؤقت) بنصه. مرسوم.',
  trip_18_empty_day: 'يوم فاضي: بطاقة المخيم بضغطة الخيمة بالمسا، وتنبيه العزبة اللي رجّع اللعب لك (العلف يخلص بعد يومين). مرسوم.',
  trip_19_off_ground: 'جنب العزبة: زر الطرح يحذر وما يشتغل، وبضغطتك على زر التحذير تنفتح بطاقته: الطرح بأرضه وموسمه بس، والشبك براها 100,000 [136] (الوكيل). مرسوم.',
  trip_20_banned: 'جنب العزبة بالصقر: زر الإرسال يحذر وما يرسل (قرار المالك 4)، وبضغطتك على زر التحذير تنفتح بطاقته والغرامة 5,000 [136]. مرسوم.',
  trip_21_back: 'رجعت: «اللي صار» بالجوال الصغير، نفس ملخص التقويم ومعه سطور المخيم؛ الطير «مثال». مرسوم: محتوى الشاشة.',
};

// each frame with its strip under it (outside the game's picture): what is real and what is drawn
async function makeStrips(b, files) {
  const pg = await b.newPage({ viewport: { width: 956, height: 470 } });
  for (const [i, f] of files.entries()) {
    await pg.setContent(`<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@500;700&display=swap"><style>
      body { margin: 0; width: 956px; background: #2a2119; direction: rtl; font-family: "IBM Plex Sans Arabic", sans-serif; } img { display: block; width: 956px; height: 440px; }
      p { margin: 0; padding: 7px 12px 9px; color: #f6f1e7; font-size: 13px; line-height: 1.45; } b { background: #e8b46c; color: #1b130a; border-radius: 5px; padding: 0 6px; margin-left: 6px; }</style>
      <img src="data:image/png;base64,${fs.readFileSync(f).toString('base64')}"><p><b>${+path.basename(f).split('_')[1]} · تصميم</b>${CAP[path.basename(f, '.png')] || ''}</p>`, { waitUntil: 'networkidle' });
    await pg.evaluate(() => document.fonts.ready);
    const png = f.replace(/\.png$/, '_s.png');
    await pg.screenshot({ path: png, fullPage: true, timeout: 600000 });
    execFileSync('convert', [png, '-quality', '88', f.replace(/\.png$/, '.jpg')]); fs.unlinkSync(png);
  }
  await pg.close();
}
async function makeBoard(b) {
  const board = await b.newPage({ viewport: { width: 1500, height: 900 } });
  const frames = fs.readdirSync(OUT).filter((f) => /^trip_\d\d_.*\.jpg$/.test(f)).sort();
  const cells = frames.map((f) => `<img src="data:image/jpeg;base64,${fs.readFileSync(path.join(OUT, f)).toString('base64')}">`).join('');
  await board.setContent(`<!doctype html><meta charset="utf-8"><style>body { margin: 0; padding: 12px; background: #2a2119; display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; width: 1500px; box-sizing: border-box; } img { width: 100%; display: block; border-radius: 6px; }</style>${cells}`);
  await board.screenshot({ path: path.join(OUT, 'trip_board.png'), fullPage: true, timeout: 600000 });
  execFileSync('convert', [path.join(OUT, 'trip_board.png'), '-quality', '85', path.join(OUT, 'trip_board.jpg')]); fs.unlinkSync(path.join(OUT, 'trip_board.png'));
  await board.close();
}
