"""The cabin as one game mesh: export_glb.py <cabin.blend> <out.glb>
Every cabin object is joined into one mesh with ONE material, so the whole interior is one draw. The materials
(imats: plain colours, no image textures) become a palette: one texel each in a small base-colour image and in a
metallic-roughness image, and every face's UVs sit on its material's texel. The shading normals the build kept
(relief_n and the lofts' smooth normals) go out as the mesh's normals.
What a palette cannot carry: the clear coat of the glossy black, the wood and the display (imats' coat); they go
out as lower roughness instead."""
import bpy, sys, os, numpy as np
blend, out = sys.argv[-2:]; bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
obs = [o for o in bpy.data.objects if o.type == 'MESH']
mats = sorted({s.material.name for o in obs for s in o.material_slots if s.material}); n = len(mats); W = 8; H = int(np.ceil(n / W))
base = np.zeros((H, W, 4), np.float32); mr = np.zeros((H, W, 4), np.float32); base[..., 3] = 1; mr[..., 3] = 1
for i, nm in enumerate(mats):
    b = bpy.data.materials[nm].node_tree.nodes['Principled BSDF']; c = b.inputs['Base Color'].default_value; coat = b.inputs['Coat Weight'].default_value
    rough = b.inputs['Roughness'].default_value * (1 - 0.6 * coat); base[i // W, i % W, :3] = c[:3]; mr[i // W, i % W, :3] = (1.0, rough, b.inputs['Metallic'].default_value)      # glTF: G roughness, B metallic
def image(name, a, colorspace):
    im = bpy.data.images.new(name, W, H, alpha=False); im.colorspace_settings.name = colorspace
    px = a.copy()
    if colorspace == 'sRGB': px[..., :3] = np.where(px[..., :3] <= 0.0031308, px[..., :3] * 12.92, 1.055 * np.power(px[..., :3], 1 / 2.4) - 0.055)      # the image holds display values
    im.pixels.foreach_set(px.ravel()); im.pack(); return im
ib, im_ = image('cabin_palette', base, 'sRGB'), image('cabin_palette_mr', mr, 'Non-Color')
# every face's UVs on its material's texel, before joining (the join keeps the layer)
tris = 0
for o in obs:
    me = o.data; uv = me.uv_layers.new(name='palette') if 'palette' not in me.uv_layers else me.uv_layers['palette']; slot = [mats.index(s.material.name) if s.material else 0 for s in o.material_slots] or [0]
    for p in me.polygons:
        k = slot[min(p.material_index, len(slot) - 1)]; u, v = (k % W + 0.5) / W, (k // W + 0.5) / H
        for li in p.loop_indices: uv.data[li].uv = (u, v)
    me.calc_loop_triangles(); tris += len(me.loop_triangles)
bpy.ops.object.select_all(action='DESELECT')
for o in obs: o.select_set(True)
bpy.context.view_layer.objects.active = obs[0]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); bpy.ops.object.join(); ob = bpy.context.view_layer.objects.active; ob.name = 'cabin'
one = bpy.data.materials.new('cabin'); one.use_backface_culling = True; one.use_nodes = True; nt = one.node_tree; b = nt.nodes['Principled BSDF']
t1 = nt.nodes.new('ShaderNodeTexImage'); t1.image = ib; t1.interpolation = 'Closest'; nt.links.new(t1.outputs['Color'], b.inputs['Base Color'])
t2 = nt.nodes.new('ShaderNodeTexImage'); t2.image = im_; t2.interpolation = 'Closest'; sep = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(t2.outputs['Color'], sep.inputs['Color'])
nt.links.new(sep.outputs['Green'], b.inputs['Roughness']); nt.links.new(sep.outputs['Blue'], b.inputs['Metallic'])
ob.data.materials.clear(); ob.data.materials.append(one)
for p in ob.data.polygons: p.material_index = 0
bpy.ops.export_scene.gltf(filepath=os.path.abspath(out), export_format='GLB', use_selection=True, export_apply=True, export_normals=True, export_texcoords=True, export_materials='EXPORT', export_yup=True)
print('cabin.glb: %d objects joined, %d materials on a %dx%d palette, %d triangles, %.2f MB' % (len(obs), n, W, H, tris, os.path.getsize(out) / 1e6))
