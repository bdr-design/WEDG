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
sys.path.insert(0, HERE); import outlines as _O
VIEWS = os.environ.get('VIEWS_DIR') or _O.VIEWS
CFG = json.load(open(os.environ.get('VIEWS_JSON') or os.path.join(HERE, 'views.json')))

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

def set_aspect(k):
    """A photo pixel spans s * k metres across and s metres up. Render pixels the same shape, so the render lands on the
    photo pixel for pixel (without this the render came out k times too narrow or too wide across)."""
    if k >= 1: sc.render.pixel_aspect_x, sc.render.pixel_aspect_y = k, 1.0
    else: sc.render.pixel_aspect_x, sc.render.pixel_aspect_y = 1.0, 1.0 / k
    cam.data.sensor_fit = 'AUTO'

def view_cam(name):
    """Place an orthographic camera so the render lands pixel for pixel on the photo."""
    c = CFG[name]; W, H = c['W'], c['H']
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.pixel_aspect_x = sc.render.pixel_aspect_y = 1.0
    if name == 'side':     # looking from the left (+y) at the left flank, the front on the image's left
        s = c['s']; cam.data.ortho_scale = max(W, H) * s
        x = L / 2 - (W / 2 - c['u0']) * s; z = (c['v0'] - H / 2) * s
        cam.location = (x, 20, z); cam.rotation_euler = (math.pi / 2, 0, math.pi)
    elif name in ('front', 'rear'):
        s = c['s']; k = c['k']; cam.data.ortho_scale = max(W * s * k, H * s)   # the photo was stretched sideways by k
        set_aspect(k)
        z = (c['v0'] - H / 2) * s
        yc = (W / 2 - c['uc']) * s * k * (1 if name == 'front' else -1)
        # the image centre is at y = +yc in both views (the front camera's right is +y, the rear camera's is -y)
        if name == 'front': cam.location = (20, yc, z); cam.rotation_euler = (math.pi / 2, 0, math.pi / 2)
        else: cam.location = (-20, yc, z); cam.rotation_euler = (math.pi / 2, 0, -math.pi / 2)
    else:                  # top: looking down, the front at the top of the image
        # the top photo was scaled by its width with mirrors, which are small from above: its body comes out 2.5 %
        # narrower than in the front photo (and than the real 1.98 m). TOP_K corrects that.
        s = c['s']; k = c['k'] * float(os.environ.get('TOP_K', '1.026')); cam.data.ortho_scale = max(W * s * k, H * s)
        set_aspect(k)
        x = L / 2 - (H / 2 - c['v0']) * s; y = -(W / 2 - c['uc']) * s * k
        # image up = +x (the front at the top, as in the photo), image right = -y (the left side on the left)
        cam.location = (x, y, 20); cam.rotation_euler = (0, 0, -math.pi / 2)
    cam.data.clip_end = 100

def score(name, path):
    from PIL import Image
    from scipy import ndimage
    import cv2
    ph = np.asarray(Image.open(next(os.path.join(VIEWS, f'{v}.{e}') for v in (name_map[name],) for e in ('png', 'webp') if os.path.exists(os.path.join(VIEWS, f'{v}.{e}')))).convert('RGB')).astype(np.float32)
    if os.environ.get('REAL'):
        ph = warp_photo(name, ph); Image.fromarray(ph.astype(np.uint8)).save(os.path.join(OUT, f'{name}_photo_real.jpg'))
    rd = np.asarray(Image.open(path).convert('RGBA')).astype(np.float32)
    if name != 'top':
        # nothing shows below the ground: the model's rigid tyres stand on the loaded radius, so they reach 28 mm under
        # z = 0, where the ground hides them (the photo's tyres stand on the ground row v0)
        rd = rd.copy(); rd[int(math.floor(CFG[name]['v0'])) + 1:, :, 3] = 0
    mag = (ph[..., 0] > 180) & (ph[..., 2] > 180) & (ph[..., 1] < 110)
    pm = ndimage.binary_fill_holes(~mag); rm = ndimage.binary_fill_holes(rd[..., 3] > 127)   # outlines: holes filled in both
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

def warp_photo(name, ph):
    """REAL=1: map the photo into the real frame (realframe.py), so a model built to the spec sheet is scored against
    the photo as it would look at the real dimensions. Each output pixel is a real-frame point; it is looked up at
    the photo-frame point it came from."""
    import cv2
    sys.path[:0] = [HERE]; import realframe as RF
    c = CFG[name]; H_, W_ = ph.shape[:2]; s = c['s']
    u, v = np.meshgrid(np.arange(W_, dtype=np.float64), np.arange(H_, dtype=np.float64))
    if name == 'side':
        xr = L / 2 - (u - c['u0']) * s; zr = (c['v0'] - v) * s
        up = c['u0'] + (L / 2 - RF.x_photo(xr)) / s; vp = c['v0'] - RF.z_photo(zr) / s
    elif name in ('front', 'rear'):
        sg = 1 if name == 'front' else -1; k = c['k']
        yr = sg * (u - c['uc']) * s * k; zr = (c['v0'] - v) * s
        up = c['uc'] + sg * (yr / RF.PHOTO_Y_SCALE[name]) / (s * k); vp = c['v0'] - RF.z_photo(zr) / s
    else:
        k = c['k'] * float(os.environ.get('TOP_K', '1.026'))
        xr = L / 2 - (v - c['v0']) * s; yr = (c['uc'] - u) * s * k
        vp = c['v0'] + (L / 2 - RF.x_photo(xr)) / s; up = c['uc'] - (yr / RF.PHOTO_Y_SCALE[name]) / (s * k)
    return cv2.remap(ph.astype(np.float32), up.astype(np.float32), vp.astype(np.float32), cv2.INTER_LINEAR,
                     borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 0, 255))

name_map = {'side': '01_left', 'front': '02_front', 'rear': '03_rear', 'top': '04_top'}
res = {}
for name in os.environ.get('SCORE_VIEWS', 'side,front,rear,top').split(','):
    view_cam(name); p = os.path.join(OUT, f'{name}.png'); sc.render.filepath = p; bpy.ops.render.render(write_still=True)
    res[name] = score(name, p)
    print(f'{name:5s}  silhouette IoU {res[name][0]:.3f}   edge distance {res[name][1]:5.1f} mm   colour error {res[name][2]:5.1f}')
json.dump({k: {'iou': v[0], 'edge_mm': v[1], 'colour': v[2]} for k, v in res.items()}, open(os.path.join(OUT, 'scores.json'), 'w'), indent=1)
