"""A part from its photo's own camera (the square-on photos): same framing and size, with the photo beside it and a
score. shot.py seat <blend> <out.png>"""
import bpy, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import masks as M
what, blend, out = sys.argv[1:4]; bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
if what == 'seat':
    import seat_measure as SM
    photo = 'seat_side'; s, to_xz, (x_ref, z_ref) = SM.frame(); sv = s
    world = lambda col, row: ((col - x_ref) * s, (z_ref - row) * s)
if what == 'door':
    import door_measure as DM
    photo = 'door_FL'; s, to_xz, (x_ref, z_ref) = DM.frame(); sv = s
    world = lambda col, row: ((col - x_ref) * s, (z_ref - row) * s)
a = M.rgb(photo); H, W = a.shape[:2]
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.film_transparent = True
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.9, 0.9, 0.9, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.7
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(W, H) * s; cx, cz = world(W / 2, H / 2); cam.location = (cx, -5.0, cz); cam.rotation_euler = (np.pi / 2, 0, 0)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 1.6; sun.rotation_euler = (np.radians(55), 0, np.radians(25)); sc.collection.objects.link(sun)
for o in bpy.data.objects:      # a low mesh with smooth normals shades in blotches along a rounded edge in Cycles; this is the renderer's remedy
    if o.type == 'MESH': o.shadow_terminator_shading_offset = 0.35; o.shadow_terminator_geometry_offset = 0.4
sc.view_settings.view_transform = 'Standard'; sc.render.filepath = os.path.abspath(out); bpy.ops.render.render(write_still=True)
from PIL import Image
from scipy import ndimage
r = np.asarray(Image.open(out).convert('RGBA')).astype(float); obj = r[..., 3] > 127; pobj = ~M.backdrop(a) if what == 'door' else ~M.outside(a)
iou = (obj & pobj).sum() / (obj | pobj).sum(); both = obj & pobj; lm, lp = r[..., :3].mean(2), a.mean(2); bl = lambda x: ndimage.gaussian_filter(x, 4)
print('%s outline IoU %.4f; model only %d px, photo only %d px; brightness photo %.0f model %.0f, mean difference after a 4 px blur %.1f' % (what, iou, (obj & ~pobj).sum(), (pobj & ~obj).sum(), lp[both].mean(), lm[both].mean(), np.abs(bl(lm) - bl(lp))[both].mean()))
d = np.zeros((H, W, 3), np.uint8); d[obj & pobj] = (70, 70, 70); d[obj & ~pobj] = (0, 255, 0); d[pobj & ~obj] = (255, 0, 0); Image.fromarray(d).save(out.replace('.png', '_diff.png'))
comp = np.where(obj[..., None], r[..., :3], np.array([255, 0, 255.0])).astype(np.uint8); side = np.hstack([a.astype(np.uint8), comp]); Image.fromarray(side).resize((side.shape[1] // 2, side.shape[0] // 2)).save(out.replace('.png', '_side.jpg'), quality=88)
