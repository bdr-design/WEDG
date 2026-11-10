"""The wheel from the photo's own camera: square-on, same framing and size, magenta behind.
shot_wheel.py <blend> <out.png> [--score]"""
import bpy, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wheel_measure as WM, masks as M
a = sys.argv[1:]; bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); m = WM.read(); s, sv = m['scale'], m['scale_v']; cx, cy = m['centre']; N = 1254
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 16; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
sc.render.resolution_x = N; sc.render.resolution_y = NY = int(round(N * sv / s)); sc.render.film_transparent = True
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.9, 0.9, 0.9, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.55
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = N * s      # square pixels over N s by N sv metres; the picture is then stretched upward to the photo's N rows
cam.location = ((N / 2 - cx) * s, -2.0, -(N / 2 - cy) * sv); cam.rotation_euler = (np.pi / 2, 0, 0)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 1.0; sun.rotation_euler = (np.radians(60), 0, np.radians(20)); sc.collection.objects.link(sun)
sc.view_settings.view_transform = 'Standard'; sc.render.filepath = os.path.abspath(a[1]); bpy.ops.render.render(write_still=True)
from PIL import Image
Image.open(a[1]).resize((N, N), Image.BICUBIC).save(a[1]); r = np.asarray(Image.open(a[1]).convert('RGBA')).astype(float); obj = r[..., 3] > 127; ph = M.rgb('wheel'); pobj = ~M.backdrop(ph)
iou = (obj & pobj).sum() / (obj | pobj).sum(); both = obj & pobj; lm, lp = r[..., :3].mean(2), ph.mean(2)
from scipy import ndimage
bl = lambda x: ndimage.gaussian_filter(x, 4)
print('wheel outline IoU %.4f; model only %d px, photo only %d px; brightness (0..255) photo %.0f model %.0f, mean difference after a 4 px blur %.1f' % (iou, (obj & ~pobj).sum(), (pobj & ~obj).sum(), lp[both].mean(), lm[both].mean(), np.abs(bl(lm) - bl(lp))[both].mean()))
out = np.zeros((N, N, 3), np.uint8); out[obj & pobj] = (70, 70, 70); out[obj & ~pobj] = (0, 255, 0); out[pobj & ~obj] = (255, 0, 0)
Image.fromarray(out).save(a[1].replace('.png', '_diff.png'))
comp = np.where(obj[..., None], r[..., :3], np.array([255, 0, 255.0])).astype(np.uint8); Image.fromarray(np.hstack([ph.astype(np.uint8), comp])).resize((1254, 627)).save(a[1].replace('.png', '_side.jpg'), quality=88)
