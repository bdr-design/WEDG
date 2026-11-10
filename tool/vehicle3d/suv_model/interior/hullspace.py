"""The space inside the hull, measured on the built car (real frame): hullspace.py <suv.blend>"""
import sys, bpy, numpy as np
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[1]); body = bpy.data.objects['body']; glass = bpy.data.objects['glass']
def cast(o, p, d):
    h = o.ray_cast(Vector(p), Vector(d)); return h[1] if h[0] else None
print('station x: roof (outer) on the centre line | body half-width at z 0.8 / 1.0 / 1.2 | glass half-width at z 1.4 / 1.6 | underside on the centre line')
for x in np.arange(1.4, -2.3, -0.2):
    roof = cast(body, (x, 0.0, 3.0), (0, 0, -1)) or cast(glass, (x, 0.0, 3.0), (0, 0, -1)); gl = cast(glass, (x, 0.0, 3.0), (0, 0, -1))
    hw = [cast(body, (x, 2.0, z), (0, -1, 0)) for z in (0.8, 1.0, 1.2)]; gw = [cast(glass, (x, 2.0, z), (0, -1, 0)) for z in (1.4, 1.6)]
    und = cast(body, (x, 0.0, -1.0), (0, 0, 1))
    f = lambda v, i: '%.3f' % v[i] if v is not None else '  -  '
    print('%+.1f: %s (glass %s) | %s %s %s | %s %s | %s' % (x, f(roof, 2), f(gl, 2), f(hw[0], 1), f(hw[1], 1), f(hw[2], 1), f(gw[0], 1), f(gw[1], 1), f(und, 2)))
print('windshield on the centre line (x at height):', ' '.join('%.2f:%s' % (z, ('%.3f' % cast(glass, (3.0, 0.0, z), (-1, 0, 0)).x) if cast(glass, (3.0, 0.0, z), (-1, 0, 0)) is not None else '-') for z in (1.25, 1.30, 1.40, 1.50, 1.60, 1.70, 1.75)))
print('rear glass on the centre line:', ' '.join('%.2f:%s' % (z, ('%.3f' % cast(glass, (-3.0, 0.0, z), (1, 0, 0)).x) if cast(glass, (-3.0, 0.0, z), (1, 0, 0)) is not None else '-') for z in (1.35, 1.45, 1.60, 1.70)))
V = np.array([v.co for v in glass.data.vertices]); print('glass: x %.3f..%.3f, z %.3f..%.3f' % (V[:, 0].min(), V[:, 0].max(), V[:, 2].min(), V[:, 2].max()))
for n in ('wheel_FL', 'wheel_RL'):
    W = np.array([bpy.data.objects[n].matrix_world @ v.co for v in bpy.data.objects[n].data.vertices]); print(n, 'hub x %.3f, inner face y %.3f, top z %.3f' % ((W[:, 0].min() + W[:, 0].max()) / 2, W[:, 1].min(), W[:, 2].max()))
