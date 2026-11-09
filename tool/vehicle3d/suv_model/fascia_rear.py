"""Step 4: the rear, measured on 03_rear (out/03_rear_grid.jpg has a 10 cm grid)."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector
from fascia_common import rrect, inside, Placer, part, bar

# The y values below are read off 03_rear with its views.json scale, which assumed a 2.2 m mirror-to-mirror width. On
# that scale the rear photo is 2.076 m across its flares; the spec sheet says 1.980. The body is built on the front
# photo's scale (2.0125 m across its flares, realframe.Y_SCALE takes it to 1.980), so rear y values are brought to the
# front photo's scale here: (1.980 / 2.076) / (1.980 / 2.0125) = 0.9694.
RY = 0.9694

def rear(shell, M):
    P = Placer(shell, -1); parts = []
    sy = lambda poly: poly * np.array([RY, 1])
    for s in (1, -1):
        # tail lamp (03_rear: y 0.43-0.965, z 1.115-1.29), a wedge pointing inward: red above, clear below
        red = np.array([(0.965, 1.29), (0.47, 1.29), (0.435, 1.235), (0.47, 1.18), (0.965, 1.17)]) * np.array([s, 1])
        clear = np.array([(0.965, 1.165), (0.48, 1.165), (0.50, 1.12), (0.965, 1.115)]) * np.array([s, 1])
        red, clear = sy(red), sy(clear)
        if s < 0: red, clear = red[::-1], clear[::-1]
        parts.append(part(P, f'tail_red{s}', red, M['tail'], offset=0.008, thick=0.015, step=0.008))
        parts.append(part(P, f'tail_clear{s}', clear, M['lens_chrome'], offset=0.008, thick=0.015, step=0.008))
        refl = sy(rrect(0.64, 0.94, 0.542, 0.577, 0.01) * np.array([s, 1]))
        parts.append(part(P, f'reflector{s}', refl if s > 0 else refl[::-1], M['tail'], offset=0.004, thick=0.008, step=0.006))
    parts.append(part(P, 'rear_diffuser', sy(rrect(-0.92, 0.92, 0.31, 0.56, 0.06)), M['trim'], offset=0.003, thick=0.02))
    parts.append(bar(P, 'rear_bumper_chrome', -0.70 * RY, 0.70 * RY, 0.47, M['chrome'], h=0.018, offset=0.012, zcurve=lambda y: 0.05 * max(0.0, (abs(y) / RY - 0.55) / 0.15)))
    parts.append(part(P, 'spoiler_brake', sy(rrect(-0.195, 0.195, 1.83, 1.85, 0.008)), M['tail'], offset=0.01, thick=0.01, step=0.006))
    parts.append(bar(P, 'tailgate_garnish', -0.40 * RY, 0.40 * RY, 1.095, M['chrome'], h=0.01, offset=0.008))
    return [p for p in parts if p]
