"""dash_front and driver_pov as two views of one dashboard: the things both show, read on each (col, row), and a
fit of driver_pov's camera and of how far along dash_front's rays each thing lies. dash_front's camera is taken as
fitted (cabin.CAMERAS); the scene's scale is pinned by the screen's display being 0.292 m wide (a 12.3 inch one).
Run: python twoview.py"""
import sys, os, math, numpy as np
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photocam as PC
from scipy.optimize import least_squares
# name: ((col, row) on dash_front, (col, row) on driver_pov). First readings, to about 4 px.
BOTH = {'wheel centre': ((404, 504), (774, 533)), 'display top left': ((709, 300), (1125, 217)), 'display top right': ((1000, 300), (1504, 217)),
        'display bottom left': ((709, 403), (1125, 353)), 'display bottom right': ((1000, 403), (1504, 353)), 'hazard switch': ((858, 465), (1322, 430)),
        'big knob': ((719, 638), (1164, 651)), 'shifter knob top': ((864, 632), (1371, 664)), 'left cup holder': ((792, 872), (1368, 928)),
        'round switch': ((659, 391), (1059, 336)), 'left vent': ((190, 397), (454, 349)), 'door knob': ((131, 533), (379, 537)),
        'glovebox latch': ((1132, 490), (1621, 454)), 'frame lower left': ((695, 560), (1118, 526)), 'frame lower right': ((1018, 560), (1539, 539))}
DISPLAY_W = 0.292
def fit(verbose=True):
    A = PC.Camera('dash_front'); names = list(BOTH); pa = np.array([BOTH[n][0] for n in names], float); pb = np.array([BOTH[n][1] for n in names], float)
    rays = A.rays(pa[:, 1], pa[:, 0]); W, H = 1672, 941
    def unpack(v): return v[:3], v[3], v[4], v[5], v[6:]
    def project(v):
        pos, yaw, pitch, f, lam = unpack(v); P = A.pos[None, :] + lam[:, None] * rays
        fwd = np.array((math.cos(yaw) * math.cos(pitch), math.sin(yaw) * math.cos(pitch), -math.sin(pitch))); right = np.cross(fwd, (0, 0, 1.0)); right /= np.linalg.norm(right); up = np.cross(right, fwd)
        d = P - pos[None, :]; z = d.dot(fwd); return np.c_[W / 2 + f * d.dot(right) / z, H / 2 - f * d.dot(up) / z], P
    def res(v):
        uv, P = project(v); i, j = names.index('display top left'), names.index('display top right')
        return np.r_[(uv - pb).ravel(), 2000 * (np.linalg.norm(P[i] - P[j]) - DISPLAY_W)]
    v0 = np.r_[(-0.30, 0.41, 1.45), 0.0, math.radians(15), 1100.0, np.full(len(names), 0.9)]
    lo = np.r_[(-1.5, -0.2, 0.9), -0.6, -0.2, 500.0, np.full(len(names), 0.2)]; hi = np.r_[(0.6, 0.9, 1.9), 0.6, 0.9, 4000.0, np.full(len(names), 3.0)]
    s = least_squares(res, v0, bounds=(lo, hi)); uv, P = project(s.x); pos, yaw, pitch, f, lam = unpack(s.x); err = np.hypot(*(uv - pb).T)
    if verbose:
        print('driver_pov camera: position %.3f %.3f %.3f, turned %.1f degrees to the left, looking down %.1f, focal length %.0f px (%.1f degrees across)' % (*pos, math.degrees(yaw), math.degrees(pitch), f, 2 * math.degrees(math.atan(W / 2 / f))))
        print('misfit on driver_pov: mean %.1f px, worst %.1f px (%s)' % (err.mean(), err.max(), names[int(err.argmax())]))
        for n, p, e in zip(names, P, err): print('  %-22s x %.3f  y %+.3f  z %.3f   (misfit %.0f px)' % (n, *p, e))
    return dict(pos=pos, yaw=yaw, pitch=pitch, f=f, points=dict(zip(names, P)), err=err)
if __name__ == '__main__': fit()
