"""seat_side.png's camera. The photo is not square-on (the review of the first pass, re-measured): the two headrest
posts, which stand one behind the other across the seat, are 32 px apart on it; the cushion's far edge is drawn
136 to 148 px above its near piping; the rail feet's bolt holes are ellipses. One camera fits those: level with row
335 (its horizon), square to the seat, far enough that the seat fills the frame with a 1970 px focal length (35
degrees across), which looks down 14 degrees onto the cushion and 23 onto the rail's feet.
The seat's own frame: x forward (the photo's right) from its rearmost point, z up from the rail's foot, y across
with the camera at -y. SIZE: nothing in the six photos gives the seat's size outright. HEIGHT, the headrest's top over the rail's foot, is
set with the widths seat3d assumes (posts 0.15 m apart, 0.455 m from the near piping to the far bolster's crest): the
photo has the posts 32 px apart and the far crest 136 to 148 px over the near piping (2 cm of that the crest's own
height), and a camera this near gives them as HEIGHT falls: 1.10 gives 27 px and 112, 1.00 gives 29 and 121, 0.96
gives 30 and 126. 1.00 is taken: with the floor at cabin.FLOOR_Z it also puts the cushion 0.845 m up, which is where
a 1.77 m headliner and the type's published headroom put it."""
import math, numpy as np
HEIGHT = 1.00
F, ROW_H, COL0, ROW0, X_REF_COL = 1970.0, 335.0, 627.0, 627.0, 152.0
PITCH = math.atan((ROW0 - ROW_H) / F)
_fwd = np.array((0.0, math.cos(PITCH), -math.sin(PITCH))); _up = np.array((0.0, math.sin(PITCH), math.cos(PITCH))); _right = np.array((1.0, 0.0, 0.0))
def _ray(r, c):
    r = np.atleast_1d(np.asarray(r, float)); c = np.atleast_1d(np.asarray(c, float))
    return _fwd[None] + ((ROW0 - r) / F)[:, None] * _up[None] + ((c - COL0) / F)[:, None] * _right[None]
# the camera's distance from the seat's middle plane and its height, from HEIGHT: the near rail foot's lowest row
# (1203, at y -0.20) is z 0 and the headrest's top (row 21, on the middle plane) is HEIGHT
def _solve():
    top, foot = _ray(21, 400)[0], _ray(1203, 400)[0]
    # z_c + (D / top_y) top_z = HEIGHT ; z_c + ((D - 0.20) / foot_y) foot_z = 0
    a1, a2 = top[2] / top[1], foot[2] / foot[1]; D = (HEIGHT - 0.20 * a2) / (a1 - a2); return D, HEIGHT - D * a1
DIST, CAM_Z = _solve(); CAM_X = (COL0 - X_REF_COL) * DIST / F
POS = np.array((CAM_X, -DIST, CAM_Z))
def on_plane(y):
    """(row, column) -> (x, z) on the upright plane at y across the seat (0 its middle, negative toward the camera)."""
    def f(rr, cc):
        d = _ray(rr, cc); t = (y - POS[1]) / d[:, 1]; return POS[0] + t * d[:, 0], POS[2] + t * d[:, 2]
    return f
def pixel(p):
    d = np.asarray(p, float) - POS; z = d.dot(_fwd); return COL0 + F * d.dot(_right) / z, ROW0 - F * d.dot(_up) / z
if __name__ == '__main__':
    print("camera %.3f m from the seat's middle plane, %.3f m above the rail's foot, opposite x %.3f; looking down %.1f degrees" % (DIST, CAM_Z, CAM_X, math.degrees(PITCH)))
    for nm, (r, c, y) in {'near piping (row 885, y -0.24)': (885, 750, -0.24), 'far cushion edge (row 752, y +0.24)': (752, 750, 0.24), 'backrest top (row 305, middle)': (305, 250, 0.0),
                           'base underside near (row 1140, y -0.25)': (1140, 700, -0.25)}.items():
        x, z = on_plane(y)(r, c); print('  %-38s x %.3f z %.3f' % (nm, x[0], z[0]))
