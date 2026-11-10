"""Are the plates and the door handles seated? seated.py <blend>
Plates: the air behind each corner and the middle of the back face. Handles: the skin against the bar's back at both ends."""
import sys, bpy, numpy as np
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[1]); dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene
body = bpy.data.objects['body']
for nm, f in (('plate_rear', -1), ('plate_front', 1)):
    o = bpy.data.objects[nm]; V = np.array([o.matrix_world @ v.co for v in o.data.vertices])
    back = V[np.argsort(V[:, 0] * f)[:4]]; c = back.mean(0); n = Vector((-f, 0, 0)); gaps = []
    for p in list(back) + [c] + [c + (q - c) * 0.5 for q in back]:
        p = Vector(p) + (Vector(c) - Vector(p)) * 0.03
        best = None
        for t in bpy.data.objects:
            if t.type != 'MESH' or t.name == nm: continue
            h = t.ray_cast(t.matrix_world.inverted() @ p, n)
            if h[0]:
                dist = (t.matrix_world @ h[1] - p).length
                if best is None or dist < best[0]: best = (dist, t.name)
        gaps.append(best)
    print(nm, 'air behind: corners', ' '.join('%.0f(%s)' % (g[0] * 1e3, g[1][:9]) if g else 'none' for g in gaps[:4]), '| centre', '%.0f(%s)' % (gaps[4][0] * 1e3, gaps[4][1][:9]) if gaps[4] else 'none', '| halfway', ' '.join('%.0f' % (g[0] * 1e3) if g else 'none' for g in gaps[5:]),
          '| back face x %.4f..%.4f, z %.3f..%.3f' % (back[:, 0].min(), back[:, 0].max(), back[:, 2].min(), back[:, 2].max()))
for o in bpy.data.objects:
    if not o.name.startswith('handle_'): continue
    V = np.array([o.matrix_world @ v.co for v in o.data.vertices]); s = 1 if V[:, 1].mean() > 0 else -1; out = []
    # the bar's back at its four corners (2 cm in from each end, 8 mm in from the top and bottom), each against the skin at its own height
    for xe in (V[:, 0].max() - 0.02, V[:, 0].min() + 0.02):
        for ze in (V[:, 2].max() - 0.008, V[:, 2].min() + 0.008):
            h = o.ray_cast(o.matrix_world.inverted() @ Vector((xe, 0.0, ze)), Vector((0, s, 0))); b = body.ray_cast(Vector((xe, s * 2.0, ze)), Vector((0, -s, 0)))
            out.append((abs(h[1].y) - abs(b[1].y)) * 1e3 if h[0] and b[0] else float('nan'))
    print(o.name, 'bar back minus skin, mm (negative is sunk): front end top %+.1f bottom %+.1f, rear end top %+.1f bottom %+.1f' % tuple(out))
