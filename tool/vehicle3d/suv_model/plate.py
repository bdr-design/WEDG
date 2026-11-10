"""The number plates, front and rear: a Saudi private plate reading  ا م ن  1  (the owner's choice, 10 Nov).
Layout (Wikipedia, "Vehicle registration plates of Saudi Arabia"): four cells, the number in Eastern Arabic digits and
the three Arabic letters on top, the same in Latin underneath, each Latin letter under its Arabic one (ا A, م Z, ن N in
the plates' own table), and a band at the right with the country's name and KSA. Size: the long plate, 520 x 110 mm
(Wikipedia's figure for the current series; other sources give 550 x 110, and 335 x 155 for the short plate).
The national emblem on the band is not drawn (a plain disc stands for it): a game choice.
The plate is one thin box with one small texture, drawn here."""
import bpy, os, math
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont
import realframe as RF

W, H, T = 0.520, 0.110, 0.002
PX = 2000                                   # texture pixels per metre
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
ARABIC, LATIN, NUM_AR, NUM = ('ن', 'م', 'ا'), ('N', 'Z', 'A'), '١', '1'      # left to right as seen
KSA_AR = '\u0627\u0644\u0633\u0639\u0648\u062f\u064a\u0629'        # the country's name; Pillow shapes it (libraqm)
_HERE = os.path.dirname(os.path.abspath(__file__))
FONT_AR = next((p for p in (os.path.join(_HERE, '..', '..', '..', 'apps', 'marah', 'assets', 'fonts', 'IBMPlexSansArabic-Bold.ttf'),
                            '/home/user/WEDG/apps/marah/assets/fonts/IBMPlexSansArabic-Bold.ttf') if os.path.exists(p)), FONT)


def texture(path):
    w, h = int(W * PX), int(H * PX); im = Image.new('RGB', (w, h), (245, 245, 242)); d = ImageDraw.Draw(im); b = 6
    d.rounded_rectangle((b, b, w - b, h - b), 14, outline=(15, 15, 15), width=5)
    band = int(w * 0.86); mid = int(w * 0.30)
    d.line((band, b, band, h - b), fill=(15, 15, 15), width=4); d.line((mid, b, mid, h - b), fill=(15, 15, 15), width=4)
    d.line((b, h // 2, band, h // 2), fill=(15, 15, 15), width=4)
    big = ImageFont.truetype(FONT, int(h * 0.36)); small = ImageFont.truetype(FONT, int(h * 0.15)); tiny = ImageFont.truetype(FONT_AR, int(h * 0.12))
    def put(text, cx, cy, font): d.text((cx, cy), text, fill=(15, 15, 15), font=font, anchor='mm')
    put(NUM_AR, mid // 2, h * 0.27, big); put(NUM, mid // 2, h * 0.75, big)
    for i in range(3):
        cx = mid + (band - mid) * (i + 0.5) / 3; put(ARABIC[i], cx, h * 0.25, big); put(LATIN[i], cx, h * 0.75, big)
    cx = (band + w - b) // 2; put(KSA_AR, cx, h * 0.16, tiny)
    d.ellipse((cx - 16, h * 0.34, cx + 16, h * 0.34 + 32), fill=(15, 15, 15))
    for i, c in enumerate('KSA'): put(c, cx, h * (0.62 + 0.13 * i), small)
    os.makedirs(os.path.dirname(path), exist_ok=True); im.save(path); return path


def _box(name, centre, facing, lean, mat):
    """A plate facing +x (facing 1) or -x (-1), leaning back by lean radians; its texture reads from outside."""
    f = facing; V = []; uv = {}
    for k, (sy, sz) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        for face in (1, 0):                                                    # outer face first, then the back
            V.append(Vector((f * (T if face else 0.0), sy * W / 2, sz * H / 2)))
    F = [[0, 2, 4, 6][::f], [1, 7, 5, 3][::f]] + [[2 * i, 2 * i + 1, 2 * j + 1, 2 * j][::f] for i, j in ((0, 1), (1, 2), (2, 3), (3, 0))]
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in V], [], F); me.update(); layer = me.uv_layers.new(name='uv')
    for p in me.polygons:
        for li, vi in zip(p.loop_indices, p.vertices):
            v = V[vi]; outer = p.index == 0
            layer.data[li].uv = ((0.5 + f * v.y / W, 0.5 + v.z / H) if outer else (0.5, 0.03))      # read from outside: left is +y behind the car, -y ahead of it
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); me.materials.append(mat)
    o.rotation_euler = (0, -f * lean, 0); o.location = centre
    bpy.context.view_layer.update(); me.transform(o.matrix_world); o.matrix_world.identity()
    return o


def build(tex_dir, proud=0.004):
    path = texture(os.path.join(tex_dir, 'plate.png'))
    m = bpy.data.materials.new('number_plate'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    img = bpy.data.images.load(path); img.pack(); tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img
    nt.links.new(tn.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.35
    dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene; out = []
    def face(x0, dirx, z, half):
        """Where the body is at height z, the farthest out over the plate's width."""
        hits = [sc.ray_cast(dg, Vector((x0, half * (i / 8 - 1), z + H * (j / 6 - 0.5))), Vector((dirx, 0, 0))) for i in range(17) for j in range(7)]
        xs = [h[1].x for h in hits if h[0]]; return (min(xs) if dirx > 0 else max(xs))
    # rear: in the plate recess (03_rear: z 0.836 to 1.062 in the photo frame), leaning with its floor
    zc = float(RF.z_real(0.949)); xa, xb = face(-4.0, 1, zc - H / 2, W / 2), face(-4.0, 1, zc + H / 2, W / 2)
    out.append(_box('plate_rear', Vector((min(xa, xb) - proud, 0, zc)), -1, math.atan2(xb - xa, H), m))
    # front: on the holder in the lower intake (02_front: z 0.467 to 0.548 in the photo frame)
    zc = float(RF.z_real(0.5075)); xf = face(4.0, -1, zc, W / 2)      # clear of the intake's bars and the holder
    out.append(_box('plate_front', Vector((xf + proud, 0, zc)), 1, 0.0, m))
    for o in out: print(f'{o.name}: centre x {sum(v.co.x for v in o.data.vertices) / 8:.3f} z {sum(v.co.z for v in o.data.vertices) / 8:.3f}')
    return out
