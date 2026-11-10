"""The chrome strip under the side glass from above, against 04_top's line (read at 04_top's stations and moved to
01_left's by outlines.TOP_CABIN): chromeplan.py <blend>"""
import sys, bpy, numpy as np
from mathutils import Vector
sys.path.insert(0, '.')
import realframe as RF, outlines as O
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
print(' d(top) d(side)  photo   strip centre  diff mm   glass opening edge  diff mm')
for dt, yp in O.CHROME_PLAN:
    d = float(O._cabin(dt)); x = float(RF.x_real(O.XF - d)); res = []
    for s, nm in ((1, 'L'), (-1, 'R')):
        o = bpy.data.objects['window_chrome_low_' + nm]; V = np.array([v.co for v in o.data.vertices]); k = np.abs(V[:, 0] - x) < 0.03
        yc = (np.abs(V[k, 1]).min() + np.abs(V[k, 1]).max()) / 2 / 1.026
        b = bpy.data.objects['body']; zc = float(RF.z_real(O.bplane(d) if d < 3.88 else np.interp(d, *zip(*((O.Q_D[0], O.bplane(O.Q_D[0])),) + O.CHROME_Z))))
        h = b.ray_cast(Vector((x, s * 2.0, zc - 0.002)), Vector((0, -s, 0))); res.append((yc, abs(h[1].y) / 1.026 if h[0] else np.nan))
    yc = np.mean([r[0] for r in res]); ye = np.mean([r[1] for r in res])
    print(' %.2f   %.3f   %.4f   %.4f     %+5.1f       %.4f        %+5.1f' % (dt, d, yp, yc, (yc - yp) * 1e3, ye, (ye - yp) * 1e3))
