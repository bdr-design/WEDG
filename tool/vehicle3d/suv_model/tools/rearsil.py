"""Rear silhouette, side photo against the model, in the real frame: for each height the distance (mm) from the car's
rear end to the rear-most thing at that height. Photo rows are mapped to real heights with realframe's z table.
Run: blendenv/bin/python tools/rearsil.py <real-frame blend> [z0 z1 step]"""
import bpy, sys, numpy as np
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import realframe as RF
from PIL import Image
from mathutils import Vector
a = sys.argv[1:]; bpy.ops.wm.open_mainfile(filepath=a[0])
z0, z1, dz = (float(v) for v in a[1:4]) if len(a) > 3 else (0.50, 1.10, 0.025)
import outlines as O
im = np.asarray(Image.open(O.photo('01_left')).convert('RGB')).astype(int)
m = ~((im[..., 0] > 180) & (im[..., 2] > 180) & (im[..., 1] < 110)); s = 0.0029422169811320754
cols = np.flatnonzero(m.any(axis=0)); uend = cols[-1]
dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
xs = [(o.matrix_world @ Vector(c)).x for o in sc.objects if o.type == 'MESH' and o.name.lower() != 'ground' for c in o.bound_box]
xend = min(xs)
print('model rear end x %.4f   photo rear end column %d' % (xend, uend))
print('  z real  z photo   photo   model   model - photo (mm; + = model further forward)')
for z in np.arange(z1, z0 - 1e-6, -dz):
    zp = float(np.interp(z, RF._ZR, RF._ZP)); v = int(round(821 - zp / s)); r = np.flatnonzero(m[v])
    xp = lambda u: float(RF.x_real(4.99 / 2 - (u - 40) * s)); ph = (xp(r[-1]) - xp(uend)) * 1000
    best = None
    for y in np.arange(0.0, 1.0, 0.01):
        hit, loc, nor, fi, ob, mw = sc.ray_cast(dg, Vector((-3.5, y, z)), Vector((1, 0, 0)))
        if hit and (best is None or loc.x < best[0]): best = (loc.x, y, ob.name)
    mo = (best[0] - xend) * 1000
    print('  %.3f   %.3f   %5.0f   %5.0f   %+5.0f   at y %.2f %s' % (z, zp, ph, mo, mo - ph, best[1], best[2]))
