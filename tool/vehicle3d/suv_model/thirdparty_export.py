"""A layer of the private car to the game's GLB. thirdparty_export.py <in.blend> <out.glb> <sharp side> [largest side: 1024; the far layer 256]
- back faces culled (the model's parts are one-sided);
- a texture whose faces all read one point of it (every UV the same: the lamps' reflector photos, a sticker) is
  replaced by that point's colour (the photos carried a maker's mark; one texel needs no texture in memory);
- byte-identical images merged into one;
- no refraction pass and no physical extras but the paint's clear coat: transmission off (the red lenses keep their
  alpha), specular and IOR at glTF's defaults (three.js then uses its standard material, not the heavier physical one);
- textures scaled for the phone's memory (ADR 0005: a vehicle's textures 1K): every texture at most 1024 px a side,
  the roughness maps 512 (they carry no fine print), and the sheet whose small print the driver reads (the switches'
  symbols, the gauges) at most <sharp side> (1024 inside: lightness first, the owner's word; 2048 was tried). Uncompressed with their mipmaps
  that is about 22 MB a 2K texture and 6 MB a 1K one; the game is to load them compressed (KTX2)."""
import bpy, sys, os
SHARP = ('Buttons_baseColor',)


def flat():
    """Textures read at one point only become that colour (see the docstring); the extensions trimmed."""
    import numpy as np
    for o in [o for o in bpy.data.objects if o.type == 'MESH']:
        me = o.data; uv = me.uv_layers.active
        if uv is None: continue
        for i, sl in enumerate(o.material_slots):
            m = sl.material
            if not m or not m.node_tree: continue
            U = np.array([uv.data[li].uv[:] for p in me.polygons if p.material_index == i for li in p.loop_indices])
            if not len(U) or np.ptp(U, 0).max() > 1e-4: continue
            for n in [n for n in m.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]:
                im = n.image; w, h = im.size; px = np.array(im.pixels[:]).reshape(h, w, -1)
                u, v = U[0] % 1.0, U[0][1] % 1.0; c = px[min(h - 1, int(U[0][1] % 1.0 * h)), min(w - 1, int(U[0][0] % 1.0 * w))]
                for l in list(n.outputs['Color'].links):
                    sock = l.to_socket
                    if sock.type == 'RGBA': sock.default_value = (*c[:3], 1.0)
                    m.node_tree.links.remove(l)
                for l in list(n.outputs['Alpha'].links): m.node_tree.links.remove(l)
                print('  flat colour for %s on %s (%.3f %.3f %.3f)' % (im.name, m.name, *c[:3]))
    for m in bpy.data.materials:
        b = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m.node_tree else None
        if not b: continue
        b.inputs['Transmission Weight'].default_value = 0.0
        b.inputs['Specular IOR Level'].default_value = 0.5; b.inputs['Specular Tint'].default_value = (1, 1, 1, 1); b.inputs['IOR'].default_value = 1.5
        for nm in ('Specular IOR Level', 'Specular Tint', 'Transmission Weight', 'IOR'):
            for l in list(b.inputs[nm].links): m.node_tree.links.remove(l)


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
