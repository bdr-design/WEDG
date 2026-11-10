"""Folds in plan along the body side: the surface's y along the car at set depths under the belt, and the turn between
one 2 cm chord and the next. planfold.py <blend> [d0 d1]"""
import sys, bpy, numpy as np
from mathutils import Vector
sys.path.insert(0, '.')
import realframe as RF, outlines as O
a = sys.argv[1:]; d0, d1 = (float(a[1]), float(a[2])) if len(a) > 2 else (1.2, 4.6)
bpy.ops.wm.open_mainfile(filepath=a[0]); ob = bpy.data.objects['body']
ds = np.arange(d0, d1, 0.02)
for dz in (-0.015, -0.035, -0.055, -0.075, -0.10, -0.15, -0.30, +0.05, +0.25):
    ys = []
    for d in ds:
        x = float(RF.x_real(O.XF - d)); z = float(RF.z_real(O.bplane(min(max(d, 1.5), 4.4)) + dz))
        r = ob.ray_cast(Vector((x, 2.0, z)), Vector((0, -1, 0))); ys.append(r[1].y if r[0] else np.nan)
    ys = np.array(ys); xr = RF.x_real(O.XF - ds); ang = np.degrees(np.arctan2(np.diff(ys), -np.diff(xr))); f = np.diff(ang)
    k = np.nanargmax(np.abs(f)); big = np.where(np.abs(f) > 4)[0]
    print('belt %+.3f: worst fold %+.1f deg at d %.2f; folds over 4 deg at d %s' % (dz, f[k], ds[k + 1], ' '.join('%.2f(%+.0f)' % (ds[i + 1], f[i]) for i in big[:14])))
