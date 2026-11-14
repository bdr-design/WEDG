import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const q = new URLSearchParams(location.search);
const file = q.get('f'), view = q.get('v') || 'side', mode = q.get('m') || 'lit', size = +(q.get('s') || 1.2);
const W = 1200, H = 800;
const r = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true }); r.setSize(W, H); r.setPixelRatio(1);
r.outputColorSpace = THREE.SRGBColorSpace; r.toneMapping = THREE.NeutralToneMapping; document.body.appendChild(r.domElement);
const sc = new THREE.Scene(); sc.background = new THREE.Color('#777');
// raking light: low, from the front-left, plus weak fill (as the game's afternoon: sun 4.4, env-like hemi)
const sun = new THREE.DirectionalLight(mode === 'night' ? '#b8c8ff' : '#ffdcae', mode === 'rake' ? 5 : mode === 'night' ? 0.35 : 3.5);
sun.position.set(...(mode === 'rake' ? [2, 0.35, 1.2] : [1.5, 2, 2])); sc.add(sun);
sc.add(new THREE.HemisphereLight('#bcd', '#875', mode === 'rake' ? 0.25 : mode === 'night' ? 0.04 : 0.8)); if (mode === 'night') sc.background = new THREE.Color('#05070c'); else if (persp) sc.background = new THREE.Color('#b9a17f'); if (mode === 'even') { sc.add(new THREE.AmbientLight('#fff', 1.6)); }
const persp = view === 'far' || view === 'fp' || view === 'hd';
const W2 = view === 'far' ? 956 : W, H2 = view === 'far' ? 440 : H;
if (persp) { r.setSize(956, 440); r.setPixelRatio(2); }
const cam = persp ? new THREE.PerspectiveCamera(40, 956 / 440, 0.1, 500) : view === 'tq' ? new THREE.PerspectiveCamera(30, W / H, 0.01, 50) : new THREE.OrthographicCamera(-size/2, size/2, size/2*H/W, -size/2*H/W, 0.01, 50);
new GLTFLoader().load(file, (g) => {
  const o = g.scene; sc.add(o);
  o.traverse((m) => { if (m.isMesh) { if (mode === 'nonormal') m.material.normalMap = null; if (mode === 'normalonly') { m.material.map = null; m.material.color.set('#bbb'); } if (mode==='rake') {} m.material.needsUpdate = true; } });
  const b = new THREE.Box3().setFromObject(o), c = b.getCenter(new THREE.Vector3());
  const t = q.get('t') ? new THREE.Vector3(...q.get('t').split(',').map(Number)) : c;
  const dirs = { side: [0, 0, 1], other: [0, 0, -1], front: [1, 0, 0], tq: [1.1, 0.5, 1.4], head: [0.6, 0.15, 1], top: [0, 1, 0.0001], ftq: [1, 0.8, 0.5], back: [-1, 0, 0], below: [0.0001, -1, 0], btq: [-1.1, 0.5, -1.4], far: [0, 0, 1], fp: [0, 0, 1], hd: [0, 0, 1] };
  const d = new THREE.Vector3(...dirs[view]).normalize();
  const A = (+(q.get('a') || 45)) * Math.PI / 180;
  if (view === 'fp' || view === 'hd') { const dist = +(q.get('d') || 1.5); cam.position.set(t.x + dist * Math.cos(A), view === 'fp' ? 1.66 : t.y, t.z + dist * Math.sin(A)); cam.lookAt(t); } else if (view === 'far') { const dist = +(q.get('d') || 15); cam.position.set(t.x + dist * 0.3, 1.6 + dist * Math.tan(0.2), t.z + dist); cam.lookAt(t); } else { cam.position.copy(t).addScaledVector(d, view === 'tq' ? size * 2.2 : 5); cam.lookAt(t); }
  if (mode === 'even') { const l = new THREE.DirectionalLight('#fff', 1.5); l.position.copy(cam.position); sc.add(l); } r.render(sc, cam); document.title = 'done';
});
