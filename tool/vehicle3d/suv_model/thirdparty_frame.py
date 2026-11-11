"""An outside model put in our car's frame: thirdparty_frame.py <scene.gltf> <out.blend>
Its front is at -y and its left at +x, in its own units (Sketchfab's export of the LC300 VXR: about 1/100 m). Its
axles are its tyres' middles (the four objects of its tyres' material, each one's box centre), and it is turned and
scaled so that they fall on ours: front axle x +1.556, wheelbase 2.850 m (the spec's), the tyres on the ground z 0.
(The lowest points' mean was used first: other low parts biased it, and the car came out 1.5 % large.)"""
import bpy, sys, os, numpy as np
from mathutils import Matrix


def main(src, out):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(src)); bpy.context.view_layer.update()
    C, Z = [], []
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.material_slots or not o.material_slots[0].material or o.material_slots[0].material.name.split('.')[0] != 'Wheel': continue
        mw = np.array(o.matrix_world); co = np.zeros(len(o.data.vertices) * 3); o.data.vertices.foreach_get('co', co); P = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
        C.append((P.min(0) + P.max(0)) / 2); Z.append(P[:, 2].min())
    C = np.array(C); assert len(C) == 4, len(C); z0 = min(Z); ym = C[:, 1].mean()
    YF, YR = C[C[:, 1] < ym, 1].mean(), C[C[:, 1] > ym, 1].mean(); k = 2.850 / (YR - YF)
    T = Matrix(((0, -k, 0, k * YF + 1.556), (k, 0, 0, 0), (0, 0, k, -k * z0), (0, 0, 0, 1)))
    for o in [o for o in bpy.data.objects if o.parent is None]: o.matrix_world = T @ o.matrix_world
    print('axles at model y %.4f and %.4f: scale %.2f' % (YF, YR, k)); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))


if __name__ == '__main__':
    main(*sys.argv[-2:])
