import sys, numpy as np
sys.path.insert(0, '.')
from glb_read import read_glb, accessor
for f in sys.argv[1:]:
    js, b = read_glb(f); pr = js['meshes'][0]['primitives'][0]
    P = accessor(js, b, pr['attributes']['POSITION']) * 1000; UV = accessor(js, b, pr['attributes']['TEXCOORD_0']); I = accessor(js, b, pr['indices']).reshape(-1, 3)
    W = 512 if 'lod1' not in f else 256
    a3 = np.linalg.norm(np.cross(P[I[:, 1]] - P[I[:, 0]], P[I[:, 2]] - P[I[:, 0]]), axis=1) / 2
    u = UV[I] * W; d1 = u[:, 1] - u[:, 0]; d2 = u[:, 2] - u[:, 0]; a2 = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / 2
    dens = np.sqrt(a2 / np.maximum(a3, 1e-9))  # texels per mm
    med = np.median(dens); low = dens < 0.25 * med
    edge = (UV[I] < 0.01).any(axis=(1, 2)) | (UV[I] > 0.99).any(axis=(1, 2))
    # stretch: ratio of singular values of the 2x2 map
    print(f'{f.split("/")[-1]}: texel density median {med:.2f} texel/mm ({1/med:.1f} mm per texel); faces under 25% of median: {low.sum()} '
          f'({a3[low].sum()/a3.sum()*100:.2f}% of area); faces touching the atlas edge: {edge.sum()}; low&edge {(low&edge).sum()}; '
          f'sampler {js.get("samplers")}')
    if '--head' in sys.argv[0:1] or True:
        pts = {n.get('name'): n.get('translation') for n in js['nodes']}
        if 'eye_l' in pts and pts['eye_l']:
            e = np.array(pts['eye_l']) * 1000; c = P[I].mean(1); m = np.linalg.norm(c - e, axis=1) < 60
            print(f'   head (within 60 mm of the eye): median {np.median(dens[m]):.2f} texel/mm ({1/np.median(dens[m]):.1f} mm per texel)')
