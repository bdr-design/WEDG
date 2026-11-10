"""The model's outline from above against the top photo's, by station: topout.py <blend> [d0 d1 step]"""
import sys, bpy, numpy as np
from mathutils import Vector
sys.path.insert(0, '.')
import realframe as RF, outlines as O
a = sys.argv[1:]; d0, d1, st = (float(v) for v in a[1:4]) if len(a) > 3 else (1.0, 4.6, 0.1)
bpy.ops.wm.open_mainfile(filepath=a[0]); dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
for o in bpy.data.objects:
    if o.name.startswith('mirror'): o.hide_viewport = True; o.hide_set(True)
dg = bpy.context.evaluated_depsgraph_get()
def out(d):
    x = float(RF.x_real(O.XF - d)); lo, hi, nm = 0.5, 1.15, ''
    for y in np.arange(1.10, 0.5, -0.001):
        ok, loc, n, fi, ob, _ = sc.ray_cast(dg, Vector((x, y * 1.026, 5.0)), Vector((0, 0, -1)))
        if ok and ob.name != 'Plane' and loc.z > 0.05: return y, ob.name, float(RF.z_photo(loc.z))
    return 0, '', 0
print('   d   model   photo   diff mm  (what, z)')
for d in np.arange(d0, d1 + 1e-6, st):
    y, nm, z = out(d); p = float(O.top_half(O.XF - d)); print('%.2f  %.4f  %.4f  %+6.1f   %s %.2f' % (d, y, p, (y - p) * 1e3, nm, z))
