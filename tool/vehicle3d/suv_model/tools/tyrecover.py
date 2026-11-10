"""Does each flare cover its tyre? The tyre's and the flare's outermost y by station, and how proud the flare is of the
body beside it at mid-height of the band: tyrecover.py <blend>"""
import sys, bpy, numpy as np
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[1]); body = bpy.data.objects['body']
f = bpy.data.objects['arch_flares']; FV = np.array([f.matrix_world @ v.co for v in f.data.vertices])
for wn in ('wheel_FL', 'wheel_RL'):
    o = bpy.data.objects[wn]; V = np.array([o.matrix_world @ v.co for v in o.data.vertices]); hub = (V[:, 0].min() + V[:, 0].max()) / 2
    F = FV[(FV[:, 1] > 0) & (np.abs(FV[:, 0] - hub) < 0.7)]; out = []
    for dx in np.arange(0.52, -0.521, -0.04):
        k = np.abs(V[:, 0] - (hub + dx)) < 0.012; kf = np.abs(F[:, 0] - (hub + dx)) < 0.012
        if not kf.any(): continue
        fy = F[kf, 1].max(); ty = V[k, 1].max() if k.any() else np.nan; zf = F[kf][np.argmax(F[kf, 1]), 2]
        h = body.ray_cast(Vector((hub + dx, 2.0, zf + 0.05)), Vector((0, -1, 0))); by = h[1].y if h[0] else np.nan
        out.append('%+.2f:%s/%+.0f' % (dx, '%+.0f' % ((fy - ty) * 1e3) if ty == ty else 'no tyre', (fy - by) * 1e3))
    print(wn, '(station ahead of hub: flare minus tyre / flare minus body, mm)'); print('   ' + ' '.join(out))
