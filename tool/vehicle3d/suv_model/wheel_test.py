"""One wheel alone: checks (signed volume, open edges, section widths) and renders face-on, from behind and at an angle.
Run: ../blendenv/bin/python wheel_test.py <out_dir>"""
import bpy, bmesh, sys, os, math, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'suv'))
OUT = sys.argv[-1]; os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
import wheels, suv_exterior as SE
from mathutils import Vector
tm = SE.tyre_material(SE.tyre_maps(os.path.join(OUT, 'tex')))
ws = wheels.build(tm)
for w in ws:
    bm = bmesh.new(); bm.from_mesh(w.data)
    print(f'{w.name}: volume {bm.calc_volume(signed=True):+.5f}, open edges {sum(e.is_boundary for e in bm.edges)}, '
          f'zero faces {sum(f.calc_area() < 1e-10 for f in bm.faces)}, triangles {sum(len(f.verts) - 2 for f in bm.faces)}')
    bm.free()
w = ws[0]; me = w.data; ti = me.materials.find('tyre')
P = np.array([me.vertices[i].co[:] for p in me.polygons if p.material_index == ti for i in p.vertices]); r = np.hypot(P[:, 0], P[:, 2])
print(f'tyre: diameter {2 * r.max():.4f}, width {P[:, 1].max() - P[:, 1].min():.4f}, widest at r {r[np.argmax(P[:, 1])]:.4f}')
dep = np.round(r.max() - r, 5); sec = sorted({(d, np.abs(P[dep == d, 1]).max()) for d in np.unique(dep)})   # the section: (depth, half width)
for d in (0.006, 0.019, 0.039):
    wd = 2 * np.interp(d, [a for a, _ in sec], [b for _, b in sec]); print(f'  {d * 1000:.0f} mm above the ground: width {wd * 1000:.0f} mm = {wd / 0.265 * 100:.0f} %')
A = np.array([v.co[:] for v in me.vertices]); print(f'whole wheel: y {A[:, 1].min():+.4f} .. {A[:, 1].max():+.4f}')
for o in ws[2:]: bpy.data.objects.remove(o)
ws[0].location = (0, 0, 0); ws[1].location = (1.2, 0, 0)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = True
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.75, 0.78, 0.82, 1); bg.inputs[1].default_value = 1.0
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3.5
sun.rotation_euler = (math.radians(-60), math.radians(20), math.radians(10))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 1100, 640; sc.view_settings.view_transform = 'Standard'
for name, loc, look in (('wheel_face', (0.6, 3.2, 0.0), (0.6, 0, 0)), ('wheel_back', (0.6, -3.2, 0.3), (0.6, 0, 0)),
                        ('wheel_angle', (-1.2, 1.6, 0.5), (0.3, 0, 0)), ('wheel_front', (-2.6, 0.25, 0.0), (0, 0, 0))):
    cam.data.lens = 60; cam.location = loc; cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, name + '.png'); bpy.ops.render.render(write_still=True)
