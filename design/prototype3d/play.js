// Play mode: the owner walks the yard seen through his own eyes (no character model: the owner's word of 11 Nov 2026,
// first person only on foot), gets into the black Land Cruiser and drives it, from the seat or from behind the car.
// Light by design: no character to draw, the car already in the scene, no physics engine (car_physics.js: a sprung
// body over four wheels and tyres that sink in sand, a few dozen sums a frame), collisions against a short list of
// boxes and circles from the yard layout.
import * as THREE from 'three';
import { createCar, makeSoftness, LC300 } from './car_physics.js';
const LC300KPA = (LC300.roadKPa + LC300.airedKPa) / 2;      // below this the tyres count as aired down
const GEAR_TOP = [0, 18, 34, 52, 72, 96, 130];      // the rpm needle's simple gears: each one's top speed, km/h (allocated once)
const TIP = Math.tan(40 / 57.3);  // the steepest side slope it goes onto (its static stability: track 1.63 m over twice a cg of 0.8 m, about 45 degrees, with a margin)
const PEDAL_UP = 0.05;           // a pedal under this is up
const SHIFT_V = 0.8;             // m/s: under this a fresh press of the other pedal takes the other gear (under the 5 km/h an automatic creeps at, so a dab of the brake at a creep is only a brake; over 0.4, so the press still counts when the car has rolled on a little down a slope; game choice)
const STEER_RATE = 8;            // 1/s: how fast the front wheels follow the pad (a hand's quick turn of the wheel: 90% in about a quarter of a second; game choice)
const STEER_RATIO = 15;          // the steering wheel's turn per road-wheel turn (the LC300's about 15-16: about 1.4 turns to lock here)
// the private car is ours, built by code from the owner's photos (tool/vehicle3d/suv_model; the owner's choice of 11 Nov
// over the downloaded model of tool/vehicle3d/suv_model/thirdparty, which is no longer in the game)

const WALK = 1.25, RUN = 3.5;                 // walking and running pace, m/s (a walk of 4.5 km/h, a jog of 12.6: game choice)
let WHEELBASE = 2.85, TRACK = 1.64;           // Land Cruiser 300; replaced by the model's own wheel positions when it has them
const ACCEL = 3.6, BRAKE = 8.0, VMAX = 140 / 3.6, VREV = 20 / 3.6;
const UP = new THREE.Vector3(0, 1, 0);

export function createPlay({ scene, camera, renderer, heightAt, car, camels, LAYOUT, loadLod, onExit, host = document.body, phone = null }) {
  const ground = (x, z) => (heightAt ? heightAt(x, z) : 0);
  // ---------------------------------------------------------------- obstacles (yard layout, metres)
  const rects = [];
  const C = LAYOUT.compound, T = 0.25;
  const wall = (x0, x1, z0, z1) => rects.push({ x0, x1, z0, z1, wall: true, h: 2.1 });      // (h: the height the chase camera must clear to see over it; world.js builds the wall 2.1 m)
  wall(C.x0 - T, C.x1 + T, C.z0 - T, C.z0 + T);                                   // north
  wall(C.x0 - T, C.x0 + T, C.z0, C.z1); wall(C.x1 - T, C.x1 + T, C.z0, C.z1);     // west, east
  wall(C.x0 - T, LAYOUT.gate.x0, C.z1 - T, C.z1 + T); wall(LAYOUT.gate.x1, C.x1 + T, C.z1 - T, C.z1 + T);   // south, with the gate
  for (const p of Object.values(LAYOUT.pens)) rects.push({ x0: p.x0, x1: p.x1, z0: p.z0, z1: p.z1 });
  rects.push({ x0: 0.7, x1: 11.3, z0: 3.4, z1: 9.6, h: 4.6 });        // the room
  rects.push({ x0: -18, x1: -6, z0: 4.2, z1: 9.8, h: 3.3 });          // the goat-hair tent
  rects.push({ x0: 34, x1: 40, z0: 4.4, z1: 7.6, h: 3.0 });           // the shepherds' cabin
  rects.push({ x0: 13.4, x1: 15.4, z0: 4.2, z1: 9.4, h: 2.1 });       // the white shas under the shade
  rects.push({ x0: 25.2, x1: 27.6, z0: -16.9, z1: -11.5, h: 2.1 });   // the shas by the feed shed
  // roofs a car drives under, with the height of their underside (world.js): the porch's pergola before the room, 3.25 m
  // up and 12 cm thick, and the car shade's cloth, 2.7 m at its edges and 3.2 at its middle. The chase camera keeps the
  // line to the car under them (it rose over them and saw only the roof)
  const roofs = [{ x0: 1.0, x1: 11.0, z0: 0.55, z1: 3.75, under: 3.19, top: 3.31 }, { x0: 12.25, x1: 20.75, z0: 3.25, z1: 9.75, under: 2.7, top: 3.3 }];      // (top: the porch's slab 12 cm; the shade's cloth peaks at 3.2 m)
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
      const dx = p.x - c.x, dz = p.z - c.z, d = Math.sqrt(dx * dx + dz * dz), rr = r + c.r;      // (sqrt, not Math.hypot: no garbage in the frame's loops)
      if (d < rr && d > 1e-6) { p.x += dx / d * (rr - d); p.z += dz / d * (rr - d); hit = true; }
    }
    for (const k of camels) {
      const q = k.root.position, dx = p.x - q.x, dz = p.z - q.z, d = Math.sqrt(dx * dx + dz * dz), rr = r + 0.8;
      if (d < rr && d > 1e-6) { p.x += dx / d * (rr - d); p.z += dz / d * (rr - d); hit = true; }
    }
    return hit;
  }

  // ---------------------------------------------------------------- the walker: a place, a heading and a speed (no model)
  const EYE = 1.66;                                // m, the eyes' height on foot (game choice: a man of about 1.76 m)
  const man = { pos: new THREE.Vector3(14.2, 0, 1.6), heading: Math.PI, speed: 0 };

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
  let settled = false, parked = true, stopWas = 0;                 // a car one gets into stands in park, as one left it
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
  // (not the shadow stand-ins: their material is shown only in the shadow pass, and a copy of it never would be)
  car.traverse((n) => { if (n.isMesh && !n.userData.shadowOnly) { n.material = n.material.clone(); carMats.push(n.material); if (n.material.name === 'taillight') tailMats.push(n.material); } });
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
      { const gx = w.wx - last.x, gz = w.wz - last.z; if (gx * gx + gz * gz < 0.16) continue; }
      if (last.x > 1e8) { last.px = w.wx; last.pz = w.wz; }
      last.x = w.wx; last.z = w.wz;
      const e = 0.3, gx = ground(w.wx + e, w.wz) - ground(w.wx - e, w.wz), gz = ground(w.wx, w.wz + e) - ground(w.wx, w.wz - e);
      trackN.set(-gx, 2 * e, -gz).normalize();
      trackP.set(w.wx, ground(w.wx, w.wz) + 0.02, w.wz); trackQ.setFromUnitVectors(UP, trackN).multiply(trackQ2.setFromAxisAngle(UP, carState.yaw + Math.PI / 2));
      trackS.set(1, 1, Math.max(1, Math.sqrt((w.wx - last.px) ** 2 + (w.wz - last.pz) ** 2) / 0.42)); last.px = w.wx; last.pz = w.wz;     // (quick, a mark stretches over the gap since the last)
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
    if (e.type === 'keyup') { keys.delete(e.code); return; }      // (let go even out of play: dropped there, the key stayed held and the man walked alone on the next start)
    if (busy()) return;             // (the enlarged phone has the keys)
    if (!state.on) return;
    keys.add(e.code);
    if (e.type === 'keydown' && e.code === 'KeyE') primary();
    if (e.type === 'keydown' && e.code === 'KeyC' && state.mode === 'drive') toggleView();
    if (e.type === 'keydown' && e.code === 'KeyR' && state.mode === 'drive') act('gear');
  };
  addEventListener('keydown', onKey); addEventListener('keyup', onKey); addEventListener('blur', () => keys.clear());

  // The controls: icons only, at the screen's edges (farm.html's .play styles; nothing written floats over the scene).
  // Top left: the view (in the car), back to the map and the phone. By the driver's door: get in and lock. Driving: a steering pad (bottom
  // left), two pedals pressed as far as the thumb slides up them (bottom right), and the car's own buttons in a row
  // (top right) while it stands; moving, only the gear shows.
  const I = {
    eye: '<svg viewBox="0 0 24 24"><path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg>',
    back: '<svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg>',
    trc: '<svg viewBox="0 0 24 24"><path d="M6 12l1.5-4h9L18 12v4H6z"/><path d="M4 20c1.5-1 2.5-1 4 0s2.5 1 4 0 2.5-1 4 0 2.5 1 4 0"/></svg>',
    phone: '<svg viewBox="0 0 24 24"><rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M10.5 18.5h3"/></svg>',
    car: '<svg viewBox="0 0 24 24"><path d="M5 13l1.5-4.5h11L19 13v5H5z"/><circle cx="8.5" cy="15.5" r="1"/><circle cx="15.5" cy="15.5" r="1"/></svg>',
    tyre: '<svg viewBox="0 0 24 24"><circle cx="12" cy="13" r="7"/><circle cx="12" cy="13" r="2.5"/><path d="M12 6V3M10 3h4"/></svg>',
    dig: '<svg viewBox="0 0 24 24"><path d="M14 4l6 6M17 7L8 16"/><path d="M8 16l-3.5 1-1.5 4 4-1.5 1-3.5z"/></svg>',
    out: '<svg viewBox="0 0 24 24"><path d="M14 4h5v16h-5"/><path d="M10 8l-4 4 4 4M6 12h9"/></svg>',
    door: '<svg viewBox="0 0 24 24"><path d="M4 20V6l7-3h7v17z"/><path d="M4 11h14M14 14h1.5"/></svg>',
    lock: '<svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>',
    unlock: '<svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 7.5-2"/></svg>',
    wheel: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2"/><path d="M4 12h6M14 12h6M12 14v6"/></svg>',
  };
  const ui = document.createElement('div'); ui.className = 'play'; ui.hidden = true;
  ui.innerHTML = `
    <div class="pl-tl">
      <button class="pl-ib" data-a="view" aria-label="بدّل المنظور: من ورا أو من عيونك">${I.eye}</button>
      <button class="pl-ib" data-a="exit" aria-label="رجوع للخريطة">${I.back}</button>
      <button class="pl-ib" data-a="phone" aria-label="الجوال">${I.phone}</button>
    </div>
    <div class="pl-car" hidden>
      <button class="pl-ib on" data-c="gear" aria-label="القير"><span>D</span></button>
      <button class="pl-ib" data-c="more" aria-label="أزرار السيارة" aria-expanded="false">${I.car}<i class="dot" hidden></i></button>
      <button class="pl-ib on" data-c="dig" aria-label="غرّزت: احفر حول الكفرات" hidden>${I.dig}</button>
      <button class="pl-ib fold" data-c="low" aria-label="الدبل الثقيل"><span>4L</span></button>
      <button class="pl-ib fold" data-c="trc" aria-label="منع التزحلق">${I.trc}</button>
      <button class="pl-ib fold" data-c="air" aria-label="تنفيس الكفرات وتعبئتها">${I.tyre}</button>
      <button class="pl-ib fold" data-c="out" aria-label="انزل">${I.out}</button>
    </div>
    <div class="pl-stick" hidden><span class="pl-knob"></span></div>
    <div class="pl-door" hidden>
      <button class="pl-ib big" data-c="in" aria-label="اركب">${I.door}</button>
      <button class="pl-ib" data-c="lock" aria-label="قفّل السيارة">${I.unlock}</button>
    </div>
    <div class="pl-steer" hidden role="slider" aria-label="الدركسون"><span class="arr"><svg viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg><svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg></span><span class="knob">${I.wheel}</span></div>
    <div class="pl-pedals" hidden>
      <div class="pl-pedal brake" data-p="brake" role="slider" aria-label="الفرامل"><i class="lvl"></i></div>
      <div class="pl-pedal gas" data-p="gas" role="slider" aria-label="البنزين"><i class="lvl"></i></div>
    </div>`;
  host.appendChild(ui);
  const $ = (s) => ui.querySelector(s);
  const stick = $('.pl-stick'), knob = $('.pl-knob'), carRow = $('.pl-car'), doorRow = $('.pl-door'), steerPad = $('.pl-steer'), steerKnob = $('.pl-steer .knob'), pedalsEl = $('.pl-pedals');
  // an element's box in the game's own frame (its layout offsets up to the UI layer: the page may be shown turned,
  // where a measured client box is in the screen's frame, not the pointer's)
  const boxOf = (el) => { let x = 0, y = 0; for (let n = el; n && n !== ui; n = n.offsetParent) { x += n.offsetLeft; y += n.offsetTop; } return { x, y, w: el.offsetWidth, h: el.offsetHeight }; };
  // the pedals: pressed by how far up the thumb is (from PEDAL_MIN at the bottom edge to 1 at the top and past it)
  const PEDAL_MIN = { gas: 0.15, brake: 0.3 };
  const pedal = { gas: 0, brake: 0 };
  const pedalReset = [];
  ui.querySelectorAll('[data-p]').forEach((el) => {
    const k = el.dataset.p, lvl = el.querySelector('.lvl'); let id = null;
    const set = (v) => { pedal[k] = v; lvl.style.height = (v * 100).toFixed(0) + '%'; };
    let b = null;                                // (its box, measured when the thumb lands: not on every move)
    const read = (e) => set(Math.min(1, Math.max(PEDAL_MIN[k], PEDAL_MIN[k] + (1 - PEDAL_MIN[k]) * (b.y + b.h - e.clientY) / (b.h * 0.9))));
    el.addEventListener('pointerdown', (e) => { e.preventDefault(); id = e.pointerId; b = boxOf(el); try { el.setPointerCapture(id); } catch {} read(e); });
    el.addEventListener('pointermove', (e) => { if (e.pointerId === id && !busy()) read(e); });
    const off = (e) => { if (e.pointerId === id) { id = null; set(0); } };
    el.addEventListener('pointerup', off); el.addEventListener('pointercancel', off); el.addEventListener('lostpointercapture', off);
    pedalReset.push(() => { id = null; set(0); });
  });
  // the steering pad: the thumb's place along it is the wheel's turn (its middle straight ahead, either end full
  // lock); let go, it returns to the middle
  const pad = { steer: 0 };
  {
    let id = null, mid = 0, half = 1;            // (the pad's middle and the knob's travel, measured when the thumb lands)
    const set = (v) => { pad.steer = v; steerKnob.style.transform = `translateX(${(-v * half).toFixed(1)}px) rotate(${(-v * 90).toFixed(0)}deg)`; };
    const read = (e) => set(Math.max(-1, Math.min(1, -(e.clientX - mid) / half)));      // (+ to the left, as the car's steer)
    steerPad.addEventListener('pointerdown', (e) => { e.preventDefault(); id = e.pointerId; const b = boxOf(steerPad); mid = b.x + b.w / 2; half = Math.max(1, (b.w - steerKnob.offsetWidth) / 2); try { steerPad.setPointerCapture(id); } catch {} read(e); });
    steerPad.addEventListener('pointermove', (e) => { if (e.pointerId === id && !busy()) read(e); });
    const off = (e) => { if (e.pointerId === id) { id = null; set(0); } };
    steerPad.addEventListener('pointerup', off); steerPad.addEventListener('pointercancel', off); steerPad.addEventListener('lostpointercapture', off);
    pad.reset = () => { id = null; set(0); };
  }
  // A button acts when the finger that pressed it lifts, not on click: a browser makes no click of a tap while
  // another finger is down, so with a thumb on the stick or a pedal the buttons were dead. (A click with no pointer,
  // from the keyboard, still acts.)
  // It acts only if it is still shown when the finger lifts, and not under the enlarged phone: held while it was hidden
  // (the get-in button as the walker moved off, the phone button as the car drove away), it acted anyway.
  const tap = (b, fn) => {
    let id = null, x = 0, y = 0;
    const live = () => b.isConnected && b.getClientRects().length > 0 && !busy();
    b.addEventListener('pointerdown', (e) => { e.preventDefault(); id = e.pointerId; x = e.clientX; y = e.clientY; try { b.setPointerCapture(id); } catch {} });
    b.addEventListener('pointerup', (e) => { if (e.pointerId === id) { id = null; if (Math.hypot(e.clientX - x, e.clientY - y) < 40 && live()) fn(); } });      // (slid well off it: let go without acting)
    b.addEventListener('pointercancel', () => { id = null; });
    b.addEventListener('click', (e) => { if (e.detail === 0 && live()) fn(); });
  };
  tap(ui.querySelector('[data-a="exit"]'), () => stop());
  tap(ui.querySelector('[data-a="view"]'), () => toggleView());
  // the phone (phone.js): opened small and closed by its button; not while the car moves (the button goes, and an open phone is put away)
  const phoneBtn = ui.querySelector('[data-a="phone"]');
  if (phone) {
    tap(phoneBtn, () => phone.toggle());
    phone.onChange((ps) => {
      phoneBtn.classList.toggle('on', ps !== 'closed'); phoneBtn.setAttribute('aria-pressed', String(ps !== 'closed'));
      // (enlarged, the phone has the screen: what the fingers and keys held is let go, the pedals and the pad too; and a
      // standing car is put in park until a pedal is pressed again, or with the brake let go it crept off unseen)
      if (ps === 'big') { stickId = lookId = null; stick.hidden = true; input.mx = input.mz = 0; input.run = false; keys.clear(); for (const f of pedalReset) f(); pad.reset(); if (state.mode === 'drive' && standing) parked = true; }
    });
  } else phoneBtn.hidden = true;
  const busy = () => !!phone && phone.big;         // the enlarged phone has the screen and the keys
  ui.querySelectorAll('[data-c]').forEach((b) => tap(b, () => act(b.dataset.c)));

  // the screen: the left half moves (a stick that appears under the thumb), the right half looks around
  const canvas = renderer.domElement;
  let stickId = null, lookId = null, stickM = 52; const s0 = { x: 0, y: 0 }, l0 = { x: 0, y: 0 };
  canvas.addEventListener('pointerdown', (e) => {
    if (!state.on) return;
    if (e.clientX < canvas.clientWidth * 0.45 && state.mode === 'walk' && stickId === null) {
      stickId = e.pointerId; s0.x = e.clientX; s0.y = e.clientY;
      stick.hidden = false; const half = stick.offsetWidth / 2; stickM = half * 0.86; stick.style.left = (e.clientX - half) + 'px'; stick.style.top = (e.clientY - half) + 'px'; knob.style.transform = '';
    } else if (lookId === null) { lookId = e.pointerId; l0.x = e.clientX; l0.y = e.clientY; }
    try { canvas.setPointerCapture(e.pointerId); } catch {}
  });
  canvas.addEventListener('pointermove', (e) => {
    if (!state.on || busy()) return;
    if (e.pointerId === stickId) {
      let dx = e.clientX - s0.x, dy = e.clientY - s0.y; const d = Math.hypot(dx, dy), m = stickM;
      if (d > m) { dx *= m / d; dy *= m / d; }
      knob.style.transform = `translate(${dx}px, ${dy}px)`;
      input.mx = dx / m; input.mz = dy / m; input.run = d > m * 0.92;
    } else if (e.pointerId === lookId) {
      const dx = e.clientX - l0.x, dy = e.clientY - l0.y;
      if (state.mode === 'walk') { input.yaw -= dx * 0.006; input.pitch = THREE.MathUtils.clamp(input.pitch + dy * 0.004, -0.5, 1.0); }
      else if (state.view === 3) { orbYaw -= dx * 0.006; orbIdle = 0; }      // (in the car, from behind: the camera round the car, a finger across the screen about 290 degrees; it does not tilt)
      l0.x = e.clientX; l0.y = e.clientY;
    }
  });
  const release = (e) => {
    if (e.pointerId === stickId) { stickId = null; stick.hidden = true; input.mx = input.mz = 0; input.run = false; }
    if (e.pointerId === lookId) lookId = null;
  };
  canvas.addEventListener('pointerup', release); canvas.addEventListener('pointercancel', release);

  // ---------------------------------------------------------------- modes, the car's buttons and the door's
  const state = { on: false, mode: 'walk', view: 1 };
  // the view: on foot always the walker's own eyes; in the car from the seat (1) or from behind it (3)
  const viewBtn = ui.querySelector('[data-a="view"]');
  function toggleView() {
    if (state.mode !== 'drive') return;
    state.view = state.view === 3 ? 1 : 3; state.snap = true;
    viewBtn.classList.toggle('on', state.view === 3);
  }
  const doorPoint = new THREE.Vector3();
  function driverDoor(out) { carFwd(carState.yaw, fwd); right.crossVectors(fwd, UP); return out.copy(carState.pos).addScaledVector(right, -(geo.half + 0.62)).addScaledVector(fwd, geo.front - 1.2); }
  // The car's buttons (top right), shown only while the car stands or is stuck; moving, the gear alone. Two show: the
  // gear and the car's button, which unfolds the rest beside it (low range, traction control, the tyres, getting out)
  // and folds them again FOLD_AFTER seconds after the last touch, or when the car is driven off; they stay out while a
  // job runs. A dot on the car's button says something behind it is not as it stands by default (low range on,
  // traction control off, the tyres aired down). Stuck, the dig button comes out on its own. The slow jobs take game
  // time and need the car standing (airing four tyres down is a few minutes' work: shortened, a game choice); the
  // button of the job under way pulses.
  const FOLD_AFTER = 4;
  let job = null, standing = true, nearDoor = false, rowKey = -1, carOpen = false, carOpenT = 0;
  const JOBS = { air: 8, dig: 10 };
  const btn = (c) => carRow.querySelector(`[data-c="${c}"]`);
  function driveCard() {
    const p = phys.s, aired = p.kPa < LC300KPA;
    let dug = 0; for (const w of phys.wheels) dug = Math.max(dug, w.dug);
    const stuckNow = p.stuck > 1.5 || dug > 0.08, speed = Math.abs(carState.v);
    standing = speed < 0.3 || (standing && speed < 1.0);                   // (shown below 0.3 m/s, hidden above 1: no flicker between)
    const full = standing || stuckNow || !!job;
    const open = carOpen || !!job;
    const key = (standing ? 512 : 0) | (full ? 1 : 0) | (aired ? 2 : 0) | (p.low ? 4 : 0) | (p.trc ? 8 : 0) | (p.gear === 'R' ? 16 : 0) | (stuckNow ? 32 : 0) | (job ? (job.kind === 'air' ? 64 : 128) : 0) | (open ? 256 : 0);
    if (phone && !standing && phone.state !== 'closed') phone.close();      // (on every frame the car moves, not only when the row changes: opened by a held button's lift, it stayed open)
    if (key === rowKey) return; rowKey = key;
    carRow.classList.toggle('moving', !full); carRow.classList.toggle('open', open);
    if (phone) { phoneBtn.hidden = !standing; if (!standing) phone.close(); }
    btn('more').classList.toggle('on', open); btn('more').setAttribute('aria-expanded', String(open)); btn('more').querySelector('.dot').hidden = open || !(p.low || !p.trc || aired);
    btn('gear').firstElementChild.textContent = p.gear === 'R' ? 'R' : 'D';
    btn('low').classList.toggle('on', p.low);
    btn('trc').classList.toggle('cut', !p.trc);
    btn('air').classList.toggle('on', aired); btn('air').classList.toggle('busy', !!job && job.kind === 'air');
    btn('dig').hidden = !(stuckNow || (job && job.kind === 'dig')); btn('dig').classList.toggle('busy', !!job && job.kind === 'dig');
  }
  function doorButtons() {                    // by the driver's door: get in (unless locked) and the lock
    doorRow.hidden = !nearDoor;
    const lock = doorRow.querySelector('[data-c="lock"]');
    doorRow.querySelector('[data-c="in"]').hidden = carState.locked;
    lock.classList.toggle('on', carState.locked); lock.innerHTML = carState.locked ? I.lock : I.unlock;
    lock.setAttribute('aria-label', carState.locked ? 'افتح القفل' : 'قفّل السيارة');
  }
  function act(c) {
    carOpenT = 0;
    if (c === 'more') { carOpen = !carOpen; driveCard(); return; }
    if (c === 'in') { if (state.mode === 'walk' && nearDoor && !carState.locked) enter(); }      // (by the unlocked door only)
    else if (c === 'out') exit();
    else if ((c === 'air' || c === 'dig') && !job && Math.abs(carState.v) < 1) job = { kind: c, t: 0 };
    else if (c === 'low' && Math.abs(carState.v) < 1) { phys.s.low = !phys.s.low; driveCard(); }
    else if (c === 'trc') { phys.s.trc = !phys.s.trc; driveCard(); }
    else if (c === 'gear' && Math.abs(carState.v) < 1) { phys.s.gear = phys.s.gear === 'R' ? 'D' : 'R'; driveCard(); }
    else if (c === 'lock') { carState.locked = !carState.locked; doorButtons(); flash(); }
  }
  function primary() { if (state.mode === 'drive') exit(); else if (nearDoor && !carState.locked) enter(); }
  function flash() {   // the indicators blink twice when it locks or unlocks
    const lamps = headMats.length || tailMats.length ? [...headMats, ...tailMats] : carMats;
    const rest = new Map(lamps.map((m) => [m, m.emissiveIntensity]));
    const set = (on) => { for (const m of lamps) { if (lamps === carMats) m.emissive?.setScalar(on ? 0.25 : 0); else m.emissiveIntensity = on ? 5 : rest.get(m); } };
    let n = 0; const t = setInterval(() => { set(n % 2 === 0); if (++n > 3) { clearInterval(t); set(false); } }, 140);
  }
  function enter() {
    animate(model.doors.FL, -1.05, 0.45, () => animate(model.doors.FL, 0, 0.4), 0.35);
    state.mode = 'drive'; carState.v = 0; viewBtn.hidden = false; state.snap = true; state.view = 1; viewBtn.classList.remove('on');      // (from the seat each time)
    steerPad.hidden = pedalsEl.hidden = carRow.hidden = false; stick.hidden = true; stickId = null; input.mx = input.mz = 0;
    nearDoor = false; doorButtons(); rowKey = -1; carOpen = false; driveCard();
    loadCabin();
  }
  function exit() {
    if (Math.abs(carState.v) <= 1.5) animate(model.doors.FL, -1.05, 0.45, () => animate(model.doors.FL, 0, 0.4), 0.7);
    if (Math.abs(carState.v) > 1.5) return;                   // not while moving
    state.mode = 'walk'; carState.v = 0; job = null; parked = true;
    if (rigged) { POSE.x = carState.pos.x; POSE.z = carState.pos.z; POSE.yaw = carState.yaw; phys.settle(POSE, env); carState.pos.y = phys.originY(); car.position.y = carState.pos.y; car.rotation.set(phys.s.roll, carState.yaw, phys.s.pitch, 'YZX'); for (const w of phys.wheels) { const c = model.corners[w.k]; if (c) c.position.y = cornerRest[w.k]; } }
    driverDoor(man.pos); pushCircle(man.pos, 0.3); carFwd(carState.yaw, fwd); right.crossVectors(fwd, UP); man.heading = Math.atan2(-right.x, -right.z); input.yaw = man.heading; input.pitch = 0.18; man.way = undefined;      // (the look level again: a drag in the car moved it, and the walker stepped out looking at his feet)
    viewBtn.hidden = true; state.snap = true; if (phone) phoneBtn.hidden = false;
    steerPad.hidden = pedalsEl.hidden = carRow.hidden = true; pedal.gas = pedal.brake = 0; pad.reset();
  }

  // ---------------------------------------------------------------- per frame
  const tmp = new THREE.Vector3(), tmp2 = new THREE.Vector3();
  const camPos = new THREE.Vector3(), camLook = new THREE.Vector3();
  function updateWalk(dt) {
    let mx = input.mx, mz = input.mz, run = input.run;
    if (keys.size) {
      mx = (keys.has('KeyD') || keys.has('ArrowRight') ? 1 : 0) - (keys.has('KeyA') || keys.has('ArrowLeft') ? 1 : 0);
      mz = (keys.has('KeyS') || keys.has('ArrowDown') ? 1 : 0) - (keys.has('KeyW') || keys.has('ArrowUp') ? 1 : 0);
      run = keys.has('ShiftLeft') || keys.has('ShiftRight');
    }
    const amt = Math.min(1, Math.sqrt(mx * mx + mz * mz));
    const target = amt < 0.08 ? 0 : run ? RUN : WALK * Math.max(0.55, amt);
    man.speed += (target - man.speed) * Math.min(1, dt * 6);
    // the stick is read relative to where the eyes look: up is ahead, the sides step sideways
    man.heading = input.yaw;
    if (amt > 0.08) man.way = Math.atan2(-mx, -mz) + input.yaw;
    tmp.set(Math.sin(man.way ?? man.heading), 0, Math.cos(man.way ?? man.heading));
    man.pos.addScaledVector(tmp, man.speed * dt);
    pushCircle(man.pos, 0.3);
    carCircles(man.pos, 0.3);
    man.pos.y = ground(man.pos.x, man.pos.z);
    // near the driver's door: the car's options
    const near = driverDoor(doorPoint).distanceTo(man.pos) < 1.8;
    if (near) loadCabin();
    if (driverDoor(doorPoint).distanceTo(man.pos) < 8) warmCabin();
    if (near !== nearDoor) { nearDoor = near; doorButtons(); }
  }
  function carCircles(p, r) {          // the car as three circles along its length, for the walker
    carFwd(carState.yaw, fwd);
    for (const k of [-1.6, 0, 1.6]) {
      tmp2.copy(carState.pos).addScaledVector(fwd, k);
      const dx = p.x - tmp2.x, dz = p.z - tmp2.z, d = Math.sqrt(dx * dx + dz * dz), rr = r + 1.05;
      if (d < rr && d > 1e-6) { p.x += dx / d * (rr - d); p.z += dz / d * (rr - d); }
    }
  }
  // how much higher one side's wheels stand than the other's, where the car is (m over the track)
  function sideTilt() { carFwd(carState.yaw, fwd); right.crossVectors(fwd, UP); const e = geo.half; return Math.abs(ground(carState.pos.x - right.x * e, carState.pos.z - right.z * e) - ground(carState.pos.x + right.x * e, carState.pos.z + right.z * e)); }
  function updateDrive(dt) {
    let gas = pedal.gas, brake = pedal.brake, steer = pad.steer, analog = true;      // (the touch pedals: 0 to 1 by how far they are pressed)
    if (keys.size) {
      gas = keys.has('KeyW') || keys.has('ArrowUp') ? 1 : gas; brake = keys.has('KeyS') || keys.has('ArrowDown') ? 1 : brake;
      steer = (keys.has('KeyA') || keys.has('ArrowLeft') ? 1 : 0) - (keys.has('KeyD') || keys.has('ArrowRight') ? 1 : 0) || steer;
      if ((gas === 1 && pedal.gas < 1) || (brake === 1 && pedal.brake < 1)) analog = false;                          // (a key is on or off: the engine eases it in)
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
    if (carOpen && !job) { carOpenT += dt; if (carOpenT > FOLD_AFTER || PEDALS.gas > 0) carOpen = false; }      // (PEDALS.gas: the last frame's, the car driven off)
    driveCard();
    // The pedals go forward and back without the gear button (the owner's word: forward and back while driving). The
    // right pedal goes forward and the left one back: in D the right is the gas and the left the brake. With the car
    // stopped, a fresh press of the left pedal takes reverse and it becomes the gas, the right one the brake, until a
    // fresh press of the right at a stop takes D again. A pedal kept down through the stop only holds the car (so it
    // waits on a slope on its brake, and does not back down it under power): lift and press again to go the other
    // way. The gear's button still changes it by hand. A pedal against the way the car rolls always brakes first.
    // (A real automatic wants the lever moved: this is a game choice.)
    const reversing = phys.s.gear === 'R';
    const go = reversing ? brake : gas, stop = reversing ? gas : brake, way = reversing ? -1 : 1, rolling = carState.v * way;
    const ctl = PEDALS; ctl.gas = 0; ctl.brake = 0; ctl.analog = analog;
    if (gas || brake) parked = false;
    if (job || parked) ctl.brake = 1;                                          // parked (got in, or the driver working outside) until a pedal is pressed
    else {
      // (a press is fresh when the pedal was up on the frame before)
      if (stop > PEDAL_UP && stopWas <= PEDAL_UP && go <= PEDAL_UP && Math.abs(carState.v) < SHIFT_V) { phys.s.gear = reversing ? 'D' : 'R'; driveCard(); stopWas = 0; return updateDrive(0); }
      if (go) { if (rolling < -0.3) ctl.brake = 1; else ctl.gas = go; }
      if (stop) ctl.brake = Math.max(ctl.brake, stop);                        // (both feet: the engine pulls against the brakes, each by how far it is pressed)
    }
    stopWas = job || parked ? 1 : stop;                                       // (parked or at a job: the pedal that wakes the car is not a fresh press for the other gear)
    // steering: the pad's travel is the whole lock at a crawl and, quicker, what takes the car to the tyres' grip there
    // (car_physics.js's steerAsk); the hand follows it in about a quarter of a second, and it returns to centre on its own
    carState.steer += (phys.steerAsk(steer, Math.abs(carState.v)) - carState.steer) * Math.min(1, dt * STEER_RATE);
    // move first (by the turn the tyres' grip allowed), then let the springs and the sand answer the ground there
    const tiltWas = sideTilt();
    carState.yaw += phys.s.yawRate * dt;
    carFwd(carState.yaw, fwd);
    carState.pos.addScaledVector(fwd, carState.v * dt);
    { const side = phys.s.slide + phys.s.vlat; if (side) { right.crossVectors(fwd, UP); carState.pos.addScaledVector(right, side * dt); } }      // sideways: sliding down a side slope too steep to hold, and the tyres' own slide in a turn
    // ground too steep across the car (past about 40 degrees it would tip): it does not drive onto it or along it, as
    // against a wall. On such ground a move that does not ease the lean is undone (driving along an even face keeps the
    // lean the same: undoing only moves that made it worse let the car drive 1.3 km along a 45 degree face, the review),
    // and of it only what the car does itself (its run and turn, and its tyres' slide in a turn): the slide down the
    // slope is gravity's and goes through, or a car sliding from a 32 degree slope onto a 45 degree face below it was
    // held at the brink for good. Steering down the slope eases the lean, so that is the way off it.
    // (A real car would roll there; the game does not roll it: a game choice.)
    { const tilt = sideTilt();
      if (tilt > 2 * geo.half * TIP && tilt > tiltWas - 1e-4) { carState.pos.addScaledVector(fwd, -carState.v * dt); carState.yaw -= phys.s.yawRate * dt; right.crossVectors(fwd, UP); carState.pos.addScaledVector(right, -phys.s.vlat * dt); carState.v = 0; phys.s.v = 0; phys.s.vyL = phys.s.r = 0; phys.s.stuck = 0; } }      // (the turn and the sideways move undone too, and not counted as stuck: it is a slope, not sand)
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
    if (hit) { const v0 = carState.v; carState.v = Math.abs(v0) > 3 ? -0.1 * v0 : 0; phys.s.v = carState.v; phys.s.vp -= v0 * 0.04; phys.s.vyL *= 0.2; phys.s.r *= 0.2; }      // (the knock takes the slide and most of the spin too)
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
      const rpm = 750 + (kmh - lo) / Math.max(1, hi - lo) * 2600 + PEDALS.gas * 400;
      needles.rpm.quaternion.copy(needleBase.rpm).multiply(qTmp.setFromAxisAngle(XAXIS, -Math.min(1, rpm / 8000) * 4.712));
    }
    // dust from the rear wheels when moving on sand
    const spinning = phys.s.slip * phys.s.thr + Math.max(0, Math.abs(phys.s.beta) - 0.12) * 2;      // wheels spinning, or the tail sliding
    puffT += dt * Math.min(1, Math.abs(carState.v) / 6 + spinning * 2);
    let softNow = 0; for (const w of phys.wheels) softNow += w.soft / 4;
    if (softNow > 0.3 && (Math.abs(carState.v) > 2 || spinning > 0.05) && puffT > 0.08) {      // dust only off the beaten ground, where there is loose sand to raise
      puffT = 0; const p = puffs[puffI++ % puffs.length];
      p.s.position.copy(carState.pos).addScaledVector(fwd, -2.3).addScaledVector(right, (puffI % 2 ? -1 : 1) * 0.8).setY(carState.pos.y + 0.35);
      p.age = 0; p.s.visible = true;
    }
  }
  const CHASE_BACK = 8.0, CHASE_UP = 2.7, CHASE_TURN = 2;      // m behind and above the car's middle; 1/s: how fast the camera's heading follows the car's (game choices; the owner: at 5.6 m and 4/s it sat very close and turned with the car)
  const ORBIT_BACK = 2, ORBIT_EASE = 2, ORBIT_TURN = 1.2, ORBIT_FAST = 3;      // s after the finger lets go before the camera turned round the car eases back behind it; 1/s how fast it does, and rad/s at most (from half a turn round it swung back at 218 degrees a second); rad/s it follows the finger at most (game choices)
  const CHASE_CAP = 5.0, CHASE_NEAR = 2.9, CHASE_CLIMB = 5, CHASE_LETGO = 4, CHASE_IN = 6;      // m over the car the camera rises at most to see over a wall, then it comes in; m from the car's middle at the nearest (its corners are 2.7 m out); m/s its climb over a wall at most; m/s it moves back out at most once a wall lets it go; m/s it comes in at most (game choices)
  let camYaw = 0, camY = null, camVy = 0, camPrevY = 0, camBack = null, camLift = 0, camPullX = 0, camPullZ = 0, camHad = false;
  let orbYaw = 0, orbNow = 0, orbIdle = 0;      // the player's own turn of the camera round the car (a finger dragged on the screen), rad: where the finger has it, and where the camera is (it follows)
  const camPrev = new THREE.Vector3();
  // where along the segment (x0, z0) to (x1, z1) it enters the box b, from 0 to 1, or 1 if it does not (the slab test;
  // no array made per call)
  function slab(p, d, lo, hi, r) {
    if (Math.abs(d) < 1e-9) return p >= lo && p <= hi;
    let a = (lo - p) / d, c = (hi - p) / d; if (a > c) { const q = a; a = c; c = q; }
    r.t0 = Math.max(r.t0, a); r.t1 = Math.min(r.t1, c); return r.t0 <= r.t1;
  }
  const SEG = { t0: 0, t1: 1 };
  function segBox(x0, z0, x1, z1, b) {
    SEG.t0 = 0; SEG.t1 = 1;
    if (!slab(x0, x1 - x0, b.x0, b.x1, SEG) || !slab(z0, z1 - z0, b.z0, b.z1, SEG)) return 1;
    return SEG.t0 > 0 ? SEG.t0 : 1;
  }
  function updateCamera(dt) {
    if (state.mode === 'walk') {
      // on foot: the walker's own eyes (first person only)
      camera.position.copy(man.pos).add(tmp.set(Math.sin(input.yaw) * 0.12, EYE, Math.cos(input.yaw) * 0.12));
      camLook.copy(camera.position).add(tmp.set(Math.sin(input.yaw) * Math.cos(-input.pitch + 0.18), Math.sin(-input.pitch + 0.18) - 0.05, Math.cos(input.yaw) * Math.cos(-input.pitch + 0.18)));
      camera.lookAt(camLook);
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
        // from behind: a set distance and height behind the car, the camera's heading following the car's with a lag
        // (it swings round in a turn, half a second behind), its height easing over bumps. (It used to ease its whole place
        // toward a point behind the car, so it fell back by the speed over the easing rate: 8 m more at 100 km/h, the owner:
        // far away and loose while moving.) 8 m from the middle is about 5.5 m behind the bumper (game choice). A finger
        // dragged across the screen turns it round the car; ORBIT_BACK s after it lets go it eases back behind. (It also
        // tilted up and down: over the porch and the room it then came down through the porch's roof and onto the room,
        // put out by its nearest side 2 m in a frame; its height is the camera's own again.)
        if (state.snap) { camYaw = carState.yaw; camY = null; orbYaw = orbNow = 0; }
        const dy = Math.atan2(Math.sin(carState.yaw - camYaw), Math.cos(carState.yaw - camYaw));
        camYaw += dy * Math.min(1, dt * CHASE_TURN);
        orbYaw = Math.atan2(Math.sin(orbYaw), Math.cos(orbYaw));      // (back the short way round)
        if (lookId === null && (orbIdle += dt) > ORBIT_BACK) {
          const ramp = Math.min(1, (orbIdle - ORBIT_BACK) / 0.5), step = orbYaw * (1 - Math.exp(-dt * ORBIT_EASE * ramp));      // (its rate rising over half a second: set off at full rate, it lurched)
          orbYaw -= Math.sign(step) * Math.min(Math.abs(step), ORBIT_TURN * ramp * dt);
        }
        const back = CHASE_BACK + Math.min(1.2, Math.abs(carState.v) * 0.03), up = CHASE_UP;
        const lookY = carState.pos.y + 1.05, cap = carState.pos.y + CHASE_CAP, nowY = camY === null ? Infinity : camY + camLift;
        // the camera's turn follows the finger's, smoothed over about 70 ms and no faster than ORBIT_FAST (flicked at 8 rad/s
        // under the porch, pushed along the room's face, the view whipped round 59 degrees a frame)
        if (lookId === null && Math.abs(orbYaw) < 1e-3 && Math.abs(orbNow) < 1e-3) orbYaw = orbNow = 0;      // (back behind: the camera's own rules alone again)
        if (state.snap || camY === null) orbNow = orbYaw;
        { const d = Math.atan2(Math.sin(orbYaw - orbNow), Math.cos(orbYaw - orbNow)) * Math.min(1, dt * 15); orbNow += Math.sign(d) * Math.min(Math.abs(d), ORBIT_FAST * dt); }
        const bx = -Math.cos(camYaw + orbNow), bz = Math.sin(camYaw + orbNow);      // (behind: the car's forward is (cos yaw, 0, -sin yaw))
        // a wall or a building between the car and the camera: up until the line from the car to the camera clears its
        // top by 0.3 m where it enters it, worked from where it enters, not from the camera's own height (worked from that
        // it rose, cleared, fell and rose again by the yard's wall, a shake of 5-7 cm three times a second; and the fixed
        // 0.6 m over the top left the car behind the wall); more than CHASE_CAP over the car, it comes in instead
        // under a roof (the porch, the car shade) it cannot rise over a building to the roof's own limit, so it comes in
        // in front of the building instead (the finger's turn swung it over the room as the car turned under the porch:
        // held over the room's top, the porch's roof hid the car 2 s)
        let capHere = cap;
        for (const r of roofs) if (lookY < r.under - 0.25 && carState.pos.x > r.x0 && carState.pos.x < r.x1 && carState.pos.z > r.z0 && carState.pos.z < r.z1) capHere = Math.min(capHere, r.under - 0.25);      // (the roofs' undersides are heights above the ground, as lookY is)
        let need = -Infinity, wantBack = back;
        for (const b of rects) {
          if (!b.h) continue;
          const top = b.h + 0.3 - lookY;      // (above the car's middle)
          if (top <= 0) continue;
          const t = segBox(carState.pos.x, carState.pos.z, carState.pos.x + bx * back, carState.pos.z + bz * back, b);
          if (t >= 1) continue;
          const at = Math.max(0.05, t) * back, h = lookY + top * back / at;      // (m from the car to where it enters; the height that sees over it from 'back')
          need = Math.max(need, Math.min(h, capHere));
          if (h > capHere) wantBack = Math.min(wantBack, at * (capHere - lookY) / top);
        }
        wantBack = Math.max(CHASE_NEAR, wantBack);
        camBack = camBack === null || state.snap ? wantBack : camBack + Math.min(CHASE_LETGO * dt, Math.max(-CHASE_IN * dt, (wantBack - camBack) * Math.min(1, dt * (wantBack < camBack ? 12 : 4))));      // (in quickly, out slowly; in no faster than CHASE_IN: at 30 fps it stepped 0.85 m in a frame)      // (and out no faster than CHASE_LETGO: let go as the car backed out from under the shade, it stepped 47 cm a frame)
        const rawX = carState.pos.x + bx * camBack, rawZ = carState.pos.z + bz * camBack;
        // never into a wall or a building below its top (0.3 m clear of it): put back out by the side it came in by, from
        // where it was the frame before, so it slides along that face; let go, the push eases off over half a second.
        // (Held at the near face along its line, it jumped up to 3 m toward the car as its line swung onto a building's
        // corner; left to ease in, a car reversing at 5 m/s took it 0.4 m inside the room.)
        if (state.snap || camY === null) { camPullX = camPullZ = 0; camHad = false; }
        const pull = Math.hypot(camPullX, camPullZ), ease = pull > 0 ? Math.max(Math.exp(-dt * 4), 1 - CHASE_LETGO * dt / pull) : 1;      // (let go no faster than CHASE_LETGO: after a slide along the tent it swooped back 30 cm a frame)
        camPos.set(rawX + camPullX * ease, 0, rawZ + camPullZ * ease);
        { const ox = camPos.x - carState.pos.x, oz = camPos.z - carState.pos.z, r = Math.hypot(ox, oz);      // (never nearer the car's middle than CHASE_NEAR while less than a metre over its roof (1.95 m): swept round under the porch it flew over the roof 0.8 m up; let go along a straight line as the finger's turn swung it back, it went through the car; higher up it may pass over the car, or it was thrown 1.1 m as it rose clear of the room beside the car)
          if (r < CHASE_NEAR && nowY < carState.pos.y + 3.0) { const k = r > 1e-3 ? CHASE_NEAR / r : 0; camPos.x = carState.pos.x + (k ? ox * k : bx * CHASE_NEAR); camPos.z = carState.pos.z + (k ? oz * k : bz * CHASE_NEAR); } }
        for (let pass = 0; pass < 2; pass++) for (const b of rects) {
          if (!b.h || nowY >= b.h + 0.3) continue;
          const x0 = b.x0 - 0.3, x1 = b.x1 + 0.3, z0 = b.z0 - 0.3, z1 = b.z1 + 0.3;
          if (camPos.x <= x0 || camPos.x >= x1 || camPos.z <= z0 || camPos.z >= z1) continue;
          const sx = !camHad ? null : camPrev.x <= x0 ? x0 : camPrev.x >= x1 ? x1 : null, sz = !camHad ? null : camPrev.z <= z0 ? z0 : camPrev.z >= z1 ? z1 : null;
          if (sx !== null && (sz === null || Math.abs(camPos.x - sx) <= Math.abs(camPos.z - sz))) camPos.x = sx;
          else if (sz !== null) camPos.z = sz;
          else { const d = Math.min(camPos.x - x0, x1 - camPos.x, camPos.z - z0, z1 - camPos.z); if (d === camPos.x - x0) camPos.x = x0; else if (d === x1 - camPos.x) camPos.x = x1; else if (d === camPos.z - z0) camPos.z = z0; else camPos.z = z1; }      // (it was inside already: out by the nearest side)
        }
        camPullX = camPos.x - rawX; camPullZ = camPos.z - rawZ;
        // a roof the line from the car to the camera passes under: the camera low enough for that line to clear the roof's
        // underside by 0.25 m where it leaves the roof (with the car under the porch, or just in front of it, the camera
        // rose over the porch and saw only its roof; held at the room's face under it, it climbed through it)
        let ceil = Infinity;
        for (const r of roofs) {
          if (lookY >= r.under - 0.25) continue;
          SEG.t0 = 0; SEG.t1 = 1;
          if (!slab(carState.pos.x, camPos.x - carState.pos.x, r.x0, r.x1, SEG) || !slab(carState.pos.z, camPos.z - carState.pos.z, r.z0, r.z1, SEG)) continue;
          ceil = Math.min(ceil, lookY + (r.under - 0.25 - lookY) / Math.max(SEG.t1, 0.05));
        }
        need = Math.min(need, ceil);
        // the car's climb, smoothed: the height eases at 6/s, so it lagged a climb by its rate over 6 (0.6 m over the car's base
        // on a 25 degree slope at 70 km/h, the car hiding the slope ahead); led by that much, it keeps its height over the car
        if (camY === null) { camVy = 0; camPrevY = carState.pos.y; }
        if (dt > 0) { camVy += ((carState.pos.y - camPrevY) / dt - camVy) * Math.min(1, dt * 4); camPrevY = carState.pos.y; }
        const want = Math.min(ceil, Math.max(carState.pos.y + up + Math.max(-2, Math.min(2, camVy / 6)), ground(camPos.x, camPos.z) + 1.0));
        camY = camY === null ? want : camY + Math.min((want - camY) * Math.min(1, dt * 6), (Math.max(0, camVy) + CHASE_CLIMB) * dt);      // (up no faster than the car climbs and CHASE_CLIMB more: let out from under a roof it rose a metre a frame)
        // the lift over the wall eases on top of that, no faster than CHASE_CLIMB (at 14/s it rose 74 cm in one frame as
        // the room came between, 1.5 m at 30 fps)
        const lift = Math.max(0, need - camY), dl = (lift - camLift) * Math.min(1, dt * 8), down = camY + camLift > ceil ? 10 : CHASE_CLIMB;      // (above a roof's limit it comes down faster)
        camLift = state.snap ? lift : camLift + Math.max(-down * dt, Math.min(CHASE_CLIMB * dt, dl));
        // over a building's top it stays over it until it is off it (it came down onto the room and was put out by its
        // nearest side, 2.1 m in a frame)
        if (camHad && !state.snap) {
          for (const b of rects) {
            if (!b.h || camPrev.y < b.h + 0.3 - 1e-6 || camPos.x <= b.x0 - 0.3 || camPos.x >= b.x1 + 0.3 || camPos.z <= b.z0 - 0.3 || camPos.z >= b.z1 + 0.3) continue;
            camLift = Math.max(camLift, b.h + 0.3 - camY);
          }
          for (const r of roofs) {      // (and over a roof: held over the room, it came down through the porch's roof as the car turned under it)
            if (camPrev.y < r.top + 0.25 - 1e-6 || camPos.x <= r.x0 - 0.3 || camPos.x >= r.x1 + 0.3 || camPos.z <= r.z0 - 0.3 || camPos.z >= r.z1 + 0.3) continue;
            camLift = Math.max(camLift, r.top + 0.25 - camY);
          }
        }
        camY = Math.max(camY, ground(camPos.x, camPos.z) + 0.6);      // (never into the sand, whatever its climb's limit: swung round beside a steep slope it went 2 m under)
        camPos.y = camY + camLift; camera.position.copy(camPos); camPrev.copy(camPos); camHad = true;
        camLook.copy(carState.pos).addScaledVector(carFwd(carState.yaw + orbNow, tmp), 2.2).add(tmp.set(0, 1.05, 0)); camera.lookAt(camLook);      // (a little ahead of the car, turned with the finger's turn)
        // is the camera where ours_game.py's eyes saw the car from (behind it within 50 degrees, 1.4-5 m up, 8 and 9.2 m
        // away, in the car's own frame)? Outside that (turned round by the finger, facing down a dune, high over the room,
        // come in close) faces the eyes never saw can show, so farm.html then draws all of the car
        car.updateMatrixWorld(); car.worldToLocal(tmp.copy(camPos));
        const r = Math.hypot(tmp.x, tmp.z);
        state.fan = tmp.y >= 1.4 && tmp.y <= 5.1 && r >= 7.4 && r <= 9.8 && -tmp.x >= r * Math.cos(50 * Math.PI / 180);
      }
    }
    state.snap = false;
    for (const p of puffs) if (p.s.visible) { p.age += dt; const t = p.age / p.life; p.s.scale.setScalar(0.7 + t * 2.0); p.s.position.y += dt * 0.35; p.s.material.opacity = 0.38 * (1 - t); if (t >= 1) p.s.visible = false; }
  }

  function start() {
    state.on = true; state.mode = 'walk'; ui.hidden = false; document.body.classList.add('playing'); state.snap = true; viewBtn.hidden = true;
    if (phone) { phone.close(); phone.setPlay(true); phoneBtn.hidden = false; }
    steerPad.hidden = pedalsEl.hidden = carRow.hidden = true; nearDoor = false; doorButtons();
    man.pos.y = ground(man.pos.x, man.pos.z); input.yaw = man.heading; man.way = undefined;
    camera.near = 0.08; camera.updateProjectionMatrix();
  }
  function stop() {
    if (phone) { phone.close(); phone.setPlay(false); }
    state.on = false; ui.hidden = true; document.body.classList.remove('playing'); stickId = lookId = null; stick.hidden = true; knob.style.transform = ''; input.mx = input.mz = 0; input.run = false; man.speed = 0; keys.clear(); pedal.gas = pedal.brake = 0; pad.reset();
    cabin.visible = false;
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
    if (!state.on) return false;
    if (state.mode === 'walk') updateWalk(dt); else updateDrive(dt);
    updateCamera(dt);
    return true;
  }
  if (rigged) setTimeout(loadCabin, 4000);
  return { start, stop, update, model, get on() { return state.on; }, focus: () => (state.mode === 'drive' ? carState.pos : man.pos), debug: { man, carState, enter, exit, toggleView, keys, state, snap: () => { state.snap = true; }, orbit: (yaw, el, hold) => { orbYaw = yaw; orbIdle = hold ? -Infinity : 0; }, get orbNow() { return orbNow; } } };
}
