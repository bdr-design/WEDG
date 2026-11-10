"""A cabin photo's camera (cabin.CAMERAS) and planes in the car to lay the photo's regions on.
A pixel fixes a direction from the camera, not a distance: a region is laid on a plane that is placed in the car
by other knowledge (the hull, an assumed station), and the plane's own frame is (a, y, b): a across to the photo's
right, b 'up' on the plane, y away from the camera."""
import math, numpy as np
from mathutils import Matrix, Vector
import cabin as C, masks as M


class Camera:
    def __init__(self, name):
        pos, look, fov, col0, _ = C.CAMERAS[name]; self.name = name; self.pos = np.array(pos, float); a = M.rgb(name); self.H, self.W = a.shape[:2]
        self.f = (self.W / 2) / math.tan(math.radians(fov) / 2); self.col0 = self.W / 2 if col0 is None else col0; self.row0 = self.H / 2
        fwd = np.array(look, float) - self.pos; self.fwd = fwd / np.linalg.norm(fwd)
        right = np.cross(self.fwd, (0, 0, 1.0)); self.right = right / np.linalg.norm(right); self.up = np.cross(self.right, self.fwd)
    def rays(self, rr, cc):
        """Pixels as directions from the camera, in the car's frame (one row each)."""
        a = (self.row0 - np.asarray(rr, float)) / self.f; b = (np.asarray(cc, float) - self.col0) / self.f
        return self.fwd[None, :] + a[:, None] * self.up[None, :] + b[:, None] * self.right[None, :]
    def pixel(self, p):
        """Where a point of the car falls on the photo: (column, row)."""
        d = np.asarray(p, float) - self.pos; z = d.dot(self.fwd); return self.col0 + self.f * d.dot(self.right) / z, self.row0 - self.f * d.dot(self.up) / z
    def plane(self, p0, away, up): return Plane(self, p0, away, up)
    def upright(self, x): return Plane(self, (x, 0, 0), (1 if self.fwd[0] > 0 else -1, 0, 0), (0, 0, 1))      # a face across the car at station x
    def level(self, z): return Plane(self, (0, 0, z), (0, 0, -1), self.fwd * (1, 1, 0))                         # a top lying at height z, seen from above
    def ceiling(self, z): return Plane(self, (0, 0, z), (0, 0, 1), -self.fwd * (1, 1, 0))                       # an underside at height z, seen from below
    def side(self, y): return Plane(self, (0, y, 0), (0, 1 if y > 0 else -1, 0), (0, 0, 1))                     # a wall along the car at y


class Plane:
    def __init__(self, cam, p0, away, up):
        self.cam = cam; self.p0 = np.array(p0, float); n = np.array(away, float); self.n = n / np.linalg.norm(n)
        v = np.array(up, float); v = v - self.n * v.dot(self.n); self.v = v / np.linalg.norm(v); self.u = np.cross(self.n, self.v)
        self.mx = Matrix(np.c_[self.u, self.n, self.v].tolist())
    def to_ab(self, rr, cc):
        d = self.cam.rays(np.atleast_1d(rr).ravel(), np.atleast_1d(cc).ravel()); dn = d.dot(self.n); t = (self.p0 - self.cam.pos).dot(self.n) / np.where(np.abs(dn) > 1e-6, dn, 1e-6)
        P = self.cam.pos[None, :] + t[:, None] * d - self.p0[None, :]; return P.dot(self.u), P.dot(self.v)
    def metres_per_px(self, rr, cc):
        a, b = self.to_ab(np.array([rr, rr + 1.0, rr]), np.array([cc, cc, cc + 1.0])); return float(math.sqrt(abs((a[1] - a[0]) * (b[2] - b[0]) - (a[2] - a[0]) * (b[1] - b[0]))))
    def to_car(self, co): return Vector(self.p0) + self.mx @ Vector(co)
    def point(self, col, row):
        a, b = self.to_ab(np.array([float(row)]), np.array([float(col)])); return self.to_car((float(a[0]), 0.0, float(b[0])))
