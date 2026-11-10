"""The number plates, front and rear: a Saudi private plate reading  ا م ن  1  (the owner's choice, 10 Nov).
Layout (Wikipedia, "Vehicle registration plates of Saudi Arabia"): four cells, the number in Eastern Arabic digits and
the three Arabic letters on top, the same in Latin underneath, each Latin letter under its Arabic one (ا A, م Z, ن N in
the plates' own table), and a band with the country's name and KSA. On the long plate the band is in the middle,
between the number and the letters (Wikipedia: "on the right side, or in the center since 2014"; matriculasdelmundo.com:
a vertical stripe in the central part, separating the numbers from the letters); up to r23 it was drawn at the right.
Size: the long plate, 520 x 110 mm (Wikipedia's figure for the current series; other sources give 550 x 110 and
520 x 113, and 335 x 155 for the short plate).
Placement: the rear plate lies on the floor of the gate's recess and leans with it; the front plate stands upright on
a black bracket that takes up the slope of the two intake bars behind it (up to r23 both were set clear of the
farthest thing near them and floated: 15 to 27 mm of air behind the rear one, the front one hanging ahead of the bars).
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
    b0, b1 = int(w * 0.435), int(w * 0.565)                                   # the band, in the middle
    for x in (b0, b1): d.line((x, b, x, h - b), fill=(15, 15, 15), width=4)
    d.line((b, h // 2, b0, h // 2), fill=(15, 15, 15), width=4); d.line((b1, h // 2, w - b, h // 2), fill=(15, 15, 15), width=4)
    big = ImageFont.truetype(FONT, int(h * 0.36)); small = ImageFont.truetype(FONT, int(h * 0.15)); tiny = ImageFont.truetype(FONT_AR, int(h * 0.12))
    def put(text, cx, cy, font): d.text((cx, cy), text, fill=(15, 15, 15), font=font, anchor='mm')
    put(NUM_AR, (b + b0) // 2, h * 0.27, big); put(NUM, (b + b0) // 2, h * 0.75, big)
    for i in range(3):
        cx = b1 + (w - b - b1) * (i + 0.5) / 3; put(ARABIC[i], cx, h * 0.25, big); put(LATIN[i], cx, h * 0.75, big)
    cx = (b0 + b1) // 2; put(KSA_AR, cx, h * 0.16, tiny)
    d.ellipse((cx - 16, h * 0.33, cx + 16, h * 0.33 + 32), fill=(15, 15, 15))
    for i, c in enumerate('KSA'): put(c, cx, h * (0.60 + 0.125 * i), small)
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


def build(tex_dir, gap=0.001):
    path = texture(os.path.join(tex_dir, 'plate.png'))
    m = bpy.data.materials.new('number_plate'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    img = bpy.data.images.load(path); img.pack(); tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img
    nt.links.new(tn.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.35
    dg = bpy.context.evaluated_depsgraph_get(); sc = bpy.context.scene; out = []
    def row(x0, dirx, z, half=W / 2 - 0.01, n=13):
        """The outermost surface along the plate's width at height z (x of the first hit; the farthest out of them)."""
        xs = [h[1].x for h in (sc.ray_cast(dg, Vector((x0, half * (2 * i / (n - 1) - 1), z)), Vector((dirx, 0, 0))) for i in range(n)) if h[0]]
        return (min(xs) if dirx > 0 else max(xs))
    # rear: on the floor of the plate recess (03_rear: z 0.836 to 1.062 in the photo frame), leaning with it. The floor
    # is flat (it leans 4.6 degrees, its top further forward); the plate's back is gap off it at the nearest point.
    zc = float(RF.z_real(0.949)); zs = [zc + H * (k / 6 - 0.5) for k in range(7)]; xs = [row(-4.0, 1, z) for z in zs]
    lean = math.atan2(xs[-1] - xs[0], H); back = lambda z: xs[0] + (z - zs[0]) * (xs[-1] - xs[0]) / H
    off = min(x - back(z) for x, z in zip(xs, zs))                       # anything standing out of the floor's line
    out.append(_box('plate_rear', Vector(((xs[0] + xs[-1]) / 2 + off - gap, 0, zc)), -1, lean, m))
    # front: on the holder in the lower intake (02_front: z 0.467 to 0.548 in the photo frame). The intake's bars lean
    # back toward the ground (15 degrees) and a plate is hung upright, so it stands on a bracket: a black wedge from
    # the plate's back to the plane of the bars.
    zc = float(RF.z_real(0.5075)); zs = [zc + H * (k / 10 - 0.5) for k in range(11)]; xs = [row(4.0, -1, z) for z in zs]
    xf = max(xs) + gap; out.append(_box('plate_front', Vector((xf, 0, zc)), 1, 0.0, m))
    hw, hh = W / 2 - 0.02, H / 2 - 0.01; k = [i for i, z in enumerate(zs) if abs(z - zc) <= hh + 1e-6]
    zt, zb = zs[k[-1]], zs[k[0]]; top = max(xs[i] for i in k[-3:]); bot = max(xs[i] for i in k[:3])      # the bars behind its upper and lower thirds
    xb = lambda z: min(top + (z - zt) * (top - bot) / (zt - zb) - 0.003, xf - 0.002)                    # on the bars' plane (measured: 4 mm ahead of the top and bottom bars, 2 mm into the middle one)
    V = [(x, y, z) for z in (zb, zt) for y in (-hw, hw) for x in (xb(z), xf)]
    F = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
    me = bpy.data.meshes.new('plate_bracket'); me.from_pydata(V, [], F); me.update()
    br = bpy.data.objects.new('plate_bracket', me); bpy.context.collection.objects.link(br)
    import bmesh
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    me.materials.append(bpy.data.materials.get('trim_black') or m); out.append(br)
    print(f'plate_rear: leans {math.degrees(lean):.1f} deg, back {gap * 1e3:.0f} mm off the recess floor; plate_front: bracket {1e3 * (xf - xb(zt)):.0f} mm deep at its top, {1e3 * (xf - xb(zb)):.0f} at its foot')
    return out
