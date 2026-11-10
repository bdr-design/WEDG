"""The full body's surface baked into a normal map on the game layer's body, so that its light and reflections are
the full model's although it has a fifth of the faces. bake_lod.py <lod.blend> <full.blend> <out.blend> [size]
The layer's body is unwrapped (smart projection), a tangent-space normal map is baked from the full body onto it
(Cycles, selected to active, a small cage), and each of its materials reads the map."""
import bpy, sys, os, math
lod, full, out = sys.argv[1:4]; size = int(sys.argv[4]) if len(sys.argv) > 4 else 2048
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(lod))
with bpy.data.libraries.load(os.path.abspath(full)) as (src, dst): dst.objects = ['body']
hi = dst.objects[0]; hi.name = 'body_hi'; bpy.context.collection.objects.link(hi)
lo = bpy.data.objects['body']
for o in bpy.context.view_layer.objects: o.select_set(False)
bpy.context.view_layer.objects.active = lo; lo.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.003, scale_to_bounds=False); bpy.ops.object.mode_set(mode='OBJECT')
img = bpy.data.images.new('body_normal', size, size, alpha=False); img.colorspace_settings.name = 'Non-Color'
for m in lo.data.materials:
    m = m.copy() if m.users > 1 else m
for i, m in enumerate(list(lo.data.materials)):
    m = m.copy(); lo.data.materials[i] = m; m.use_nodes = True; nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(t.outputs['Color'], nm.inputs['Color'])
    t.select = True; nt.nodes.active = t; m['_nm'] = nm.name; m['_b'] = b.name
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 1
hi.select_set(True); lo.select_set(True); bpy.context.view_layer.objects.active = lo
bpy.ops.object.bake(type='NORMAL', use_selected_to_active=True, cage_extrusion=0.03, max_ray_distance=0.06, normal_space='TANGENT', margin=6)
for m in lo.data.materials:
    nt = m.node_tree; nt.links.new(nt.nodes[m['_nm']].outputs['Normal'], nt.nodes[m['_b']].inputs['Normal'])
img.filepath_raw = os.path.abspath(out).replace('.blend', '_body_normal.png'); img.file_format = 'PNG'; img.save(); img.pack()
bpy.data.objects.remove(hi); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
print('baked %dpx normal map onto the layer body (%d faces)' % (size, len(lo.data.polygons)))
