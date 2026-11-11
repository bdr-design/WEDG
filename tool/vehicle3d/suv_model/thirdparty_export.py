"""A layer of the private car to the game's GLB. thirdparty_export.py <in.blend> <out.glb> <sharp side>
- back faces culled (the model's parts are one-sided);
- textures scaled for the phone's memory (ADR 0005: a vehicle's textures 1K): every texture at most 1024 px a side,
  the roughness maps 512 (they carry no fine print), and the sheet whose small print the driver reads (the switches'
  symbols, the gauges) at most <sharp side> (2048 for the interior, 1024 outside). Uncompressed with their mipmaps
  that is about 22 MB a 2K texture and 6 MB a 1K one; the game is to load them compressed (KTX2)."""
import bpy, sys, os
SHARP = ('Buttons_baseColor',)


def main(src, out, sharp):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src)); used = set()
    for m in {s.material for o in bpy.data.objects if o.type == 'MESH' for s in o.material_slots if s.material}:      # (what the meshes use: the GLB carries no other)
        m.use_backface_culling = True
        for n in (m.node_tree.nodes if m.node_tree else ()):
            if n.type == 'TEX_IMAGE' and n.image: used.add(n.image)
    mem = 0
    for im in used:
        nm = im.name.split('.')[0]; side = int(sharp) if nm in SHARP else 512 if nm.endswith('metallicRoughness') else 1024; w, h = im.size
        if max(w, h) > side:
            if im.packed_file is None and not os.path.exists(bpy.path.abspath(im.filepath)): raise SystemExit('missing image ' + im.name)
            k = side / max(w, h); im.scale(max(1, round(w * k)), max(1, round(h * k)))
        mem += im.size[0] * im.size[1] * 4 * 4 / 3
        print('  %-36s %4d x %4d' % (im.name, *im.size))
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), export_format='GLB', export_apply=True)
    print('%s: %d textures, %.0f MB uncompressed with mipmaps' % (os.path.basename(out), len(used), mem / 2 ** 20))


if __name__ == '__main__':
    main(*sys.argv[-3:])
