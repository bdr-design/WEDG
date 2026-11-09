"""Step 3: the front, measured on 02_front (out/02_front_grid.jpg has a 10 cm grid)."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector
from fascia_common import rrect, inside, Placer, part, bar

def front(shell, M):
    P = Placer(shell, 1); parts = []
    # grille: a dark mesh field, a chrome frame, four full-width chrome bars (02_front: y +-0.60, z 0.665-1.19)
    g = rrect(-0.60, 0.60, 0.665, 1.195, 0.03)
    parts.append(part(P, 'grille_mesh', g, M['grille'], offset=0.003, thick=0.02))
    parts.append(part(P, 'grille_frame', g, M['chrome'], offset=0.012, thick=0.012, hole=rrect(-0.575, 0.575, 0.69, 1.17, 0.02), step=0.008))
    for i, z in enumerate((1.175, 1.04, 0.91, 0.785)):
        parts.append(bar(P, f'grille_bar{i}', -0.58, 0.58, z, M['chrome'], h=0.016 if i == 0 else 0.012, offset=0.02))
    for k in range(10):                                   # the thin dark slats between the bars
        parts.append(bar(P, f'slat{k}', -0.57, 0.57, 0.70 + k * 0.047, M['trim'], h=0.006, offset=0.012))
    for s in (1, -1):
        # headlamp: a black housing with a clear lens, three projectors and a DRL strip along its top
        hl = rrect(0.605, 0.93, 1.10, 1.215, 0.02) * np.array([s, 1])
        if s < 0: hl = hl[::-1]
        parts.append(part(P, f'headlamp_housing{s}', hl, M['black_gloss'], offset=0.002, thick=0.02))
        for k, yc in enumerate((0.66, 0.74, 0.82)):
            loc, nrm = P.hit(s * yc, 1.15)
            if loc:
                bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.026, depth=0.02, location=loc + nrm * 0.012, rotation=(0, math.pi / 2, 0))
                c = bpy.context.active_object; c.data.materials.append(M['lens_chrome']); parts.append(c)
        parts.append(bar(P, f'drl_top{s}', s * 0.61, s * 0.92, 1.203, M['drl'], h=0.008, offset=0.016))
        # the L-shaped chrome and light bar down the side of the grille (y +-0.86, z 0.70-1.10)
        parts.append(part(P, f'drl_side{s}', rrect(0.845, 0.875, 0.70, 1.095, 0.01) * np.array([s, 1]) if s > 0 else (rrect(0.845, 0.875, 0.70, 1.095, 0.01) * np.array([s, 1]))[::-1], M['chrome'], offset=0.012, thick=0.012, step=0.006))
        parts.append(part(P, f'drl_foot{s}', rrect(0.62, 0.875, 0.70, 0.725, 0.01) * np.array([s, 1]) if s > 0 else (rrect(0.62, 0.875, 0.70, 0.725, 0.01) * np.array([s, 1]))[::-1], M['chrome'], offset=0.012, thick=0.012, step=0.006))
        # fog lamp in the bumper corner (y +-0.88, z 0.48)
        fl = rrect(0.83, 0.93, 0.455, 0.505, 0.012) * np.array([s, 1])
        parts.append(part(P, f'foglamp{s}', fl if s > 0 else fl[::-1], M['lens_chrome'], offset=0.004, thick=0.01, step=0.006))
    # lower bumper: a black intake band with a chrome strip, and a silver skid plate
    parts.append(part(P, 'front_intake', rrect(-0.66, 0.66, 0.34, 0.64, 0.05), M['trim'], offset=0.003, thick=0.02))
    parts.append(bar(P, 'front_bumper_chrome', -0.62, 0.62, 0.445, M['chrome'], h=0.014, offset=0.012))
    parts.append(part(P, 'skid_plate', rrect(-0.42, 0.42, 0.28, 0.345, 0.02), M['silver'], offset=0.006, thick=0.012))
    return [p for p in parts if p]

