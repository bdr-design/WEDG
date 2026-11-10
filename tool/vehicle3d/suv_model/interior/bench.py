"""The second row's bench, from rear_bench.png, in the car's frame. First pass: its main masses as regions of the
photo laid on planes through that photo's camera (photocam): the cushion's top (level), its front face and the
headrests (upright) and the seat backs (leaning). Where the planes stand is a CHOICE (cabin.CAMERAS says why no
camera fits this photo exactly); the regions are first readings to about 6 px."""
import bpy, bmesh, os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import relief as R, photocam as PC, masks as M
from seat import _mat
from skimage.draw import polygon as _poly
from mathutils import Vector

CAM = PC.Camera('rear_bench')
FRONT_X, TOP_Z = -0.75, 0.93                     # the cushion's front edge
BACK_FOOT, BACK_HEAD = (-1.22, 0.0, 0.97), (-1.44, 0.0, 1.52)         # the seat backs' face, at the cushion and at their top
def _s(pts): return [(x / 0.76, y / 0.76) for x, y in pts]             # readings were taken on a 0.76 enlargement
BACK = CAM.plane(BACK_FOOT, (-1, 0, -(BACK_HEAD[0] - BACK_FOOT[0]) / (BACK_HEAD[2] - BACK_FOOT[2])), (BACK_HEAD[0] - BACK_FOOT[0], 0, BACK_HEAD[2] - BACK_FOOT[2]))
# name: (plane, thickness behind it, edge rounding, material, corners on the photo)
PARTS = {
    'cushion': (CAM.level(TOP_Z), 0.20, 0.05, 'leather', _s([(270, 470), (1030, 470), (1200, 560), (1190, 600), (770, 585), (640, 585), (160, 590), (85, 560), (120, 520)])),
    'front': (CAM.upright(FRONT_X), 0.30, 0.04, 'leather', _s([(85, 560), (160, 590), (640, 585), (770, 585), (1190, 600), (1200, 560), (1195, 620), (1140, 670), (280, 690), (140, 650), (90, 610)])),
    'back_L': (BACK, 0.14, 0.05, 'leather', _s([(245, 160), (300, 140), (500, 140), (505, 470), (270, 470), (235, 360)])),
    'back_C': (BACK, 0.14, 0.03, 'leather', _s([(570, 160), (715, 160), (715, 470), (570, 470)])),
    'back_R': (BACK, 0.14, 0.05, 'leather', _s([(720, 140), (960, 140), (1030, 170), (1040, 360), (1010, 470), (715, 470)])),
    'head_L': (CAM.upright(BACK_HEAD[0] + 0.02), 0.10, 0.04, 'leather', _s([(350, 30), (455, 30), (465, 60), (462, 125), (445, 140), (360, 140), (342, 125), (340, 60)])),
    'head_C': (CAM.upright(BACK_HEAD[0] + 0.02), 0.10, 0.035, 'leather', _s([(588, 78), (698, 78), (708, 100), (706, 145), (692, 155), (594, 155), (580, 145), (578, 100)])),
    'head_R': (CAM.upright(BACK_HEAD[0] + 0.02), 0.10, 0.04, 'leather', _s([(820, 30), (930, 30), (940, 60), (938, 125), (922, 140), (828, 140), (812, 125), (810, 60)])),
}


def build(name='seat_bench_2'):
    a = M.rgb('rear_bench'); H, W = a.shape[:2]; Mt = {'leather': _mat('seat_leather', (0.60, 0.49, 0.34), rough=0.55), 'black': _mat('cabin_black', (0.03, 0.03, 0.031), rough=0.5)}
    idx = {k: i for i, k in enumerate(Mt)}; bm = bmesh.new(); lay = bm.verts.layers.float_vector.new('relief_n')
    for part, (pl, thick, rad, mat, shape) in PARTS.items():
        m = np.zeros((H, W), bool); r, c = _poly([p[1] for p in shape], [p[0] for p in shape], m.shape); m[r, c] = True
        n0 = len(bm.verts); mpp = pl.metres_per_px(r.mean(), c.mean())
        R.solid(bm, m, pl.to_ab, mpp, thick, min(rad, thick / 2), y0=thick / 2, mat=idx[mat], rings=5, spacing=0.014, fill=0.07)
        bm.verts.ensure_lookup_table()
        for v in bm.verts[n0:]: v.co = pl.to_car(v.co); v[lay] = pl.mx @ Vector(v[lay])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in Mt.values(): me.materials.append(m)
    R.shade(me); ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    V = np.array([v.co for v in me.vertices]); print('bench: x %.2f..%.2f, y %.2f..%.2f, z %.2f..%.2f' % (V[:, 0].min(), V[:, 0].max(), V[:, 1].min(), V[:, 1].max(), V[:, 2].min(), V[:, 2].max()))
    return ob


if __name__ == '__main__':
    out = sys.argv[-1]; bpy.ops.wm.read_factory_settings(use_empty=True); ob = build(); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
