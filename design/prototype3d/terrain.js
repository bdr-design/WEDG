// Real Najd terrain around the yard: elevation from 30 m data (AWS Terrain Tiles / SRTM),
// colour from a cloud-free Sentinel-2 scene (NASA HLS S30, 2026-01-17).
// The area is 70 x 66 km of western Qassim: Aban al-Asmar 6.4 km east of the yard,
// Aban al-Ahmar 37 km south-west, Wadi al-Rumah between them, Nafud sand to the west.
import * as THREE from 'three';

async function pixels(url) {
  const img = new Image(); img.src = url; await img.decode();
  const c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
  const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(img, 0, 0);
  return { data: g.getImageData(0, 0, img.width, img.height).data, w: img.width, h: img.height };
}

// A land's data (dir: '' for the farm's, 'grounds/<ground>/' for a hunting or trapping ground's, T18 part C): its
// metadata, heights and satellite colour, read once and kept while it is the current land
export async function loadLand(dir, renderer) {
  const meta = await (await fetch(`${dir}terrain.json`)).json();
  const hm = await pixels(`${dir}terrain_h.png`);
  const N = meta.size;
  const H = new Float32Array(N * N);
  for (let i = 0; i < N * N; i++) H[i] = ((hm.data[i * 4] << 8) | hm.data[i * 4 + 1]) / 10 - 1000;
  const W = meta.xEast - meta.xWest, D = meta.zSouth - meta.zNorth;
  const heightAt = (x, z) => {
    const u = THREE.MathUtils.clamp((x - meta.xWest) / W, 0, 1) * (N - 1), v = THREE.MathUtils.clamp((z - meta.zNorth) / D, 0, 1) * (N - 1);
    const i = Math.floor(u), j = Math.floor(v), fu = u - i, fv = v - j, i1 = Math.min(i + 1, N - 1), j1 = Math.min(j + 1, N - 1);
    const a = H[j * N + i], b = H[j * N + i1], c = H[j1 * N + i], d = H[j1 * N + i1];
    return (a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv;
  };
  const sat = await new THREE.TextureLoader().loadAsync(`${dir}terrain_sat.jpg`);
  sat.colorSpace = THREE.SRGBColorSpace; sat.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy()); sat.name = `${dir || 'farm '}terrain_sat`;
  return { dir, meta, N, H, heightAt, W, D, sat };
}

// the land's material: satellite colour, with the owner's sand photo blended in close to the camera for ground detail
function landMaterial(sat, sandTex) {
  const mat = new THREE.MeshStandardMaterial({ map: sat, roughness: 1 });
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.detailMap = { value: sandTex };
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vWorldP;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWorldP = (modelMatrix * vec4(transformed, 1.0)).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nuniform sampler2D detailMap;\nvarying vec3 vWorldP;')
      .replace('#include <map_fragment>', `#include <map_fragment>
        float dCam = distance(vWorldP, cameraPosition);
        vec3 det = texture2D(detailMap, vWorldP.xz / 22.0).rgb * 1.55;
        vec3 det2 = texture2D(detailMap, vWorldP.xz / 170.0).rgb * 1.55;
        float near = 1.0 - smoothstep(250.0, 1400.0, dCam);
        diffuseColor.rgb *= mix(mix(vec3(1.0), det2, 0.35), det, near * 0.85);`);
  };
  return mat;
}

// The land's three rings round a centre (cx, cz in the land's own metres), drawn with that centre at the world's origin:
// the farm's centre is its yard (0, 0); a camp's is its tent. Its heightAt is the world's ground there.
export function landRings(land, mat, cx = 0, cz = 0, parent = null) {
  const { meta, heightAt: h, W, D } = land;
  const h0 = cx || cz ? h(cx, cz) : 0;
  const heightAt = (x, z) => h(x + cx, z + cz) - h0;
  const group = new THREE.Group(); group.name = `land ${land.dir || 'farm'}`;
  if (parent) parent.add(group);
  const grid = (x0, x1, z0, z1, nx, nz, sink) => {
    const g = new THREE.PlaneGeometry(1, 1, nx, nz); g.rotateX(-Math.PI / 2);
    const p = g.attributes.position, uv = g.attributes.uv;
    for (let i = 0; i < p.count; i++) {
      const x = x0 + (p.getX(i) + 0.5) * (x1 - x0), z = z0 + (p.getZ(i) + 0.5) * (z1 - z0);
      p.setXYZ(i, x, heightAt(x, z) - (sink ? sink(x, z) : 0), z);
      uv.setXY(i, (x + cx - meta.xWest) / W, 1 - (z + cz - meta.zNorth) / D);
    }
    g.computeVertexNormals();
    const m = new THREE.Mesh(g, mat); m.receiveShadow = true; group.add(m); return m;
  };
  // three rings, each tucked a few metres under the finer one inside it (about 73k triangles in all):
  // 4 x 4 km around the yard at 50 m, 12 x 12 km at 100 m (Aban al-Asmar), the whole 70 km area at about 550 m
  const inside = (r) => (x, z) => (Math.abs(x) < r && Math.abs(z) < r ? 6 : 0);
  // drawn near to far (the depth key was each ring's centre, the same for all three, so the coarse rings went first and the
  // ground was shaded up to twice over on GPUs that do not sort it themselves: the review)
  grid(-2000, 2000, -2000, 2000, 80, 80).renderOrder = 0;
  // sink every coarse vertex inside the finer ring (its edge vertices included), so no band of the
  // two surfaces lies at the same height and flickers
  grid(-6000, 6000, -6000, 6000, 120, 120, inside(1999)).renderOrder = 0.1;
  grid(meta.xWest - cx, meta.xEast - cx, meta.zNorth - cz, meta.zSouth - cz, 128, 121, inside(5999)).renderOrder = 0.2;
  return { group, heightAt, dispose: () => { group.removeFromParent(); for (const m of group.children) m.geometry.dispose(); } };
}

// the farm's land, as it always was: its rings straight in the scene round the yard
export async function buildTerrain(scene, renderer, sandTex) {
  const land = await loadLand('', renderer);
  const mat = landMaterial(land.sat, sandTex);
  const r = landRings(land, mat, 0, 0, null);
  for (const m of [...r.group.children]) scene.add(m);      // (each ring a child of the scene, as before: the shadows' bake and the merges find them there)
  return { meta: land.meta, heightAt: land.heightAt, mat, land, rings: r };
}

// a camp's land (T18 part C): the ground's own (a far ground's cut, loaded now) or the farm's (a near ground), its
// rings round the camp's point, with that point at the world's origin
export async function buildCampLand(dir, farm, sandTex, renderer, cx = 0, cz = 0) {
  const land = dir ? await loadLand(dir, renderer) : farm.land;
  const mat = dir ? landMaterial(land.sat, sandTex) : farm.mat;
  const r = landRings(land, mat, cx, cz, null);
  return { ...r, land, mat, dispose: () => { r.dispose(); if (dir) { mat.dispose(); land.sat.dispose(); } } };
}
