"""What is inside the steering wheel's outline on wheel.png, read off gridded enlargements (zoom.py) in the photo's
own pixels (x right, y down) and pulled onto the nearest strong edge within a few pixels (snap). The right-hand
switch pod is the left one mirrored about the rim's centre line (their silver parts agree within 1 mm)."""
import numpy as np
from scipy import ndimage
import masks as M

# the pad's outer outline (where it meets the spokes and, along its top, the opening over it), clockwise from its top left corner
PAD = [(412, 444), (450, 430), (530, 423), (625, 420), (720, 423), (800, 430), (838, 444), (866, 475), (872, 530), (872, 630),
       (862, 760), (840, 810), (800, 850), (740, 872), (625, 880), (510, 872), (450, 850), (410, 810), (388, 760), (378, 630),
       (378, 530), (384, 475)]
# the left pod: the silver bezel's outline, the dark window in it, and the buttons
BEZEL = [(370, 493), (300, 496), (253, 502), (212, 529), (180, 581), (148, 631), (134, 661), (131, 675), (148, 709), (170, 743),
         (203, 751), (300, 754), (391, 752), (391, 700), (386, 600), (380, 530)]
WINDOW = [(374, 537), (300, 539), (248, 543), (226, 553), (201, 589), (191, 603), (166, 653), (189, 684), (200, 688), (300, 688), (387, 688),
          (386, 610), (380, 560)]
BUTTONS = [  # (outline, what it is made of, how far it stands out of the window's floor in mm)
    ([(232, 548), (296, 545), (296, 596), (203, 598), (212, 580)], 'plastic', 2.0),                    # top left
    ([(300, 545), (375, 541), (377, 595), (300, 596)], 'plastic', 2.0),                                # top right
    ([(189, 610), (218, 610), (231, 622), (231, 664), (218, 677), (189, 677), (170, 652)], 'plastic', 2.5),      # the six-sided one
    ([(249, 610), (313, 610), (313, 677), (249, 677)], 'gloss', 1.0),                                  # the rocker's well
    ([(253, 634), (309, 634), (309, 652), (253, 652)], 'silver', 3.0),                                 # the rocker's bar
    ([(345, 610), (387, 610), (387, 675), (345, 675), (333, 662), (333, 622)], 'plastic', 2.5),        # the rounded one
    ([(201, 690), (304, 690), (304, 729), (222, 729), (208, 720)], 'silver', 2.0),                     # bottom left
    ([(313, 690), (384, 690), (384, 729), (313, 729)], 'silver', 2.0)]                                 # bottom right


def snap(pts, name='wheel', sigma=1.5, reach=6):
    """Each point moved along the outline's normal to the strongest edge within reach pixels."""
    g = ndimage.gaussian_filter(M.rgb(name).mean(2), sigma); e = np.hypot(ndimage.sobel(g, 0), ndimage.sobel(g, 1))
    p = np.asarray(pts, float); n = len(p); out = p.copy()
    for i in range(n):
        t = p[(i + 1) % n] - p[i - 1]; t /= np.hypot(*t) + 1e-9; nr = np.array([-t[1], t[0]])
        ks = np.arange(-reach, reach + 0.01, 0.5); q = p[i] + ks[:, None] * nr
        v = ndimage.map_coordinates(e, [q[:, 1], q[:, 0]], order=1); out[i] = q[np.argmax(v - 0.02 * v.max() * np.abs(ks))]
    return out


def mirror(pts, cx): return [(2 * cx - x, y) for x, y in pts][::-1]
