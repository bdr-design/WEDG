"""door_FL.png (the front left door's trim, seen square-on from inside the cabin; the photo's right is the car's
front) split by colour into its main parts, and the frame that takes the photo to the door's own space: x forward
along the door from the photo's left edge, z up from its bottom edge, y across the car with the cabin at -y.

SCALE: the photo runs from the door's rear edge to its front edge, and the model's front door is 1.075 m long
(sides.py: its front edge 0.617 m and the B-pillar seam 1.692 m behind the front hub), so a pixel is 0.70 mm. At
that scale the lever in the handle's recess is 153 mm long, as such levers are, and the trim is 0.65 m from its
bottom edge to the window's sill."""
import numpy as np
from scipy import ndimage
import masks as M
DOOR_LENGTH = 1.075
PARTS = ('window', 'panel', 'beige', 'wood', 'silver')
def labels():
    a = M.rgb('door_FL'); R, B = a[..., 0], a[..., 2]; lum = a.mean(2); sat = a.max(2) - a.min(2); win = M.backdrop(a)
    cl = lambda m, k=2: ndimage.binary_opening(ndimage.binary_closing(m, iterations=k), iterations=k)
    beige = cl(~win & (R > 150) & (R - B > 35) & (lum > 130), 3); wood = cl(~win & ~beige & (R - B > 30) & (lum > 45) & (lum < 135), 2)
    silver = cl(~win & (lum > 150) & (sat < 28), 1)
    lab = np.zeros(a.shape[:2], np.uint8); lab[~win] = 1; lab[beige] = 2; lab[wood] = 3; lab[silver] = 4
    return lab
def frame():
    a = M.rgb('door_FL'); H, W = a.shape[:2]; s = DOOR_LENGTH / W
    return s, (lambda rr, cc: (np.asarray(cc) * s, (H - np.asarray(rr)) * s)), (0, H)
