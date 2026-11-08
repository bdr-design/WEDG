"""Make lighter copies of the rigged camel (same skeleton, same clips) and report sizes."""
import os, bpy, json
res = {}
for name, tris, tex in (('lod1', 8000, 1024), ('lod2', 1500, 512)):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath('camel_rigged.blend'))
    ob = bpy.data.objects['Camel']
    full = len(ob.data.polygons)
    bpy.context.view_layer.objects.active = ob
    d = ob.modifiers.new('dec', 'DECIMATE'); d.ratio = tris / full
    bpy.ops.object.modifier_move_to_index(modifier='dec', index=0)
    bpy.ops.object.modifier_apply(modifier='dec')
    for img in bpy.data.images:
        if img.size[0] > tex: img.scale(tex, tex)
    arm = bpy.data.objects['CamelRig']
    for tr in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(tr)
    arm.animation_data.action = None
    for o in bpy.data.objects: o.select_set(o.name in ('Camel', 'CamelRig'))
    path = os.path.abspath(f'camel_wodh_female_{name}.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_animations=True,
                              export_animation_mode='ACTIONS', export_image_format='JPEG', export_jpeg_quality=85)
    res[name] = {'triangles': len(ob.data.polygons), 'texture': tex, 'glb_kb': os.path.getsize(path) // 1024}
res['lod0'] = {'triangles': 40000, 'texture': 2048, 'glb_kb': os.path.getsize('camel_wodh_female.glb') // 1024}
print(json.dumps(res))
