"""Step 1: the body shell, a quad loft of cross sections set by the photo outlines (outlines.py).
Each station across the length is a closed section: its height from the side outline, its half-width at each height
the softer of the front outline (the greenhouse's lean-in, the shoulders) and the top outline (the plan's rounded
corners), with rounded roof and sill edges. The result is one clean quad mesh, mirrored about the centre line."""
import bpy, bmesh, math, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outlines as O

# The top photo at TOP_K 1.026 is 1.980 m across its flares, the spec width; the body is built on the front photo's
# scale, which realframe.Y_SCALE (1.980 / 2.0125) takes to the spec. So top-photo widths go in at 1.026 / Y_SCALE.
import realframe as RF
TOP_TO_FRONT = 1.026 / RF.Y_SCALE

def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)

# The roof's crown across the car, measured on the front and rear photos: a parabola, 9 mm down at |y| 0.45 m
# (front photo 9.3, rear photo 9.6) and 13.4 mm at 0.55. It fades out down the windshield (real x +0.45 -> +1.05)
# and over the tail (-2.10 -> -2.30), where the photos show no roof.
CROWN_K = 0.0134 / 0.55 ** 2                  # per metre, real frame
CROWN_FADE = (0.45, 1.05, -2.10, -2.30)
_Z_TOP_SLOPE = (RF._ZR[-1] - RF._ZR[-2]) / (RF._ZP[-1] - RF._ZP[-2])      # real per photo height, up at the roof

def _step(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)

def crown(x, y):
    """How far the roof is below its centre line at half-width y, in the photo frame (x, y in the photo frame)."""
    xr = float(RF.x_real(x)); a, b, c, d = CROWN_FADE
    f = (1 - _step((xr - a) / (b - a))) * _step((xr - d) / (c - d))
    return f * CROWN_K / _Z_TOP_SLOPE * (np.asarray(y, dtype=float) * RF.Y_SCALE) ** 2

def section(x, n_side=64, n_top=10, n_bot=8, r_top=0.07, r_bot=0.05):
    zt, zb = float(O.side_top(x)), float(O.side_bottom(x))
    if zt - zb < 0.02: zt = zb + 0.02
    t = (1 - np.cos(np.linspace(0, math.pi, n_side))) / 2
    ze = zt                                    # the roof's height at its edge: the centre line less the crown there
    for _ in range(4):
        zs = zb + t * (ze - zb)
        # the AI views disagree on width: the top view is scaled to the front view's body width (1.97 m)
        w = smin(O.front_half(zs), np.full_like(zs, O.top_half(x) * TOP_TO_FRONT), 0.03)
        # round the roof and the sill edges
        rt = min(r_top, (ze - zb) / 3); rb = min(r_bot, (ze - zb) / 3)
        up = np.clip((zs - (ze - rt)) / rt, 0, 1); dn = np.clip(((zb + rb) - zs) / rb, 0, 1)
        w = w - rt * (1 - np.sqrt(np.clip(1 - up ** 2, 0, 1))) - rb * (1 - np.sqrt(np.clip(1 - dn ** 2, 0, 1)))
        w = np.maximum(w, 0.02)
        ze = max(zt - float(crown(x, w[-1])), zb + 0.02)
    zs = zb + t * (ze - zb)
    top = [(w[-1] * (1 - i / n_top), zt - float(crown(x, w[-1] * (1 - i / n_top)))) for i in range(1, n_top)]
    half = [(0.0, zb)] + [(w[0] * (i / n_bot), zb) for i in range(1, n_bot)] + list(zip(w, zs)) + top + [(0.0, zt)]
    # the closed loop: up the left side, then down the right side (mirrored), without repeating the centre points
    loop = [(x, y, z) for y, z in half] + [(x, -y, z) for y, z in half[-2:0:-1]]
    return loop

def build(step=0.02):
    xs = np.arange(O.X_REAR + 0.004, O.X_FRONT - 0.004, step)
    secs = [section(x) for x in xs]; n = len(secs[0])
    V = [p for s in secs for p in s]; F = []
    for i in range(len(secs) - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n; F.append([a, b, b + n, a + n])
    # caps
    c0 = len(V); V.append((xs[0], 0, float(np.mean([p[2] for p in secs[0]])))); c1 = len(V); V.append((xs[-1], 0, float(np.mean([p[2] for p in secs[-1]]))))
    for j in range(n):
        F.append([c0, (j + 1) % n, j]); k = (len(secs) - 1) * n; F.append([c1, k + j, k + (j + 1) % n])
    me = bpy.data.meshes.new('body'); me.from_pydata(V, [], F); me.update()
    ob = bpy.data.objects.new('body', me); bpy.context.collection.objects.link(ob)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    return ob

if __name__ == '__main__':
    out = sys.argv[-1]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ob = build()
    m = bpy.data.materials.new('paint'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1); b.inputs['Roughness'].default_value = 0.2; b.inputs['Coat Weight'].default_value = 1.0
    ob.data.materials.append(m)
    print('body faces', len(ob.data.polygons))
    os.makedirs(out, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, 'body.blend'))
