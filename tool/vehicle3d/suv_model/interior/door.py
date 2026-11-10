"""The front left door's trim, from door_FL.png. First pass: the panel as a slab and the beige armrest and sweep
standing out of it, each the photo's own region (relief.solid). How far anything stands out of the panel is not in
this photo (it is square-on): DEPTH is a game choice until the cabin photos are measured."""
import bpy, bmesh, os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import door_measure as DM, relief as R
from seat import _mat

DEPTH = {'panel': (0.030, 0.006), 'beige': (0.075, 0.030), 'wood': (0.060, 0.004), 'silver': (0.040, 0.003)}      # how far out of the door, and the edge's rounding


def materials():
    return {'panel': _mat('cabin_black', (0.03, 0.03, 0.031), rough=0.5), 'beige': _mat('seat_leather', (0.60, 0.49, 0.34), rough=0.55),
            'wood': _mat('cabin_wood_brown', (0.16, 0.075, 0.035), rough=0.3, coat=0.7), 'silver': _mat('cabin_silver', (0.50, 0.50, 0.50), metal=1.0, rough=0.38)}


def build(name='door_trim_FL'):
    lab = DM.labels(); s, to_xz, _ = DM.frame(); M = materials(); idx = {k: i for i, k in enumerate(M)}; bm = bmesh.new()
    for part, (out, rad) in DEPTH.items():
        m = lab != 0 if part == 'panel' else lab == DM.PARTS.index(part)
        if m.sum() > 400: R.solid(bm, m, to_xz, s, 2 * out, rad, y0=0.0, mat=idx[part], rings=6 if rad > 0.02 else 2, spacing=0.012, fill=0.06)
    # only the cabin's side is wanted: drop what lies behind the door's inner plane
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().y > 1e-4], context='FACES')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in M.values(): me.materials.append(m)
    R.shade(me); ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob


if __name__ == '__main__':
    out = sys.argv[-1]; bpy.ops.wm.read_factory_settings(use_empty=True); ob = build()
    me = ob.data; me.calc_loop_triangles(); print('door trim: %d triangles' % len(me.loop_triangles))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
