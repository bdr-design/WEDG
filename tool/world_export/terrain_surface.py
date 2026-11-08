"""Height of the rendered terrain.glb surface (the topmost ring) at given x, z, using its real triangles."""
import json, numpy as np
from glbio import read_glb, accessor
from PIL import Image

class Ring:
    def __init__(self, js, b, name):
        node = [n for n in js['nodes'] if n['name'] == name][0]
        prim = js['meshes'][node['mesh']]['primitives'][0]
        P = accessor(js, b, prim['attributes']['POSITION']).astype(np.float64)
        self.Nrm = accessor(js, b, prim['attributes']['NORMAL']).astype(np.float64)
        I = accessor(js, b, prim['indices']).reshape(-1, 3)
        self.P, self.I = P, I
        self.x0, self.x1 = P[:, 0].min(), P[:, 0].max(); self.z0, self.z1 = P[:, 2].min(), P[:, 2].max()
        xs = np.unique(np.round(P[:, 0], 3)); zs = np.unique(np.round(P[:, 2], 3))
        self.nx, self.nz = len(xs) - 1, len(zs) - 1
        self.dx = (self.x1 - self.x0) / self.nx; self.dz = (self.z1 - self.z0) / self.nz
        c = P[I].mean(axis=1)
        ci = np.clip(((c[:, 0] - self.x0) / self.dx).astype(int), 0, self.nx - 1)
        cj = np.clip(((c[:, 2] - self.z0) / self.dz).astype(int), 0, self.nz - 1)
        cell = cj * self.nx + ci
        order = np.argsort(cell, kind='stable')
        self.tri_by_cell = I[order].reshape(self.nx * self.nz, 2, 3)   # two triangles per cell

    def inside(self, x, z):
        return (x >= self.x0) & (x <= self.x1) & (z >= self.z0) & (z <= self.z1)

    def height(self, x, z):
        x = np.asarray(x, float); z = np.asarray(z, float)
        ci = np.clip(((x - self.x0) / self.dx).astype(int), 0, self.nx - 1)
        cj = np.clip(((z - self.z0) / self.dz).astype(int), 0, self.nz - 1)
        tris = self.tri_by_cell[cj * self.nx + ci]          # (n, 2, 3)
        best = np.full(x.shape, np.nan)
        for t in range(2):
            A, B, C = (self.P[tris[:, t, k]] for k in range(3))
            # barycentric in xz
            v0x, v0z = B[:, 0] - A[:, 0], B[:, 2] - A[:, 2]; v1x, v1z = C[:, 0] - A[:, 0], C[:, 2] - A[:, 2]
            v2x, v2z = x - A[:, 0], z - A[:, 2]
            den = v0x * v1z - v1x * v0z
            u = (v2x * v1z - v1x * v2z) / den; v = (v0x * v2z - v2x * v0z) / den; w = 1 - u - v
            ok = (u >= -1e-7) & (v >= -1e-7) & (w >= -1e-7) & np.isnan(best)
            y = w * A[:, 1] + u * B[:, 1] + v * C[:, 1]
            best = np.where(ok, y, best)
        return best

class TerrainSurface:
    def __init__(self, path):
        js, b = read_glb(path)
        self.near = Ring(js, b, 'terrain_near'); self.mid = Ring(js, b, 'terrain_mid'); self.far = Ring(js, b, 'terrain_far')

    def height(self, x, z):
        x = np.asarray(x, float); z = np.asarray(z, float)
        h = self.far.height(x, z)
        for r in (self.mid, self.near):
            m = r.inside(x, z)
            if m.any():
                hh = r.height(x[m], z[m]); h[m] = np.fmax(h[m], hh)
        return h

class HeightMap:
    """the prototype's heightAt (bilinear on terrain_h.png)"""
    def __init__(self, src):
        meta = json.load(open(src + '/terrain.json')); self.meta = meta
        hm = np.array(Image.open(src + '/terrain_h.png').convert('RGBA')).astype(np.int64)
        self.N = meta['size']; self.H = ((hm[..., 0] << 8) | hm[..., 1]) / 10.0 - 1000.0
        self.W, self.D = meta['xEast'] - meta['xWest'], meta['zSouth'] - meta['zNorth']

    def height(self, x, z):
        m, N, H = self.meta, self.N, self.H
        u = np.clip((np.asarray(x) - m['xWest']) / self.W, 0, 1) * (N - 1); v = np.clip((np.asarray(z) - m['zNorth']) / self.D, 0, 1) * (N - 1)
        i, j = np.floor(u).astype(int), np.floor(v).astype(int); fu, fv = u - i, v - j
        i1, j1 = np.minimum(i + 1, N - 1), np.minimum(j + 1, N - 1)
        a, b, c, d = H[j, i], H[j, i1], H[j1, i], H[j1, i1]
        return (a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv
