"""A solid from a square-on photo's outline: the region is given its width across the photo's plane, flat over its
middle and rounded off toward its edge, so that from the photo's side its outline is the region's own, to a fraction
of a pixel. The mesh is rings set in from the outline (close together where the edge rounds) and a sparse fill."""
import numpy as np, bmesh
from scipy import ndimage
from scipy.spatial import Delaunay
from skimage import measure


def _resample(c, spacing):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]; n = max(8, int(d[-1] / spacing))
    t = np.linspace(0, d[-1], n, endpoint=False); return np.c_[np.interp(t, d, c[:, 0]), np.interp(t, d, c[:, 1])]


def outline(mask, smooth=1.2):
    """The region's outline (row, column), from the mask blurred a little so that pixel steps do not show."""
    f = ndimage.gaussian_filter(np.pad(mask.astype(float), 2), smooth); cs = measure.find_contours(f, 0.5)
    return max(cs, key=len) - 2


def solid(bm, mask, to_xz, scale, width, radius, y0=0.0, mat=0, rings=4, spacing=0.015, fill=0.04, smooth=True):
    """Add the solid for mask to bm. to_xz maps (row, column) arrays to model x, z; scale is metres per pixel;
    width is the solid's full width across, radius its edge rounding (at most width / 2)."""
    radius = min(radius, width / 2); edt = ndimage.distance_transform_edt(np.pad(mask, 2))[2:-2, 2:-2] * scale
    rings = min(rings, int(radius / scale / 3))          # a rounding of a few pixels cannot carry rings: their contours tangle (the screen's top came out in spikes)
    # every outline of the region: its outer one and those of its holes, each a closed loop of its own
    fm = ndimage.gaussian_filter(np.pad(mask.astype(float), 2), 1.2); loops = [_resample(c - 2, spacing / scale) for c in measure.find_contours(fm, 0.5) if len(c) > 12]
    pts = [np.vstack(loops)]; nb = len(pts[0]); ends = np.cumsum([len(l) for l in loops]); starts = ends - [len(l) for l in loops]
    # the rings: each outline point carried inward along the distance field to each ring's depth, so that the rings'
    # points stand in rows across the rounding (rings resampled each on its own left the edge crumpled: the
    # triangles between them leaned every way)
    f = ndimage.gaussian_filter(edt, 1.0) / scale; gr, gc = np.gradient(ndimage.gaussian_filter(edt, 1.5) / scale); p = pts[0].copy()
    for k in range(1, rings + 1):
        lvl = radius * (1 - np.cos(k * np.pi / 2 / rings)) / scale
        for _ in range(int(lvl * 3) + 12):
            d = ndimage.map_coordinates(f, p.T, order=1); need = d < lvl - 0.05
            if not need.any(): break
            g = np.c_[ndimage.map_coordinates(gr, p.T, order=1), ndimage.map_coordinates(gc, p.T, order=1)]; ln = np.maximum(np.hypot(g[:, 0], g[:, 1]), 0.5)
            p[need] += (g / ln[:, None] * np.minimum(lvl - d, 0.7)[:, None])[need]
        q = p[::2] if k >= 4 else p; key = np.round(q / 0.6).astype(np.int64); _, first = np.unique(key[:, 0] * 100003 + key[:, 1], return_index=True); pts.append(q[np.sort(first)])
    rr, cc = np.mgrid[0:mask.shape[0]:max(2, int(fill / scale)), 0:mask.shape[1]:max(2, int(fill / scale))]
    k = edt[rr, cc] > radius * 1.05 + fill * 0.3; pts.append(np.c_[rr[k], cc[k]].astype(float))
    P = np.vstack(pts); tri = Delaunay(P).simplices
    cen = P[tri].mean(1); ok = ndimage.map_coordinates(mask.astype(float), [cen[:, 0], cen[:, 1]], order=1) > 0.5
    # a triangle wholly on the outline (three outline points) that cuts across a hollow is outside: its middle is tested too
    tri = tri[ok]
    d = np.clip(ndimage.map_coordinates(edt, [P[:, 0], P[:, 1]], order=1), 0, None); d[:nb] = 0.0
    h = width / 2 - radius + np.sqrt(np.clip(radius ** 2 - (radius - np.minimum(d, radius)) ** 2, 0, None))
    lay = bm.verts.layers.float_vector.get('relief_n') or bm.verts.layers.float_vector.new('relief_n')      # before any vertex: a new layer moves them
    x, z = to_xz(P[:, 0], P[:, 1]); near = [bm.verts.new((x[i], y0 - h[i], z[i])) for i in range(len(P))]; far = [bm.verts.new((x[i], y0 + h[i], z[i])) for i in range(len(P))]
    # the surface's own normals, kept for shading (the triangles between the rings are uneven and shade in scallops):
    # in the photo's plane they point away from the region, turning to straight across as the edge's rounding ends
    g = ndimage.gaussian_filter(edt, 2.0); gr, gc = np.gradient(g); nr = ndimage.map_coordinates(gr, [P[:, 0], P[:, 1]], order=1); nc = ndimage.map_coordinates(gc, [P[:, 0], P[:, 1]], order=1)
    x1, z1 = to_xz(P[:, 0] + nr, P[:, 1] + nc); ix, iz = x1 - x, z1 - z; ln = np.hypot(ix, iz) + 1e-12; ix, iz = -ix / ln, -iz / ln      # outward, in the plane
    t = np.clip(1 - np.minimum(d, radius) / radius, 0, 1) if radius > 0 else np.zeros(len(P)); ca = np.sqrt(np.clip(1 - t * t, 0, 1))      # t: 1 at the outline, 0 on the flat
    for i in range(len(P)): near[i][lay] = (ix[i] * t[i], -ca[i], iz[i] * t[i]); far[i][lay] = (ix[i] * t[i], ca[i], iz[i] * t[i])
    faces = []
    for a, b, c in tri:
        for vs in ((near[a], near[b], near[c]), (far[a], far[c], far[b])):
            try: faces.append(bm.faces.new(vs))
            except ValueError: pass
    if width / 2 - radius > 1e-5:
        for s0, e0 in zip(starts, ends):
            for i in range(s0, e0):
                j = i + 1 if i + 1 < e0 else s0
                try: faces.append(bm.faces.new((near[i], near[j], far[j], far[i])))
                except ValueError: pass
    else:
        for i in range(nb): bmesh.ops.pointmerge(bm, verts=[near[i], far[i]], merge_co=near[i].co)
    for f in faces:
        if f.is_valid: f.material_index = mat; f.smooth = smooth
    return faces


def shade(me):
    """Give the mesh the normals solid() kept (call once the bmesh has been written to it)."""
    a = me.attributes.get('relief_n')
    if a is None: return
    n = np.zeros(len(me.vertices) * 3); a.data.foreach_get('vector', n); n = n.reshape(-1, 3); ln = np.linalg.norm(n, axis=1)
    auto = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get('normal', auto); auto = auto.reshape(-1, 3)
    n = np.where(ln[:, None] > 0.5, n / np.maximum(ln, 1e-9)[:, None], auto); me.normals_split_custom_set_from_vertices([tuple(v) for v in n])


def ngon(bm, pts, y, mat):
    """A flat many-sided face at depth y, looking toward -y (the photo's side). pts: model (x, z) pairs."""
    vs = [bm.verts.new((x, y, z)) for x, z in pts]; f = bm.faces.new(vs); f.material_index = mat
    if f.normal.y > 0: f.normal_flip()
    return vs


def prism(bm, pts, y_front, y_back, mat, wall=None):
    """A raised part: its face at y_front (toward the photo's side) and walls back to y_back."""
    a = ngon(bm, pts, y_front, mat); b = [bm.verts.new((v.co.x, y_back, v.co.z)) for v in a]; n = len(a)
    for k in range(n):
        f = bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k])); f.material_index = mat if wall is None else wall


def ring(bm, outer, inner, y, mat, y_back=None):
    """A flat band between two outlines at depth y (a bezel round an opening), with an outer wall back to y_back."""
    from skimage.measure import points_in_poly
    vo = [bm.verts.new((x, y, z)) for x, z in outer]; vi = [bm.verts.new((x, y, z)) for x, z in inner]
    ed = [bm.edges.new((vo[k], vo[(k + 1) % len(vo)])) for k in range(len(vo))] + [bm.edges.new((vi[k], vi[(k + 1) % len(vi)])) for k in range(len(vi))]
    fl = [g for g in bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=ed)['geom'] if isinstance(g, bmesh.types.BMFace)]
    cen = np.array([(f.calc_center_median().x, f.calc_center_median().z) for f in fl]); bmesh.ops.delete(bm, geom=[f for f, k in zip(fl, points_in_poly(cen, np.asarray(inner))) if k], context='FACES')
    for f in fl:
        if f.is_valid:
            f.material_index = mat
            if f.normal.y > 0: f.normal_flip()
    if y_back is not None:
        for loop in (vo, vi):
            b = [bm.verts.new((v.co.x, y_back, v.co.z)) for v in loop]
            for k in range(len(loop)):
                f = bm.faces.new((loop[k], loop[(k + 1) % len(loop)], b[(k + 1) % len(loop)], b[k])); f.material_index = mat


def near_face(mask, scale, width, radius, y0=0.0):
    """Where solid()'s near face is: a function (row, column) -> y, for laying lines on it."""
    radius = min(radius, width / 2); edt = ndimage.distance_transform_edt(np.pad(mask, 2))[2:-2, 2:-2] * scale
    def f(rr, cc):
        d = np.clip(ndimage.map_coordinates(edt, [np.asarray(rr, float), np.asarray(cc, float)], order=1), 0, None)
        return y0 - (width / 2 - radius + np.sqrt(np.clip(radius ** 2 - (radius - np.minimum(d, radius)) ** 2, 0, None)))
    return f


def ribbon(bm, line, to_xz, y_at, width, mat, lift=0.0005, step=6.0):
    """A thin band along a line of the photo ((col, row) points), lying on a surface whose depth y_at gives: a seam or
    a row of stitching. width in metres; the line is walked in steps of `step` pixels."""
    p = np.asarray(line, float); d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]; n = max(2, int(d[-1] / step) + 1)
    t = np.linspace(0, d[-1], n); c = np.interp(t, d, p[:, 0]); r = np.interp(t, d, p[:, 1])
    x, z = to_xz(r, c); y = y_at(r, c) - lift; tx, tz = np.gradient(x), np.gradient(z); ln = np.hypot(tx, tz) + 1e-12; nx, nz = -tz / ln * width / 2, tx / ln * width / 2
    a = [bm.verts.new((x[i] + nx[i], y[i], z[i] + nz[i])) for i in range(n)]; b = [bm.verts.new((x[i] - nx[i], y[i], z[i] - nz[i])) for i in range(n)]
    for i in range(n - 1):
        f = bm.faces.new((a[i], a[i + 1], b[i + 1], b[i])); f.material_index = mat
        if f.normal.y > 0: f.normal_flip()
