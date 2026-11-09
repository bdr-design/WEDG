"""Render a built SUV from the exact cameras of the owner's four exterior photos and score the match.

Each photo is orthographic and was the source of the hull, so its mapping to the model is known exactly
(views.json from build_vehicle.py). For each view this writes the render, a side-by-side, and an overlay of the
two outlines, and prints:
- silhouette IoU: how well the outlines agree (1.0 = identical)
- edge distance: the mean distance in mm from the photo's strong edges to the nearest edge in the render
- colour error: the mean absolute difference inside the photo's outline (0-255)
Run: blendenv/bin/python compare_ext.py <model.glb or .blend> <out_dir>
"""
import bpy, sys, os, json, math, numpy as np
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
SRC, OUT = args[0], args[1]
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
VIEWS = os.environ.get('VIEWS_DIR') or os.path.join(HERE, '..', 'vehicles', 'Black_SUV_Views')
CFG = json.load(open(os.environ.get('VIEWS_JSON') or os.path.join(HERE, '..', 'vehicles', 'suv2', 'views.json')))

if SRC.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=SRC)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=SRC)
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT') or o.name in ('Ground', 'ground'): bpy.data.objects.remove(o)
# The hull's frame is the photos' frame: x forward (centred), y left, z up from the ground. suv_complete.py keeps it.
sc.render.engine = 'CYCLES'; sc.cycles.samples = 12; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = True
sc.render.film_transparent = True; sc.view_settings.view_transform = 'Standard'; sc.view_settings.exposure = 0
w = bpy.data.worlds.new('flat'); sc.world = w; w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (1, 1, 1, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1.0
cam = bpy.data.objects.new('cmp_cam', bpy.data.cameras.new('cmp_cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
L, Hm = CFG['L'], CFG['Hm']

def view_cam(name):
    """Place an orthographic camera so the render lands pixel for pixel on the photo."""
    c = CFG[name]; W, H = c['W'], c['H']
    sc.render.resolution_x, sc.render.resolution_y = W, H
    if name == 'side':     # looking from the left (+y) at the left flank, the front on the image's left
        s = c['s']; cam.data.ortho_scale = max(W, H) * s
        x = L / 2 - (W / 2 - c['u0']) * s; z = (c['v0'] - H / 2) * s
        cam.location = (x, 20, z); cam.rotation_euler = (math.pi / 2, 0, math.pi)
    elif name in ('front', 'rear'):
        s = c['s']; k = c['k']; cam.data.ortho_scale = max(W * s * k, H * s)   # the photo was stretched sideways by k
        sc.render.pixel_aspect_x, sc.render.pixel_aspect_y = 1.0, 1.0
        z = (c['v0'] - H / 2) * s
        yc = (W / 2 - c['uc']) * s * k * (1 if name == 'front' else -1)
        if name == 'front': cam.location = (20, -yc, z); cam.rotation_euler = (math.pi / 2, 0, math.pi / 2)
        else: cam.location = (-20, -yc, z); cam.rotation_euler = (math.pi / 2, 0, -math.pi / 2)
    else:                  # top: looking down, the front at the top of the image
        # the top photo was scaled by its width with mirrors, which are small from above: its body comes out 2.5 %
        # narrower than in the front photo (and than the real 1.98 m). TOP_K corrects that.
        s = c['s']; k = c['k'] * float(os.environ.get('TOP_K', '1.026')); cam.data.ortho_scale = max(W * s * k, H * s)
        x = L / 2 - (H / 2 - c['v0']) * s; y = -(W / 2 - c['uc']) * s * k
        cam.location = (x, -y, 20); cam.rotation_euler = (0, 0, math.pi / 2)
    cam.data.clip_end = 100

def score(name, path):
    from PIL import Image
    from scipy import ndimage
    import cv2
    ph = np.asarray(Image.open(next(os.path.join(VIEWS, f'{v}.{e}') for v in (name_map[name],) for e in ('png', 'webp') if os.path.exists(os.path.join(VIEWS, f'{v}.{e}')))).convert('RGB')).astype(np.float32)
    rd = np.asarray(Image.open(path).convert('RGBA')).astype(np.float32)
    mag = (ph[..., 0] > 180) & (ph[..., 2] > 180) & (ph[..., 1] < 110)
    pm = ndimage.binary_fill_holes(~mag); rm = rd[..., 3] > 127
    iou = (pm & rm).sum() / max((pm | rm).sum(), 1)
    s = CFG[name]['s']
    e1 = cv2.Canny(cv2.cvtColor(ph.astype(np.uint8), cv2.COLOR_RGB2GRAY), 60, 160) > 0
    comp = rd[..., :3] * (rd[..., 3:] / 255) + 255 * (1 - rd[..., 3:] / 255)
    e2 = cv2.Canny(cv2.cvtColor(comp.astype(np.uint8), cv2.COLOR_RGB2GRAY), 60, 160) > 0
    dt = ndimage.distance_transform_edt(~e2)
    edge_mm = float(dt[e1 & pm].mean() * s * 1000) if (e1 & pm).any() else float('nan')
    col = float(np.abs(comp - ph)[pm & rm].mean())
    over = ph.copy(); over[pm & ~rm] = (255, 0, 0); over[rm & ~pm] = (0, 160, 255)
    side = np.concatenate([ph, comp], 1)
    Image.fromarray(side.clip(0, 255).astype(np.uint8)).resize((side.shape[1] // 2, side.shape[0] // 2)).save(os.path.join(OUT, f'{name}_side.jpg'))
    Image.fromarray(over.clip(0, 255).astype(np.uint8)).resize((over.shape[1] // 2, over.shape[0] // 2)).save(os.path.join(OUT, f'{name}_overlay.jpg'))
    return iou, edge_mm, col

name_map = {'side': '01_left', 'front': '02_front', 'rear': '03_rear', 'top': '04_top'}
res = {}
for name in ('side', 'front', 'rear', 'top'):
    view_cam(name); p = os.path.join(OUT, f'{name}.png'); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
    res[name] = score(name, p)
    print(f'{name:5s}  silhouette IoU {res[name][0]:.3f}   edge distance {res[name][1]:5.1f} mm   colour error {res[name][2]:5.1f}')
json.dump({k: {'iou': v[0], 'edge_mm': v[1], 'colour': v[2]} for k, v in res.items()}, open(os.path.join(OUT, 'scores.json'), 'w'), indent=1)
