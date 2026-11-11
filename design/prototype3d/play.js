// Play mode: the owner walks the yard as a man in thobe and shemagh, gets into the black Land Cruiser and drives it.
// Light by design: one skinned character, the car already in the scene, no physics engine (car_physics.js: a sprung
// body over four wheels and tyres that sink in sand, a few dozen sums a frame), collisions against a short list of
// boxes and circles from the yard layout.
import * as THREE from 'three';
import { createCar, makeSoftness, LC300 } from './car_physics.js';
const LC300KPA = (LC300.roadKPa + LC300.airedKPa) / 2;      // below this the tyres count as aired down
const GEAR_TOP = [0, 18, 34, 52, 72, 96, 130];      // the rpm needle's simple gears: each one's top speed, km/h (allocated once)
const STEER_RATIO = 15;          // the steering wheel's turn per road-wheel turn (the LC300's about 15-16: about 1.4 turns to lock here)
// the private car's model is "2024 Toyota Land Cruiser LC300 VXR 409 TT" by Ddiaz Design (Sketchfab), CC BY-NC-SA 4.0,
// changed (see tool/vehicle3d/suv_model/thirdparty/README.md): credited on the card shown beside the car
const CREDIT = '<small class="pl-credit" dir="ltr">Model: Ddiaz Design · CC BY-NC-SA 4.0 · modified</small>';

const WALK = 1.25, RUN = 3.5;                 // the speeds the walk and run clips were made for (m/s, measured on the planted foot)
let WHEELBASE = 2.85, TRACK = 1.64;           // Land Cruiser 300; replaced by the model's own wheel positions when it has them
const ACCEL = 3.6, BRAKE = 8.0, VMAX = 140 / 3.6, VREV = 20 / 3.6;
const UP = new THREE.Vector3(0, 1, 0);

export function createPlay({ scene, camera, renderer, heightAt, car, camels, LAYOUT, loadLod, onExit }) {
  const ground = (x, z) => (heightAt ? heightAt(x, z) : 0);
  // ---------------------------------------------------------------- obstacles (yard layout, metres)
  const rects = [];
  const C = LAYOUT.compound, T = 0.25;
  const wall = (x0, x1, z0, z1) => rects.push({ x0, x1, z0, z1, wall: true });
  wall(C.x0 - T, C.x1 + T, C.z0 - T, C.z0 + T);                                   // north
  wall(C.x0 - T, C.x0 + T, C.z0, C.z1); wall(C.x1 - T, C.x1 + T, C.z0, C.z1);     // west, east
  wall(C.x0 - T, LAYOUT.gate.x0, C.z1 - T, C.z1 + T); wall(LAYOUT.gate.x1, C.x1 + T, C.z1 - T, C.z1 + T);   // south, with the gate
  for (const p of Object.values(LAYOUT.pens)) rects.push({ x0: p.x0, x1: p.x1, z0: p.z0, z1: p.z1 });
  rects.push({ x0: 0.7, x1: 11.3, z0: 3.4, z1: 9.6 });        // the room
  rects.push({ x0: -18, x1: -6, z0: 4.2, z1: 9.8 });          // the goat-hair tent
  rects.push({ x0: 34, x1: 40, z0: 4.4, z1: 7.6 });           // the shepherds' cabin
  rects.push({ x0: 13.4, x1: 15.4, z0: 4.2, z1: 9.4 });       // the white shas under the shade
  rects.push({ x0: 28.4, x1: 30.8, z0: -16.9, z1: -11.5 });   // the shas by the feed shed
  const posts = [];
  for (const dx of [-1.4, 1.4]) for (const dz of [-1.4, 1.4]) posts.push({ x: 30 + dx, z: -40 + dz, r: 0.18 });
  for (const dx of [-3.2, 3.2]) for (const dz of [-6.2, 0, 6.2]) posts.push({ x: 32 + dx, z: -21 + dz, r: 0.15 });
  for (const dx of [-4.25, 4.25]) for (const dz of [-3.25, 3.25]) posts.push({ x: 16.5 + dx, z: 6.5 + dz, r: 0.12 });

  function pushCircle(p, r) {           // p: Vector3 (x, z used); returns true if it touched something
    let hit = false;
    for (const b of rects) {
      const qx = Math.max(b.x0, Math.min(p.x, b.x1)), qz = Math.max(b.z0, Math.min(p.z, b.z1));
      let dx = p.x - qx, dz = p.z - qz; const d2 = dx * dx + dz * dz;
      if (d2 >= r * r) continue;
      hit = true;
      if (d2 > 1e-8) { const d = Math.sqrt(d2), k = (r - d) / d; p.x += dx * k; p.z += dz * k; }
      else {                                   // inside: leave by the nearest side
        const o = [p.x - b.x0 + r, b.x1 - p.x + r, p.z - b.z0 + r, b.z1 - p.z + r], m = Math.min(...o), i = o.indexOf(m);
        if (i === 0) p.x -= m; else if (i === 1) p.x += m; else if (i === 2) p.z -= m; else p.z += m;
      }
    }
    for (const c of posts) {
      const dx = p.x - c.x, dz = p.z - c.z, d = Math.hypot(dx, dz), rr = r + c.r;
      if (d < rr && d > 1e-6) { p.x += dx / d * (rr - d); p.z += dz / d * (rr - d); hit = true; }
    }
    for (const k of camels) {
      const q = k.root.position, dx = p.x - q.x, dz = p.z - q.z, d = Math.hypot(dx, dz), rr = r + 0.8;
      if (d < rr && d > 1e-6) { p.x += dx / d * (rr - d); p.z += dz / d * (rr - d); hit = true; }
    }
    return hit;
  }

  // ---------------------------------------------------------------- the man
  const man = { root: null, mixer: null, act: {}, pos: new THREE.Vector3(14.2, 0, 1.6), heading: Math.PI, speed: 0 };
  const ready = loadLod('man.json').then((g) => {
    man.root = g.scene;
    // thin double-sided cloth self-shadows into jagged specks: it casts, and takes the sun's shadow only on its outer face
    man.root.traverse((n) => { if (n.isMesh) { n.castShadow = true; n.receiveShadow = true; n.frustumCulled = false; n.material.shadowSide = THREE.FrontSide; } });
    man.mixer = new THREE.AnimationMixer(man.root);
    for (const clip of g.animations) { const a = man.mixer.clipAction(clip); a.play(); a.setEffectiveWeight(0); man.act[clip.name] = a; }
    man.root.visible = false; scene.add(man.root);
  });

  // ---------------------------------------------------------------- the car
  const carState = { pos: car.position.clone(), yaw: car.rotation.y, v: 0, steer: 0, pitch: 0, roll: 0, locked: false };
  const fwd = new THREE.Vector3(), right = new THREE.Vector3();
  const carFwd = (yaw, out) => out.set(Math.cos(yaw), 0, -Math.sin(yaw));       // the model's +x is its front
  // the cabin for the driver's view: dash, wheel, pillars, headliner and door cards, in the car's own frame
  // the car built by code carries its own cabin and moving parts; the older photo model gets a simple cabin
  const part = (n) => car.getObjectByName(n);
  const model = { interior: part('interior'), steer: part('steering'), doors: { FL: part('door_FL'), FR: part('door_FR'), RL: part('door_RL'), RR: part('door_RR') },
    tailgate: part('tailgate'), wheels: { FL: part('wheel_FL'), FR: part('wheel_FR'), RL: part('wheel_RL'), RR: part('wheel_RR') },
    corners: { FL: part('corner_FL'), FR: part('corner_FR'), RL: part('corner_RL'), RR: part('corner_RR') } };
  // the private car carries its corners (they ride on the springs and steer) and loads its interior when the player gets in
  const rigged = !!model.corners.FL;
  let hasCabin = !!model.interior || rigged;
  let steerBase = model.steer ? model.steer.quaternion.clone() : null;
  const cornerRest = Object.fromEntries(Object.entries(model.corners).filter(([, c]) => c).map(([k, c]) => [k, c.position.y]));
  // the model's own geometry: axles, track, tyre radius, the driver's eye, the cluster needles
  const geo = { front: 1.43, rear: -1.43, half: 0.82, tyre: 0.401, eye: null, look: null };
  const hubFL = model.corners.FL || model.wheels.FL, hubRL = model.corners.RL || model.wheels.RL;
  if (hubFL && hubRL) {
    geo.front = hubFL.position.x; geo.rear = hubRL.position.x; geo.half = Math.abs(hubFL.position.z);
    const bb = new THREE.Box3().setFromObject(model.wheels.FL); geo.tyre = (bb.max.y - bb.min.y) / 2 / car.scale.y;
    WHEELBASE = geo.front - geo.rear; TRACK = geo.half * 2;
  }
  if (part('eye') && part('eye_look')) { geo.eye = part('eye').position.clone(); geo.look = part('eye_look').position.clone(); }
  // the ride and the sand (car_physics.js); the yard and an apron round it are beaten hard
  const phys = createCar(geo);
  const inYard = (x, z) => x > C.x0 - 12 && x < C.x1 + 12 && z > C.z0 - 12 && z < C.z1 + 25;
  const soft = makeSoftness(ground, inYard);
  const env = { height: ground, soft };
  let settled = false, parked = true;                 // a car one gets into stands in park, as one left it
  const BODY_CIRCLES = [[-1.55, 0, 1.02], [0, 0, 1.02], [1.55, 0, 1.02], [2.25, 0.72, 0.28], [2.25, -0.72, 0.28], [-2.2, 0.72, 0.28], [-2.2, -0.72, 0.28]];
  const PEDALS = { gas: 0, brake: 0 }, POSE = { x: 0, z: 0, yaw: 0 };      // (reused every frame)
  const needles = { speed: part('needle_speed'), rpm: part('needle_rpm') };
  const needleBase = { speed: needles.speed?.quaternion.clone(), rpm: needles.rpm?.quaternion.clone() };
  const XAXIS = new THREE.Vector3(1, 0, 0), qTmp = new THREE.Quaternion();
  const tailMats = [];

  let spin = 0;
  const tween = [];
  // the private car's interior: fetched a few seconds after the page is ready, in the background (it is drawn only
  // from the driver's seat and while the door stands open); coming to the door fetches it at once if it is not here yet
  let cabinLoading = false, cabinFailed = -1e9, cabinWarm = false;
  function loadCabin() {
    if (!rigged || model.interior || cabinLoading || performance.now() - cabinFailed < 30000) return;      // (after a failure, try again in 30 s, not every frame)
    cabinLoading = true;
    loadLod('veh_suvcabin.json').then((g) => {
      const it = g.scene.getObjectByName('interior') || g.scene; it.name = 'interior';
      it.traverse((n) => { if (n.isMesh) { n.castShadow = false; n.receiveShadow = true; } });
      car.add(it); model.interior = it; model.doorcard = it.getObjectByName('doorcard_FL');
      model.steer = it.getObjectByName('steering'); steerBase = model.steer ? model.steer.quaternion.clone() : null;
      it.visible = false;
    }).catch(() => { cabinLoading = false; cabinFailed = performance.now(); });
  }
  // its shaders compiled and its textures sent to the GPU as the player walks up to the car (not on every page load:
  // the 33 MB of textures stay off the GPU until then), so the door opening does not stall
  function warmCabin() {
    if (cabinWarm || !model.interior) return;
    cabinWarm = true; const it = model.interior; it.visible = true;
    it.traverse((n) => { if (n.isMesh) for (const k of ['map', 'normalMap', 'roughnessMap', 'metalnessMap', 'aoMap', 'emissiveMap']) if (n.material[k]) renderer.initTexture(n.material[k]); });
    (renderer.compileAsync ? renderer.compileAsync(it, camera, scene) : Promise.resolve(renderer.compile(it, camera, scene))).catch(() => {}).finally(() => { if (model.interior === it && !(state.mode === 'drive' && state.view === 1)) it.visible = false; });
  }                                   // simple part animations: { obj, key, from, to, t, dur }
  // one animation per part at a time; `then` runs after an optional hold, in game time (not wall-clock)
  function animate(obj, to, dur = 0.45, then = null, hold = 0) {
    if (!obj) return;
    for (let i = tween.length - 1; i >= 0; i--) if (tween[i].obj === obj) tween.splice(i, 1);
    tween.push({ obj, from: obj.rotation.y, to, t: 0, dur, then, hold });
  }
  const cabin = new THREE.Group(); cabin.visible = false; car.add(cabin);
  {
    const dark = new THREE.MeshStandardMaterial({ color: '#1d1b19', roughness: 0.8 });
    const trim = new THREE.MeshStandardMaterial({ color: '#2b2824', roughness: 0.6 });
    const head = new THREE.MeshStandardMaterial({ color: '#cfc5b5', roughness: 0.95, side: THREE.DoubleSide });
    const leather = new THREE.MeshStandardMaterial({ color: '#7a5a3e', roughness: 0.55 });
    const box = (w, h, d, m, x, y, z, rz = 0) => { const o = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m); o.position.set(x, y, z); o.rotation.z = rz; cabin.add(o); return o; };
    box(0.55, 0.32, 1.86, dark, 0.92, 1.02, 0);                     // dashboard
    box(0.45, 0.06, 1.80, trim, 0.78, 1.20, 0, -0.25);             // dash top
    box(0.06, 0.95, 0.07, dark, 0.62, 1.55, -0.86, 0.62);          // A-pillars
    box(0.06, 0.95, 0.07, dark, 0.62, 1.55, 0.86, 0.62);
    const hl = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 1.8).rotateX(Math.PI / 2), head); hl.position.set(-0.3, 1.86, 0); cabin.add(hl);
    box(2.4, 0.55, 0.05, trim, -0.2, 0.92, -0.86); box(2.4, 0.55, 0.05, trim, -0.2, 0.92, 0.86);   // door cards
    box(0.12, 0.6, 0.18, trim, 0.62, 0.85, 0);                       // centre console
    box(0.5, 0.12, 0.5, leather, -0.05, 0.62, -0.42);                // driver seat cushion
    // the wheel turns with the steering
    const col = new THREE.Group(); col.position.set(0.62, 1.12, -0.42); col.rotation.z = 0.42; cabin.add(col);
    const rim = new THREE.Mesh(new THREE.TorusGeometry(0.19, 0.018, 8, 28), leather); rim.rotation.y = Math.PI / 2; col.add(rim);
    const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.05, 16), dark); hub.rotation.z = Math.PI / 2; col.add(hub);
    for (const a of [0, 2.1, -2.1]) { const sp = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.16, 0.03), dark); sp.position.set(0, Math.cos(a) * 0.09, Math.sin(a) * 0.09); sp.rotation.x = -a; col.add(sp); }
    cabin.userData.wheel = col;
  }
  // body seen from inside: front faces only, so the shell is see-through from the driver's seat but the hood still shows
  const carMats = [];
  car.traverse((n) => { if (n.isMesh) { n.material = n.material.clone(); carMats.push(n.material); if (n.material.name === 'taillight') tailMats.push(n.material); } });
  tailMats.splice(0, tailMats.length, ...carMats.filter((m) => m.name === 'taillight' || m.name === 'tail_light' || m.name === 'Light_Red_Back'));
  const headMats = carMats.filter((m) => m.name === 'head_light' || m.name === 'Front_Light');
  for (const m of headMats) m.emissiveIntensity = 1.0;                  // daytime running lamps

  // ---------------------------------------------------------------- dust behind the wheels (a small pool)
  const dustTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d'); const gr = g.createRadialGradient(32, 32, 2, 32, 32, 30); gr.addColorStop(0, 'rgba(200,170,130,0.9)'); gr.addColorStop(1, 'rgba(200,170,130,0)'); g.fillStyle = gr; g.fillRect(0, 0, 64, 64); return new THREE.CanvasTexture(c); })();
  const puffs = Array.from({ length: 18 }, () => { const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: dustTex, transparent: true, depthWrite: false, opacity: 0 })); s.visible = false; scene.add(s); return { s, age: 0, life: 1.6 }; });
  let puffI = 0, puffT = 0;

  // ---------------------------------------------------------------- the tyres' tracks in soft sand (one draw: a ring of marks)
  const TRACKS = 600, trackMesh = new THREE.InstancedMesh(new THREE.PlaneGeometry(0.27, 0.42).rotateX(-Math.PI / 2),
    new THREE.MeshBasicMaterial({ color: '#ffffff', transparent: true, opacity: 0.5, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 }), TRACKS);
  trackMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage); trackMesh.count = 0; trackMesh.frustumCulled = false; scene.add(trackMesh);
  trackMesh.setColorAt(0, new THREE.Color('#a08767'));          // (the colour buffer from the start: made later it recompiles the shader)
  const trackDark = new THREE.Color('#6e5a43'), trackLight = new THREE.Color('#a08767'), trackM = new THREE.Matrix4(), trackQ = new THREE.Quaternion(), trackS = new THREE.Vector3(1, 1, 1), trackP = new THREE.Vector3(), trackC = new THREE.Color();
  let trackI = 0; const trackLast = { RL: { x: 1e9, z: 0 }, RR: { x: 1e9, z: 0 } }, trackN = new THREE.Vector3(), trackQ2 = new THREE.Quaternion();
  // the rear tyres' marks (they run in the front ones' ruts), laid on the ground's own slope, where the sand takes a print
  function tracks() {
    trackMesh.instanceMatrix.clearUpdateRanges(); if (trackMesh.instanceColor) trackMesh.instanceColor.clearUpdateRanges();      // (once a frame: per mark, the second wheel's cleared the first's)
    for (const w of phys.wheels) {
      if (w.front || w.soft < 0.3 || w.wx === undefined) continue;
      const last = trackLast[w.k];
      if (Math.hypot(w.wx - last.x, w.wz - last.z) < 0.4) continue;
      if (last.x > 1e8) { last.px = w.wx; last.pz = w.wz; }
      last.x = w.wx; last.z = w.wz;
      const e = 0.3, gx = ground(w.wx + e, w.wz) - ground(w.wx - e, w.wz), gz = ground(w.wx, w.wz + e) - ground(w.wx, w.wz - e);
      trackN.set(-gx, 2 * e, -gz).normalize();
      trackP.set(w.wx, ground(w.wx, w.wz) + 0.02, w.wz); trackQ.setFromUnitVectors(UP, trackN).multiply(trackQ2.setFromAxisAngle(UP, carState.yaw + Math.PI / 2));
      trackS.set(1, 1, Math.max(1, Math.hypot(w.wx - last.px, w.wz - last.pz) / 0.42)); last.px = w.wx; last.pz = w.wz;     // (quick, a mark stretches over the gap since the last)
      trackM.compose(trackP, trackQ, trackS); trackMesh.setMatrixAt(trackI, trackM);
      trackMesh.setColorAt(trackI, trackC.copy(trackLight).lerp(trackDark, Math.min(1, w.sink / 0.12)));
      trackMesh.instanceMatrix.addUpdateRange(trackI * 16, 16); trackMesh.instanceMatrix.needsUpdate = true;
      if (trackMesh.instanceColor) { trackMesh.instanceColor.addUpdateRange(trackI * 3, 3); trackMesh.instanceColor.needsUpdate = true; }
      trackI = (trackI + 1) % TRACKS; trackMesh.count = Math.min(TRACKS, trackMesh.count + 1);      // (only the new mark is sent to the GPU)
    }
  }

  // ---------------------------------------------------------------- input
  const input = { mx: 0, mz: 0, run: false, gas: 0, brake: 0, steer: 0, yaw: Math.PI, pitch: 0.18 };
  const keys = new Set();
  const onKey = (e) => {
    if (!state.on) return;
    if (e.type === 'keydown') keys.add(e.code); else keys.delete(e.code);
    if (e.type === 'keydown' && e.code === 'KeyE') primary();
    if (e.type === 'keydown' && e.code === 'KeyC') toggleView();
    if (e.type === 'keydown' && e.code === 'KeyR' && state.mode === 'drive') act('gear');
  };
  addEventListener('keydown', onKey); addEventListener('keyup', onKey);

  const ui = document.createElement('div'); ui.className = 'play'; ui.dir = 'rtl'; ui.hidden = true;
  ui.innerHTML = `
    <div class="pl-top">
      <button class="pl-btn" data-a="exit" aria-label="رجوع للخريطة"><svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg></button>
      <span class="pl-speed" hidden><b>0</b><small>كم/س</small></span>
      <button class="pl-btn" data-a="view" aria-label="بدّل المنظور"><svg viewBox="0 0 24 24"><path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg><span>خلف</span></button>
    </div>
    <div class="pl-stick" hidden><span class="pl-knob"></span></div>
    <div class="pl-drive" hidden>
      <div class="pl-steer"><button data-h="steerL" aria-label="يسار"><svg viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg></button><button data-h="steerR" aria-label="يمين"><svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg></button></div>
      <div class="pl-pedals"><button class="brake" data-h="brake">فرامل</button><button class="gas" data-h="gas">بنزين</button></div>
    </div>
    <div class="pl-card" hidden></div>`;
  document.body.appendChild(ui);
  const $ = (s) => ui.querySelector(s);
  const stick = $('.pl-stick'), knob = $('.pl-knob'), card = $('.pl-card'), speedEl = $('.pl-speed b'); let shownKmh = -1;
  const held = { steerL: 0, steerR: 0, gas: 0, brake: 0 };
  ui.querySelectorAll('[data-h]').forEach((b) => {
    const k = b.dataset.h;
    const on = (e) => { e.preventDefault(); held[k] = 1; b.classList.add('on'); try { b.setPointerCapture(e.pointerId); } catch {} };
    const off = () => { held[k] = 0; b.classList.remove('on'); };
    b.addEventListener('pointerdown', on); b.addEventListener('pointerup', off); b.addEventListener('pointercancel', off); b.addEventListener('lostpointercapture', off);
  });
  ui.querySelector('[data-a="exit"]').addEventListener('click', () => stop());
  ui.querySelector('[data-a="view"]').addEventListener('click', () => toggleView());

  // the screen: the left half moves (a stick that appears under the thumb), the right half looks around
  const canvas = renderer.domElement;
  let stickId = null, lookId = null; const s0 = { x: 0, y: 0 }, l0 = { x: 0, y: 0 };
  canvas.addEventListener('pointerdown', (e) => {
    if (!state.on) return;
    if (e.clientX < innerWidth * 0.45 && state.mode === 'walk' && stickId === null) {
      stickId = e.pointerId; s0.x = e.clientX; s0.y = e.clientY;
      stick.hidden = false; stick.style.left = (e.clientX - 60) + 'px'; stick.style.top = (e.clientY - 60) + 'px'; knob.style.transform = '';
    } else if (lookId === null) { lookId = e.pointerId; l0.x = e.clientX; l0.y = e.clientY; }
    try { canvas.setPointerCapture(e.pointerId); } catch {}
  });
  canvas.addEventListener('pointermove', (e) => {
    if (!state.on) return;
    if (e.pointerId === stickId) {
      let dx = e.clientX - s0.x, dy = e.clientY - s0.y; const d = Math.hypot(dx, dy), m = 52;
      if (d > m) { dx *= m / d; dy *= m / d; }
      knob.style.transform = `translate(${dx}px, ${dy}px)`;
      input.mx = dx / m; input.mz = dy / m; input.run = d > m * 0.92;
    } else if (e.pointerId === lookId) {
      input.yaw -= (e.clientX - l0.x) * 0.006; input.pitch = THREE.MathUtils.clamp(input.pitch + (e.clientY - l0.y) * 0.004, -0.5, 1.0);
      l0.x = e.clientX; l0.y = e.clientY;
    }
  });
  const release = (e) => {
    if (e.pointerId === stickId) { stickId = null; stick.hidden = true; input.mx = input.mz = 0; input.run = false; }
    if (e.pointerId === lookId) lookId = null;
  };
  canvas.addEventListener('pointerup', release); canvas.addEventListener('pointercancel', release);

  // ---------------------------------------------------------------- modes and the context card
  const state = { on: false, mode: 'walk', view: 3 };
  function toggleView() {
    state.view = state.view === 3 ? 1 : 3;
    ui.querySelector('[data-a="view"] span').textContent = state.view === 3 ? 'خلف' : 'عيوني';
    if (state.mode === 'walk' && state.view === 1) input.yaw = man.heading;
  }
  const doorPoint = new THREE.Vector3();
  function driverDoor(out) { carFwd(carState.yaw, fwd); right.crossVectors(fwd, UP); return out.copy(carState.pos).addScaledVector(right, -(geo.half + 0.62)).addScaledVector(fwd, geo.front - 1.2); }
  let cardKey = '';
  function setCard(key, html) {
    if (key === cardKey) return; cardKey = key;
    card.hidden = !key; card.innerHTML = html || '';
    card.querySelectorAll('button').forEach((b) => b.addEventListener('click', () => act(b.dataset.c)));
  }
  // the drive card: out, the tyres' pressure, the low range, traction control; dig when stuck. The slow jobs take
  // game time and need the car standing (airing four tyres down is a few minutes' work: shortened, a game choice).
  let job = null, standing = true;
  const JOBS = { air: 8, dig: 10 };
  function driveCard() {
    // shown only while the car stands (or is stuck): moving, the scene is left clear
    const p = phys.s, aired = p.kPa < LC300KPA;
    let dug = 0; for (const w of phys.wheels) dug = Math.max(dug, w.dug);
    const stuckNow = p.stuck > 1.5 || dug > 0.08, speed = Math.abs(carState.v);
    standing = speed < 0.3 || (standing && speed < 1.0);                   // (shown below 0.3 m/s, hidden above 1: no flicker between)
    if (!standing && !stuckNow && !job) { setCard('', ''); return; }
    const key = 'drive' + aired + p.low + p.trc + p.gear + stuckNow + (job ? job.kind : '');
    if (key === cardKey) return;
    const busy = job ? `<span class="pl-busy">${job.kind === 'air' ? (aired ? 'أعبّي الكفرات' : 'أنفّس الكفرات') : 'أحفر حول الكفرات'}…</span>` : '';
    setCard(key, `${busy}${stuckNow && !job ? '<span class="pl-busy">غرّزت</span><button data-c="dig" class="pri">احفر</button>' : ''}`
      + `<button data-c="air">${aired ? 'عبّ الكفرات' : 'نفّس الكفرات'} <small>${Math.round(p.kPa / 6.895)} psi</small></button>`
      + `<button data-c="gear">${p.gear === 'R' ? 'R ريوس' : 'D قدّام'}</button><button data-c="low">${p.low ? 'L4' : 'H4'}</button><button data-c="trc">TRC ${p.trc ? 'شغّال' : 'طافي'}</button><button data-c="out">انزل</button>`);
  }
  function act(c) {
    if (c === 'in') enter();
    else if (c === 'out') exit();
    else if ((c === 'air' || c === 'dig') && !job && Math.abs(carState.v) < 1) job = { kind: c, t: 0 };
    else if (c === 'low' && Math.abs(carState.v) < 1) { phys.s.low = !phys.s.low; driveCard(); }
    else if (c === 'trc') { phys.s.trc = !phys.s.trc; driveCard(); }
    else if (c === 'gear' && Math.abs(carState.v) < 1) { phys.s.gear = phys.s.gear === 'R' ? 'D' : 'R'; driveCard(); }
    else if (c === 'lock') { carState.locked = !carState.locked; cardKey = ''; flash(); }
  }
  function primary() { if (state.mode === 'drive') exit(); else if (cardKey.startsWith('near') && !carState.locked) enter(); }
  function flash() {   // the indicators blink twice when it locks or unlocks
    const lamps = headMats.length || tailMats.length ? [...headMats, ...tailMats] : carMats;
    const rest = new Map(lamps.map((m) => [m, m.emissiveIntensity]));
    const set = (on) => { for (const m of lamps) { if (lamps === carMats) m.emissive?.setScalar(on ? 0.25 : 0); else m.emissiveIntensity = on ? 5 : rest.get(m); } };
    let n = 0; const t = setInterval(() => { set(n % 2 === 0); if (++n > 3) { clearInterval(t); set(false); } }, 140);
  }
  function enter() {
    animate(model.doors.FL, -1.05, 0.45, () => animate(model.doors.FL, 0, 0.4), 0.35);
    state.mode = 'drive'; man.root.visible = false; carState.v = 0;
    $('.pl-drive').hidden = false; $('.pl-speed').hidden = false; stick.hidden = true; stickId = null;
    driveCard();
    loadCabin();
  }
  function exit() {
    if (Math.abs(carState.v) <= 1.5) animate(model.doors.FL, -1.05, 0.45, () => animate(model.doors.FL, 0, 0.4), 0.7);
    if (Math.abs(carState.v) > 1.5) return;                   // not while moving
    state.mode = 'walk'; carState.v = 0; job = null; parked = true;
    if (rigged) { POSE.x = carState.pos.x; POSE.z = carState.pos.z; POSE.yaw = carState.yaw; phys.settle(POSE, env); carState.pos.y = phys.originY(); car.position.y = carState.pos.y; car.rotation.set(phys.s.roll, carState.yaw, phys.s.pitch, 'YZX'); for (const w of phys.wheels) { const c = model.corners[w.k]; if (c) c.position.y = cornerRest[w.k]; } }
    driverDoor(man.pos); pushCircle(man.pos, 0.3); carFwd(carState.yaw, fwd); right.crossVectors(fwd, UP); man.heading = Math.atan2(-right.x, -right.z); input.yaw = man.heading;
    man.root.visible = state.view === 3;
    $('.pl-drive').hidden = true; $('.pl-speed').hidden = true; cardKey = '';
  }

  // ---------------------------------------------------------------- per frame
  const tmp = new THREE.Vector3(), tmp2 = new THREE.Vector3(), look = new THREE.Vector3();
  const camPos = new THREE.Vector3(), camLook = new THREE.Vector3();
  const blend = { idle: 1, walk: 0, run: 0 };
  function updateWalk(dt) {
    let mx = input.mx, mz = input.mz, run = input.run;
    if (keys.size) {
      mx = (keys.has('KeyD') || keys.has('ArrowRight') ? 1 : 0) - (keys.has('KeyA') || keys.has('ArrowLeft') ? 1 : 0);
      mz = (keys.has('KeyS') || keys.has('ArrowDown') ? 1 : 0) - (keys.has('KeyW') || keys.has('ArrowUp') ? 1 : 0);
      run = keys.has('ShiftLeft') || keys.has('ShiftRight');
    }
    const amt = Math.min(1, Math.hypot(mx, mz));
    const target = amt < 0.08 ? 0 : run ? RUN : WALK * Math.max(0.55, amt);
    man.speed += (target - man.speed) * Math.min(1, dt * 6);
    if (amt > 0.08) {
      // the stick is read relative to where the camera looks
      const want = Math.atan2(-mx, -mz) + input.yaw;
      let d = ((want - man.heading + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
      man.heading += d * Math.min(1, dt * 10);
    }
    tmp.set(Math.sin(man.heading), 0, Math.cos(man.heading));
    man.pos.addScaledVector(tmp, man.speed * dt);
    pushCircle(man.pos, 0.3);
    carCircles(man.pos, 0.3);
    man.pos.y = ground(man.pos.x, man.pos.z);
    man.root.position.copy(man.pos); man.root.rotation.y = man.heading;
    // blend the clips by speed and play them at the matching rate, so the feet do not slide
    const w = man.speed < 0.05 ? 0 : man.speed <= WALK ? 1 : Math.max(0, 1 - (man.speed - WALK) / (RUN - WALK));
    const r = man.speed <= WALK ? 0 : 1 - w;
    const goal = { idle: man.speed < 0.05 ? 1 : Math.max(0, 1 - man.speed / 0.4), walk: man.speed < 0.05 ? 0 : w, run: r };
    for (const k of ['idle', 'walk', 'run']) { blend[k] += (goal[k] - blend[k]) * Math.min(1, dt * 8); man.act[k]?.setEffectiveWeight(blend[k]); }
    man.act.walk?.setEffectiveTimeScale(Math.max(0.5, man.speed / WALK));
    man.act.run?.setEffectiveTimeScale(Math.max(0.6, man.speed / RUN));
    man.mixer.update(dt);
    // near the driver's door: the car's options
    const near = driverDoor(doorPoint).distanceTo(man.pos) < 1.8;
    if (near) loadCabin();
    if (driverDoor(doorPoint).distanceTo(man.pos) < 8) warmCabin();
    if (near && cardKey !== 'near' + carState.locked) setCard('near' + carState.locked, (carState.locked ? '<button data-c="lock">افتح القفل</button>' : '<button data-c="in" class="pri">اركب</button><button data-c="lock">قفّل</button>') + (rigged ? CREDIT : ''));
    else setCard('', '');
    if (near) placeCard(tmp2.copy(carState.pos).setY(carState.pos.y + 2.4));
  }
  function carCircles(p, r) {          // the car as three circles along its length, for the man on foot
    carFwd(carState.yaw, fwd);
    for (const k of [-1.6, 0, 1.6]) {
      tmp2.copy(carState.pos).addScaledVector(fwd, k);
      const dx = p.x - tmp2.x, dz = p.z - tmp2.z, d = Math.hypot(dx, dz), rr = r + 1.05;
      if (d < rr && d > 1e-6) { p.x += dx / d * (rr - d); p.z += dz / d * (rr - d); }
    }
  }
  function updateDrive(dt) {
    let gas = held.gas, brake = held.brake, steer = held.steerL - held.steerR;
    if (keys.size) {
      gas = keys.has('KeyW') || keys.has('ArrowUp') ? 1 : gas; brake = keys.has('KeyS') || keys.has('ArrowDown') ? 1 : brake;
      steer = (keys.has('KeyA') || keys.has('ArrowLeft') ? 1 : 0) - (keys.has('KeyD') || keys.has('ArrowRight') ? 1 : 0) || steer;
    }
    if (job) {
      job.t += dt;
      if (job.kind === 'dig') for (const w of phys.wheels) w.dug *= Math.exp(-dt * 0.35);
      if (job.t >= JOBS[job.kind]) {
        if (job.kind === 'air') {
          const down = phys.s.kPa >= LC300KPA; phys.s.kPa = down ? LC300.airedKPa : LC300.roadKPa;
          if (down) for (const w of phys.wheels) w.dug *= 0.6;                 // the softened tyres spread and ride up out of their holes (game choice)
        }
        job = null;
      }
    }
    driveCard();
    // the pedals: gas drives the way the gear points (and brakes a car rolling the other way); the brake slows the car
    // and holds it standing, on a slope too (the gear, D or R, is changed on the card while the car stands)
    const way = phys.s.gear === 'R' ? -1 : 1, rolling = carState.v * way;
    const ctl = PEDALS; ctl.gas = 0; ctl.brake = 0;
    if (gas || brake) parked = false;
    if (job || parked) ctl.brake = 1;                                          // parked (got in, or the driver working outside) until a pedal is pressed
    else {
      if (gas) { if (rolling < -0.3) ctl.brake = 1; else ctl.gas = 1; }
      if (brake) ctl.brake = 1;                                               // (both feet: the brake holds against the engine)
    }
    // steering: quick at walking pace, gentle at speed; it returns to centre on its own
    const maxSteer = 0.6 / (1 + Math.abs(carState.v) / 9);
    carState.steer += (steer * maxSteer - carState.steer) * Math.min(1, dt * 5);
    // move first (by the turn the tyres' grip allowed), then let the springs and the sand answer the ground there
    carState.yaw += phys.s.yawRate * dt;
    carFwd(carState.yaw, fwd);
    carState.pos.addScaledVector(fwd, carState.v * dt);
    if (phys.s.slide) { right.crossVectors(fwd, UP); carState.pos.addScaledVector(right, phys.s.slide * dt); }      // sliding down a side slope too steep to hold
    POSE.x = carState.pos.x; POSE.z = carState.pos.z; POSE.yaw = carState.yaw;
    if (!settled) { phys.settle(POSE, env); settled = true; }
    phys.s.v = carState.v;
    phys.step(dt, ctl, carState.steer, POSE, env);
    carState.v = phys.s.v;
    // bumps against the yard: the car stops and rebounds a little
    let hit = false;
    right.crossVectors(fwd, UP);
    for (const [k, sd, r] of BODY_CIRCLES) {                                   // three along the body and the four bumper corners
      tmp.copy(carState.pos).addScaledVector(fwd, k).addScaledVector(right, sd); const bx = tmp.x, bz = tmp.z;
      if (pushCircle(tmp, r)) { carState.pos.x += tmp.x - bx; carState.pos.z += tmp.z - bz; hit = true; }
    }
    // the yard's walls and posts: a car meeting one stops (a hard knock rebounds a little and pitches the body);
    // pressing on into it, it stays put
    if (hit) { const v0 = carState.v; carState.v = Math.abs(v0) > 3 ? -0.1 * v0 : 0; phys.s.v = carState.v; phys.s.vp -= v0 * 0.04; }
    // the body on its springs: height, pitch and roll from car_physics.js; each corner rides its own spring
    right.crossVectors(fwd, UP);
    carState.pitch = phys.s.pitch; carState.roll = phys.s.roll; carState.pos.y = phys.originY();
    car.position.copy(carState.pos); car.rotation.set(carState.roll, carState.yaw, carState.pitch, 'YZX');
    cabin.userData.wheel.rotation.x = -carState.steer * 3.2;
    for (const w of phys.wheels) {
      const c = model.corners[w.k], wh = model.wheels[w.k];
      if (c) { c.position.y = cornerRest[w.k] + Math.max(-LC300.droop, Math.min(LC300.bump, w.u)); c.rotation.y = w.front ? carState.steer : 0; }
      if (wh) { wh.rotation.order = 'YZX'; if (!c) wh.rotation.y = w.front ? carState.steer : 0; wh.rotation.z = -phys.s.spinAngle; }
    }
    const a = phys.s.aLong;
    tracks(dt);
    if (model.steer) model.steer.quaternion.copy(steerBase).multiply(qTmp.setFromAxisAngle(XAXIS, carState.steer * STEER_RATIO));
    const braking = PEDALS.brake && Math.abs(carState.v) > 0.3;
    for (const m of tailMats) m.emissiveIntensity = braking ? 4.0 : 0.6;
    // the cluster: speed 0-220 km/h and engine speed (a simple gear model) over a 270 degree sweep
    if (needles.speed) needles.speed.quaternion.copy(needleBase.speed).multiply(qTmp.setFromAxisAngle(XAXIS, -Math.min(1, Math.abs(carState.v) * 3.6 / 220) * 4.712));
    if (needles.rpm) {
      const kmh = Math.abs(carState.v) * 3.6; let gear = 1; while (gear < 7 && kmh >= GEAR_TOP[gear]) gear++;
      const lo = GEAR_TOP[gear - 1], hi = gear < 7 ? GEAR_TOP[gear] : 220;
      const rpm = 750 + (kmh - lo) / Math.max(1, hi - lo) * 2600 + (gas > 0 ? 400 : 0);
      needles.rpm.quaternion.copy(needleBase.rpm).multiply(qTmp.setFromAxisAngle(XAXIS, -Math.min(1, rpm / 8000) * 4.712));
    }
    const kmh = Math.round(Math.abs(carState.v) * 3.6); if (kmh !== shownKmh) { shownKmh = kmh; speedEl.textContent = kmh; }
    // dust from the rear wheels when moving on sand
    const spinning = phys.s.slip * phys.s.thr;
    puffT += dt * Math.min(1, Math.abs(carState.v) / 6 + spinning * 2);
    let softNow = 0; for (const w of phys.wheels) softNow += w.soft / 4;
    if (softNow > 0.3 && (Math.abs(carState.v) > 2 || spinning > 0.05) && puffT > 0.08) {      // dust only off the beaten ground, where there is loose sand to raise
      puffT = 0; const p = puffs[puffI++ % puffs.length];
      p.s.position.copy(carState.pos).addScaledVector(fwd, -2.3).addScaledVector(right, (puffI % 2 ? -1 : 1) * 0.8).setY(carState.pos.y + 0.35);
      p.age = 0; p.s.visible = true;
    }
    if (man.mixer) man.mixer.update(dt);
    placeCard(tmp2.copy(carState.pos).setY(carState.pos.y + 2.4));
  }
  const proj = new THREE.Vector3();
  function placeCard(p) {
    proj.copy(p).project(camera);
    const x = (proj.x + 1) / 2 * innerWidth, y = (1 - proj.y) / 2 * innerHeight;
    if (state.mode === 'drive') { card.style.left = ''; card.style.top = ''; card.classList.add('docked'); return; }
    card.classList.remove('docked');
    card.style.left = Math.min(innerWidth - 20, Math.max(20, x)) + 'px'; card.style.top = Math.max(80, y) + 'px';
  }
  function updateCamera(dt) {
    const k = state.snap ? 1 : Math.min(1, dt * 6);
    if (state.mode === 'walk') {
      man.root.visible = state.view === 3;
      if (state.view === 3) {
        look.copy(man.pos).add(tmp.set(0, 1.5, 0));
        const d = 4.4;
        camPos.set(look.x - Math.sin(input.yaw) * Math.cos(input.pitch) * d, look.y + Math.sin(input.pitch) * d + 0.3, look.z - Math.cos(input.yaw) * Math.cos(input.pitch) * d);
        camPos.y = Math.max(camPos.y, ground(camPos.x, camPos.z) + 0.4);
        camera.position.lerp(camPos, k); camera.lookAt(look);
      } else {
        man.heading = input.yaw;
        camera.position.copy(man.pos).add(tmp.set(Math.sin(man.heading) * 0.12, 1.66, Math.cos(man.heading) * 0.12));
        camLook.copy(camera.position).add(tmp.set(Math.sin(input.yaw) * Math.cos(-input.pitch + 0.18), Math.sin(-input.pitch + 0.18) - 0.05, Math.cos(input.yaw) * Math.cos(-input.pitch + 0.18)));
        camera.lookAt(camLook);
      }
    } else {
      carFwd(carState.yaw, fwd); right.crossVectors(fwd, UP);
      const inside = state.view === 1;
      cabin.visible = inside && !hasCabin;
      if (!hasCabin) for (const m of carMats) { const side = inside ? THREE.FrontSide : THREE.DoubleSide; if (m.side !== side) { m.side = side; m.needsUpdate = true; } }
      if (inside) {
        car.updateMatrixWorld();
        if (geo.eye) { camera.position.copy(tmp.copy(geo.eye).applyMatrix4(car.matrixWorld)); camLook.copy(tmp.copy(geo.look).applyMatrix4(car.matrixWorld)); }
        else { camera.position.copy(tmp.set(hasCabin ? -0.17 : 0.0, hasCabin ? 1.57 : 1.46, hasCabin ? -0.40 : -0.42).applyMatrix4(car.matrixWorld)); camLook.copy(tmp.set(6, hasCabin ? 1.25 : 1.15, -0.36).applyMatrix4(car.matrixWorld)); }
        camera.lookAt(camLook);
      } else {
        const back = 7.2 + Math.abs(carState.v) * 0.05;
        camPos.copy(carState.pos).addScaledVector(fwd, -back).add(tmp.set(0, 2.9, 0));
        camPos.y = Math.max(camPos.y, ground(camPos.x, camPos.z) + 1.0);
        camera.position.lerp(camPos, state.snap ? 1 : Math.min(1, dt * 3.5));
        camLook.copy(carState.pos).addScaledVector(fwd, 2.5).add(tmp.set(0, 1.2, 0)); camera.lookAt(camLook);
      }
    }
    state.snap = false;
    for (const p of puffs) if (p.s.visible) { p.age += dt; const t = p.age / p.life; p.s.scale.setScalar(0.7 + t * 2.0); p.s.position.y += dt * 0.35; p.s.material.opacity = 0.38 * (1 - t); if (t >= 1) p.s.visible = false; }
  }

  function start() {
    state.on = true; state.mode = 'walk'; ui.hidden = false; document.body.classList.add('playing');
    ready.then(() => { man.pos.y = ground(man.pos.x, man.pos.z); man.root.visible = true; input.yaw = man.heading; });
    camera.near = 0.08; camera.updateProjectionMatrix();
  }
  function stop() {
    state.on = false; ui.hidden = true; setCard('', ''); document.body.classList.remove('playing');
    if (man.root) man.root.visible = false; cabin.visible = false;
    if (!hasCabin) for (const m of carMats) { m.side = THREE.DoubleSide; m.needsUpdate = true; }
    camera.near = 0.5; camera.updateProjectionMatrix();
    onExit && onExit(state.mode === 'drive' ? carState.pos : man.pos);
  }
  function update(dt) {
    for (let i = tween.length - 1; i >= 0; i--) {
      const a = tween[i]; a.t = Math.min(1, a.t + dt / a.dur); const e = a.t * a.t * (3 - 2 * a.t);
      a.obj.rotation.y = a.from + (a.to - a.from) * e;
      if (a.t >= 1) { if (a.hold > 0) { a.hold -= dt; continue; } tween.splice(i, 1); if (a.then) a.then(); }
    }
    if (model.doorcard && model.doors.FL) model.doorcard.rotation.y = model.doors.FL.rotation.y;      // the door's trim swings with it
    if (!state.on || !man.root) return false;
    if (state.mode === 'walk') updateWalk(dt); else updateDrive(dt);
    updateCamera(dt);
    return true;
  }
  if (rigged) setTimeout(loadCabin, 4000);
  return { start, stop, update, model, get on() { return state.on; }, focus: () => (state.mode === 'drive' ? carState.pos : man.pos), debug: { man, carState, enter, exit, toggleView, keys, state, snap: () => { state.snap = true; } } };
}
