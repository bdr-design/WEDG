// The camp at a hunting or trapping ground (T18 part C, the approved storyboard design/hunt/trip.cjs frames 7, 8 and 13):
// the tent, the camp's supplies, and for trapping the pigeon cage and the bird net. Built by code from real sizes as a
// provisional look for the owner's eye (he has sent no photos of these; the plan's question 4): a canvas ridge tent
// 4 x 3 m and 2.2 m high of the kind sold for desert camping, 20-litre water jerrycans, a fuel can, a cooler, food
// boxes, a gas cylinder, firewood and a ring of stones for the fire; a wire pigeon cage 70 x 45 x 45 cm; a vertical
// bird net (the trappers' dho-gaza) 3 m wide and 2 m high between two poles.
// Everything solid is one vertex-coloured mesh (one draw, one shadow draw); the net is the only other (a small grid
// texture cut by alpha test). The camp's origin is the tent's door; +x is the tent's right as one faces it.
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

// the ridge tent: two roof panels from the ridge to the eaves, low side walls, the two gables with the door's dark
// opening in the front one; indexed, with uvs, so it merges with the boxes
function ridgeTent(W = 3, L = 4, H = 2.2, wall = 0.55) {
  const hw = W / 2, hl = L / 2;
  const P = [], I = [], UV = [];
  const quad = (a, b, c, d) => { const o = P.length / 3; P.push(...a, ...b, ...c, ...d); UV.push(0, 0, 1, 0, 1, 1, 0, 1); I.push(o, o + 1, o + 2, o, o + 2, o + 3); };
  const tri = (a, b, c) => { const o = P.length / 3; P.push(...a, ...b, ...c); UV.push(0, 0, 1, 0, 0.5, 1); I.push(o, o + 1, o + 2); };
  for (const s of [-1, 1]) {
    quad([s * hw, wall, hl], [s * hw, wall, -hl], [0, H, -hl], [0, H, hl]);            // roof panel
    quad([s * hw, 0, hl], [s * hw, 0, -hl], [s * hw, wall, -hl], [s * hw, wall, hl]);  // side wall
  }
  for (const z of [hl, -hl]) {
    quad([-hw, 0, z], [hw, 0, z], [hw, wall, z], [-hw, wall, z]);
    tri([-hw, wall, z], [hw, wall, z], [0, H, z]);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(P, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(UV, 2));
  g.setIndex(I);
  g.computeVertexNormals();      // (shared corners: each face has its own vertices, so the normals stay flat)
  // both faces lit: the panels are drawn double-sided by the material; normals pointed out from the tent's middle
  const n = g.attributes.normal, p = g.attributes.position;
  for (let i = 0; i < n.count; i++) {
    const out = new THREE.Vector3(p.getX(i), p.getY(i) - H / 2, p.getZ(i)), nn = new THREE.Vector3(n.getX(i), n.getY(i), n.getZ(i));
    if (nn.dot(out) < 0) n.setXYZ(i, -nn.x, -nn.y, -nn.z);
  }
  return g;
}

export function buildCamp(kind) {
  const parts = [];
  const add = (geo, hex, shade) => parts.push(painted(geo, hex, shade));
  // the tent, its door facing +z (the camp's front), set back 2.2 m so the door is at the origin
  const T = { W: 3, L: 4, H: 2.2 }, tz = -T.L / 2;
  add(at(ridgeTent(T.W, T.L, T.H), 0, 0, tz), '#d4c19a', 0.18);
  add(at(box(0.9, 1.5, 0.02), 0, 0.75, 0.005), '#3a2f24', 0);                                  // the door's opening
  add(at(cyl(0.025, 0.025, T.H + 0.25, 6), 0, (T.H + 0.25) / 2, 0.03), '#7a6a52', 0);           // front pole
  add(at(cyl(0.025, 0.025, T.H + 0.25, 6), 0, (T.H + 0.25) / 2, -T.L - 0.03), '#7a6a52', 0);    // back pole
  for (const [x, z] of [[-2.3, 0.9], [2.3, 0.9], [-2.3, -T.L - 0.9], [2.3, -T.L - 0.9]]) add(at(cyl(0.02, 0.02, 0.3, 5), x, 0.12, z), '#8a8a8a', 0);      // the guy ropes' pegs
  // the supplies on the tent's right: three blue water jerrycans, a green fuel can, a cooler, two boxes, a gas cylinder
  for (let i = 0; i < 3; i++) add(at(box(0.25, 0.42, 0.34), 2.0 + i * 0.29, 0.21, -0.6), '#2c6ea6', 0.25);
  add(at(box(0.17, 0.46, 0.34), 2.95, 0.23, -0.6), '#4f6b3a', 0.25);
  add(at(box(0.62, 0.4, 0.38), 2.2, 0.2, -1.25), '#e9e6e0', 0.2);
  add(at(box(0.64, 0.08, 0.4), 2.2, 0.44, -1.25), '#b23a2f', 0);
  add(at(box(0.5, 0.32, 0.36), 2.9, 0.16, -1.3, 0.2), '#b88c58', 0.2);
  add(at(box(0.44, 0.28, 0.32), 2.88, 0.46, -1.3, -0.1), '#c49a63', 0.2);
  add(at(cyl(0.15, 0.15, 0.55, 12), 1.75, 0.275, -1.35), '#d8dad8', 0.2);
  // the fire in front-left: a ring of stones, firewood beside it
  for (let i = 0; i < 9; i++) { const a = (i / 9) * Math.PI * 2; add(at(new THREE.DodecahedronGeometry(0.12, 0), -2.2 + Math.cos(a) * 0.45, 0.07, 1.6 + Math.sin(a) * 0.45, a), '#8c8273', 0.3); }
  add(at(cyl(0.3, 0.38, 0.06, 10), -2.2, 0.03, 1.6), '#3b332c', 0);
  for (let i = 0; i < 6; i++) add(at(cyl(0.035, 0.04, 0.9, 6), -3.1, 0.06 + (i % 3) * 0.07, 0.9 + Math.floor(i / 3) * 0.08 + (i % 3) * 0.02, 0.15 * i, 0, Math.PI / 2), '#6b4c2e', 0.2);
  let net = null;
  if (kind === 'trapping') {
    // the pigeon cage on the tent's left: a wooden frame and wire bars
    const cx = -2.1, cz = -0.8;
    add(at(box(0.72, 0.03, 0.47), cx, 0.06, cz), '#7b5a3a', 0);
    add(at(box(0.72, 0.03, 0.47), cx, 0.5, cz), '#7b5a3a', 0);
    for (const [x, z] of [[-0.35, -0.22], [0.35, -0.22], [-0.35, 0.22], [0.35, 0.22]]) add(at(box(0.03, 0.47, 0.03), cx + x, 0.28, cz + z), '#7b5a3a', 0);
    for (let i = 1; i < 9; i++) for (const z of [-0.22, 0.22]) add(at(cyl(0.004, 0.004, 0.44, 4), cx - 0.35 + i * 0.0778, 0.28, cz + z), '#9a9a96', 0);
    for (let i = 1; i < 6; i++) for (const x of [-0.35, 0.35]) add(at(cyl(0.004, 0.004, 0.44, 4), cx + x, 0.28, cz - 0.22 + i * 0.0733), '#9a9a96', 0);
    // the bird net 3 x 2 m between two poles, 6 m out in front of the camp
    const nx = 0, nz = 6.5;
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
  const group = new THREE.Group(); group.name = `camp ${kind}`;
  group.add(solid);
  if (net) { net.castShadow = true; group.add(net); }
  return group;
}
