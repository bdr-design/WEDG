"""Rear view of a built .blend beside the same window of the rear photo, both under one grid in the body's photo frame
(y on the front photo's scale, z as the side photo). The .blend is in the real frame; the render is mapped back.
usage: rcmp.py <blend> <name> y0 y1 z0 z1 [zoom] [step]"""
import bpy, sys, os, numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'suvm7'))
import realframe as RF
UC, V0, S, K = 627.0, 1159.0, 0.0019445199644753774, 1.0285314815677868
RY = 0.9694; SY = S * K * RY
a = sys.argv[1:]; blend, name = a[0], a[1]; y0, y1, z0, z1 = map(float, a[2:6])
zoom = float(a[6]) if len(a) > 6 else 4; step = float(a[7]) if len(a) > 7 else 0.05
G = float(os.environ.get('GAMMA', '1'))
u = lambda y: UC - y / SY; v = lambda z: V0 - z / S
box = (int(u(y1)), int(v(z1)), int(u(y0)) + 1, int(v(z0)) + 1)
size = (int((box[2] - box[0]) * zoom), int((box[3] - box[1]) * zoom))
# the crop's true edges in the photo frame
ya, yb = (UC - box[2]) * SY, (UC - box[0]) * SY; za, zb = (V0 - box[3]) * S, (V0 - box[1]) * S
sys.path.insert(0, os.path.join(HERE, '..')); import outlines as _O
im = Image.open(_O.photo('03_rear')).convert('RGB')
photo = im.crop(box).resize(size, Image.LANCZOS)

bpy.ops.wm.open_mainfile(filepath=blend); sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT'): bpy.data.objects.remove(o)
sc.render.engine = 'CYCLES'; sc.cycles.samples = int(os.environ.get('SAMPLES', '24')); sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
w = bpy.data.worlds.new('sky'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.75, 0.8, 0.9, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.0; sun.rotation_euler = (0.9, 0.0, 2.2); sc.collection.objects.link(sun)
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0)); g = bpy.context.active_object; m = bpy.data.materials.new('g'); m.use_nodes = True
b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (0.55, 0.45, 0.33, 1); b.inputs['Roughness'].default_value = 0.9; g.data.materials.append(m)
sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = 0.3
if os.environ.get('STUDIO'):      # a pale floor and an even sky: parts that lean over still show their own colour
    b.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1); w.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1)
    w.node_tree.nodes['Background'].inputs[1].default_value = 0.6; sun.data.energy = 1.5; sc.view_settings.exposure = 0.0
ra, rb = RF.y_real(ya), RF.y_real(yb); qa, qb = RF.z_real(za), RF.z_real(zb); wr, hr = rb - ra, qb - qa
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = max(wr, hr); cam.data.clip_end = 40
cam.location = (-9.0, (ra + rb) / 2, (qa + qb) / 2); cam.rotation_euler = (np.pi / 2, 0, -np.pi / 2)
ppm = size[0] / wr; sc.render.resolution_x, sc.render.resolution_y = size[0], max(4, int(round(hr * ppm))); sc.render.resolution_percentage = 100
tmp = os.path.join(HERE, name + '_r.png'); sc.render.filepath = tmp; bpy.ops.render.render(write_still=True)
R = np.asarray(Image.open(tmp).convert('RGB')); Hr = R.shape[0]
# rows of the photo frame taken from the render's real-frame rows
zs = zb - (np.arange(size[1]) + 0.5) / size[1] * (zb - za)
rows = np.clip(((qb - np.array([RF.z_real(z) for z in zs])) / hr * Hr).astype(int), 0, Hr - 1)
rend = Image.fromarray(R[rows])
def grid(c):
    if G != 1: c = Image.fromarray((255 * (np.asarray(c) / 255.0) ** (1 / G)).astype(np.uint8))
    d = ImageDraw.Draw(c)
    for y in np.arange(np.ceil(y0 / step) * step, y1 + 1e-6, step):
        x = (u(y) - box[0]) * zoom; d.line([(x, 0), (x, c.size[1])], fill=(0, 255, 255), width=1); d.text((x + 2, 2), f'{y:.2f}', fill=(255, 255, 0))
    for z in np.arange(np.ceil(z0 / step) * step, z1 + 1e-6, step):
        yy = (v(z) - box[1]) * zoom; d.line([(0, yy), (c.size[0], yy)], fill=(0, 255, 255), width=1); d.text((2, yy + 2), f'{z:.2f}', fill=(255, 255, 0))
    return c
if os.environ.get('NOGRID'): grid = lambda c: c
P, Q = grid(photo), grid(rend)
if size[0] >= size[1]:
    out = Image.new('RGB', (size[0], size[1] * 2 + 6), (255, 0, 255)); out.paste(P, (0, 0)); out.paste(Q, (0, size[1] + 6))
else:
    out = Image.new('RGB', (size[0] * 2 + 6, size[1]), (255, 0, 255)); out.paste(P, (0, 0)); out.paste(Q, (size[0] + 6, 0))
out.save(os.path.join(HERE, name + '.png')); os.remove(tmp); print('saved', name, out.size)
