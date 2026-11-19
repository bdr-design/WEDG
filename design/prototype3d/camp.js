// The camp at a hunting or trapping ground (T18 part C, the approved storyboard design/hunt/trip.cjs frames 7, 8 and 13):
// the tent, the camp's supplies, and for trapping the pigeon cage and the bird net. Built by code from real sizes (he
// has sent no photos of these): the big square canvas tent of desert camps (his choice of 19 Nov, bigTent below), 20-litre water jerrycans, a fuel can, a cooler, food
// boxes, a gas cylinder, firewood and a ring of stones for the fire; a wire pigeon cage 70 x 45 x 45 cm; a vertical
// bird net (the trappers' dho-gaza) 3 m wide and 2 m high between two poles.
// Everything solid is one vertex-coloured mesh; the tent's canvas another (its weave and seams a small texture); the
// net a third (a grid texture cut by alpha test): 3 draws and their shadows. The camp's origin is the tent's door; +x is the tent's right as one faces it.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// a geometry with every vertex the given colour (a little darkened below, so the shapes read without textures)
function painted(geo, hex, shade = 0.12) {
  const g = geo.index ? geo.toNonIndexed() : geo;      // (all alike for the merge: the stones' polyhedra have no index)
  const c = new THREE.Color(hex), p = g.attributes.position, n = p.count, col = new Float32Array(n * 3);
  g.computeBoundingBox();
  const y0 = g.boundingBox.min.y, y1 = g.boundingBox.max.y, span = Math.max(1e-3, y1 - y0);
  for (let i = 0; i < n; i++) {
    const k = 1 - shade * (1 - (p.getY(i) - y0) / span);
    col[i * 3] = c.r * k; col[i * 3 + 1] = c.g * k; col[i * 3 + 2] = c.b * k;
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return g;
}
const at = (geo, x, y, z, ry = 0, rx = 0, rz = 0) => {
  const m = new THREE.Matrix4().compose(new THREE.Vector3(x, y, z), new THREE.Quaternion().setFromEuler(new THREE.Euler(rx, ry, rz)), new THREE.Vector3(1, 1, 1));
  return geo.applyMatrix4(m);
};
const box = (w, h, d) => new THREE.BoxGeometry(w, h, d);
const cyl = (r0, r1, h, s = 12) => new THREE.CylinderGeometry(r0, r1, h, s);

// a line of rope or a pole between two points (a thin cylinder), for the guy ropes
function between(a, b, r, sides = 4) {
  const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b), d = B.clone().sub(A), len = d.length();
  const g = cyl(r, r, len, sides);
  const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize());
  return g.applyMatrix4(new THREE.Matrix4().compose(A.add(B).multiplyScalar(0.5), q, new THREE.Vector3(1, 1, 1)));
}
// a panel of canvas from a grid of points f(u, v) (u, v in 0..1), with uvs in metres for the weave and its seams
function cloth(f, nu, nv, metresU, metresV) {
  const P = [], UV = [], I = [];
  for (let j = 0; j <= nv; j++) for (let i = 0; i <= nu; i++) { const p = f(i / nu, j / nv); P.push(p.x, p.y, p.z); UV.push((i / nu) * metresU, (j / nv) * metresV); }
  for (let j = 0; j < nv; j++) for (let i = 0; i < nu; i++) { const a = j * (nu + 1) + i, b = a + 1, c = a + nu + 1, d = c + 1; I.push(a, b, d, a, d, c); }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(UV, 2));
  g.setIndex(I); g.computeVertexNormals();
  return g;
}
// the canvas's weave and its seams: cotton duck, a seam every metre of the width (the cloth comes in widths of about a
// metre), drawn once on a small canvas and repeated by the uvs in metres
function canvasTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const g = c.getContext('2d');
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, 128, 128);
  for (let y = 0; y < 128; y += 2) { g.fillStyle = `rgba(120,100,70,${0.05 + (y % 4 ? 0.02 : 0.04)})`; g.fillRect(0, y, 128, 1); }
  for (let x = 0; x < 128; x += 2) { g.fillStyle = 'rgba(120,100,70,0.04)'; g.fillRect(x, 0, 1, 128); }
  g.fillStyle = 'rgba(95,72,45,0.35)'; g.fillRect(0, 0, 3, 128); g.fillStyle = 'rgba(255,255,255,0.25)'; g.fillRect(3, 0, 2, 128);      // (the seam: a double stitch and its fold)
  const t = new THREE.CanvasTexture(c); t.name = 'tentCanvas'; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return t;
}

// The big square canvas tent of desert camps (the owner's choice of 19 Nov: «خيمة برزنتي مربعة» big and real): 5 x 5 m,
// walls 1.9 m, a pyramid roof to 3.3 m on a centre pole, a brown valance round the eaves and a brown hem at the foot,
// guy ropes from the eaves to pegs, the door's flap rolled up and tied, a window each side; inside, a red lining with
// a Sadu band, a carpet and cushions along the back, seen through the door. Its door at the origin facing +z.
function bigTent(add, addCanvas) {
  const S = 5, h = S / 2, WALL = 1.9, PEAK = 3.3, Z = -h;      // (the tent's middle at z = -2.5)
  const CREAM = '#efe4c8', TRIM = '#7c5233';
  // the four walls (the front one round its door), each a little drawn in at its middle as canvas hangs
  const sag = (u, v) => Math.sin(Math.PI * u) * 0.04 * (1 - v);
  const wall = (x0, z0, x1, z1, nx, nz, uFrom = 0, uTo = 1, vFrom = 0, vTo = 1) => addCanvas(cloth((u, v) => {
    const uu = uFrom + (uTo - uFrom) * u, vv = vFrom + (vTo - vFrom) * v;
    return new THREE.Vector3(x0 + (x1 - x0) * uu - nx * sag(uu, vv), WALL * vv, Z + z0 + (z1 - z0) * uu - nz * sag(uu, vv));
  }, 10, 4, S * (uTo - uFrom), WALL * (vTo - vFrom)), CREAM);
  wall(-h, -h, h, -h, 0, -1);                       // back
  wall(-h, h, -h, -h, -1, 0); wall(h, -h, h, h, 1, 0);      // sides
  const door = { w: 1.4, h: 1.8 }, du = door.w / S / 2;
  wall(-h, h, h, h, 0, 1, 0, 0.5 - du); wall(-h, h, h, h, 0, 1, 0.5 + du, 1);                    // front, either side of the door
  wall(-h, h, h, h, 0, 1, 0.5 - du, 0.5 + du, door.h / WALL, 1);                                  // over the door
  // the roof: four panels from the eaves to the peak, sagging between the pole and the corners
  const corners = [[-h, -h], [h, -h], [h, h], [-h, h]];
  for (let k = 0; k < 4; k++) {
    const [ax, az] = corners[k], [bx, bz] = corners[(k + 1) % 4];
    addCanvas(cloth((u, v) => {
      const x = (ax + (bx - ax) * u) * (1 - v), z = (az + (bz - az) * u) * (1 - v);
      return new THREE.Vector3(x, WALL + (PEAK - WALL) * v - 0.14 * Math.sin(Math.PI * u) * Math.sin(Math.PI * v), Z + z);
    }, 10, 8, S, Math.hypot(h, PEAK - WALL)), CREAM);
  }
  // the valance round the eaves (30 cm, a hand out from the wall) and the hem at the foot (25 cm)
  for (const [x0, z0, x1, z1, nx, nz] of [[-h, -h, h, -h, 0, -1], [h, -h, h, h, 1, 0], [h, h, -h, h, 0, 1], [-h, h, -h, -h, -1, 0]]) {
    const o = 0.06;
    addCanvas(cloth((u, v) => new THREE.Vector3(x0 + (x1 - x0) * u + nx * o, WALL - 0.3 + 0.32 * v, Z + z0 + (z1 - z0) * u + nz * o), 10, 1, S, 0.32), TRIM);
    const hem = (a, b) => addCanvas(cloth((u, v) => new THREE.Vector3(x0 + (x1 - x0) * (a + (b - a) * u) + nx * 0.012, 0.25 * v, Z + z0 + (z1 - z0) * (a + (b - a) * u) + nz * 0.012), 6, 1, S * (b - a), 0.25), TRIM);
    if (nz === 1) { hem(0, 0.5 - du); hem(0.5 + du, 1); } else hem(0, 1);
  }
  // the door: its flap rolled up over it and tied with two straps; the side windows, their flaps rolled up too
  add(at(cyl(0.1, 0.1, door.w + 0.1, 12), 0, door.h + 0.07, Z + h + 0.11, 0, 0, Math.PI / 2), CREAM, 0.2);      // (on the front wall: z = Z + h)
  for (const x of [-0.5, 0.5]) add(at(box(0.04, 0.3, 0.02), x, door.h + 0.03, Z + h + 0.22), TRIM, 0);
  for (const sx of [-1, 1]) {
    add(at(box(0.02, 0.6, 1.0), sx * (h + 0.015), 1.15, Z), '#2b241d', 0);                                 // the window's opening, its mesh dark
    add(at(cyl(0.07, 0.07, 1.05, 10), sx * (h + 0.09), 1.52, Z, 0, Math.PI / 2), CREAM, 0.2);              // its flap rolled
  }
  // the pole, and the ropes from the eaves' corners and middles to pegs 1.6 m out
  add(at(cyl(0.05, 0.06, PEAK, 10), 0, PEAK / 2, Z), '#8a6a4a', 0.1);
  for (const [x, z] of [[-h, -h], [h, -h], [h, h], [-h, h], [0, -h], [0, h], [-h, 0], [h, 0]]) {
    if (x === 0 && z === h) continue;      // (none across the door)
    const dx = Math.sign(x), dz = Math.sign(z), px = x + dx * 1.6, pz = z + dz * 1.6;
    add(between([x + dx * 0.06, WALL - 0.02, Z + z + dz * 0.06], [px, 0.05, Z + pz], 0.008), '#d8cdb4', 0);
    add(at(cyl(0.018, 0.012, 0.32, 5), px, 0.1, Z + pz, 0, 0.4 * dz, -0.4 * dx), '#7d7d7d', 0);
  }
  // inside: the lining (red, drawn a little in from the walls), its Sadu band, the carpet, the cushions along the back
  const IN = h - 0.05;
  for (const [x0, z0, x1, z1] of [[-IN, -IN, IN, -IN], [-IN, IN, -IN, -IN], [IN, -IN, IN, IN]]) {
    add(cloth((u, v) => new THREE.Vector3(x0 + (x1 - x0) * u, WALL * 0.98 * v, Z + z0 + (z1 - z0) * u), 1, 1, 1, 1), '#8e2b22', 0.2);
    const ix = x0 === x1 ? -Math.sign(x0) * 0.006 : 0, iz = z0 === z1 ? -Math.sign(z0) * 0.006 : 0;      // (a few millimetres in from the lining)
    for (const [y, c] of [[1.35, '#1d1814'], [1.42, '#efe6d6'], [1.49, '#1d1814']]) add(cloth((u, v) => new THREE.Vector3(x0 + (x1 - x0) * u + ix, y + 0.07 * v, Z + z0 + (z1 - z0) * u + iz), 1, 1, 1, 1), c, 0);
  }
  add(at(box(S - 0.2, 0.02, S - 0.2), 0, 0.01, Z), '#8b2a20', 0);
  add(at(box(S - 0.6, 0.022, S - 0.6), 0, 0.012, Z), '#b7843f', 0);
  add(at(box(S - 0.9, 0.024, S - 0.9), 0, 0.013, Z), '#7a1f1a', 0);
  add(at(box(S - 0.8, 0.18, 0.62), 0, 0.11, Z - IN + 0.4), '#6e1d18', 0.15);
  add(at(box(S - 0.8, 0.42, 0.18), 0, 0.33, Z - IN + 0.12), '#6e1d18', 0.15);
}

export function buildCamp(kind) {
  const parts = [], cloths = [];
  const add = (geo, hex, shade) => parts.push(painted(geo, hex, shade));
  const addCanvas = (geo, hex) => cloths.push(painted(geo, hex, 0.08));
  bigTent(add, addCanvas);
  // the supplies on the tent's right: three blue water jerrycans, a green fuel can, a cooler, two boxes, a gas cylinder
  const SX = 3.4;      // (out past the big tent's right wall and its ropes' pegs' line)
  for (let i = 0; i < 3; i++) add(at(box(0.25, 0.42, 0.34), SX + i * 0.29, 0.21, 0.6), '#2c6ea6', 0.25);
  add(at(box(0.17, 0.46, 0.34), SX + 0.95, 0.23, 0.6), '#4f6b3a', 0.25);
  add(at(box(0.62, 0.4, 0.38), SX + 0.2, 0.2, 1.25), '#e9e6e0', 0.2);
  add(at(box(0.64, 0.08, 0.4), SX + 0.2, 0.44, 1.25), '#b23a2f', 0);
  add(at(box(0.5, 0.32, 0.36), SX + 0.9, 0.16, 1.3, 0.2), '#b88c58', 0.2);
  add(at(box(0.44, 0.28, 0.32), SX + 0.88, 0.46, 1.3, -0.1), '#c49a63', 0.2);
  add(at(cyl(0.15, 0.15, 0.55, 12), SX - 0.25, 0.275, 1.35), '#d8dad8', 0.2);
  // the fire in front-left: a ring of stones, firewood beside it
  for (let i = 0; i < 9; i++) { const a = (i / 9) * Math.PI * 2; add(at(new THREE.DodecahedronGeometry(0.12, 0), -2.6 + Math.cos(a) * 0.45, 0.07, 2.6 + Math.sin(a) * 0.45, a), '#8c8273', 0.3); }
  add(at(cyl(0.3, 0.38, 0.06, 10), -2.6, 0.03, 2.6), '#3b332c', 0);
  for (let i = 0; i < 6; i++) add(at(cyl(0.035, 0.04, 0.9, 6), -3.5, 0.06 + (i % 3) * 0.07, 1.9 + Math.floor(i / 3) * 0.08 + (i % 3) * 0.02, 0.15 * i, 0, Math.PI / 2), '#6b4c2e', 0.2);
  let net = null;
  if (kind === 'trapping') {
    // the pigeon cage on the tent's left: a wooden frame and wire bars
    const cx = -4.6, cz = -1.2;      // (past the tent's left wall and its pegs)
    add(at(box(0.72, 0.03, 0.47), cx, 0.06, cz), '#7b5a3a', 0);
    add(at(box(0.72, 0.03, 0.47), cx, 0.5, cz), '#7b5a3a', 0);
    for (const [x, z] of [[-0.35, -0.22], [0.35, -0.22], [-0.35, 0.22], [0.35, 0.22]]) add(at(box(0.03, 0.47, 0.03), cx + x, 0.28, cz + z), '#7b5a3a', 0);
    for (let i = 1; i < 9; i++) for (const z of [-0.22, 0.22]) add(at(cyl(0.004, 0.004, 0.44, 4), cx - 0.35 + i * 0.0778, 0.28, cz + z), '#9a9a96', 0);
    for (let i = 1; i < 6; i++) for (const x of [-0.35, 0.35]) add(at(cyl(0.004, 0.004, 0.44, 4), cx + x, 0.28, cz - 0.22 + i * 0.0733), '#9a9a96', 0);
    // the bird net 3 x 2 m between two poles, 6 m out in front of the camp
    const nx = 0, nz = 9;
    for (const x of [-1.5, 1.5]) add(at(cyl(0.025, 0.03, 2.3, 6), nx + x, 1.15, nz), '#5a5a55', 0);
    const c = document.createElement('canvas'); c.width = c.height = 64;
    const g = c.getContext('2d'); g.strokeStyle = 'rgba(40,40,38,1)'; g.lineWidth = 2;
    for (let i = 0; i <= 64; i += 16) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, 64); g.stroke(); g.beginPath(); g.moveTo(0, i); g.lineTo(64, i); g.stroke(); }
    const tex = new THREE.CanvasTexture(c); tex.name = 'birdNet'; tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.repeat.set(30, 20); tex.colorSpace = THREE.SRGBColorSpace;
    net = new THREE.Mesh(new THREE.PlaneGeometry(3, 2), new THREE.MeshStandardMaterial({ map: tex, alphaTest: 0.5, transparent: false, side: THREE.DoubleSide, roughness: 1 }));
    net.position.set(nx, 1.2, nz); net.name = 'camp net';
  }
  const solid = new THREE.Mesh(mergeGeometries(parts, false), new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.92, side: THREE.DoubleSide }));
  solid.name = 'camp'; solid.castShadow = true; solid.receiveShadow = true;
  const canvas = new THREE.Mesh(mergeGeometries(cloths, false), new THREE.MeshStandardMaterial({ map: canvasTexture(), vertexColors: true, roughness: 0.95, side: THREE.DoubleSide }));
  canvas.name = 'tent canvas'; canvas.castShadow = true; canvas.receiveShadow = true;
  const group = new THREE.Group(); group.name = `camp ${kind}`;
  group.add(solid, canvas);
  if (net) { net.castShadow = true; group.add(net); }
  return group;
}

// The ground's near detail at the gravel plains and the coasts (the owner's choice of 19 Nov: gravel made by code until
// his photos come): a pale desert pavement of small stones close together, 1-6 cm and a few to 10 cm (the texture repeats every 22 m near the camera: 2 cm a
// pixel), its average held at 1/1.55 in every channel so the land's shader, which multiplies it by 1.55, leaves the
// satellite colour as it is and adds only the grain (his Qassim sand photo averages red and reddened الحماد's plain)
export function gravelTexture() {
  const N = 1024, c = document.createElement('canvas'); c.width = c.height = N;
  const g = c.getContext('2d');
  let seed = 7; const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  g.fillStyle = 'rgb(176,164,148)'; g.fillRect(0, 0, N, N);
  for (let i = 0; i < 2600; i++) {      // (fine grit, then pebbles, light and dark, a few larger stones)
    const x = rnd() * N, y = rnd() * N, r = 0.6 + rnd() * 1.4, k = 120 + rnd() * 110;
    g.fillStyle = `rgb(${k},${k - 10},${k - 22})`; g.fillRect(x, y, r, r);
  }
  for (let i = 0; i < 26000; i++) {      // (a desert pavement: small stones close together, 1-6 cm; a few larger)
    const big = rnd() < 0.03, x = rnd() * N, y = rnd() * N, r = big ? 2 + rnd() * 2.5 : 0.6 + rnd() * rnd() * 1.6, dark = rnd() < 0.5, k = dark ? 85 + rnd() * 55 : 165 + rnd() * 55;
    g.fillStyle = `rgb(${k + rnd() * 18},${k - 4 - rnd() * 10},${k - 16 - rnd() * 14})`;
    g.beginPath(); g.ellipse(x, y, r, r * (0.6 + rnd() * 0.4), rnd() * 3.14, 0, 6.283); g.fill();
    if (!dark) { g.fillStyle = 'rgba(60,48,36,0.35)'; g.beginPath(); g.ellipse(x + r * 0.35, y + r * 0.4, r, r * 0.55, 0, 0, 6.283); g.fill(); }      // (each stone's shadow on its sunless side)
  }
  // the average to 1/1.55 in linear light in every channel
  const img = g.getImageData(0, 0, N, N), d = img.data, lin = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
  const srgb = (v) => Math.round(255 * (v <= 0.0031308 ? v * 12.92 : 1.055 * v ** (1 / 2.4) - 0.055));
  const sum = [0, 0, 0];
  for (let i = 0; i < d.length; i += 4) for (let k = 0; k < 3; k++) sum[k] += lin(d[i + k]);
  const n = d.length / 4, gain = sum.map((x) => (1 / 1.55) / (x / n));
  for (let i = 0; i < d.length; i += 4) for (let k = 0; k < 3; k++) d[i + k] = Math.min(255, srgb(Math.min(1, lin(d[i + k]) * gain[k])));
  g.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c); t.name = 'gravel'; t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = 4;
  return t;
}
