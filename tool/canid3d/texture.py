"""The skin's texture pair: colour (with the occlusion baked in) and a tangent-space normal map (the fur's grain).

Each texel is found on the skin (its face and place), then on the nearest piece of the posed build, then at the same
place on the same piece of the standing build (the rest frame), where paint.Coat lays out the marks.
"""
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import paint
import skin


def piece_list(m):
    """The posed build's skin pieces in a fixed order (the same order in every pose of the same animal)."""
    out = []
    for k in sorted(m.parts):
        for pc in m.parts[k]:
            if getattr(pc, 'group', k) not in skin.SKIN_GROUPS_EXCLUDED:
                out.append(pc)
    return out


def flatten(pieces):
    Vs, Ts, owner, UVs = [], [], [], []
    base = 0
    for i, pc in enumerate(pieces):
        V, T = skin.piece_arrays(pc)
        Vs.append(V)
        Ts.append(T + base)
        owner.append(np.full(len(T), i))
        UVs.append(np.array(pc.UV, np.float64))
        base += len(V)
    return np.concatenate(Vs), np.concatenate(Ts), np.concatenate(owner), np.concatenate(UVs)


def bary(p, a, b, c):
    v0, v1, v2 = b - a, c - a, p - a
    d00 = (v0 * v0).sum(-1)
    d01 = (v0 * v1).sum(-1)
    d11 = (v1 * v1).sum(-1)
    d20 = (v2 * v0).sum(-1)
    d21 = (v2 * v1).sum(-1)
    den = np.maximum(d00 * d11 - d01 * d01, 1e-18)
    v = (d11 * d20 - d01 * d21) / den
    w = (d00 * d21 - d01 * d20) / den
    return np.stack([1 - v - w, v, w], -1)


def tri_frames(V, T):
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    e1 = b - a
    e1 /= np.maximum(np.linalg.norm(e1, axis=1, keepdims=True), 1e-12)
    n = np.cross(b - a, c - a)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    e2 = np.cross(n, e1)
    return np.stack([e1, e2, n], 1)                 # rows: the triangle's axes


def bake(kind, posed, rest, obj, UV, n_skin_faces, extra_blocks, size, H):
    """[obj]: the skin (and any extra pieces after face n_skin_faces, their blocks in [extra_blocks] as
    (first_face, block)). Returns (colour, normal) as [size, size, 3] float arrays, v up (Blender's images)."""
    V, Fv = skin.mesh_arrays(obj)
    VN = skin.vertex_normals(V, Fv)
    fid, bw = skin.raster(UV, size)
    mask = fid >= 0
    f = fid[mask]
    w = bw[mask].astype(np.float64)
    P = (V[Fv[f]] * w[..., None]).sum(1)
    N = (VN[Fv[f]] * w[..., None]).sum(1)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)

    # where each texel lies on the standing animal
    pp, pr = piece_list(posed), piece_list(rest)
    assert len(pp) == len(pr) and all(len(a.V) == len(b.V) for a, b in zip(pp, pr))
    Vp, T, owner, PUV = flatten(pp)
    Vr = flatten(pr)[0]
    bvh = BVHTree.FromPolygons([tuple(v) for v in Vp], [tuple(int(i) for i in t) for t in T])
    skin_tex = f < n_skin_faces
    idx = np.zeros(len(f), np.int64)
    loc = P.copy()
    for i in np.nonzero(skin_tex)[0]:
        hit = bvh.find_nearest(Vector(P[i]))
        loc[i] = hit[0]
        idx[i] = hit[2]
    tw = bary(loc, Vp[T[idx, 0]], Vp[T[idx, 1]], Vp[T[idx, 2]])
    tw = np.clip(tw, 0, 1)
    tw /= tw.sum(1, keepdims=True)
    Pr = (Vr[T[idx]] * tw[..., None]).sum(1)
    # the skin's own outward direction, turned from the pose back to the standing animal by the nearest piece
    # triangle's turn (the pieces' normals would point into the hollows where the skin bridges two pieces)
    Fr = tri_frames(Vr, T)[idx]
    Fp = tri_frames(Vp, T)[idx]
    Nr = np.einsum('nji,nj->ni', Fr, np.einsum('nij,nj->ni', Fp, N))
    Nr /= np.maximum(np.linalg.norm(Nr, axis=1, keepdims=True), 1e-12)
    ST = (PUV[idx] * tw[..., None]).sum(1)
    blocks = np.array([pp[o].block for o in owner[idx]], dtype=object)
    groups = np.array([getattr(pp[o], 'group', '') for o in owner[idx]], dtype=object)
    # the extra pieces: painted as themselves, flat
    for k, (first, block) in enumerate(extra_blocks):
        last = extra_blocks[k + 1][0] if k + 1 < len(extra_blocks) else 1 << 60
        sel = (f >= first) & (f < last)
        blocks[sel] = block
        groups[sel] = block
        Pr[sel] = P[sel]
        Nr[sel] = N[sel]
        ST[sel] = 0.5
    coat = paint.Coat(kind, rest, mouth_open=posed.P.get('jaw', 0.0) > 5)
    import os
    if os.environ.get('CANID_DEBUG'):
        np.savez(os.environ['CANID_DEBUG'], P=P, Pr=Pr, Nr=Nr, blocks=blocks.astype(str), groups=groups.astype(str), ST=ST)
    col = np.zeros((len(f), 3), np.float32)
    hgt_grad = np.zeros((len(f), 3), np.float64)
    keys = sorted(set(zip(blocks, groups)))
    e = 0.5
    for b, g in keys:
        sel = (blocks == b) & (groups == g)
        col[sel] = coat(Pr[sel], Nr[sel], ST[sel, 0], ST[sel, 1], b, g)
        q = Pr[sel]
        grad = np.stack([(coat.height(q + np.eye(3)[a] * e, b) - coat.height(q - np.eye(3)[a] * e, b)) / (2 * e)
                         for a in range(3)], 1)
        hgt_grad[sel] = grad

    # the occlusion, from rays at the skin's vertices, into the colour
    ao_v = skin.occlusion(V, VN, Fv, H)
    ao = (ao_v[Fv[f]] * w).sum(1)
    col *= (0.58 + 0.42 * ao)[:, None]

    # the normal map: the fur's relief turned from the standing animal into the pose (by the nearest piece
    # triangle's turn), then into the skin face's tangent frame
    g = hgt_grad - Nr * (hgt_grad * Nr).sum(1, keepdims=True)
    gl = np.einsum('nij,nj->ni', Fr, g)                 # into the rest triangle's axes
    gp = np.einsum('nji,nj->ni', Fp, gl)                # out of the posed triangle's axes
    gp[~skin_tex] = 0
    nn = N - 0.9 * gp
    nn /= np.linalg.norm(nn, axis=1, keepdims=True)
    # the skin face's tangent frame from its texture places
    uvf = UV[f].astype(np.float64)
    p0, p1, p2 = V[Fv[f, 0]], V[Fv[f, 1]], V[Fv[f, 2]]
    du1, dv1 = uvf[:, 1, 0] - uvf[:, 0, 0], uvf[:, 1, 1] - uvf[:, 0, 1]
    du2, dv2 = uvf[:, 2, 0] - uvf[:, 0, 0], uvf[:, 2, 1] - uvf[:, 0, 1]
    r = du1 * dv2 - du2 * dv1
    r = np.where(np.abs(r) < 1e-12, 1e-12, r)
    Tg = ((p1 - p0) * dv2[:, None] - (p2 - p0) * dv1[:, None]) / r[:, None]
    Bg = ((p2 - p0) * du1[:, None] - (p1 - p0) * du2[:, None]) / r[:, None]
    Tg = Tg - N * (Tg * N).sum(1, keepdims=True)
    Tg /= np.maximum(np.linalg.norm(Tg, axis=1, keepdims=True), 1e-12)
    sign = np.sign((np.cross(N, Tg) * Bg).sum(1))
    sign[sign == 0] = 1
    Bt = np.cross(N, Tg) * sign[:, None]
    enc = np.stack([(nn * Tg).sum(1), (nn * Bt).sum(1), (nn * N).sum(1)], 1) * 0.5 + 0.5

    colimg = np.zeros((size, size, 3), np.float32)
    nrmimg = np.zeros((size, size, 3), np.float32)
    nrmimg[...] = (0.5, 0.5, 1.0)
    colimg[mask] = np.clip(col, 0, 1)
    nrmimg[mask] = np.clip(enc, 0, 1)
    colimg = skin.fill(colimg, mask)
    nrmimg = skin.fill(nrmimg, mask)
    return colimg, nrmimg, float(mask.mean())
