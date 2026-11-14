import sys, numpy as np
sys.path.insert(0, '.')
from slice import cut, pt
e = pt['eye_l']; print('eyes', np.round(pt['eye_l']), np.round(pt['eye_r']), 'spacing', round(abs(pt['eye_l'][2]-pt['eye_r'][2])), 'ear bases', round(abs(pt['ear_l'][2]-pt['ear_r'][2])), 'nose', np.round(pt['nose']))
for dx in (0, -20, -40, -60):
    c = cut(e[0] + dx, axis=0); c = c[(c[:, 1] < e[1] + 25) & (c[:, 1] > pt['nose'][1] - 60)]
    print(f'section {dx} mm from the eyes, below eye+25: max width {np.ptp(c[:,2]):.0f} mm, depth {np.ptp(c[:,1]):.0f}')
