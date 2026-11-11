// The farm world: ground, vegetation, roads and buildings at real size.
// Coordinates in metres: x east, z south, y up. Everything repeated is instanced.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export function mulberry(a) { return () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const rand = mulberry(1108);
const R = (a, b) => a + (b - a) * rand();
export function noise2(x, y) {
  const h = (i, j) => { const s = Math.sin(i * 127.1 + j * 311.7) * 43758.5453; return s - Math.floor(s); };
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  const L = THREE.MathUtils.lerp;
  return L(L(h(xi, yi), h(xi + 1, yi), u), L(h(xi, yi + 1), h(xi + 1, yi + 1), u), v);
}
const fbm = (x, y) => noise2(x, y) * 0.55 + noise2(x * 2.1 + 7, y * 2.1 - 3) * 0.3 + noise2(x * 4.3 - 11, y * 4.3 + 5) * 0.15;
function canvasTex(w, h, draw, srgb = true) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}
const M4 = () => new THREE.Matrix4();
const V = (x, y, z) => new THREE.Vector3(x, y, z);
const UP = V(0, 1, 0);


// three crossed alpha cards: how real-time games draw grass, bushes and foliage
function cardCluster(w, h, n = 3, upNormals = true) {
  const pos = [], uv = [], nor = [], idx = []; let off = 0;
  for (let i = 0; i < n; i++) {
    const g = new THREE.PlaneGeometry(w, h); g.translate(0, h / 2, 0); g.rotateY(i * Math.PI / n);
    pos.push(...g.attributes.position.array); uv.push(...g.attributes.uv.array);
    const c = g.attributes.position.count;
    for (let k = 0; k < c; k++) nor.push(...(upNormals ? [0, 1, 0] : [Math.sin(i * Math.PI / n), 0.6, Math.cos(i * Math.PI / n)]));
    idx.push(...Array.from(g.index.array, (v) => v + off)); off += c;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3)); g.setIndex(idx);
  return g;
}
const grassTexture = () => canvasTex(128, 128, (g, w, h) => {
  g.clearRect(0, 0, w, h);
  for (let i = 0; i < 26; i++) {
    const x = w / 2 + (rand() - 0.5) * w * 0.35, lean = (rand() - 0.5) * 70, top = h * (0.08 + rand() * 0.55);
    const dry = rand();
    g.strokeStyle = dry < 0.45 ? `rgb(${150 + rand() * 40},${140 + rand() * 30},${80 + rand() * 25})` : `rgb(${110 + rand() * 40},${135 + rand() * 35},${60 + rand() * 25})`;
    g.lineWidth = 0.9 + rand() * 1.2; g.lineCap = 'round';
    g.beginPath(); g.moveTo(x, h); g.quadraticCurveTo(x + lean * 0.3, (h + top) / 2, x + lean, top); g.stroke();
  }
});
const bushTexture = () => canvasTex(256, 256, (g, w, h) => {
  g.clearRect(0, 0, w, h);
  const branch = (x, y, a, len, depth) => {
    const x2 = x + Math.cos(a) * len, y2 = y - Math.sin(a) * len;
    g.strokeStyle = `rgba(${95 + rand() * 25},${80 + rand() * 20},${60 + rand() * 15},1)`; g.lineWidth = Math.max(0.8, depth * 0.9);
    g.beginPath(); g.moveTo(x, y); g.lineTo(x2, y2); g.stroke();
    if (depth <= 1) {
      for (let k = 0; k < 7; k++) { g.fillStyle = `rgba(${85 + rand() * 40},${100 + rand() * 35},${55 + rand() * 25},0.95)`; g.beginPath(); g.ellipse(x2 + (rand() - 0.5) * 14, y2 + (rand() - 0.5) * 14, 2 + rand() * 3, 1.5 + rand() * 2, rand() * 3, 0, 6.28); g.fill(); }
      return;
    }
    const n = 2 + Math.floor(rand() * 2);
    for (let i = 0; i < n; i++) branch(x2, y2, a + (rand() - 0.5) * 1.3, len * (0.62 + rand() * 0.2), depth - 1);
  };
  for (let i = 0; i < 7; i++) branch(w / 2 + (rand() - 0.5) * 30, h - 2, Math.PI / 2 + (rand() - 0.5) * 1.6, 46 + rand() * 20, 4);
});
const tamariskTexture = () => canvasTex(256, 256, (g, w, h) => {
  g.clearRect(0, 0, w, h);
  for (let i = 0; i < 260; i++) {
    const cx = w / 2 + (rand() - 0.5) * w * 0.85, cy = h * (0.08 + rand() * 0.55), len = 30 + rand() * 70, sway = (rand() - 0.5) * 30;
    const r = 85 + rand() * 30, gg = 100 + rand() * 30, b = 78 + rand() * 20;
    g.strokeStyle = `rgba(${r},${gg},${b},${0.75 + rand() * 0.25})`; g.lineWidth = 1 + rand() * 1.6; g.lineCap = 'round';
    g.beginPath(); g.moveTo(cx, cy); g.quadraticCurveTo(cx + sway, cy + len * 0.5, cx + sway * 0.6, cy + len); g.stroke();
  }
});

// ------------------------------------------------------------ layout (real metres)
// meshes laid on the ground that must follow the real terrain beyond the flat yard
// cell sizes (game choice, measured 2026-11-11): one draw per cell, so larger cells mean fewer draws. With the bands taken
// from each cell's nearest edge, 50 m grass and stone cells and 160 m bush cells cut the ground cover from 124 draws to
// 45 in the drone view, for 10k more triangles of cheap cards.
const GRASS_CELL = 50, BUSH_CELL = 160, STONE_CELL = 50;
export const DRAPE = [];
// ground cover is cut into cells; each cell draws all, part or none of its instances by distance
export const SCATTER = [];
function scatterCells(geo, mat, items, { cell = 25, bands, cast = false, receive = true, shadowDist = 0 }) {
  const buckets = new Map();
  for (const it of items) {
    const key = Math.floor(it.x / cell) + ',' + Math.floor(it.z / cell);
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key).push(it);
  }
  const group = new THREE.Group();
  for (const list of buckets.values()) {
    // shuffle so that any prefix is an even sample of the cell
    for (let i = list.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [list[i], list[j]] = [list[j], list[i]]; }
    const m = new THREE.InstancedMesh(geo, mat, list.length);
    let cx = 0, cz = 0;
    list.forEach((it, i) => { m.setMatrixAt(i, it.m); if (it.c) m.setColorAt(i, it.c); cx += it.x; cz += it.z; });
    cx /= list.length; cz /= list.length;
    let r = 0; for (const it of list) r = Math.max(r, Math.hypot(it.x - cx, it.z - cz));
    m.castShadow = cast; m.receiveShadow = receive;
    m.computeBoundingSphere();
    group.add(m);
    SCATTER.push({ m, n: list.length, x: cx, z: cz, r, bands, cast, shadowDist });
  }
  return group;
}
// bands: [[distance, share of instances drawn], ...], nothing beyond the last band. The distance is to the cell's
// nearest edge, not its middle: every instance is drawn at least as densely as its own distance asks, so the cells
// can be large (one draw each) without the cover thinning near the viewer.
export function updateScatter(cam, shadowCenter = cam) {
  for (const c of SCATTER) {
    const dx = cam.x - c.x, dz = cam.z - c.z, edge = Math.max(0, Math.sqrt(dx * dx + dz * dz) - c.r), dy = cam.y * 0.5;
    const d = Math.sqrt(edge * edge + dy * dy);      // (not Math.hypot: it left garbage behind on every call, 300 cells a frame)
    let share = 0;
    for (let i = 0; i < c.bands.length; i++) if (d < c.bands[i][0]) { share = c.bands[i][1]; break; }
    const n = Math.round(c.n * share);
    c.m.visible = n > 0;
    c.m.count = n;
    if (c.cast) { const sx = shadowCenter.x - c.x, sz = shadowCenter.z - c.z; c.m.castShadow = Math.sqrt(sx * sx + sz * sz) - c.r < c.shadowDist; }   // only cells that reach into the shadow area cast
  }
}
export function drapeOnTerrain(heightAt) {
  for (const m of DRAPE) {
    const p = m.geometry.attributes.position;
    for (let i = 0; i < p.count; i++) p.setY(i, p.getY(i) + heightAt(p.getX(i), p.getZ(i)));
    p.needsUpdate = true; m.geometry.computeVertexNormals(); m.geometry.computeBoundingSphere();
  }
}
export const VEHICLES = [
  { model: 'shas', x: 14.4, z: 6.8, rot: Math.PI / 2 },
  { model: 'suv', x: 18.6, z: 6.8, rot: Math.PI / 2 },
  { model: 'shas', x: 26.4, z: -14.2, rot: -Math.PI / 2 + 0.12, tint: '#e2d3b4', hay: true },      // beside the feed shed, clear of its posts (at x 29.6 the shed's post at 28.8 stood through it)
];
export const LAYOUT = {
  compound: { x0: -40, x1: 44, z0: -52, z1: 14 }, gate: { x0: 20, x1: 28 },
  pens: {
    main: { x0: -32, x1: -2, z0: -46, z1: -24, name: 'شبك النوق' },
    young: { x0: -2, x1: 18, z0: -46, z1: -24, name: 'شبك المفاريد' },
    calves: { x0: -32, x1: -17, z0: -20, z1: -7, name: 'الحيران' },
    bull: { x0: -15, x1: -7, z0: -20, z1: -12, name: 'الفحل' },
    sick: { x0: -5, x1: 3, z0: -20, z1: -12, name: 'العزل' },
    spare: { x0: 5, x1: 13, z0: -20, z1: -12, name: '' },
  },
  graze: { x0: -300, x1: -170, z0: 196, z1: 292 },
  camp: { x: -232, z: 248 },
  roadZ: 112,
};
const inCompound = (x, z, m = 0) => x > LAYOUT.compound.x0 - m && x < LAYOUT.compound.x1 + m && z > LAYOUT.compound.z0 - m && z < LAYOUT.compound.z1 + m;

export function buildWorld(scene, renderer, sandTex) {
  const aniso = Math.min(4, renderer.capabilities.getMaxAnisotropy());
  sandTex.anisotropy = aniso;
  const metal = new THREE.MeshStandardMaterial({ color: '#aeb2b4', metalness: 0.85, roughness: 0.38 });

  // ---------- ground: near detailed patch with colour variation, far dunes
  const tint = (x, z) => {
    const n = fbm(x / 60, z / 60), m = fbm(x / 18 + 40, z / 18 - 9);
    const c = new THREE.Color(1, 1, 1);
    c.lerp(new THREE.Color(1.0, 0.86, 0.74), THREE.MathUtils.smoothstep(n, 0.45, 0.75) * 0.8);   // redder sand
    c.lerp(new THREE.Color(1.1, 1.07, 1.02), THREE.MathUtils.smoothstep(m, 0.62, 0.85) * 0.6);   // pale drift sand
    const g = grassDensity(x, z);
    c.lerp(new THREE.Color(0.88, 0.92, 0.74), g * 0.55);                                           // green after the Wasm rain
    if (inCompound(x, z, 2)) c.multiplyScalar(0.9);
    return c;
  };
  // the ground itself is the real terrain (terrain.js); only decals and dressing are added here
  // compacted ground inside the compound and in the pens
  const dirt = (x0, z0, x1, z1, color, opacity) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(x1 - x0, z1 - z0).rotateX(-Math.PI / 2),
      new THREE.MeshStandardMaterial({ color, roughness: 1, transparent: true, opacity, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -1 }));
    m.position.set((x0 + x1) / 2, 0.02, (z0 + z1) / 2); m.receiveShadow = true; scene.add(m); return m;
  };
  dirt(LAYOUT.compound.x0, LAYOUT.compound.z0, LAYOUT.compound.x1, LAYOUT.compound.z1, '#8c6a47', 0.16);
  const penFloor = canvasTex(256, 256, (g, w, h) => {
    g.fillStyle = 'rgba(96,66,40,0.55)'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(${200 + rand() * 40},${170 + rand() * 40},${80 + rand() * 30},${0.35 + rand() * 0.4})`; g.save(); g.translate(rand() * w, rand() * h); g.rotate(rand() * 6.28); g.fillRect(0, 0, 6 + rand() * 8, 1.2); g.restore(); }
    for (let i = 0; i < 220; i++) { g.fillStyle = `rgba(45,30,18,${0.4 + rand() * 0.4})`; g.beginPath(); g.ellipse(rand() * w, rand() * h, 2 + rand() * 2, 1.5 + rand() * 1.5, rand() * 3, 0, 6.28); g.fill(); }
  });
  penFloor.name = 'penFloor'; penFloor.wrapS = penFloor.wrapT = THREE.RepeatWrapping;
  for (const p of Object.values(LAYOUT.pens)) {
    const t = penFloor.clone(); t.needsUpdate = true; t.repeat.set((p.x1 - p.x0) / 6, (p.z1 - p.z0) / 6);
    const m = new THREE.Mesh(new THREE.PlaneGeometry(p.x1 - p.x0, p.z1 - p.z0).rotateX(-Math.PI / 2),
      new THREE.MeshStandardMaterial({ map: t, transparent: true, roughness: 1, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 }));
    m.position.set((p.x0 + p.x1) / 2, 0.03, (p.z0 + p.z1) / 2); m.receiveShadow = true; scene.add(m);
  }

  // ---------- roads: the asphalt road, the graded track to the gate, the farm lanes
  const asphaltTex = canvasTex(64, 512, (g, w, h) => {
    g.fillStyle = '#3b3a39'; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 4000; i++) { const v = 40 + rand() * 40; g.fillStyle = `rgba(${v},${v},${v},0.5)`; g.fillRect(rand() * w, rand() * h, 1, 1); }
    g.fillStyle = '#e9c341'; g.fillRect(3, 0, 2, h); g.fillRect(w - 5, 0, 2, h);
    g.fillStyle = '#efefe8'; for (let y = 0; y < h; y += 64) g.fillRect(w / 2 - 1, y, 2, 30);
  });
  asphaltTex.name = 'asphalt'; asphaltTex.wrapT = THREE.RepeatWrapping;
  // the road runs 6 km east-west and follows the real ground (draped once the terrain loads)
  const road = new THREE.Mesh(new THREE.PlaneGeometry(9, 6000, 1, 600).rotateX(-Math.PI / 2).rotateY(Math.PI / 2).translate(0, 0.08, LAYOUT.roadZ),
    new THREE.MeshStandardMaterial({ map: asphaltTex, roughness: 0.92 }));
  asphaltTex.repeat.set(1, 6000 / 40);
  road.receiveShadow = true; road.userData.keep = true; scene.add(road); DRAPE.push(road);
  const shoulder = new THREE.Mesh(new THREE.PlaneGeometry(6000, 15, 600, 1).rotateX(-Math.PI / 2).translate(0, 0.05, LAYOUT.roadZ),
    new THREE.MeshStandardMaterial({ color: '#a98463', roughness: 1, transparent: true, opacity: 0.35, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -1 }));
  shoulder.userData.keep = true; scene.add(shoulder); DRAPE.push(shoulder);
  const trackTex = canvasTex(64, 256, (g, w, h) => {
    g.fillStyle = 'rgba(120,86,56,0.55)'; g.fillRect(0, 0, w, h);
    for (const x of [w * 0.28, w * 0.72]) { const gr = g.createLinearGradient(x - 8, 0, x + 8, 0); gr.addColorStop(0, 'rgba(70,48,28,0)'); gr.addColorStop(0.5, 'rgba(70,48,28,0.55)'); gr.addColorStop(1, 'rgba(70,48,28,0)'); g.fillStyle = gr; g.fillRect(x - 8, 0, 16, h); }
    for (let i = 0; i < 600; i++) { g.fillStyle = `rgba(255,240,220,${rand() * 0.15})`; g.fillRect(rand() * w, rand() * h, 2, 2); }
  });
  trackTex.name = 'track'; trackTex.wrapT = THREE.RepeatWrapping;
  // the wheel tracks, all one mesh: a flat see-through decal, drawn in one pass (three.js draws a see-through two-sided
  // material twice, back faces then front, and rebuilds its program state at each; a decal on the ground shows one side)
  const tracks = [];
  const ribbon = (pts, width) => {
    const curve = new THREE.CatmullRomCurve3(pts.map(([x, z]) => V(x, 0, z)));
    const n = Math.max(8, Math.round(curve.getLength() / 2)), pos = [], uv = [], idx = [];
    for (let i = 0; i <= n; i++) {
      const t = i / n, p = curve.getPointAt(t), d = curve.getTangentAt(t), s = V(-d.z, 0, d.x).multiplyScalar(width / 2);
      pos.push(p.x + s.x, 0.05, p.z + s.z, p.x - s.x, 0.05, p.z - s.z);
      uv.push(0, t * curve.getLength() / 10, 1, t * curve.getLength() / 10);
      if (i < n) idx.push(i * 2, i * 2 + 1, i * 2 + 2, i * 2 + 1, i * 2 + 3, i * 2 + 2);
    }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.setIndex(idx); g.computeVertexNormals();
    tracks.push(g);
  };
  ribbon([[24, 10], [24, 40], [27, 70], [30, 95], [30, LAYOUT.roadZ - 4]], 6);
  ribbon([[24, 14], [24, -2], [10, -3], [-34, -3]], 5);
  ribbon([[24, -3], [36, -3], [37, -30], [36, -48]], 5);
  ribbon([[24, 18], [0, 60], [-60, 120], [-130, 170], [-196, 226], [-226, 244]], 3.6);   // the track out to the grazing ground (about 330 m)
  {
    const m = new THREE.Mesh(mergeGeometries(tracks, false), new THREE.MeshStandardMaterial({ map: trackTex, transparent: true, depthWrite: false, roughness: 1, polygonOffset: true, polygonOffsetFactor: -3, side: THREE.DoubleSide, forceSinglePass: true }));
    m.receiveShadow = true; scene.add(m); tracks.forEach((g) => g.dispose());
  }

  // ---------- the camel yard wall: corrugated "shinko" sheets on steel posts, a double gate
  {
    const sheet = canvasTex(256, 64, (g, w, h) => { g.fillStyle = '#d9cfbd'; g.fillRect(0, 0, w, h); for (let x = 0; x < w; x += 8) { const gr = g.createLinearGradient(x, 0, x + 8, 0); gr.addColorStop(0, 'rgba(0,0,0,0.10)'); gr.addColorStop(0.5, 'rgba(255,255,255,0.16)'); gr.addColorStop(1, 'rgba(0,0,0,0.10)'); g.fillStyle = gr; g.fillRect(x, 0, 8, h); } for (let i = 0; i < 260; i++) { g.fillStyle = `rgba(150,110,70,${rand() * 0.12})`; g.fillRect(rand() * w, h - rand() * 18, 3 + rand() * 6, 2); } });
    sheet.name = 'sheet'; sheet.wrapS = THREE.RepeatWrapping;
    const C = LAYOUT.compound, G = LAYOUT.gate, H = 2.1;
    const wallSeg = (ax, az, bx, bz) => {
      const len = Math.hypot(bx - ax, bz - az), t = sheet.clone(); t.needsUpdate = true; t.repeat.set(len / 4, 1);
      const m = new THREE.Mesh(new THREE.BoxGeometry(len, H, 0.05), new THREE.MeshStandardMaterial({ map: t, metalness: 0.35, roughness: 0.55 }));
      m.position.set((ax + bx) / 2, H / 2, (az + bz) / 2); m.rotation.y = -Math.atan2(bz - az, bx - ax);
      m.castShadow = m.receiveShadow = true; scene.add(m);
      const n = Math.round(len / 3);
      for (let i = 0; i <= n; i++) { const post = new THREE.Mesh(new THREE.BoxGeometry(0.08, H + 0.15, 0.08), metal); post.position.set(ax + (bx - ax) * i / n, (H + 0.15) / 2, az + (bz - az) * i / n); scene.add(post); }
    };
    wallSeg(C.x0, C.z0, C.x1, C.z0); wallSeg(C.x1, C.z0, C.x1, C.z1); wallSeg(C.x0, C.z0, C.x0, C.z1);
    wallSeg(C.x0, C.z1, G.x0, C.z1); wallSeg(G.x1, C.z1, C.x1, C.z1);
    for (const [x0, rot] of [[G.x0, -0.9], [G.x1, Math.PI + 0.9]]) {   // two gate leaves, swung open
      const leaf = new THREE.Group(); leaf.position.set(x0, 0, C.z1); leaf.rotation.y = rot;
      const frame = new THREE.Mesh(new THREE.BoxGeometry(4, 0.08, 0.08), metal);
      for (const y of [0.15, 1.0, 1.95]) { const f = frame.clone(); f.position.set(2, y, 0); leaf.add(f); }
      for (let i = 0; i <= 10; i++) { const bar = new THREE.Mesh(new THREE.BoxGeometry(0.04, 1.85, 0.04), metal); bar.position.set(i * 0.4, 1.05, 0); leaf.add(bar); }
      leaf.traverse((n) => { if (n.isMesh) n.castShadow = true; }); scene.add(leaf);
    }
  }

  // ---------- pens: galvanized pipe, mesh panels, gates, troughs, shades
  const meshTex = canvasTex(128, 128, (g, w, h) => { g.clearRect(0, 0, w, h); g.strokeStyle = 'rgba(190,195,198,1)'; g.lineWidth = 2.2; for (let i = 0; i <= w; i += 16) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, h); g.stroke(); g.beginPath(); g.moveTo(0, i); g.lineTo(w, i); g.stroke(); } });
  meshTex.name = 'mesh'; meshTex.wrapS = meshTex.wrapT = THREE.RepeatWrapping;
  const panelMat = new THREE.MeshStandardMaterial({ map: meshTex, alphaTest: 0.4, side: THREE.DoubleSide, metalness: 0.7, roughness: 0.45 });
  const posts = [], rails = [], panels = [];
  const penFence = (p, gateSide) => {
    const c = [[p.x0, p.z0], [p.x1, p.z0], [p.x1, p.z1], [p.x0, p.z1], [p.x0, p.z0]];
    for (let s = 0; s < 4; s++) {
      const [ax, az] = c[s], [bx, bz] = c[s + 1], len = Math.hypot(bx - ax, bz - az), n = Math.max(1, Math.round(len / 2.5));
      for (let i = 0; i < n; i++) {
        const a = V(ax + (bx - ax) * i / n, 0, az + (bz - az) * i / n), b = V(ax + (bx - ax) * (i + 1) / n, 0, az + (bz - az) * (i + 1) / n);
        posts.push(a);
        const gate = s === gateSide && i === Math.floor(n / 2);
        rails.push([a.clone().setY(1.75), b.clone().setY(1.75)], [a.clone().setY(0.2), b.clone().setY(0.2)]);
        if (!gate) { rails.push([a.clone().setY(0.95), b.clone().setY(0.95)]); panels.push([a, b]); }
        else { rails.push([a.clone().setY(0.6), b.clone().setY(0.6)], [a.clone().setY(1.25), b.clone().setY(1.25)]); }
      }
    }
  };
  for (const [k, p] of Object.entries(LAYOUT.pens)) penFence(p, 2);
  {
    const pg = new THREE.CylinderGeometry(0.05, 0.055, 1.85, 8); pg.translate(0, 0.92, 0);
    const pm = new THREE.InstancedMesh(pg, metal, posts.length); posts.forEach((p, i) => pm.setMatrixAt(i, M4().makeTranslation(p.x, 0, p.z)));
    pm.castShadow = true; scene.add(pm);
    const rg = new THREE.CylinderGeometry(0.028, 0.028, 1, 6), rm = new THREE.InstancedMesh(rg, metal, rails.length);
    rails.forEach(([a, b], i) => { const d = b.clone().sub(a); rm.setMatrixAt(i, M4().compose(a.clone().add(b).multiplyScalar(0.5), new THREE.Quaternion().setFromUnitVectors(UP, d.clone().normalize()), V(1, d.length(), 1))); });
    rm.castShadow = true; scene.add(rm);
    const plg = new THREE.PlaneGeometry(1, 1); plg.translate(0, 0.5, 0);
    const plm = new THREE.InstancedMesh(plg, panelMat, panels.length);
    panels.forEach(([a, b], i) => { const d = b.clone().sub(a); plm.setMatrixAt(i, M4().compose(a.clone().add(b).multiplyScalar(0.5).setY(0.2), new THREE.Quaternion().setFromAxisAngle(UP, Math.atan2(d.x, d.z) - Math.PI / 2), V(d.length(), 1.55, 1))); });
    plm.castShadow = true; scene.add(plm);
  }
  // feeding troughs (concrete) with alfalfa along the south fence of the big pens
  const hayTex = canvasTex(128, 64, (g, w, h) => { g.fillStyle = '#9da34f'; g.fillRect(0, 0, w, h); for (let i = 0; i < 500; i++) { g.strokeStyle = `rgba(${120 + rand() * 90},${130 + rand() * 70},${50 + rand() * 30},0.7)`; g.beginPath(); const x = rand() * w, y = rand() * h; g.moveTo(x, y); g.lineTo(x + 5 + rand() * 9, y + (rand() - 0.5) * 3); g.stroke(); } });
  hayTex.name = 'hay';
  const concrete = new THREE.MeshStandardMaterial({ color: '#bdb5a8', roughness: 0.95 });
  for (const p of [LAYOUT.pens.main, LAYOUT.pens.young, LAYOUT.pens.calves]) {
    const len = (p.x1 - p.x0) * 0.6, cx = (p.x0 + p.x1) / 2 - (p.x1 - p.x0) * 0.12, cz = p.z1 - 0.9;
    const t = new THREE.Mesh(new THREE.BoxGeometry(len, 0.55, 0.75), concrete); t.position.set(cx, 0.28, cz); t.castShadow = t.receiveShadow = true; scene.add(t);
    const hay = new THREE.Mesh(new THREE.PlaneGeometry(len - 0.2, 0.55).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: hayTex, roughness: 1 })); hay.position.set(cx, 0.5, cz); scene.add(hay);
  }
  const shadeMat = new THREE.MeshStandardMaterial({ color: '#2c4434', roughness: 0.92, side: THREE.DoubleSide });
  const shade = (cx, cz, w, d) => {
    const cloth = new THREE.PlaneGeometry(w, d, 24, 10); cloth.rotateX(-Math.PI / 2);
    const p = cloth.attributes.position; for (let i = 0; i < p.count; i++) { const sx = p.getX(i) / (w / 2), sz = p.getZ(i) / (d / 2); p.setY(i, -0.16 * (1 - sx * sx) * (1 - sz * sz)); }
    cloth.computeVertexNormals();
    const m = new THREE.Mesh(cloth, shadeMat); m.position.set(cx, 3.2, cz); m.castShadow = m.receiveShadow = true; scene.add(m);
    const pg = new THREE.CylinderGeometry(0.07, 0.07, 3.2, 8); pg.translate(0, 1.6, 0);
    const nx = Math.max(2, Math.round(w / 5) + 1);
    for (let i = 0; i < nx; i++) for (const sz of [-1, 1]) { const post = new THREE.Mesh(pg, metal); post.position.set(cx - w / 2 + w * i / (nx - 1), 0, cz + sz * d / 2); post.castShadow = true; scene.add(post); }
    const beam = new THREE.Mesh(new THREE.BoxGeometry(w, 0.12, 0.12), metal);
    for (const sz of [-1, 1]) { const b = beam.clone(); b.position.set(cx, 3.15, cz + sz * d / 2); scene.add(b); }
  };
  shade(-17, -40.5, 22, 8); shade(8, -41, 14, 7); shade(-24.5, -16.5, 12, 5); shade(-11, -18, 6, 3.5);

  // ---------- services: elevated water tank, feed hangar, cabin, generator
  {
    const legs = new THREE.CylinderGeometry(0.09, 0.09, 4.2, 8); legs.translate(0, 2.1, 0);
    for (const [dx, dz] of [[-1, -1], [1, -1], [1, 1], [-1, 1]]) { const l = new THREE.Mesh(legs, metal); l.position.set(30 + dx * 1.4, 0, -40 + dz * 1.4); l.castShadow = true; scene.add(l); }
    const deck = new THREE.Mesh(new THREE.BoxGeometry(3.4, 0.15, 3.4), metal); deck.position.set(30, 4.2, -40); deck.castShadow = true; scene.add(deck);
    const tank = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 1.55, 2.6, 40), new THREE.MeshStandardMaterial({ color: '#ece8e0', roughness: 0.55 }));
    tank.position.set(30, 5.6, -40); tank.castShadow = tank.receiveShadow = true; scene.add(tank);
    const pipe = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 1, 8), new THREE.MeshStandardMaterial({ color: '#2f4f6f', roughness: 0.6 }));
    const a = V(30, 0.15, -40), b = V(18.5, 0.15, -30); const d = b.clone().sub(a);
    pipe.position.copy(a.clone().add(b).multiplyScalar(0.5)); pipe.quaternion.setFromUnitVectors(UP, d.clone().normalize()); pipe.scale.y = d.length(); scene.add(pipe);
    for (const [x, z, rot] of [[17.4, -32, 0], [-2.6, -35, 0]]) {
      const tr = new THREE.Mesh(new THREE.BoxGeometry(0.75, 0.55, 5), metal); tr.position.set(x, 0.28, z); tr.rotation.y = rot; tr.castShadow = true; scene.add(tr);
      const w = new THREE.Mesh(new THREE.PlaneGeometry(0.6, 4.85).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: '#3d5b57', roughness: 0.05 })); w.position.set(x, 0.5, z); scene.add(w);
    }
  }
  {
    const shed = new THREE.Group(); shed.position.set(32, 0, -21);
    const roof = new THREE.Mesh(new THREE.BoxGeometry(7, 0.08, 13), new THREE.MeshStandardMaterial({ color: '#cfc8bb', metalness: 0.5, roughness: 0.5 }));
    roof.position.set(0, 3.6, 0); roof.rotation.z = 0.08; roof.castShadow = roof.receiveShadow = true; shed.add(roof);
    for (const x of [-3.2, 3.2]) for (const z of [-6.2, 0, 6.2]) { const pst = new THREE.Mesh(new THREE.BoxGeometry(0.12, 3.6, 0.12), metal); pst.position.set(x, 1.8 + (x > 0 ? -0.25 : 0.25), z); pst.castShadow = true; shed.add(pst); }
    scene.add(shed);
    const bales = new THREE.InstancedMesh(new THREE.BoxGeometry(1.0, 0.42, 0.5), new THREE.MeshStandardMaterial({ map: hayTex, roughness: 1 }), 48);
    let i = 0; for (let row = 0; row < 3; row++) for (let col = 0; col < 8; col++) for (let lay = 0; lay < 2; lay++) bales.setMatrixAt(i++, M4().makeTranslation(30.2 + lay * 0.52, 0.21 + row * 0.42, -25 + col * 1.02).multiply(M4().makeRotationY(Math.PI / 2)));
    bales.castShadow = bales.receiveShadow = true; scene.add(bales);
    const sacks = new THREE.InstancedMesh(new RoundedBoxGeometry(0.55, 0.26, 0.85, 2, 0.08), new THREE.MeshStandardMaterial({ color: '#ebe8e0', roughness: 0.9 }), 24);
    for (let j = 0; j < 24; j++) sacks.setMatrixAt(j, M4().makeTranslation(33.2 + (j % 2) * 0.6, 0.13 + Math.floor(j / 12) * 0.26, -26 + (Math.floor(j / 2) % 6) * 0.9));
    sacks.castShadow = true; scene.add(sacks);
  }
  {
    const cab = new THREE.Group(); cab.position.set(37, 0, 6);
    const b = new THREE.Mesh(new RoundedBoxGeometry(7, 2.7, 3, 2, 0.06), new THREE.MeshStandardMaterial({ color: '#f0eee8', roughness: 0.6 })); b.position.y = 1.55; b.castShadow = b.receiveShadow = true; cab.add(b);
    const glass = new THREE.MeshStandardMaterial({ color: '#27313a', roughness: 0.15, metalness: 0.3 });
    for (const x of [-2.2, 0.6, 2.4]) { const w = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.7), glass); w.position.set(x, 1.9, 1.51); cab.add(w); }
    const door = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 2.0), new THREE.MeshStandardMaterial({ color: '#8a979c', roughness: 0.5 })); door.position.set(-0.9, 1.2, 1.51); cab.add(door);
    const ac = new THREE.Mesh(new THREE.BoxGeometry(0.85, 0.6, 0.35), new THREE.MeshStandardMaterial({ color: '#d0d3d3', roughness: 0.5 })); ac.position.set(1.6, 2.0, 1.68); cab.add(ac);
    const roofTank = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 0.9, 24), new THREE.MeshStandardMaterial({ color: '#e9e5dc', roughness: 0.55 })); roofTank.position.set(2.5, 3.35, 0); roofTank.castShadow = true; cab.add(roofTank);
    const base = new THREE.Mesh(new THREE.BoxGeometry(7.2, 0.25, 3.2), concrete); base.position.y = 0.12; cab.add(base);
    scene.add(cab);
  }
  // light poles at the lanes
  for (const [x, z] of [[19, 12], [36, -8]]) {
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.1, 7, 8), metal); pole.position.set(x, 3.5, z); pole.castShadow = true; scene.add(pole);
    const lamp = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.15, 0.3), new THREE.MeshStandardMaterial({ color: '#d6d8d8', emissive: '#fff2d0', emissiveIntensity: 0.15 })); lamp.position.set(x + 0.35, 7, z); scene.add(lamp);
  }

  // ---------- the farm room (غرفة العزبة): block walls, a glass front looking over the pens
  {
    const room = new THREE.Group(); room.position.set(6, 0, 6.5);
    const blocks = canvasTex(256, 128, (g, w, h) => { g.fillStyle = '#e4d8c3'; g.fillRect(0, 0, w, h); g.strokeStyle = 'rgba(150,130,105,0.35)'; g.lineWidth = 1; for (let y = 0; y < h; y += 16) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); for (let x = (y / 16) % 2 ? 0 : 20; x < w; x += 40) { g.beginPath(); g.moveTo(x, y); g.lineTo(x, y + 16); g.stroke(); } } });
    blocks.name = 'blocks'; blocks.wrapS = blocks.wrapT = THREE.RepeatWrapping; blocks.repeat.set(3, 1.2);
    const wallMat = new THREE.MeshStandardMaterial({ map: blocks, roughness: 0.92 });
    const W = 10, D = 5.5, H = 3.2;
    const plinth = new THREE.Mesh(new THREE.BoxGeometry(W + 0.6, 0.35, D + 0.6), concrete); plinth.position.y = 0.17; plinth.receiveShadow = true; room.add(plinth);
    const back = new THREE.Mesh(new THREE.BoxGeometry(W, H, 0.25), wallMat); back.position.set(0, 0.35 + H / 2, D / 2); room.add(back);
    for (const sx of [-1, 1]) { const side = new THREE.Mesh(new THREE.BoxGeometry(0.25, H, D), wallMat); side.position.set(sx * W / 2, 0.35 + H / 2, 0); room.add(side); }
    const slab = new THREE.Mesh(new THREE.BoxGeometry(W + 0.5, 0.25, D + 0.5), wallMat); slab.position.set(0, 0.35 + H + 0.12, 0); room.add(slab);
    const parapet = new THREE.Mesh(new THREE.BoxGeometry(W + 0.5, 0.45, 0.12), wallMat);
    for (const sz of [-1, 1]) { const pp = parapet.clone(); pp.position.set(0, 0.35 + H + 0.45, sz * (D + 0.5) / 2); room.add(pp); }
    // the glass front: tinted panes in bronze aluminium frames
    const frameMat = new THREE.MeshStandardMaterial({ color: '#3a3027', metalness: 0.6, roughness: 0.35 });
    const glassMat = new THREE.MeshStandardMaterial({ color: '#a9bcc2', roughness: 0.04, metalness: 0.1, transparent: true, opacity: 0.32, envMapIntensity: 1.6 });
    const pane = new THREE.Mesh(new THREE.PlaneGeometry(W - 0.3, H - 0.2), glassMat); pane.position.set(0, 0.35 + H / 2, -D / 2); pane.rotation.y = Math.PI; room.add(pane);
    for (let i = 0; i <= 4; i++) { const mu = new THREE.Mesh(new THREE.BoxGeometry(0.08, H, 0.1), frameMat); mu.position.set(-W / 2 + 0.15 + i * (W - 0.3) / 4, 0.35 + H / 2, -D / 2); room.add(mu); }
    for (const y of [0.4, 0.35 + H - 0.05]) { const tr = new THREE.Mesh(new THREE.BoxGeometry(W, 0.1, 0.1), frameMat); tr.position.set(0, y, -D / 2); room.add(tr); }
    // inside, seen through the glass: a carpet and floor cushions along the walls
    const carpet = canvasTex(128, 64, (g, w, h) => { g.fillStyle = '#7a1f1c'; g.fillRect(0, 0, w, h); g.strokeStyle = '#d8b46a'; g.lineWidth = 3; g.strokeRect(6, 6, w - 12, h - 12); g.fillStyle = '#1e2d4a'; g.beginPath(); g.ellipse(w / 2, h / 2, 26, 14, 0, 0, 6.28); g.fill(); });
    carpet.name = 'carpet';
    const rugIn = new THREE.Mesh(new THREE.PlaneGeometry(W - 1, D - 1).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: carpet, roughness: 1 })); rugIn.position.set(0, 0.37, 0); room.add(rugIn);
    const cushion = new THREE.MeshStandardMaterial({ color: '#8b2620', roughness: 0.9 });
    const seat = new THREE.Mesh(new RoundedBoxGeometry(W - 1.2, 0.22, 0.7, 2, 0.06), cushion); seat.position.set(0, 0.48, D / 2 - 0.55); room.add(seat);
    const lean = new THREE.Mesh(new RoundedBoxGeometry(W - 1.2, 0.5, 0.18, 2, 0.06), cushion); lean.position.set(0, 0.75, D / 2 - 0.25); room.add(lean);
    for (const sx of [-1, 1]) { const s2 = new THREE.Mesh(new RoundedBoxGeometry(0.7, 0.22, D - 1.6, 2, 0.06), cushion); s2.position.set(sx * (W / 2 - 0.55), 0.48, 0); room.add(s2); }
    // the door on the east side, split air conditioners, a roof tank
    const door = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 2.2), frameMat); door.position.set(W / 2 + 0.13, 0.35 + 1.1, 0.8); door.rotation.y = Math.PI / 2; room.add(door);
    for (const z of [-1.2, 1.4]) { const ac = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.6, 0.85), new THREE.MeshStandardMaterial({ color: '#d4d6d6', roughness: 0.5 })); ac.position.set(-W / 2 - 0.3, 1.0, z); room.add(ac); }
    const rt = new THREE.Mesh(new THREE.CylinderGeometry(0.6, 0.6, 1.0, 24), new THREE.MeshStandardMaterial({ color: '#e9e5dc', roughness: 0.55 })); rt.position.set(3.3, 0.35 + H + 0.75, 1.2); room.add(rt);
    // a shaded porch in front with outdoor seating facing the camels
    const pergola = new THREE.Mesh(new THREE.BoxGeometry(W, 0.12, 3.2), new THREE.MeshStandardMaterial({ color: '#6b5640', roughness: 0.8 })); pergola.position.set(0, 3.25, -D / 2 - 1.6); room.add(pergola);
    for (const sx of [-1, 1]) { const pst = new THREE.Mesh(new THREE.BoxGeometry(0.16, 3.2, 0.16), new THREE.MeshStandardMaterial({ color: '#6b5640', roughness: 0.8 })); pst.position.set(sx * (W / 2 - 0.2), 1.6, -D / 2 - 3.0); room.add(pst); }
    const outRug = new THREE.Mesh(new THREE.PlaneGeometry(W - 2, 2.4).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: carpet, roughness: 1 })); outRug.position.set(0, 0.04, -D / 2 - 1.6); room.add(outRug);
    const bench = new THREE.Mesh(new RoundedBoxGeometry(W - 2.4, 0.2, 0.6, 2, 0.05), new THREE.MeshStandardMaterial({ color: '#2b3f5a', roughness: 0.9 })); bench.position.set(0, 0.12, -D / 2 - 0.6); room.add(bench);
    room.traverse((n) => { if (n.isMesh && n !== pane) { n.castShadow = true; n.receiveShadow = true; } });
    scene.add(room);
  }

  // ---------- the owner's majlis: goat-hair tent, Sadu rug, fire pit
  {
    const wool = canvasTex(256, 256, (g, w, h) => { g.fillStyle = '#1c1916'; g.fillRect(0, 0, w, h); for (let x = 0; x < w; x += 32) { g.fillStyle = 'rgba(120,105,90,0.35)'; g.fillRect(x, 0, 2, h); } for (let i = 0; i < 3000; i++) { g.fillStyle = `rgba(255,255,255,${rand() * 0.04})`; g.fillRect(rand() * w, rand() * h, 1, 2); } });
    wool.name = 'wool';
    const L = 12, D = 5.5, H = 2.3, E = 1.35;
    const v = [-L / 2, E, -D / 2, L / 2, E, -D / 2, L / 2, H, 0, -L / 2, E, -D / 2, L / 2, H, 0, -L / 2, H, 0, -L / 2, H, 0, L / 2, H, 0, L / 2, E, D / 2, -L / 2, H, 0, L / 2, E, D / 2, -L / 2, E, D / 2,
      -L / 2, 0, -D / 2, L / 2, 0, -D / 2, L / 2, E, -D / 2, -L / 2, 0, -D / 2, L / 2, E, -D / 2, -L / 2, E, -D / 2, -L / 2, 0, -D / 2, -L / 2, E, -D / 2, -L / 2, H, 0, -L / 2, 0, -D / 2, -L / 2, H, 0, -L / 2, 0, 0,
      L / 2, 0, -D / 2, L / 2, H, 0, L / 2, E, -D / 2, L / 2, 0, -D / 2, L / 2, 0, 0, L / 2, H, 0];
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3));
    const uv = []; for (let i = 0; i < v.length; i += 3) uv.push(v[i] / 3, (v[i + 1] + v[i + 2]) / 3);
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.computeVertexNormals();
    const tent = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ map: wool, roughness: 1, side: THREE.DoubleSide })); tent.position.set(-12, 0, 7); tent.rotation.y = Math.PI; tent.castShadow = tent.receiveShadow = true; scene.add(tent);
    const sadu = canvasTex(256, 128, (c, w, h) => { c.fillStyle = '#8f2a22'; c.fillRect(0, 0, w, h); c.fillStyle = '#efe6d6'; c.fillRect(0, 18, w, 10); c.fillRect(0, h - 28, w, 10); c.fillStyle = '#1d1a17'; for (let x = 0; x < w; x += 24) { c.beginPath(); c.moveTo(x, 86); c.lineTo(x + 12, 42); c.lineTo(x + 24, 86); c.fill(); } c.fillStyle = '#efe6d6'; for (let x = 12; x < w; x += 24) { c.beginPath(); c.moveTo(x - 5, 64); c.lineTo(x, 54); c.lineTo(x + 5, 64); c.lineTo(x, 74); c.fill(); } });
    sadu.name = 'sadu';
    const rug = new THREE.Mesh(new THREE.PlaneGeometry(5, 2.4).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: sadu, roughness: 1 })); rug.position.set(-12, 0.04, 2.6); rug.receiveShadow = true; scene.add(rug);
    const stones = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(0.16, 0), new THREE.MeshStandardMaterial({ color: '#6f6559', roughness: 1 }), 10);
    for (let i = 0; i < 10; i++) { const a = i / 10 * 6.283; stones.setMatrixAt(i, M4().makeTranslation(-12 + Math.cos(a) * 0.55, 0.08, 0.6 + Math.sin(a) * 0.55)); } scene.add(stones);
    const ash = new THREE.Mesh(new THREE.CircleGeometry(0.45, 20).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: '#2a2622', roughness: 1 })); ash.position.set(-12, 0.05, 0.6); scene.add(ash);
    const ropes = []; for (const sx of [-1, -0.5, 0, 0.5, 1]) ropes.push(-12 + sx * L / 2, H, 7, -12 + sx * L / 2 * 1.05, 0, 7 + D / 2 + 2.4);
    const rg = new THREE.BufferGeometry(); rg.setAttribute('position', new THREE.Float32BufferAttribute(ropes, 3)); scene.add(new THREE.LineSegments(rg, new THREE.LineBasicMaterial({ color: '#cbb994' })));
  }

  // ---------- inside the goat-hair tent: carpets, floor cushions, the hearth and the coffee set
  {
    const T = new THREE.Group(); T.position.set(-12, 0, 7); T.rotation.y = Math.PI; scene.add(T);
    const L = 12, D = 5.5, H = 2.3, E = 1.35;
    const wood = new THREE.MeshStandardMaterial({ color: '#7a5a3a', roughness: 0.85 });
    for (const x of [-4, 0, 4]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.07, H, 8), wood); p.position.set(x, H / 2, 0); T.add(p); }
    for (const x of [-6, -3, 0, 3, 6]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, E, 8), wood); p.position.set(x, E / 2, D / 2); T.add(p); }
    const rugTex = (bg, fg, mid) => canvasTex(256, 128, (g, w, h) => {
      g.fillStyle = bg; g.fillRect(0, 0, w, h); g.strokeStyle = fg; g.lineWidth = 6; g.strokeRect(8, 8, w - 16, h - 16);
      g.lineWidth = 2; g.strokeRect(18, 18, w - 36, h - 36);
      g.fillStyle = mid; for (let i = 0; i < 5; i++) { const cx = 40 + i * 44; g.beginPath(); g.moveTo(cx, 40); g.lineTo(cx + 16, 64); g.lineTo(cx, 88); g.lineTo(cx - 16, 64); g.fill(); }
      for (let i = 0; i < 1400; i++) { g.fillStyle = `rgba(0,0,0,${rand() * 0.06})`; g.fillRect(rand() * w, rand() * h, 1, 1); }
    });
    const rugs = [[rugTex('#7d1d1b', '#d9b25e', '#1f2f52'), 0, -0.6, 5.2, 3.0], [rugTex('#5e1a2a', '#e3c27a', '#7d1d1b'), -3.6, 0.2, 3.6, 3.8], [rugTex('#1f2f52', '#d9b25e', '#7d1d1b'), 3.6, 0.2, 3.6, 3.8]];
    rugs.forEach(([t], i) => { t.name = 'rug' + i; });
    for (const [tex, x, z, w, d] of rugs) { const r = new THREE.Mesh(new THREE.PlaneGeometry(w, d).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: tex, roughness: 1 })); r.position.set(x, 0.03 + rand() * 0.004, z); r.receiveShadow = true; T.add(r); }
    const cushTex = canvasTex(128, 32, (g, w, h) => { g.fillStyle = '#8c2420'; g.fillRect(0, 0, w, h); g.fillStyle = '#d6ad55'; for (let x = 0; x < w; x += 16) { g.beginPath(); g.moveTo(x, h / 2); g.lineTo(x + 8, 4); g.lineTo(x + 16, h / 2); g.lineTo(x + 8, h - 4); g.fill(); } g.fillRect(0, 0, w, 2); g.fillRect(0, h - 2, w, 2); });
    cushTex.name = 'cushion'; cushTex.wrapS = THREE.RepeatWrapping; cushTex.repeat.set(6, 1);
    const cush = new THREE.MeshStandardMaterial({ map: cushTex, roughness: 0.95 });
    const seat = new THREE.Mesh(new RoundedBoxGeometry(L - 1.2, 0.16, 0.75, 2, 0.05), cush); seat.position.set(0, 0.1, -D / 2 + 0.55); T.add(seat);
    const back = new THREE.Mesh(new RoundedBoxGeometry(L - 1.2, 0.5, 0.2, 2, 0.06), cush); back.position.set(0, 0.42, -D / 2 + 0.22); T.add(back);
    for (const sx of [-1, 1]) { const ss = new THREE.Mesh(new RoundedBoxGeometry(0.75, 0.16, D - 1.6, 2, 0.05), cush); ss.position.set(sx * (L / 2 - 0.55), 0.1, 0.2); T.add(ss); const sb = new THREE.Mesh(new RoundedBoxGeometry(0.2, 0.45, D - 1.6, 2, 0.06), cush); sb.position.set(sx * (L / 2 - 0.22), 0.38, 0.2); T.add(sb); }
    const roll = new THREE.CylinderGeometry(0.11, 0.11, 0.55, 14).rotateX(Math.PI / 2);
    for (let x = -L / 2 + 1.4; x < L / 2 - 1; x += 1.25) { const r = new THREE.Mesh(roll, cush); r.position.set(x, 0.29, -D / 2 + 0.75); T.add(r); }
    // the Sadu curtain (القاطع) closing the far end
    const saduCurtain = canvasTex(256, 128, (c, w, h) => { c.fillStyle = '#8f2a22'; c.fillRect(0, 0, w, h); c.fillStyle = '#efe6d6'; c.fillRect(0, 20, w, 9); c.fillRect(0, h - 29, w, 9); c.fillStyle = '#1d1a17'; for (let x = 0; x < w; x += 24) { c.beginPath(); c.moveTo(x, 86); c.lineTo(x + 12, 42); c.lineTo(x + 24, 86); c.fill(); } });
    saduCurtain.name = 'curtain';
    const qt = new THREE.Mesh(new THREE.PlaneGeometry(D - 0.4, 1.9), new THREE.MeshStandardMaterial({ map: saduCurtain, roughness: 1, side: THREE.DoubleSide })); qt.position.set(L / 2 - 1.4, 0.95, 0); qt.rotation.y = Math.PI / 2; T.add(qt);
    // the hearth (وجار) with embers, the brass dallahs, a thermos, cups and dates
    const hearth = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.18, 0.9), new THREE.MeshStandardMaterial({ color: '#8a7b68', roughness: 1 })); hearth.position.set(0, 0.09, D / 2 - 1.2); T.add(hearth);
    const embers = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.6).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: '#2a1d14', emissive: '#ff5a1f', emissiveIntensity: 0.9, roughness: 1 })); embers.position.set(0, 0.185, D / 2 - 1.2); T.add(embers);
    const brass = new THREE.MeshStandardMaterial({ color: '#caa14c', metalness: 1, roughness: 0.28 });
    const dallahProfile = [[0, 0], [0.075, 0], [0.08, 0.015], [0.06, 0.05], [0.05, 0.09], [0.066, 0.13], [0.072, 0.16], [0.06, 0.19], [0.035, 0.22], [0.03, 0.25], [0.046, 0.27], [0.03, 0.3], [0.012, 0.33], [0.006, 0.36], [0, 0.37]].map(([r, y]) => new THREE.Vector2(r, y));
    const dallahGeo = new THREE.LatheGeometry(dallahProfile, 24);
    const spout = new THREE.TubeGeometry(new THREE.CatmullRomCurve3([V(0.05, 0.15, 0), V(0.11, 0.2, 0), V(0.15, 0.29, 0), V(0.18, 0.32, 0)]), 12, 0.012, 8);
    const handle = new THREE.TorusGeometry(0.07, 0.008, 6, 16, Math.PI); handle.rotateZ(-Math.PI / 2); handle.translate(-0.07, 0.18, 0);
    for (const [x, z, s] of [[-0.3, D / 2 - 1.25, 1], [0.05, D / 2 - 1.05, 0.85], [0.35, D / 2 - 1.3, 0.75]]) {
      const d = new THREE.Group(); d.add(new THREE.Mesh(dallahGeo, brass), new THREE.Mesh(spout, brass), new THREE.Mesh(handle, brass));
      d.position.set(x, 0.18, z); d.scale.setScalar(s); d.rotation.y = rand() * 6.28; T.add(d);
    }
    const thermos = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.065, 0.32, 16), new THREE.MeshStandardMaterial({ color: '#c9c9cc', metalness: 0.9, roughness: 0.25 })); thermos.position.set(0.9, 0.19, D / 2 - 1.6); T.add(thermos);
    const tray = new THREE.Mesh(new THREE.CylinderGeometry(0.26, 0.26, 0.015, 32), brass); tray.position.set(-0.9, 0.04, D / 2 - 1.7); T.add(tray);
    const cup = new THREE.CylinderGeometry(0.025, 0.02, 0.045, 12);
    for (let i = 0; i < 6; i++) { const c = new THREE.Mesh(cup, new THREE.MeshStandardMaterial({ color: '#f4f1ea', roughness: 0.3 })); const a = i / 6 * 6.283; c.position.set(-0.9 + Math.cos(a) * 0.15, 0.07, D / 2 - 1.7 + Math.sin(a) * 0.15); T.add(c); }
    const bowl = new THREE.Mesh(new THREE.SphereGeometry(0.12, 16, 8, 0, 6.283, Math.PI / 2, Math.PI / 2), new THREE.MeshStandardMaterial({ color: '#d8d2c6', roughness: 0.4, side: THREE.DoubleSide })); bowl.position.set(-1.4, 0.15, D / 2 - 1.3); T.add(bowl);
    const date = new THREE.SphereGeometry(0.018, 8, 6); date.scale(1, 1, 1.6);
    for (let i = 0; i < 14; i++) { const d = new THREE.Mesh(date, new THREE.MeshStandardMaterial({ color: '#4a2412', roughness: 0.5 })); d.position.set(-1.4 + R(-0.07, 0.07), 0.08 + R(0, 0.02), D / 2 - 1.3 + R(-0.07, 0.07)); T.add(d); }
    const lantern = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.1, 0.22, 12), new THREE.MeshStandardMaterial({ color: '#f7d58a', emissive: '#ffb54a', emissiveIntensity: 1.6, transparent: true, opacity: 0.95 })); lantern.position.set(-2, H - 0.45, 0); T.add(lantern);
    T.traverse((n) => { if (n.isMesh) { n.receiveShadow = true; n.castShadow = n.geometry.type !== 'PlaneGeometry'; } });
  }

  // ---------- the grazing ground (مسراح), ~330 m out: the shepherd's caravan on a trailer and its tractor unit
  {
    const C = LAYOUT.camp;
    // at the camp: a portable trough the tanker fills, bales on the ground, the shepherd's mat and fire
    const troughCamp = new THREE.Mesh(new THREE.BoxGeometry(6, 0.5, 0.7), metal); troughCamp.position.set(C.x - 16, 0.25, C.z - 6); troughCamp.castShadow = true; scene.add(troughCamp);
    const wcamp = new THREE.Mesh(new THREE.PlaneGeometry(5.85, 0.55).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: '#3d5b57', roughness: 0.05 })); wcamp.position.set(C.x - 16, 0.46, C.z - 6); scene.add(wcamp);
    const bl = new THREE.InstancedMesh(new THREE.BoxGeometry(1.0, 0.42, 0.5), new THREE.MeshStandardMaterial({ map: hayTex, roughness: 1 }), 12);
    for (let i = 0; i < 12; i++) bl.setMatrixAt(i, M4().makeTranslation(C.x + 10 + (i % 4) * 1.05, 0.21 + Math.floor(i / 8) * 0.42, C.z - 8 + Math.floor(i / 4) % 2 * 0.52));
    bl.castShadow = true; scene.add(bl);
  }

  // ---------- vehicles: the owner's Land Cruisers and the water tanker
  const paint = new THREE.MeshStandardMaterial({ color: '#f1f1ee', roughness: 0.3 });
  const glass = new THREE.MeshStandardMaterial({ color: '#1e252b', roughness: 0.08, metalness: 0.4 });
  const rubber = new THREE.MeshStandardMaterial({ color: '#1b1a19', roughness: 0.9 });
  const steel = new THREE.MeshStandardMaterial({ color: '#c9ccce', metalness: 0.9, roughness: 0.25 });
  const wheel = (grp, x, z, r = 0.38, w = 0.28) => { const t = new THREE.Mesh(new THREE.CylinderGeometry(r, r, w, 20).rotateX(Math.PI / 2), rubber); t.position.set(x, r, z); t.castShadow = true; grp.add(t); const h = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.55, r * 0.55, w + 0.02, 12).rotateX(Math.PI / 2), steel); h.position.copy(t.position); grp.add(h); };
  const blackTrim = new THREE.MeshStandardMaterial({ color: '#141414', roughness: 0.6 });
  const lamp = new THREE.MeshStandardMaterial({ color: '#f4f1e6', emissive: '#fff4cf', emissiveIntensity: 0.25, roughness: 0.1 });
  // the car shade by the room, the owner's two Land Cruisers under it
  {
    const cs = new THREE.Group(); cs.position.set(16.5, 0, 6.5);
    const fabric = new THREE.PlaneGeometry(8.5, 6.5, 12, 10); fabric.rotateX(-Math.PI / 2);
    const fp = fabric.attributes.position; for (let i = 0; i < fp.count; i++) { const sx = fp.getX(i) / 4.25, sz = fp.getZ(i) / 3.25; fp.setY(i, 0.5 * (1 - Math.max(Math.abs(sx), Math.abs(sz)))); }
    fabric.computeVertexNormals();
    const fm = new THREE.Mesh(fabric, new THREE.MeshStandardMaterial({ color: '#e8dfcd', roughness: 0.9, side: THREE.DoubleSide })); fm.position.y = 2.7; fm.castShadow = fm.receiveShadow = true; cs.add(fm);
    for (const sx of [-1, 1]) for (const sz of [-1, 1]) { const pst = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, 2.7, 8), metal); pst.position.set(sx * 4.2, 1.35, sz * 3.2); pst.castShadow = true; cs.add(pst); }
    scene.add(cs);
  }
  // the vehicles themselves are photo-built models placed by the page (see VEHICLES)
  {
    const g = new THREE.Group();
    const cab = new THREE.Mesh(new RoundedBoxGeometry(2.2, 2.3, 2.4, 3, 0.15), paint); cab.position.set(3.1, 1.75, 0); g.add(cab);
    const win = new THREE.Mesh(new RoundedBoxGeometry(0.1, 0.9, 2.2, 2, 0.04), glass); win.position.set(4.2, 2.3, 0); g.add(win);
    const chassis = new THREE.Mesh(new THREE.BoxGeometry(8.4, 0.35, 2.2), new THREE.MeshStandardMaterial({ color: '#2c2c2c', roughness: 0.8 })); chassis.position.set(0, 0.85, 0); g.add(chassis);
    const tank = new THREE.Mesh(new THREE.CylinderGeometry(1.05, 1.05, 5.6, 32).rotateZ(Math.PI / 2), steel); tank.position.set(-1.2, 2.0, 0); g.add(tank);
    for (const x of [2.9, -0.8, -2.4]) { wheel(g, x, 1.0, 0.5, 0.35); wheel(g, x, -1.0, 0.5, 0.35); }
    g.traverse((n) => { if (n.isMesh) { n.castShadow = true; n.receiveShadow = true; } });
    g.position.set(37.2, 0, -30); g.rotation.y = Math.PI / 2 + 0.03; scene.add(g);
  }

  // ---------- trees: a few tamarisks (athel) for shade, as on a camel farm
  {
    const trunks = [], clumps = [];
    const athel = (x, z, s) => {
      const n = 3 + Math.floor(rand() * 2);
      trunks.push([V(x, 0, z), V(x + R(-0.3, 0.3), 1.7 * s, z + R(-0.3, 0.3)), 0.2 * s]);
      for (let i = 0; i < n; i++) {
        const a = i / n * 6.283 + R(-0.4, 0.4), top = V(x + Math.cos(a) * 1.6 * s, R(3.6, 4.8) * s, z + Math.sin(a) * 1.6 * s);
        trunks.push([V(x, 1.6 * s, z), top, 0.1 * s]);
        for (let k = 0; k < 4; k++) clumps.push([top.clone().add(V(R(-1, 1), R(-0.6, 0.9), R(-1, 1)).multiplyScalar(s)), R(1.0, 1.6) * s]);
      }
      clumps.push([V(x, 4.9 * s, z), 1.6 * s]);
    };
    for (const [x, z] of [[-4, 11], [-36, 10], [41, 10], [-60, 30], [-48, 66], [-14, 58], [-26, 40], [60, -20], [-70, -30]]) athel(x, z, R(1.0, 1.3));
    const tg = new THREE.CylinderGeometry(0.6, 1, 1, 7); tg.translate(0, 0.5, 0);
    const tm = new THREE.InstancedMesh(tg, new THREE.MeshStandardMaterial({ color: '#5c4d3f', roughness: 1 }), trunks.length);
    trunks.forEach(([a, b, r], i) => { const d = b.clone().sub(a); tm.setMatrixAt(i, M4().compose(a, new THREE.Quaternion().setFromUnitVectors(UP, d.clone().normalize()), V(r, d.length(), r))); });
    tm.castShadow = true; scene.add(tm);
    const cg = cardCluster(2.6, 2.4, 3, false); cg.translate(0, -1.2, 0);
    const cm = new THREE.InstancedMesh(cg, new THREE.MeshStandardMaterial({ map: tamariskTexture(), alphaTest: 0.35, side: THREE.DoubleSide, roughness: 1 }), clumps.length * 2), col = new THREE.Color();
    let ci = 0;
    clumps.forEach(([c, s]) => { for (let r = 0; r < 2; r++) { cm.setMatrixAt(ci, M4().compose(c.clone().add(V(R(-0.3, 0.3), R(-0.2, 0.3), R(-0.3, 0.3))), new THREE.Quaternion().setFromEuler(new THREE.Euler(R(-0.15, 0.15), R(0, 6.28), R(-0.15, 0.15))), V(s * 1.15, s * 1.1, s * 1.15))); cm.setColorAt(ci++, col.setHSL(0.24 + R(-0.03, 0.03), 0.12, 0.62 + R(-0.06, 0.06))); } });
    cm.castShadow = cm.receiveShadow = true; scene.add(cm);
  }
  // ---------- grass after the Wasm rain, shrubs, stones
  {
    const tuft = cardCluster(0.66, 0.5, 3, true);
    const n = 42000, items = [];
    let k = 0, tries = 0;
    while (k < n && tries < 700000) {
      tries++;
      const far = rand() < 0.42, x = far ? LAYOUT.camp.x + R(-110, 110) : R(-190, 190), z = far ? LAYOUT.camp.z + R(-100, 100) : R(-170, 200);
      if (inCompound(x, z, 5) || Math.abs(z - LAYOUT.roadZ) < 9 || (Math.abs(x - 27) < 5 && z > 10 && z < LAYOUT.roadZ)) continue;
      if (rand() > grassDensity(x, z)) continue;
      const s = R(0.6, 1.5);
      items.push({ x, z, m: M4().compose(V(x, 0, z), new THREE.Quaternion().setFromAxisAngle(UP, R(0, 6.28)), V(s, s * R(0.7, 1.3), s)),
        c: new THREE.Color().setHSL(0.13 + R(-0.02, 0.05), 0.18, 0.86 + R(-0.08, 0.08)) });
      k++;
    }
    // every tuft up close, a thinning sample further out, none past 260 m (the sand texture carries the colour)
    scene.add(scatterCells(tuft, new THREE.MeshStandardMaterial({ map: grassTexture(), alphaTest: 0.4, side: THREE.DoubleSide, roughness: 1 }), items,
      { cell: GRASS_CELL, bands: [[45, 1], [90, 0.45], [160, 0.2], [260, 0.08]] }));
  }
  {
    const g = cardCluster(1.2, 1.0, 3, true);
    const n = 1500, items = [];
    let k = 0;
    while (k < n) {
      const far = rand() < 0.35, x = far ? LAYOUT.camp.x + R(-120, 120) : R(-300, 300), z = far ? LAYOUT.camp.z + R(-110, 110) : R(-260, 300);
      if (inCompound(x, z, 6) || Math.abs(z - LAYOUT.roadZ) < 10) continue;
      const s = R(0.45, 1.25);
      items.push({ x, z, m: M4().compose(V(x, -0.03, z), new THREE.Quaternion().setFromAxisAngle(UP, R(0, 6.28)), V(s, s * R(0.65, 1.0), s)),
        c: new THREE.Color().setHSL(0.12 + R(-0.02, 0.04), 0.1, 0.82 + R(-0.1, 0.1)) });
      k++;
    }
    // (shadowDist 102 m: the half-diagonal of the sun's 144 m shadow square, so a cell casts whenever any of it can lie inside)
    scene.add(scatterCells(g, new THREE.MeshStandardMaterial({ map: bushTexture(), alphaTest: 0.4, side: THREE.DoubleSide, roughness: 1 }), items,
      { cell: BUSH_CELL, cast: true, shadowDist: 102, bands: [[120, 1], [260, 0.5], [450, 0.25]] }));
    // stones: 8 triangles each (they are a few centimetres across), only near the camera
    const sg = new THREE.OctahedronGeometry(0.12, 0); sg.scale(1, 0.5, 1.25);
    const stones = [];
    for (let i = 0; i < 2600; i++) { const x = R(-200, 200), z = R(-180, 220), s = R(0.5, 2.2); stones.push({ x, z, m: M4().compose(V(x, 0.02, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(0, R(0, 6), 0)), V(s, s, s)), c: new THREE.Color().setHSL(0.07, 0.18, 0.34 + R(-0.08, 0.1)) }); }
    scene.add(scatterCells(sg, new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 1 }), stones, { cell: STONE_CELL, bands: [[40, 1], [90, 0.35]] }));
  }
}

// grass grows in patches and in the low ground of the pasture after the rain
export function grassDensity(x, z) {
  const patch = THREE.MathUtils.smoothstep(fbm(x / 26 + 3, z / 26 - 7), 0.42, 0.66);
  const pasture = (x > LAYOUT.graze.x0 - 25 && x < LAYOUT.graze.x1 + 25 && z > LAYOUT.graze.z0 - 25 && z < LAYOUT.graze.z1 + 30) ? 0.35 : 0;
  return Math.min(0.95, patch * 0.85 + pasture * patch + pasture * 0.25);
}
