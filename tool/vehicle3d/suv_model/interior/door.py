"""The front left door's trim, from door_FL.png. First pass: the panel as a slab and the beige armrest and sweep
standing out of it, each the photo's own region (relief.solid). How far anything stands out of the panel is not in
this photo (it is square-on): DEPTH is a game choice until the cabin photos are measured."""
import bpy, bmesh, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import door_measure as DM, relief as R
from seat import _mat

import door_features as F, wheel_features as WF
from skimage.draw import polygon as _poly

# How far each thing stands out of the door's inner plane toward the cabin (metres), and its edge rounding where it
# is a soft part. A game choice: the photo is square-on.
PANEL, BEIGE = (0.030, 0.006), (0.075, 0.030)
POCKET_DEPTH, CUP_DEPTH = 0.050, 0.022          # behind the panel's face
OUT = {'rim': 0.032, 'lever': 0.026, 'lock': 0.020, 'slat': 0.033, 'switch_panel': 0.078, 'switch': 0.084, 'knob': 0.087, 'wood': 0.062,
       'speaker': 0.0305, 'lamp': 0.0315}


def materials():
    return {'panel': _mat('cabin_black', (0.03, 0.03, 0.031), rough=0.5), 'beige': _mat('seat_leather', (0.60, 0.49, 0.34), rough=0.55),
            'wood': _mat('cabin_wood_brown', (0.16, 0.075, 0.035), rough=0.3, coat=0.7), 'silver': _mat('cabin_silver', (0.50, 0.50, 0.50), metal=1.0, rough=0.38),
            'gloss': _mat('cabin_black_gloss', (0.012, 0.012, 0.013), rough=0.12, coat=1.0), 'dark': _mat('cabin_shadow', (0.008, 0.008, 0.008), rough=0.8),
            'grille': _mat('cabin_grille', (0.018, 0.018, 0.019), rough=0.75), 'red': _mat('cabin_red', (0.55, 0.03, 0.02), rough=0.4),
            'lamp': _mat('cabin_lamp', (0.8, 0.8, 0.78), rough=0.3), 'seam': _mat('seat_seam', (0.33, 0.26, 0.17), rough=0.8),
            'thread': _mat('seat_thread', (0.70, 0.60, 0.44), rough=0.7)}


def build(name='door_trim_FL'):
    lab = DM.labels(); s, to_xz, _ = DM.frame(); M = materials(); idx = {k: i for i, k in enumerate(M)}; bm = bmesh.new()
    snap = lambda p, reach=4: WF.snap(p, name='door_FL', reach=reach)
    xz = lambda p: np.c_[to_xz(np.asarray(p, float)[:, 1], np.asarray(p, float)[:, 0])]
    # the panel, with the map pocket and the handle's cup cut through it, and the beige armrest and sweep on it
    panel = lab != 0; pocket, cup = snap(F.POCKET), snap(F.HANDLE_CUP, 3)
    for p in (pocket, cup):
        r, c = _poly(p[:, 1], p[:, 0], panel.shape); panel[r, c] = False
    R.solid(bm, panel, to_xz, s, 2 * PANEL[0], PANEL[1], mat=idx['panel'], rings=2, spacing=0.012, fill=0.06)
    R.solid(bm, lab == DM.PARTS.index('beige'), to_xz, s, 2 * BEIGE[0], BEIGE[1], mat=idx['beige'], rings=6, spacing=0.012, fill=0.06)
    # only the cabin's side is wanted: drop the caps that lie on the door's far side
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if min(v.co.y for v in f.verts) > 0.004], context='FACES')
    grow = lambda p, k: p.mean(0) + (p - p.mean(0)) * k          # the floors reach past the openings' rounded rims
    R.ngon(bm, xz(grow(pocket, 1.10)), -PANEL[0] + POCKET_DEPTH, idx['dark']); R.ngon(bm, xz(grow(cup, 1.10)), -PANEL[0] + CUP_DEPTH, idx['gloss'])
    R.ring(bm, xz(snap(F.HANDLE_RIM)), xz(cup), -OUT['rim'], idx['gloss'], y_back=-PANEL[0])
    R.prism(bm, xz(snap(F.LEVER, 3)), -OUT['lever'], -PANEL[0] + CUP_DEPTH, idx['silver'])
    R.prism(bm, xz(F.LOCK_TAB), -OUT['lock'], -PANEL[0] + CUP_DEPTH, idx['red'])
    for sl in F.SLATS: R.prism(bm, xz(sl), -OUT['slat'], -PANEL[0], idx['gloss'])
    R.prism(bm, xz(snap(F.SWITCH_PANEL)), -OUT['switch_panel'], -PANEL[0], idx['gloss'], wall=idx['silver'])
    for sw in F.SWITCHES: R.prism(bm, xz(sw), -OUT['switch'], -OUT['switch_panel'], idx['panel'])
    kx, ky, kr = F.MIRROR_KNOB; R.prism(bm, xz([(kx + kr * np.cos(a), ky + kr * np.sin(a)) for a in np.linspace(0, 2 * np.pi, 20, endpoint=False)]), -OUT['knob'], -OUT['switch_panel'], idx['silver'])
    R.prism(bm, xz(snap(F.WOOD)), -OUT['wood'], -PANEL[0], idx['wood'])
    R.ngon(bm, xz(snap(F.SPEAKER)), -OUT['speaker'], idx['grille']); R.prism(bm, xz(F.LAMP), -OUT['lamp'], -PANEL[0], idx['lamp'])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # on the beige: the seam that parts the armrest's pad from the band under it, and the stitching along its upper sweep
    beige = lab == DM.PARTS.index('beige'); y_at = R.near_face(beige, s, 2 * BEIGE[0], BEIGE[1])
    R.ribbon(bm, F.ARMREST_SEAM, to_xz, y_at, 0.0022, idx['seam']); R.ribbon(bm, F.STITCH, to_xz, y_at, 0.0016, idx['thread'])
    R.ribbon(bm, [(x, y + 7) for x, y in F.STITCH], to_xz, y_at, 0.0016, idx['thread'])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in M.values(): me.materials.append(m)
    R.shade(me); ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob


if __name__ == '__main__':
    out = sys.argv[-1]; bpy.ops.wm.read_factory_settings(use_empty=True); ob = build()
    me = ob.data; me.calc_loop_triangles(); print('door trim: %d triangles' % len(me.loop_triangles))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
