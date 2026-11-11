"""An outside model put in our car's frame: thirdparty_frame.py <scene.gltf> <out.blend>
Its front is at -y and its left at +x, in its own units (Sketchfab's export of the LC300 VXR: about 1/100 m). Its
axles are found where its tyres meet the ground (the lowest points, ahead and behind its middle), and it is turned and
scaled so that they fall on ours: front axle x +1.556, wheelbase 2.850 m (the spec's), on the ground z 0."""
import bpy, sys, os, numpy as np
from mathutils import Matrix


def main(src, out):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=os.path.abspath(src)); bpy.context.view_layer.update()
    V = []
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        mw = np.array(o.matrix_world); co = np.zeros(len(o.data.vertices) * 3); o.data.vertices.foreach_get('co', co); V.append(co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3])
    V = np.vstack(V); z0 = V[:, 2].min(); low = V[V[:, 2] < z0 + 0.063 * (V[:, 2].max() - z0)]; ym = V[:, 1].mean()      # (the tyres' lowest 6 % of the car's height: their contact patches); ym = V[:, 1].mean()
    YF, YR = low[low[:, 1] < ym, 1].mean(), low[low[:, 1] > ym, 1].mean(); k = 2.850 / (YR - YF)
    T = Matrix(((0, -k, 0, k * YF + 1.556), (k, 0, 0, 0), (0, 0, k, -k * z0), (0, 0, 0, 1)))
    for o in [o for o in bpy.data.objects if o.parent is None]: o.matrix_world = T @ o.matrix_world
    print('axles at model y %.4f and %.4f: scale %.2f' % (YF, YR, k)); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))


if __name__ == '__main__':
    main(*sys.argv[-2:])
