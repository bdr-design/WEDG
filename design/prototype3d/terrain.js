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

export async function buildTerrain(scene, renderer, sandTex) {
  const meta = await (await fetch('terrain.json')).json();
  const hm = await pixels('terrain_h.png');
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
  const sat = await new THREE.TextureLoader().loadAsync('terrain_sat.jpg');
  sat.colorSpace = THREE.SRGBColorSpace; sat.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());

  // satellite colour, with the owner's sand photo blended in close to the camera for ground detail
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

  const grid = (x0, x1, z0, z1, nx, nz, sink) => {
    const g = new THREE.PlaneGeometry(1, 1, nx, nz); g.rotateX(-Math.PI / 2);
    const p = g.attributes.position, uv = g.attributes.uv;
    for (let i = 0; i < p.count; i++) {
      const x = x0 + (p.getX(i) + 0.5) * (x1 - x0), z = z0 + (p.getZ(i) + 0.5) * (z1 - z0);
      p.setXYZ(i, x, heightAt(x, z) - (sink ? sink(x, z) : 0), z);
      uv.setXY(i, (x - meta.xWest) / W, 1 - (z - meta.zNorth) / D);
    }
    g.computeVertexNormals();
    const m = new THREE.Mesh(g, mat); m.receiveShadow = true; scene.add(m); return m;
  };
  // three rings, each tucked a few metres under the finer one inside it (about 73k triangles in all):
  // 4 x 4 km around the yard at 50 m, 12 x 12 km at 100 m (Aban al-Asmar), the whole 70 km area at about 550 m
  const inside = (r) => (x, z) => (Math.abs(x) < r && Math.abs(z) < r ? 6 : 0);
  grid(-2000, 2000, -2000, 2000, 80, 80);
  // sink every coarse vertex inside the finer ring (its edge vertices included), so no band of the
  // two surfaces lies at the same height and flickers
  grid(-6000, 6000, -6000, 6000, 120, 120, inside(1999));
  grid(meta.xWest, meta.xEast, meta.zNorth, meta.zSouth, 128, 121, inside(5999));
  return { meta, heightAt };
}
