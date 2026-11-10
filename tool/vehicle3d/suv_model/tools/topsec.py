"""What the top view sees along a station: rays straight down, y in the top photo's scale, heights in the photo frame.
topsec.py <blend> d ...   (d metres behind the nose, photo frame)"""
import sys, bpy, numpy as np
from mathutils import Vector
sys.path.insert(0, '.')
import realframe as RF
XF = 2.498
bpy.ops.wm.open_mainfile(filepath=sys.argv[1]); dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
def hit(d, yt):
    x = float(RF.x_real(XF - d)); y = yt * 1.026
    ok, loc, n, fi, ob, _ = sc.ray_cast(dg, Vector((x, y, 5.0)), Vector((0, 0, -1)))
    if not ok: return None
    mats = ob.data.materials; mat = mats[ob.data.polygons[fi].material_index].name if len(mats) else '-'
    return float(RF.z_photo(loc.z)), ob.name, mat, n
for d in [float(v) for v in sys.argv[2:]]:
    print('d %.2f' % d); prev = None; start = None
    ys = np.arange(0.60, 1.0, 0.0025); rows = []
    for yt in ys:
        h = hit(d, yt); key = (h[1], h[2]) if h else None
        if key != prev:
            if prev is not None: rows.append((start, yt, prev, z0, zl))
            prev, start, z0 = key, yt, (h[0] if h else 0)
        zl = h[0] if h else 0
    rows.append((start, ys[-1], prev, z0, zl))
    for a, b, k, z0, z1 in rows:
        if k and k[0] != 'Plane': print('   y %.4f - %.4f  (%3.0f mm)  z %.3f -> %.3f   %s / %s' % (a, b, (b - a) * 1e3, z0, z1, k[0], k[1]))
