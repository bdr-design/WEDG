// The farm world: ground, vegetation, roads and buildings at real size.
// Coordinates in metres: x east, z south, y up. Everything repeated is instanced.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

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
  graze: { x0: -64, x1: 10, z0: 26, z1: 74 },
  roadZ: 112,
};
const inCompound = (x, z, m = 0) => x > LAYOUT.compound.x0 - m && x < LAYOUT.compound.x1 + m && z > LAYOUT.compound.z0 - m && z < LAYOUT.compound.z1 + m;

export function buildWorld(scene, renderer, sandTex) {
  const aniso = renderer.capabilities.getMaxAnisotropy();
  sandTex.anisotropy = aniso;

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
  {
    const size = 640, seg = 200;
    const g = new THREE.PlaneGeometry(size, size, seg, seg); g.rotateX(-Math.PI / 2);
    const p = g.attributes.position, uv = g.attributes.uv, col = new Float32Array(p.count * 3);
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i), z = p.getZ(i);
      uv.setXY(i, x / 22, z / 22);
      const c = tint(x, z); col.set([c.r, c.g, c.b], i * 3);
      p.setY(i, (fbm(x / 70, z / 70) - 0.5) * 0.6 * THREE.MathUtils.smoothstep(Math.hypot(x, z + 10), 70, 180));
    }
    g.setAttribute('color', new THREE.BufferAttribute(col, 3)); g.computeVertexNormals();
    const near = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ map: sandTex, vertexColors: true, roughness: 1 }));
    near.receiveShadow = true; scene.add(near);
  }
  {
    const size = 4000, seg = 180;
    const g = new THREE.PlaneGeometry(size, size, seg, seg); g.rotateX(-Math.PI / 2);
    const p = g.attributes.position, uv = g.attributes.uv;
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i), z = p.getZ(i), r = Math.hypot(x, z);
      const far = THREE.MathUtils.smoothstep(r, 300, 1000);
      p.setY(i, -0.4 + far * (fbm(x / 160, z / 100) * 34 + noise2(x / 45, z / 35) * 6));
      uv.setXY(i, x / 22, z / 22);
    }
    g.computeVertexNormals();
    const far = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ map: sandTex, color: '#f1e3cf', roughness: 1 }));
    far.receiveShadow = true; scene.add(far);
  }
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
  penFloor.wrapS = penFloor.wrapT = THREE.RepeatWrapping;
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
  asphaltTex.wrapT = THREE.RepeatWrapping; asphaltTex.repeat.set(1, 3000 / 40);
  const road = new THREE.Mesh(new THREE.PlaneGeometry(9, 3000).rotateX(-Math.PI / 2).rotateY(Math.PI / 2),
    new THREE.MeshStandardMaterial({ map: asphaltTex, roughness: 0.92 }));
  road.position.set(0, 0.06, LAYOUT.roadZ); road.receiveShadow = true; scene.add(road);
  const shoulder = new THREE.Mesh(new THREE.PlaneGeometry(3000, 15).rotateX(-Math.PI / 2),
    new THREE.MeshStandardMaterial({ color: '#a98463', roughness: 1, transparent: true, opacity: 0.35, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -1 }));
  shoulder.position.set(0, 0.04, LAYOUT.roadZ); scene.add(shoulder);
  const trackTex = canvasTex(64, 256, (g, w, h) => {
    g.fillStyle = 'rgba(120,86,56,0.55)'; g.fillRect(0, 0, w, h);
    for (const x of [w * 0.28, w * 0.72]) { const gr = g.createLinearGradient(x - 8, 0, x + 8, 0); gr.addColorStop(0, 'rgba(70,48,28,0)'); gr.addColorStop(0.5, 'rgba(70,48,28,0.55)'); gr.addColorStop(1, 'rgba(70,48,28,0)'); g.fillStyle = gr; g.fillRect(x - 8, 0, 16, h); }
    for (let i = 0; i < 600; i++) { g.fillStyle = `rgba(255,240,220,${rand() * 0.15})`; g.fillRect(rand() * w, rand() * h, 2, 2); }
  });
  trackTex.wrapT = THREE.RepeatWrapping;
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
    const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ map: trackTex, transparent: true, depthWrite: false, roughness: 1, polygonOffset: true, polygonOffsetFactor: -3, side: THREE.DoubleSide }));
    m.receiveShadow = true; scene.add(m);
  };
  ribbon([[24, 10], [24, 40], [27, 70], [30, 95], [30, LAYOUT.roadZ - 4]], 6);
  ribbon([[24, 14], [24, -2], [10, -3], [-34, -3]], 5);
  ribbon([[24, -3], [36, -3], [37, -30], [36, -48]], 5);
  ribbon([[18, 22], [-8, 30], [-30, 42], [-52, 50]], 3.4);   // the herd's daily trail to the pasture

  // ---------- earth berm around the compound with the gate gap
  const sandMat = new THREE.MeshStandardMaterial({ map: sandTex, color: '#d9b994', roughness: 1 });
  const berm = (ax, az, bx, bz) => {
    const len = Math.hypot(bx - ax, bz - az);
    const g = new THREE.CylinderGeometry(1, 1, len, 14, 1, true, 0, Math.PI);
    g.rotateX(Math.PI / 2); g.rotateZ(Math.PI / 2); g.scale(1.3, 0.8, 1);
    const bp = g.attributes.position;
    for (let i = 0; i < bp.count; i++) { const k = 0.8 + 0.45 * noise2(bp.getZ(i) * 0.35 + ax * 0.1, bp.getX(i) * 1.7 + az * 0.1); bp.setX(i, bp.getX(i) * (0.9 + 0.2 * k)); bp.setY(i, bp.getY(i) * k); }
    g.computeVertexNormals();
    const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, uv.getX(i) * 0.2, uv.getY(i) * len / 22);
    const m = new THREE.Mesh(g, sandMat);
    m.position.set((ax + bx) / 2, 0, (az + bz) / 2); m.rotation.y = Math.atan2(bx - ax, bz - az);
    m.castShadow = m.receiveShadow = true; scene.add(m);
  };
  const C = LAYOUT.compound, G = LAYOUT.gate, o = 3;
  berm(C.x0 - o, C.z0 - o, C.x1 + o, C.z0 - o); berm(C.x1 + o, C.z0 - o, C.x1 + o, C.z1 + o); berm(C.x0 - o, C.z0 - o, C.x0 - o, C.z1 + o);
  berm(C.x0 - o, C.z1 + o, G.x0, C.z1 + o); berm(G.x1, C.z1 + o, C.x1 + o, C.z1 + o);

  // ---------- pens: galvanized pipe, mesh panels, gates, troughs, shades
  const metal = new THREE.MeshStandardMaterial({ color: '#aeb2b4', metalness: 0.85, roughness: 0.38 });
  const meshTex = canvasTex(128, 128, (g, w, h) => { g.clearRect(0, 0, w, h); g.strokeStyle = 'rgba(190,195,198,1)'; g.lineWidth = 2.2; for (let i = 0; i <= w; i += 16) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, h); g.stroke(); g.beginPath(); g.moveTo(0, i); g.lineTo(w, i); g.stroke(); } });
  meshTex.wrapS = meshTex.wrapT = THREE.RepeatWrapping;
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
    const wall = canvasTex(256, 128, (g, w, h) => { g.fillStyle = '#d7d1c4'; g.fillRect(0, 0, w, h); for (let x = 0; x < w; x += 6) { g.fillStyle = x % 12 ? 'rgba(0,0,0,0.07)' : 'rgba(255,255,255,0.2)'; g.fillRect(x, 0, 3, h); } });
    const hangar = new THREE.Group(); hangar.position.set(36, 0, -20);
    const body = new THREE.Mesh(new THREE.BoxGeometry(10, 4, 12), new THREE.MeshStandardMaterial({ map: wall, roughness: 0.7, metalness: 0.25 })); body.position.y = 2; body.castShadow = body.receiveShadow = true; hangar.add(body);
    const roofMat = new THREE.MeshStandardMaterial({ color: '#c3bcb0', roughness: 0.55, metalness: 0.5 });
    for (const s of [-1, 1]) { const r = new THREE.Mesh(new THREE.BoxGeometry(5.6, 0.12, 12.6), roofMat); r.position.set(s * 2.6, 4.55, 0); r.rotation.z = -s * 0.2; r.castShadow = true; hangar.add(r); }
    const door = new THREE.Mesh(new THREE.PlaneGeometry(4.5, 3.4), new THREE.MeshStandardMaterial({ color: '#4c4a46', roughness: 0.8 })); door.position.set(-5.01, 1.7, 0); door.rotation.y = -Math.PI / 2; hangar.add(door);
    scene.add(hangar);
    const bales = new THREE.InstancedMesh(new THREE.BoxGeometry(1.0, 0.42, 0.5), new THREE.MeshStandardMaterial({ map: hayTex, roughness: 1 }), 48);
    let i = 0; for (let row = 0; row < 3; row++) for (let col = 0; col < 8; col++) for (let lay = 0; lay < 2; lay++) bales.setMatrixAt(i++, M4().makeTranslation(29.6 + lay * 0.52, 0.21 + row * 0.42, -26 + col * 1.02).multiply(M4().makeRotationY(Math.PI / 2)));
    bales.castShadow = bales.receiveShadow = true; scene.add(bales);
    const sacks = new THREE.InstancedMesh(new RoundedBoxGeometry(0.55, 0.26, 0.85, 2, 0.08), new THREE.MeshStandardMaterial({ color: '#ebe8e0', roughness: 0.9 }), 24);
    for (let j = 0; j < 24; j++) sacks.setMatrixAt(j, M4().makeTranslation(29.8 + (j % 2) * 0.6, 0.13 + Math.floor(j / 12) * 0.26, -14.5 + (Math.floor(j / 2) % 6) * 0.9));
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
  for (const [x, z] of [[21, 12], [24, -6], [-30, -6], [36, -46], [36, -6]]) {
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.1, 7, 8), metal); pole.position.set(x, 3.5, z); pole.castShadow = true; scene.add(pole);
    const lamp = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.15, 0.3), new THREE.MeshStandardMaterial({ color: '#d6d8d8', emissive: '#fff2d0', emissiveIntensity: 0.15 })); lamp.position.set(x + 0.35, 7, z); scene.add(lamp);
  }

  // ---------- the owner's majlis: goat-hair tent, Sadu rug, fire pit
  {
    const wool = canvasTex(256, 256, (g, w, h) => { g.fillStyle = '#1c1916'; g.fillRect(0, 0, w, h); for (let x = 0; x < w; x += 32) { g.fillStyle = 'rgba(120,105,90,0.35)'; g.fillRect(x, 0, 2, h); } for (let i = 0; i < 3000; i++) { g.fillStyle = `rgba(255,255,255,${rand() * 0.04})`; g.fillRect(rand() * w, rand() * h, 1, 2); } });
    const L = 12, D = 5.5, H = 2.3, E = 1.35;
    const v = [-L / 2, E, -D / 2, L / 2, E, -D / 2, L / 2, H, 0, -L / 2, E, -D / 2, L / 2, H, 0, -L / 2, H, 0, -L / 2, H, 0, L / 2, H, 0, L / 2, E, D / 2, -L / 2, H, 0, L / 2, E, D / 2, -L / 2, E, D / 2,
      -L / 2, 0, -D / 2, L / 2, 0, -D / 2, L / 2, E, -D / 2, -L / 2, 0, -D / 2, L / 2, E, -D / 2, -L / 2, E, -D / 2, -L / 2, 0, -D / 2, -L / 2, E, -D / 2, -L / 2, H, 0, -L / 2, 0, -D / 2, -L / 2, H, 0, -L / 2, 0, 0,
      L / 2, 0, -D / 2, L / 2, H, 0, L / 2, E, -D / 2, L / 2, 0, -D / 2, L / 2, 0, 0, L / 2, H, 0];
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3));
    const uv = []; for (let i = 0; i < v.length; i += 3) uv.push(v[i] / 3, (v[i + 1] + v[i + 2]) / 3);
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2)); g.computeVertexNormals();
    const tent = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ map: wool, roughness: 1, side: THREE.DoubleSide })); tent.position.set(4, 0, 6); tent.castShadow = tent.receiveShadow = true; scene.add(tent);
    const sadu = canvasTex(256, 128, (c, w, h) => { c.fillStyle = '#8f2a22'; c.fillRect(0, 0, w, h); c.fillStyle = '#efe6d6'; c.fillRect(0, 18, w, 10); c.fillRect(0, h - 28, w, 10); c.fillStyle = '#1d1a17'; for (let x = 0; x < w; x += 24) { c.beginPath(); c.moveTo(x, 86); c.lineTo(x + 12, 42); c.lineTo(x + 24, 86); c.fill(); } c.fillStyle = '#efe6d6'; for (let x = 12; x < w; x += 24) { c.beginPath(); c.moveTo(x - 5, 64); c.lineTo(x, 54); c.lineTo(x + 5, 64); c.lineTo(x, 74); c.fill(); } });
    const rug = new THREE.Mesh(new THREE.PlaneGeometry(5, 2.4).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ map: sadu, roughness: 1 })); rug.position.set(4, 0.04, 9.6); rug.receiveShadow = true; scene.add(rug);
    const stones = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(0.16, 0), new THREE.MeshStandardMaterial({ color: '#6f6559', roughness: 1 }), 10);
    for (let i = 0; i < 10; i++) { const a = i / 10 * 6.283; stones.setMatrixAt(i, M4().makeTranslation(4 + Math.cos(a) * 0.55, 0.08, 12.2 + Math.sin(a) * 0.55)); } scene.add(stones);
    const ash = new THREE.Mesh(new THREE.CircleGeometry(0.45, 20).rotateX(-Math.PI / 2), new THREE.MeshStandardMaterial({ color: '#2a2622', roughness: 1 })); ash.position.set(4, 0.05, 12.2); scene.add(ash);
    const ropes = []; for (const sx of [-1, -0.5, 0, 0.5, 1]) ropes.push(4 + sx * L / 2, H, 6, 4 + sx * L / 2 * 1.05, 0, 6 - D / 2 - 2.4);
    const rg = new THREE.BufferGeometry(); rg.setAttribute('position', new THREE.Float32BufferAttribute(ropes, 3)); scene.add(new THREE.LineSegments(rg, new THREE.LineBasicMaterial({ color: '#cbb994' })));
  }

  // ---------- vehicles: two pickups by the majlis, a water tanker on the service lane
  const paint = new THREE.MeshPhysicalMaterial({ color: '#f1f1ee', roughness: 0.32, clearcoat: 0.7, clearcoatRoughness: 0.2 });
  const glass = new THREE.MeshStandardMaterial({ color: '#1e252b', roughness: 0.08, metalness: 0.4 });
  const rubber = new THREE.MeshStandardMaterial({ color: '#1b1a19', roughness: 0.9 });
  const steel = new THREE.MeshStandardMaterial({ color: '#c9ccce', metalness: 0.9, roughness: 0.25 });
  const wheel = (grp, x, z, r = 0.38, w = 0.28) => { const t = new THREE.Mesh(new THREE.CylinderGeometry(r, r, w, 20).rotateX(Math.PI / 2), rubber); t.position.set(x, r, z); t.castShadow = true; grp.add(t); const h = new THREE.Mesh(new THREE.CylinderGeometry(r * 0.55, r * 0.55, w + 0.02, 12).rotateX(Math.PI / 2), steel); h.position.copy(t.position); grp.add(h); };
  const pickup = (x, z, rot, load) => {
    const g = new THREE.Group();
    const body = new THREE.Mesh(new RoundedBoxGeometry(5.3, 0.62, 1.82, 3, 0.12), paint); body.position.set(0, 0.86, 0); g.add(body);
    const cab = new THREE.Mesh(new RoundedBoxGeometry(2.3, 0.82, 1.74, 3, 0.18), paint); cab.position.set(0.55, 1.55, 0); g.add(cab);
    const win = new THREE.Mesh(new RoundedBoxGeometry(2.05, 0.5, 1.78, 2, 0.12), glass); win.position.set(0.6, 1.66, 0); g.add(win);
    const hood = new THREE.Mesh(new RoundedBoxGeometry(1.5, 0.18, 1.78, 2, 0.08), paint); hood.position.set(2.0, 1.2, 0); g.add(hood);
    for (const s of [-1, 1]) { const side = new THREE.Mesh(new THREE.BoxGeometry(1.95, 0.42, 0.06), paint); side.position.set(-1.6, 1.36, s * 0.87); g.add(side); }
    const tail = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.42, 1.8), paint); tail.position.set(-2.58, 1.36, 0); g.add(tail);
    const grille = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.3, 1.2), glass); grille.position.set(2.66, 0.95, 0); g.add(grille);
    for (const s of [-1, 1]) { const l = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.12, 0.28), new THREE.MeshStandardMaterial({ color: '#fffbe6', emissive: '#fff4cf', emissiveIntensity: 0.2 })); l.position.set(2.66, 1.08, s * 0.66); g.add(l); }
    wheel(g, 1.65, 0.84); wheel(g, 1.65, -0.84); wheel(g, -1.6, 0.84); wheel(g, -1.6, -0.84);
    if (load) for (let i = 0; i < 2; i++) { const bl = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.42, 0.5), new THREE.MeshStandardMaterial({ map: hayTex, roughness: 1 })); bl.position.set(-1.6, 1.38, -0.3 + i * 0.6); bl.rotation.y = Math.PI / 2; g.add(bl); }
    g.traverse((n) => { if (n.isMesh) { n.castShadow = true; n.receiveShadow = true; } });
    g.position.set(x, 0, z); g.rotation.y = rot; scene.add(g);
  };
  pickup(14, 7.5, -1.35, true); pickup(17.2, 8.2, -1.5, false);
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

  // ---------- trees: tamarisk (athel) windbreak and palms by the majlis
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
    for (let x = LAYOUT.compound.x0; x <= LAYOUT.compound.x1; x += 6.5) athel(x + R(-0.8, 0.8), LAYOUT.compound.z0 - 7 + R(-0.6, 0.6), R(0.9, 1.15));
    for (let z = LAYOUT.compound.z0; z <= LAYOUT.compound.z1; z += 6.5) athel(LAYOUT.compound.x0 - 7 + R(-0.6, 0.6), z + R(-0.8, 0.8), R(0.9, 1.15));
    for (const [x, z] of [[-60, 30], [-48, 66], [-14, 58], [6, 34]]) athel(x, z, R(1.0, 1.3));
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
  {
    const frondTex = canvasTex(128, 512, (g, w, h) => { g.clearRect(0, 0, w, h); g.strokeStyle = '#6b6a36'; g.lineWidth = 5; g.beginPath(); g.moveTo(w / 2, 0); g.lineTo(w / 2, h); g.stroke(); g.strokeStyle = '#5f7a3a'; g.lineWidth = 3; for (let y = 20; y < h; y += 9) { const l = (w / 2 - 4) * (0.35 + 0.65 * Math.sin(Math.PI * y / h)); g.beginPath(); g.moveTo(w / 2, y); g.lineTo(w / 2 - l, y + 26); g.moveTo(w / 2, y); g.lineTo(w / 2 + l, y + 26); g.stroke(); } });
    const fg = new THREE.PlaneGeometry(1.1, 3.4, 1, 10); fg.translate(0, 1.7, 0);
    const p = fg.attributes.position; for (let i = 0; i < p.count; i++) { const t = p.getY(i) / 3.4; p.setZ(i, -t * t * 1.6); }
    fg.computeVertexNormals();
    const palms = [[11, 2.5, 7.5], [14, 0.5, 8.5], [-2, 2, 6.8]];
    const fm = new THREE.InstancedMesh(fg, new THREE.MeshStandardMaterial({ map: frondTex, alphaTest: 0.4, side: THREE.DoubleSide, roughness: 0.9 }), palms.length * 18);
    const ringTex = canvasTex(32, 256, (g, w, h) => { g.fillStyle = '#7d6a54'; g.fillRect(0, 0, w, h); for (let y = 0; y < h; y += 10) { g.fillStyle = 'rgba(40,30,20,0.45)'; g.fillRect(0, y, w, 3); } });
    ringTex.wrapT = THREE.RepeatWrapping;
    let k = 0;
    for (const [x, z, hgt] of palms) {
      const t = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.28, hgt, 12), new THREE.MeshStandardMaterial({ map: ringTex, roughness: 1 })); t.position.set(x, hgt / 2, z); t.castShadow = true; scene.add(t);
      for (let i = 0; i < 18; i++) {
        const yaw = i / 18 * 6.283 + R(-0.15, 0.15), tilt = (i % 2 ? 0.5 : 0.95) + R(-0.1, 0.1);
        fm.setMatrixAt(k++, M4().compose(V(x, hgt, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(tilt, yaw, 0, 'YXZ')), V(1, 1, 1)));
      }
    }
    fm.castShadow = true; scene.add(fm);
  }

  // ---------- grass after the Wasm rain, shrubs, stones
  {
    const tuft = cardCluster(0.66, 0.5, 3, true);
    const n = 42000, gm = new THREE.InstancedMesh(tuft, new THREE.MeshStandardMaterial({ map: grassTexture(), alphaTest: 0.4, side: THREE.DoubleSide, roughness: 1 }), n);
    const col = new THREE.Color(); let k = 0, tries = 0;
    while (k < n && tries < 700000) {
      tries++;
      const x = R(-200, 200), z = R(-170, 210);
      if (inCompound(x, z, 5) || Math.abs(z - LAYOUT.roadZ) < 9 || (Math.abs(x - 27) < 5 && z > 10 && z < LAYOUT.roadZ)) continue;
      if (rand() > grassDensity(x, z)) continue;
      const s = R(0.6, 1.5);
      gm.setMatrixAt(k, M4().compose(V(x, 0, z), new THREE.Quaternion().setFromAxisAngle(UP, R(0, 6.28)), V(s, s * R(0.7, 1.3), s)));
      gm.setColorAt(k, col.setHSL(0.13 + R(-0.02, 0.05), 0.18, 0.86 + R(-0.08, 0.08)));
      k++;
    }
    gm.count = k; gm.receiveShadow = true; scene.add(gm);
  }
  {
    const g = cardCluster(1.2, 1.0, 3, true);
    const n = 1500, m = new THREE.InstancedMesh(g, new THREE.MeshStandardMaterial({ map: bushTexture(), alphaTest: 0.4, side: THREE.DoubleSide, roughness: 1 }), n), c = new THREE.Color();
    let k = 0;
    while (k < n) {
      const x = R(-300, 300), z = R(-260, 300);
      if (inCompound(x, z, 6) || Math.abs(z - LAYOUT.roadZ) < 10) continue;
      const s = R(0.45, 1.25);
      m.setMatrixAt(k, M4().compose(V(x, -0.03, z), new THREE.Quaternion().setFromAxisAngle(UP, R(0, 6.28)), V(s, s * R(0.65, 1.0), s)));
      m.setColorAt(k, c.setHSL(0.12 + R(-0.02, 0.04), 0.1, 0.82 + R(-0.1, 0.1)));
      k++;
    }
    m.castShadow = m.receiveShadow = true; scene.add(m);
    const sg = new THREE.DodecahedronGeometry(0.12, 0); sg.scale(1, 0.55, 1.2);
    const stones = new THREE.InstancedMesh(sg, new THREE.MeshStandardMaterial({ color: '#ffffff', roughness: 1 }), 2600);
    for (let i = 0; i < 2600; i++) { const x = R(-200, 200), z = R(-180, 220), s = R(0.5, 2.2); stones.setMatrixAt(i, M4().compose(V(x, 0.02, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(0, R(0, 6), 0)), V(s, s, s))); stones.setColorAt(i, c.setHSL(0.07, 0.18, 0.34 + R(-0.08, 0.1))); }
    stones.receiveShadow = true; scene.add(stones);
  }
}

// grass grows in patches and in the low ground of the pasture after the rain
export function grassDensity(x, z) {
  const patch = THREE.MathUtils.smoothstep(fbm(x / 26 + 3, z / 26 - 7), 0.42, 0.66);
  const pasture = (x > LAYOUT.graze.x0 - 25 && x < LAYOUT.graze.x1 + 25 && z > LAYOUT.graze.z0 - 25 && z < LAYOUT.graze.z1 + 30) ? 0.35 : 0;
  return Math.min(0.95, patch * 0.85 + pasture * patch + pasture * 0.25);
}
