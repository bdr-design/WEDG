"""A front seat, from seat_side.png. Each part is the photo's own region given a width across the car and rounded
edges (relief.solid), so from the side the outline is the photo's. The seat faces +x; the photo's side is -y, which
is this seat's right: the photo is of a seat whose controls are on its right, the passenger's in a left-hand-drive
car. build(mirror=True) gives the driver's.
Across the car nothing is in this photo: the widths and edge radii below are a game choice until the cabin photos
are measured (WIDTHS)."""
import bpy, bmesh, os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seat_measure as SM, seat_features as F, relief as R

# part: (width across, edge radius, centre across, material)
WIDTHS = {'headrest': (0.270, 0.065, 0.0, 'leather'), 'back': (0.500, 0.075, 0.0, 'leather'), 'cushion': (0.520, 0.065, 0.0, 'leather'),
          'base': (0.510, 0.030, 0.0, 'plastic'), 'bracket': (0.300, 0.004, 0.0, 'black'), 'buckle': (0.045, 0.008, 0.215, 'black')}
POST_Y, POST_D = 0.075, 0.013
RAIL_Y, RAIL_W = 0.200, 0.045


def _mat(name, color, metal=0.0, rough=0.5, coat=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough; b.inputs['Coat Weight'].default_value = coat
    return m


def materials():
    return {'leather': _mat('seat_leather', (0.60, 0.49, 0.34), rough=0.55), 'plastic': _mat('cabin_beige', (0.55, 0.45, 0.31), rough=0.45),
            'black': _mat('cabin_black', (0.03, 0.03, 0.031), rough=0.5), 'chrome': _mat('cabin_chrome', (0.8, 0.8, 0.82), metal=1.0, rough=0.15)}


def build(name='seat_front', mirror=False):
    lab = SM.labels(); s, to_xz, _ = SM.frame(); M = materials(); idx = {k: i for i, k in enumerate(M)}; bm = bmesh.new()
    for part, (w, rad, yc, mat) in WIDTHS.items():
        R.solid(bm, lab == SM.PARTS.index(part), to_xz, s, w, rad, y0=yc, mat=idx[mat], rings=7 if rad > 0.02 else 3, spacing=0.011)
    for sy in (-1, 1):
        R.solid(bm, lab == SM.PARTS.index('posts'), to_xz, s, POST_D, POST_D / 2, y0=sy * POST_Y, mat=idx['chrome'], rings=2, spacing=0.004)
        R.solid(bm, lab == SM.PARTS.index('rail'), to_xz, s, RAIL_W, 0.004, y0=sy * RAIL_Y, mat=idx['black'], rings=1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if mirror:
        bmesh.ops.scale(bm, vec=(1, -1, 1), verts=bm.verts); bmesh.ops.reverse_faces(bm, faces=bm.faces); lay = bm.verts.layers.float_vector.get('relief_n')
        for v in bm.verts: v[lay] = (v[lay][0], -v[lay][1], v[lay][2])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in M.values(): me.materials.append(m)
    R.shade(me)
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); return ob


if __name__ == '__main__':
    out = sys.argv[-1]; bpy.ops.wm.read_factory_settings(use_empty=True); ob = build()
    me = ob.data; me.calc_loop_triangles(); print('seat: %d triangles' % len(me.loop_triangles))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
