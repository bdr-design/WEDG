"""The interior photos: where they are, and what in them is backdrop (magenta: glass, screens, the studio)."""
import os, numpy as np
from PIL import Image
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__))
DIRS = (os.environ.get('SUV_INTERIOR'), os.path.join(HERE, '..', '..', 'suv_parts', 'interior'), HERE)
def path(name): return next(os.path.join(d, name + '.png') for d in DIRS if d and os.path.exists(os.path.join(d, name + '.png')))
def rgb(name): return np.asarray(Image.open(path(name)).convert('RGB')).astype(float)
def backdrop(a):
    """Magenta: red and blue both well over green (the photos use two magentas, 252/3/252 and 252/53/195)."""
    return (a[..., 0] - a[..., 1] > 120) & (a[..., 2] - a[..., 1] > 90)
def outside(a):
    """The backdrop that reaches the image's edge (holes inside the object are kept apart)."""
    m = backdrop(a); lab, _ = ndimage.label(m); ids = set(lab[0]) | set(lab[-1]) | set(lab[:, 0]) | set(lab[:, -1]); ids.discard(0)
    return np.isin(lab, list(ids))
