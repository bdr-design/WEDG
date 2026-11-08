// Export hook (my copy only): build the yard exactly as the prototype does, then dump every fixed
// object in world space, every scatter/tree instance, the canvas textures and the vehicle placements.
import * as THREE from 'three';
import { buildWorld, LAYOUT, VEHICLES, SCATTER, DRAPE } from './world.js';

const renderer = new THREE.WebGLRenderer({ antialias: false });
renderer.setSize(32, 32);
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
const sand = new THREE.Texture();
buildWorld(scene, renderer, sand);
scene.updateMatrixWorld(true);

const r5 = (v) => Math.round(v * 1e5) / 1e5;
const lin = (c) => [r5(c.r), r5(c.g), r5(c.b)];
const textures = {};
function texName(t) {
  if (!t) return null;
  const name = t.name || ('tex_' + t.source.uuid.slice(0, 8));
  if (!textures[name]) {
    const img = t.image;
    textures[name] = { w: img.width, h: img.height, png: img.toDataURL('image/png'), wrapS: t.wrapS, wrapT: t.wrapT, flipY: t.flipY };
  }
  return name;
}
function matRecord(m) {
  return {
    type: m.type, color: m.color ? lin(m.color) : null, roughness: m.roughness, metalness: m.metalness,
    emissive: m.emissive ? lin(m.emissive) : [0, 0, 0], emissiveIntensity: m.emissiveIntensity ?? 1,
    transparent: m.transparent, opacity: m.opacity, alphaTest: m.alphaTest, side: m.side, depthWrite: m.depthWrite,
    map: texName(m.map), uvMatrix: m.map ? (m.map.updateMatrix(), Array.from(m.map.matrix.elements)) : null,
    polygonOffset: m.polygonOffset ? m.polygonOffsetFactor : 0,
  };
}
function geomRecord(g, matrix, uvMatrix) {
  const geo = g.clone();
  if (!geo.index) geo.setIndex(Array.from({ length: geo.attributes.position.count }, (_, i) => i));
  if (!geo.attributes.normal) geo.computeVertexNormals();
  geo.applyMatrix4(matrix);
  let idx = Array.from(geo.index.array);
  if (matrix.determinant() < 0) for (let i = 0; i < idx.length; i += 3) [idx[i + 1], idx[i + 2]] = [idx[i + 2], idx[i + 1]];
  const pos = Array.from(geo.attributes.position.array, r5), nor = Array.from(geo.attributes.normal.array, r5);
  let uv = null;
  if (geo.attributes.uv) {
    const a = geo.attributes.uv.array; uv = new Array(a.length);
    const e = uvMatrix || [1, 0, 0, 0, 1, 0, 0, 0, 1];
    for (let i = 0; i < a.length; i += 2) { const u = a[i], v = a[i + 1]; uv[i] = r5(e[0] * u + e[3] * v + e[6]); uv[i + 1] = r5(e[1] * u + e[4] * v + e[7]); }
  }
  return { pos, nor, uv, idx };
}

// ---- classify
const scatterMeshes = new Set(SCATTER.map((c) => c.m));
const drapeMeshes = new Set(DRAPE);
const kinds = new Map();   // parent group -> kind
for (const c of SCATTER) if (!kinds.has(c.m.parent)) kinds.set(c.m.parent, ['grass', 'bush', 'stone'][kinds.size]);
let trunk = null, clump = null;
scene.traverse((o) => {
  if (!o.isInstancedMesh || scatterMeshes.has(o)) return;
  if (o.geometry.type === 'CylinderGeometry' && o.geometry.parameters.radialSegments === 7) trunk = o;
  if (o.material.map && o.material.alphaTest === 0.35) clump = o;
});

const parts = [], lines = [], skipped = [];
const M = new THREE.Matrix4(), IM = new THREE.Matrix4();
scene.traverse((o) => {
  if (o === trunk || o === clump || scatterMeshes.has(o)) return;
  if (drapeMeshes.has(o)) { texName(o.material.map); o.geometry.computeBoundingBox(); skipped.push({ what: o.material.map ? 'road' : 'shoulder', box: o.geometry.boundingBox, pos: o.position }); return; }
  if (o.isLineSegments) { const p = o.geometry.attributes.position; for (let i = 0; i < p.count; i++) { const v = new THREE.Vector3().fromBufferAttribute(p, i).applyMatrix4(o.matrixWorld); lines.push(r5(v.x), r5(v.y), r5(v.z)); } lines.color = o.material.color; return; }
  if (!o.isMesh) return;
  const mat = matRecord(o.material);
  const n = o.isInstancedMesh ? o.count : 1;
  for (let i = 0; i < n; i++) {
    if (o.isInstancedMesh) { o.getMatrixAt(i, IM); M.multiplyMatrices(o.matrixWorld, IM); } else M.copy(o.matrixWorld);
    const g = geomRecord(o.geometry, M, mat.uvMatrix);
    let cx = 0, cz = 0; const k = g.pos.length / 3; for (let j = 0; j < g.pos.length; j += 3) { cx += g.pos[j]; cz += g.pos[j + 2]; }
    parts.push({ name: o.name || o.geometry.type, geoType: o.geometry.type, params: o.geometry.parameters || null, groups: o.geometry.groups, mat, ...g, cx: cx / k, cz: cz / k });
  }
});

// ---- scatter instances (prototype order: per cell, shuffled so a prefix is an even sample)
const decompose = (m) => { const p = new THREE.Vector3(), q = new THREE.Quaternion(), s = new THREE.Vector3(); m.decompose(p, q, s); return { p, q, s }; };
const scatter = { grass: { cells: [] }, bush: { cells: [] }, stone: { cells: [] } };
const col = new THREE.Color();
for (const c of SCATTER) {
  const kind = kinds.get(c.m.parent), K = scatter[kind];
  K.bands = c.bands; K.cast = c.cast; K.shadowDist = c.shadowDist;
  const inst = [];
  for (let i = 0; i < c.n; i++) {
    c.m.getMatrixAt(i, IM); const { p, q, s } = decompose(IM);
    const yaw = 2 * Math.atan2(q.y, q.w);
    c.m.getColorAt(i, col);
    inst.push([p.x, p.y, p.z, yaw, s.x, s.y, s.z, q.x, q.y, q.z, q.w, col.r, col.g, col.b]);
  }
  K.cells.push({ x: c.x, z: c.z, n: c.n, inst });
}
const geoOut = (g) => { const r = geomRecord(g, new THREE.Matrix4(), null); return r; };
for (const [kind, mesh] of [['grass', null], ['bush', null], ['stone', null]]) {
  const m = SCATTER.find((c) => kinds.get(c.m.parent) === kind).m;
  scatter[kind].geo = geoOut(m.geometry); scatter[kind].mat = matRecord(m.material);
}
const treeInst = (o, withColor) => {
  const out = [];
  for (let i = 0; i < o.count; i++) {
    o.getMatrixAt(i, IM); const { p, q, s } = decompose(IM);
    const row = [p.x, p.y, p.z, q.x, q.y, q.z, q.w, s.x, s.y, s.z];
    if (withColor) { o.getColorAt(i, col); row.push(col.r, col.g, col.b); }
    out.push(row);
  }
  return out;
};
scatter.tamarisk_trunk = { geo: geoOut(trunk.geometry), mat: matRecord(trunk.material), inst: treeInst(trunk, false) };
scatter.tamarisk_clump = { geo: geoOut(clump.geometry), mat: matRecord(clump.material), inst: treeInst(clump, true) };

// ---- vehicles: the same transforms the page uses
const vehicles = [];
const hayBales = [];
for (const v of VEHICLES) {
  const o = new THREE.Group(); o.position.set(v.x, 0, v.z); o.rotation.y = v.rot; o.updateMatrixWorld(true);
  vehicles.push({ model: v.model, x: v.x, z: v.z, yaw: v.rot, tint: v.tint || null, hay: !!v.hay, tintLinear: v.tint ? lin(new THREE.Color(v.tint)) : null });
  if (v.hay) for (let i = 0; i < 3; i++) {
    const b = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.42, 1.0)); b.position.set(-0.9 - i * 0.6, 1.4, 0); o.add(b); o.updateMatrixWorld(true);
    hayBales.push(geomRecord(b.geometry, b.matrixWorld, null));
  }
}
const C = LAYOUT.camp, rig = new THREE.Group();
rig.position.set(C.x - 2, 0, C.z - 22); rig.rotation.y = 0.35;
const car = new THREE.Group(); rig.add(car);
const head = new THREE.Group(); head.position.set(6.85, 0, 0); rig.add(head);
rig.updateMatrixWorld(true);
const wp = (o) => { const p = new THREE.Vector3(), q = new THREE.Quaternion(), s = new THREE.Vector3(); o.matrixWorld.decompose(p, q, s); return { x: p.x, y: p.y, z: p.z, yaw: 2 * Math.atan2(q.y, q.w) }; };
const rigOut = { rig: { x: rig.position.x, z: rig.position.z, yaw: 0.35 }, caravan: wp(car), tractor: wp(head), tractorLocal: [6.85, 0, 0] };
const hayColor = lin(new THREE.Color('#b3a256'));

window.__export = JSON.stringify({ parts, lines: { pos: lines, color: lin(lines.color) }, skipped, textures, scatter, vehicles, hayBales, hayColor, rig: rigOut, layout: LAYOUT });
window.__ready = true;
