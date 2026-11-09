"""Exterior finish of the photo SUV: deep gloss-black paint, working lamps, tyres with tread and sidewalls.

- Paint: the photo texture carries the studio's reflections, which made the black body read grey and see-through
  once real reflections were added on top. The dark, unsaturated (paint) pixels are pushed darker on a power curve;
  chrome, lamps and glass keep their tones. The paint gets a low roughness and a full clear coat.
- Lamps: the faces round the head and tail lamps get their own materials, with emission maps cut from the photo
  (bright white pixels at the front, red pixels at the back), so the game can light the tail lamps when braking.
- Tyres: a tread of staggered blocks between three zig-zag grooves, sidewalls with fine rings near the rim; one tiling
  colour map and one normal map, no lettering (no brand marks).
"""
import bpy, os, math, numpy as np
from PIL import Image

def _pixels(img):
    w, h = img.size; a = np.zeros(w * h * 4, np.float32); img.pixels.foreach_get(a); return a.reshape(h, w, 4), w, h

def _new_image(name, arr, noncolor=False):
    h, w = arr.shape[:2]
    im = bpy.data.images.new(name, w, h, alpha=False)
    im.colorspace_settings.name = 'Non-Color' if noncolor else 'sRGB'
    im.pixels.foreach_set(arr.astype(np.float32).ravel()); im.pack(); return im

def paint_setup(obj):
    """Strip vertex colours, darken the paint pixels of the photo, and set a gloss clear-coat paint."""
    me = obj.data
    for a in list(me.color_attributes): me.color_attributes.remove(a)
    m = me.materials[0]; nt = m.node_tree
    tex = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
    px, w, h = _pixels(tex.image)
    rgb = px[..., :3]
    L = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    mx_, mn_ = rgb.max(-1), rgb.min(-1); sat = (mx_ - mn_) / np.maximum(mx_, 1e-4)
    paint = (L < 0.40) & (sat < 0.35)
    f = np.where(paint, np.power(np.clip(L / 0.40, 1e-4, 1), 0.8), 1.0)[..., None]
    out = px.copy(); out[..., :3] = rgb * f
    # the photo's own sky and tree reflections: neutral mid-grey blots inside wide paint areas. They are pulled to the
    # paint around them, so they do not read as grey stains under the real reflections (thin bright chrome stays)
    from scipy import ndimage
    pf = ndimage.uniform_filter(paint.astype(np.float32), 31)
    mean = np.stack([ndimage.uniform_filter(out[..., k] * paint, 31) for k in range(3)], -1) / np.maximum(pf, 1e-3)[..., None]
    blot = (~paint) & (L < 0.52) & (sat < 0.25) & (pf > 0.72)          # chrome strips (brighter) stay
    w_ = np.clip((pf - 0.72) / 0.15, 0, 1)[..., None] * blot[..., None]
    out[..., :3] = out[..., :3] * (1 - w_) + mean * w_
    img = _new_image('suv_paint_albedo', out)
    # rebuild the node tree: image -> base colour, nothing else
    for n in list(nt.nodes):
        if n.type not in ('BSDF_PRINCIPLED', 'OUTPUT_MATERIAL'): nt.nodes.remove(n)
    b = nt.nodes['Principled BSDF']; t = nt.nodes.new('ShaderNodeTexImage'); t.image = img
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    # solid black: the colour layer is satin with almost no shine of its own; the clear coat gives the crisp reflections
    b.inputs['Roughness'].default_value = 0.5; b.inputs['Metallic'].default_value = 0.0
    b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.03
    b.inputs['Specular IOR Level'].default_value = 0.1
    m.blend_method = 'OPAQUE'
    try: m.surface_render_method = 'DITHERED'
    except Exception: pass
    return img, px

def lamp_materials(paint_mat, albedo_px, albedo_img):
    """Two materials sharing the paint's look, each with an emission map cut from the photo."""
    rgb = albedo_px[..., :3]
    L = rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    mx_, mn_ = rgb.max(-1), rgb.min(-1); sat = (mx_ - mn_) / np.maximum(mx_, 1e-4)
    red = (rgb[..., 0] > 0.28) & (rgb[..., 0] > 1.7 * rgb[..., 1]) & (rgb[..., 0] > 1.7 * rgb[..., 2])
    white = (L > 0.62) & (sat < 0.15)
    def emit_img(name, mask, colour=None):
        e = np.zeros_like(albedo_px); e[..., 3] = 1
        if colour is None: e[..., :3] = np.where(mask[..., None], np.clip(rgb * 1.6, 0, 1), 0)
        else: e[..., :3] = np.where(mask[..., None], np.array(colour, np.float32), 0)
        im = _new_image(name, e); im.scale(1024, 1024); return im
    mats = {}
    for name, mask, colour in (('tail_light', red, None), ('head_light', white, (1.0, 0.97, 0.92))):
        m = paint_mat.copy(); m.name = name; nt = m.node_tree; b = nt.nodes['Principled BSDF']
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = emit_img(name + '_emit', mask, colour)
        nt.links.new(t.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = 1.0
        mats[name] = m
    return mats

def assign_lamps(obj, mats, XF, K):
    """Faces in the lamp zones (measured on the photos) take the lamp materials."""
    me = obj.data; mw = obj.matrix_world
    idx = {}
    for n, m in mats.items():
        if m.name not in [x.name for x in me.materials]: me.materials.append(m)
        idx[n] = [x.name for x in me.materials].index(m.name)
    paint_i = 0; n_t = n_h = 0
    for p in me.polygons:
        if p.material_index != paint_i: continue
        c = mw @ p.center; d = (XF - c.x) / K; ay = abs(c.y) / K; z = c.z / K
        if d > 4.55 and ay > 0.30 and 0.95 < z < 1.40: p.material_index = idx['tail_light']; n_t += 1
        elif d < 0.45 and 0.58 < ay < 0.98 and 0.90 < z < 1.16: p.material_index = idx['head_light']; n_h += 1   # the lamp clusters, not the grille bars
    print('lamps', obj.name, 'tail', n_t, 'head', n_h)

# ------------------------------------------------------------------ tyres
def tyre_maps(out_dir, n=1024, m=256):
    """u runs round the tyre (12 tread blocks per tile), v across it: 0-0.3 outer sidewall, 0.3-0.7 tread, 0.7-1 inner."""
    os.makedirs(out_dir, exist_ok=True)
    u = (np.arange(n) + 0.5) / n; v = (np.arange(m) + 0.5) / m
    U, V = np.meshgrid(u, v)
    hgt = np.zeros_like(U); col = np.full_like(U, 0.105)
    tread = (V > 0.30) & (V < 0.70)
    tv = (V - 0.30) / 0.40                                     # 0..1 across the tread
    blocks = 12
    # zig-zag circumferential grooves
    zz = 0.018 * np.abs(((U * blocks * 2) % 2) - 1)
    for g in (0.22, 0.50, 0.78):
        groove = np.abs(tv - g - zz + 0.009) < 0.035
        hgt[tread & groove] = -1.0
    # slanted lateral sipes, staggered between the rows
    row = np.floor(tv * 4)
    phase = (U * blocks + tv * 0.6 + row * 0.5) % 1.0
    sipe = (np.abs(phase - 0.5) < 0.06) & tread
    hgt[sipe & (hgt == 0)] = -0.7
    # shoulder notches
    shoulder = tread & ((tv < 0.08) | (tv > 0.92)) & (((U * blocks * 2) % 1.0) < 0.35)
    hgt[shoulder] = -0.8
    col = np.where(tread, 0.060, 0.052) + hgt * 0.020
    # sidewalls: fine rings near the rim, a smooth band, a darker bead
    side = ~tread
    sv = np.where(V < 0.5, V / 0.30, (1 - V) / 0.30)           # 0 at the rim, 1 at the shoulder
    rings = (np.sin(sv * 2 * np.pi * 18) > 0.6) & (sv < 0.28)
    hgt[side & rings] = 0.25
    col = np.where(side, 0.050 + 0.010 * np.sin(sv * np.pi), col)          # linear: a black tyre is about 3% reflectance
    col += np.random.default_rng(3).normal(0, 0.002, col.shape)
    gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 2.0; gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 2.0
    nrm = np.stack([-gx, -gy, np.ones_like(hgt)], -1); nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)   # rows run up v here
    c8 = (np.clip(col, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)
    Image.fromarray(np.stack([c8] * 3, -1)[::-1]).save(f'{out_dir}/tyre_c.png')
    Image.fromarray(((nrm * 0.5 + 0.5) * 255).astype(np.uint8)[::-1]).save(f'{out_dir}/tyre_n.png')
    return f'{out_dir}/tyre_c.png', f'{out_dir}/tyre_n.png'

def tyre_material(paths):
    m = bpy.data.materials.new('tyre'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(paths[0]); t.image.pack()
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = bpy.data.images.load(paths[1]); tn.image.colorspace_settings.name = 'Non-Color'; tn.image.pack()
    nm = nt.nodes.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 1.0
    nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.85
    return m

def tyre_mesh(name, r_rim, r_tyre, width, mat, segs=56, prof_n=17, repeats=6):
    """A revolved tyre with UVs (u round, v across). The ends of the profile meet the rim at r_rim."""
    prof = []
    for i in range(prof_n):
        t = i / (prof_n - 1); a = math.pi * t
        rr = r_rim + (r_tyre - r_rim) * math.sin(a) ** 0.45
        ww = (width / 2) * math.cos(a) * (1.0 + 0.07 * math.sin(a))
        prof.append((rr, ww, t))
    V, F, UV = [], [], []
    for k in range(segs + 1):
        ang = 2 * math.pi * k / segs
        for rr, ww, t in prof: V.append((rr * math.cos(ang), ww, rr * math.sin(ang)))
    mm = len(prof)
    for k in range(segs):
        for i in range(mm - 1):
            a_, b_ = k * mm + i, (k + 1) * mm + i
            F.append([a_, b_, b_ + 1, a_ + 1])
            UV.append([(k / segs * repeats, prof[i][2]), ((k + 1) / segs * repeats, prof[i][2]),
                       ((k + 1) / segs * repeats, prof[i + 1][2]), (k / segs * repeats, prof[i + 1][2])])
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.update()
    lay = me.uv_layers.new(name='UVMap')
    for p, uvs in zip(me.polygons, UV):
        for li, uv in zip(p.loop_indices, uvs): lay.data[li].uv = uv
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); me.materials.append(mat)
    return ob
