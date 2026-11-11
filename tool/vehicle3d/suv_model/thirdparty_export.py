"""A layer of the private car to the game's GLB. thirdparty_export.py <in.blend> <out.glb> <sharp side> [largest side: 1024; the far layer 256]
- back faces culled (the model's parts are one-sided);
- a texture whose faces all read one point of it (every UV of the map it reads the same), or that hardly varies (the
  leather's roughness maps), is replaced by that colour: a plain value needs no texture in memory; the UV maps no
  texture reads are dropped; metallic only on the metals (METALS); a clear coat only on the paint;
- byte-identical images merged into one;
- no refraction pass and no physical extras but the paint's clear coat: transmission off (the red lenses keep their
  alpha), specular and IOR at glTF's defaults (three.js then uses its standard material, not the heavier physical one);
- textures scaled for the phone's memory (ADR 0005: a vehicle's textures 1K): every texture at most 1024 px a side,
  the roughness maps 512 (they carry no fine print), and the sheet whose small print the driver reads (the switches'
  symbols, the gauges) at most <sharp side> (1024 inside: lightness first, the owner's word; 2048 was tried). Uncompressed with their mipmaps
  that is about 22 MB a 2K texture and 6 MB a 1K one; the game is to load them compressed (KTX2)."""
import bpy, sys, os
SHARP = ('Buttons_baseColor',)


METALS = ('Chrome', 'Metal', 'Mirror')        # the materials that are metal; the rest (leather, fabric, plastic, rubber, the trims' sheet) are not
FLAT_SPREAD = 6 / 255                           # a texture varying less than this (its 1st to 99th percentile, every channel) is a plain value


def tex_uv(me, n):
    """The UV map an image node reads: its UV Map node's, else the mesh's render map."""
    v = n.inputs['Vector']
    if v.links and v.links[0].from_node.type == 'UVMAP' and v.links[0].from_node.uv_map: return me.uv_layers.get(v.links[0].from_node.uv_map)
    return next((l for l in me.uv_layers if l.active_render), me.uv_layers.active)


def flat():
    """Textures read at one point only, or nearly constant, become that colour (see the docstring); metal only where it
    is metal; the extensions trimmed; the UV maps no texture reads dropped."""
    import numpy as np
    def set_flat(m, n, c, why):
        for l in list(n.outputs['Color'].links):
            if l.to_socket.type == 'RGBA': l.to_socket.default_value = (*c[:3], 1.0)
            m.node_tree.links.remove(l)
        for l in list(n.outputs['Alpha'].links): m.node_tree.links.remove(l)
        print('  flat colour for %s on %s (%.3f %.3f %.3f): %s' % (n.image.name, m.name, *c[:3], why))
    pixels = {}
    def px(im):
        if im.name not in pixels: w, h = im.size; pixels[im.name] = np.array(im.pixels[:]).reshape(h, w, -1)
        return pixels[im.name]
    for o in [o for o in bpy.data.objects if o.type == 'MESH']:
        me = o.data; read = set()
        for i, sl in enumerate(o.material_slots):
            m = sl.material
            if not m or not m.node_tree: continue
            for n in [n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and n.outputs['Color'].links]:
                uv = tex_uv(me, n)
                if uv is None: continue
                read.add(uv.name); a = px(n.image)
                U = np.array([uv.data[li].uv[:] for p in me.polygons if p.material_index == i for li in p.loop_indices])
                if len(U) and np.ptp(U, 0).max() < 1e-4:
                    h, w = a.shape[:2]; set_flat(m, n, a[min(h - 1, int(U[0][1] % 1.0 * h)), min(w - 1, int(U[0][0] % 1.0 * w))], 'its faces read one point')
                else:
                    lo, hi = np.percentile(a[..., :3].reshape(-1, 3), [1, 99], axis=0)
                    if (hi - lo).max() < FLAT_SPREAD: set_flat(m, n, a[..., :3].reshape(-1, 3).mean(0), 'nearly constant')
        for l in [l for l in me.uv_layers if l.name not in read]:
            if len(me.uv_layers) > 1 or not read: me.uv_layers.remove(l)
    for m in bpy.data.materials:
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m.node_tree else None
        if not b: continue
        b.inputs['Transmission Weight'].default_value = 0.0
        b.inputs['Specular IOR Level'].default_value = 0.5; b.inputs['Specular Tint'].default_value = (1, 1, 1, 1); b.inputs['IOR'].default_value = 1.5
        for nm in ('Specular IOR Level', 'Specular Tint', 'Transmission Weight', 'IOR'):
            for l in list(b.inputs[nm].links): m.node_tree.links.remove(l)
        if not any(w in m.name for w in METALS):                                 # (the source's metallic 0.4-0.7 on leather and rubber, without its specular, read as dark metal)
            for l in list(b.inputs['Metallic'].links): m.node_tree.links.remove(l)
            b.inputs['Metallic'].default_value = 0.0
        if m.name != 'CarPaint':                                                  # (the paint's clear coat only: the one physical material)
            for l in list(b.inputs['Coat Weight'].links): m.node_tree.links.remove(l)
            b.inputs['Coat Weight'].default_value = 0.0


def dedupe(used):
    """Byte-identical images: every node reads the first."""
    import hashlib
    seen = {}; out = set()
    for im in sorted(used, key=lambda i: i.name):
        key = hashlib.sha1(bytes(memoryview(im.packed_file.data)) if im.packed_file else open(bpy.path.abspath(im.filepath), 'rb').read()).hexdigest() if (im.packed_file or os.path.exists(bpy.path.abspath(im.filepath))) else im.name
        if key in seen:
            for m in bpy.data.materials:
                for n in (m.node_tree.nodes if m.node_tree else ()):
                    if n.type == 'TEX_IMAGE' and n.image == im: n.image = seen[key]
            print('  %s is %s: merged' % (im.name, seen[key].name))
        else: seen[key] = im; out.add(im)
    return {n.image for m in bpy.data.materials if m.node_tree for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and any(l for l in n.outputs['Color'].links) and n.image in out}


def main(src, out, sharp, most='1024'):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src)); used = set()
    tex = os.path.join(os.path.dirname(os.path.abspath(src)), 'tex')
    if os.path.isdir(tex):                                                      # the cleaned textures (thirdparty_tex.py), applied again here: the last word on brand marks
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import thirdparty_tex as TX; TX.relink(tex)
    for m in {s.material for o in bpy.data.objects if o.type == 'MESH' for s in o.material_slots if s.material}:      # (what the meshes use: the GLB carries no other)
        m.use_backface_culling = True
        for n in (m.node_tree.nodes if m.node_tree else ()):
            if n.type == 'TEX_IMAGE' and n.image: used.add(n.image)
    flat(); used = dedupe(used)
    mem = 0
    for im in used:
        nm = im.name.split('.')[0]; side = int(sharp) if nm in SHARP else min(int(most), 512 if nm.endswith('metallicRoughness') else 1024); w, h = im.size
        if max(w, h) > side:
            if im.packed_file is None and not os.path.exists(bpy.path.abspath(im.filepath)): raise SystemExit('missing image ' + im.name)
            k = side / max(w, h); im.scale(max(1, round(w * k)), max(1, round(h * k)))
        mem += im.size[0] * im.size[1] * 4 * 4 / 3
        print('  %-36s %4d x %4d' % (im.name, *im.size))
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), export_format='GLB', export_apply=True, export_image_format='JPEG', export_jpeg_quality=90)      # (JPEG: no texture left here has alpha; a quarter of PNG's bytes)
    print('%s: %d textures, %.0f MB uncompressed with mipmaps' % (os.path.basename(out), len(used), mem / 2 ** 20))


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [x for x in sys.argv[1:] if not x.endswith('.py')][-4:] if sys.argv[-1].isdigit() and sys.argv[-2].isdigit() else sys.argv[-3:]
    main(*a)
