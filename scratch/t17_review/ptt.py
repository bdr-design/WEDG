import numpy as np
def pt_tri(p, a, b, c):  # exact distance point to many triangles (Ericson)
    ab, ac, ap = b - a, c - a, p - a; d1 = (ab * ap).sum(1); d2 = (ac * ap).sum(1)
    n = np.cross(ab, ac); nn = (n * n).sum(1); dist_plane = np.abs((ap * n).sum(1)) / np.sqrt(np.maximum(nn, 1e-30))
    # barycentric projection
    v = ((ab * ab).sum(1) * d2 - (ab * ac).sum(1) * d1) / np.maximum(nn, 1e-30); u = ((ac * ac).sum(1) * d1 - (ab * ac).sum(1) * d2) / np.maximum(nn, 1e-30)
    inside = (u >= 0) & (v >= 0) & (u + v <= 1); d = np.where(inside, dist_plane, np.inf)
    def seg(p, x, y):
        e = y - x; t = np.clip(((p - x) * e).sum(1) / np.maximum((e * e).sum(1), 1e-30), 0, 1); return np.linalg.norm(p - (x + e * t[:, None]), axis=1)
    return np.minimum(d, np.minimum(seg(p, a, b), np.minimum(seg(p, b, c), seg(p, a, c)))).min()
