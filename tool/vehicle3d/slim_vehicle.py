"""Slim a packed vehicle GLB for phones: fewer triangles, 1K texture, no extra vertex colours."""
import os, sys, json, base64
import bpy
src, dst, tris, tex = sys.argv[-4], sys.argv[-3], int(sys.argv[-2]), int(sys.argv[-1])
glb = os.path.abspath(os.path.splitext(dst)[0] + '_in.glb')
open(glb, 'wb').write(base64.b64decode(json.load(open(src))['glb']))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
for ob in [o for o in bpy.data.objects if o.type == 'MESH']:
    me = ob.data
    for a in list(me.color_attributes):
        me.color_attributes.remove(a)
    n = len(me.polygons)
    if n > tris:
        bpy.context.view_layer.objects.active = ob
        for o in bpy.data.objects:
            o.select_set(o == ob)
        d = ob.modifiers.new('dec', 'DECIMATE')
        d.ratio = tris / n
        bpy.ops.object.modifier_apply(modifier='dec')
    print(ob.name, n, '->', len(me.polygons))
for img in bpy.data.images:
    if img.size[0] > tex:
        img.scale(tex, int(img.size[1] * tex / img.size[0]))
        print('image', img.name, img.size[:])
out = os.path.abspath(os.path.splitext(dst)[0] + '_out.glb')
bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_image_format='JPEG', export_jpeg_quality=85)
json.dump({'glb': base64.b64encode(open(out, 'rb').read()).decode()}, open(dst, 'w'))
print('done', dst, os.path.getsize(out) // 1024, 'KB')
