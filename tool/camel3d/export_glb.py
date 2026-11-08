import os, bpy
bpy.ops.wm.open_mainfile(filepath=os.path.abspath('camel_rigged.blend'))
arm=bpy.data.objects['CamelRig']
for tr in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(tr)
arm.animation_data.action=None
for o in bpy.data.objects: o.select_set(o.name in ('Camel','CamelRig'))
kw=dict(filepath=os.path.abspath('camel_wodh_female.glb'), export_format='GLB', use_selection=True,
        export_animations=True, export_image_format='JPEG', export_jpeg_quality=86, export_apply=False)
try:
    bpy.ops.export_scene.gltf(export_animation_mode='ACTIONS', **kw)
except TypeError:
    bpy.ops.export_scene.gltf(**kw)
print('exported', os.path.getsize(kw['filepath']))
