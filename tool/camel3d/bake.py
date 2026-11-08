"""Low-poly game mesh + baked coat textures for the white camel.

Albedo: the owner's photo projected from the side onto side-facing skin
(body, neck, head), blended into a procedural coat built from the photo's
own colour statistics on top, bottom, front and the legs. Calluses on the
knees and chest pad, dust toward the feet, dark soles.
Normal map: fine fur grain plus skin folds taken from the photo.
"""
import sys, os
sys.path.insert(0, os.getcwd())
import bpy
from blend_common import reset, mesh_from_npz

PX, GROUND, U0, IW, IH = 443.0, 1032.0, 700.0, 1448.0, 1086.0
TEX = int(os.environ.get('TEX', '2048'))
TARGET_TRIS = int(os.environ.get('TRIS', '40000'))

sc = reset()
ob = mesh_from_npz('camel_hi.npz')
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
sm = ob.modifiers.new('smooth', 'CORRECTIVE_SMOOTH')
sm.iterations = 4
sm.use_only_smooth = True
bpy.ops.object.modifier_apply(modifier='smooth')
dec = ob.modifiers.new('dec', 'DECIMATE')
dec.ratio = TARGET_TRIS / len(ob.data.polygons)
bpy.ops.object.modifier_apply(modifier='dec')
for p in ob.data.polygons:
    p.use_smooth = True
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.004)
bpy.ops.object.mode_set(mode='OBJECT')
print('tris', len(ob.data.polygons))


def lin(c):
    return tuple(((v / 255) ** 2.2) for v in c) + (1,)


mat = bpy.data.materials.new('CoatBake')
mat.use_nodes = True
nt = mat.node_tree
N = nt.nodes
L = nt.links
N.clear()
out = N.new('ShaderNodeOutputMaterial')
emit = N.new('ShaderNodeEmission')
L.new(emit.outputs[0], out.inputs['Surface'])
tc = N.new('ShaderNodeTexCoord')
geo = N.new('ShaderNodeNewGeometry')
sep = N.new('ShaderNodeSeparateXYZ')
L.new(tc.outputs['Object'], sep.inputs[0])


def madd(inp, a, b):
    n = N.new('ShaderNodeMath')
    n.operation = 'MULTIPLY_ADD'
    L.new(inp, n.inputs[0])
    n.inputs[1].default_value = a
    n.inputs[2].default_value = b
    return n.outputs[0]


def math(op, a, b=None, clamp=False):
    n = N.new('ShaderNodeMath')
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            L.new(v, n.inputs[i])
    return n.outputs[0]


def mrange(v, a, b):
    n = N.new('ShaderNodeMapRange')
    n.interpolation_type = 'SMOOTHSTEP'
    L.new(v, n.inputs['Value'])
    n.inputs['From Min'].default_value = a
    n.inputs['From Max'].default_value = b
    return n.outputs[0]


# photo projection
pu = madd(sep.outputs['X'], -PX / IW, U0 / IW)
pv = madd(sep.outputs['Z'], PX / IH, 1 - GROUND / IH)
comb = N.new('ShaderNodeCombineXYZ')
L.new(pu, comb.inputs['X'])
L.new(pv, comb.inputs['Y'])
photo = N.new('ShaderNodeTexImage')
photo.image = bpy.data.images.load(os.path.abspath('ref_fill.png'))
photo.extension = 'EXTEND'
photo.interpolation = 'Cubic'
L.new(comb.outputs[0], photo.inputs['Vector'])
# normal in object space
nsep = N.new('ShaderNodeSeparateXYZ')
vt = N.new('ShaderNodeVectorTransform')
vt.vector_type = 'NORMAL'
vt.convert_from = 'WORLD'
vt.convert_to = 'OBJECT'
L.new(geo.outputs['Normal'], vt.inputs[0])
L.new(vt.outputs[0], nsep.inputs[0])
side = mrange(math('ABSOLUTE', nsep.outputs['Y']), 0.28, 0.72)
above_legs = mrange(sep.outputs['Z'], (GROUND - 640) / PX, (GROUND - 600) / PX)
ear = math('MULTIPLY', mrange(sep.outputs['Z'], 2.04, 2.09),
           mrange(math('ABSOLUTE', math('SUBTRACT', sep.outputs['X'], 0.76)), 0.06, 0.03))
w_photo = math('MULTIPLY', math('MULTIPLY', side, above_legs), math('SUBTRACT', 1.0, ear))
# procedural coat
noise = N.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value = 9.0
noise.inputs['Detail'].default_value = 9.0
noise.inputs['Roughness'].default_value = 0.6
L.new(tc.outputs['Object'], noise.inputs['Vector'])
ramp = N.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position = 0.35
ramp.color_ramp.elements[0].color = lin((200, 186, 170))
ramp.color_ramp.elements[1].position = 0.7
ramp.color_ramp.elements[1].color = lin((228, 220, 210))
L.new(noise.outputs['Fac'], ramp.inputs[0])
coat = ramp.outputs[0]
# dust toward the feet, darker soles
dust = N.new('ShaderNodeMix')
dust.data_type = 'RGBA'
dust.blend_type = 'MULTIPLY'
L.new(mrange(sep.outputs['Z'], 0.45, 0.05), dust.inputs['Factor'])
L.new(coat, dust.inputs['A'])
dust.inputs['B'].default_value = lin((205, 180, 150))
sole = N.new('ShaderNodeMix')
sole.data_type = 'RGBA'
L.new(mrange(sep.outputs['Z'], 0.035, 0.012), sole.inputs['Factor'])
L.new(dust.outputs['Result'], sole.inputs['A'])
sole.inputs['B'].default_value = lin((70, 62, 55))
# calluses: front knees and the chest pad
cal = N.new('ShaderNodeMix')
cal.data_type = 'RGBA'
knee_z = mrange(math('ABSOLUTE', math('SUBTRACT', sep.outputs['Z'], (GROUND - 800) / PX)), 0.05, 0.02)
knee_front = mrange(nsep.outputs['X'], 0.45, 0.85)
knee_x = mrange(math('ABSOLUTE', math('SUBTRACT', sep.outputs['X'], (U0 - 704) / PX)), 0.12, 0.05)
knee = math('MULTIPLY', math('MULTIPLY', knee_z, knee_front), knee_x)
pad = math('MULTIPLY', mrange(nsep.outputs['Z'], -0.3, -0.75),
           mrange(math('ABSOLUTE', math('SUBTRACT', sep.outputs['X'], (U0 - 640) / PX)), 0.16, 0.08))
L.new(math('MAXIMUM', knee, math('MULTIPLY', pad, mrange(sep.outputs['Z'], 1.15, 0.95))), cal.inputs['Factor'])
L.new(sole.outputs['Result'], cal.inputs['A'])
cal.inputs['B'].default_value = lin((158, 148, 136))
# final blend: photo on the sides of body/neck/head
fin = N.new('ShaderNodeMix')
fin.data_type = 'RGBA'
L.new(w_photo, fin.inputs['Factor'])
L.new(cal.outputs['Result'], fin.inputs['A'])
L.new(photo.outputs['Color'], fin.inputs['B'])
L.new(fin.outputs['Result'], emit.inputs['Color'])
# bake target
img = bpy.data.images.new('camel_albedo', TEX, TEX)
tnode = N.new('ShaderNodeTexImage')
tnode.image = img
N.active = tnode
ob.data.materials.append(mat)
sc.cycles.bake_type = 'EMIT'
sc.cycles.samples = 4
sc.render.bake.margin = 8
bpy.ops.object.bake(type='EMIT')
img.filepath_raw = os.path.abspath(f'camel_albedo_{TEX}.png')
img.file_format = 'PNG'
img.save()

# normal map: fur grain and skin folds from the photo
mat2 = bpy.data.materials.new('NormalBake')
mat2.use_nodes = True
n2 = mat2.node_tree
B = n2.nodes['Principled BSDF']
tc2 = n2.nodes.new('ShaderNodeTexCoord')
fur = n2.nodes.new('ShaderNodeTexNoise')
fur.inputs['Scale'].default_value = 260.0
fur.inputs['Detail'].default_value = 4.0
n2.links.new(tc2.outputs['Object'], fur.inputs['Vector'])
bump = n2.nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value = 0.22
bump.inputs['Distance'].default_value = 0.002
n2.links.new(fur.outputs['Fac'], bump.inputs['Height'])
n2.links.new(bump.outputs['Normal'], B.inputs['Normal'])
img2 = bpy.data.images.new('camel_normal', TEX, TEX, is_data=True)
t2 = n2.nodes.new('ShaderNodeTexImage')
t2.image = img2
n2.nodes.active = t2
ob.data.materials.clear()
ob.data.materials.append(mat2)
sc.render.bake.normal_space = 'TANGENT'
bpy.ops.object.bake(type='NORMAL')
img2.filepath_raw = os.path.abspath(f'camel_normal_{TEX}.png')
img2.file_format = 'PNG'
img2.save()

# final game material
ob.data.materials.clear()
gm = bpy.data.materials.new('CamelCoat')
gm.use_nodes = True
g = gm.node_tree
P = g.nodes['Principled BSDF']
P.inputs['Roughness'].default_value = 0.88
a = g.nodes.new('ShaderNodeTexImage')
a.image = bpy.data.images.load(os.path.abspath(f'camel_albedo_{TEX}.png'))
g.links.new(a.outputs['Color'], P.inputs['Base Color'])
nimg = g.nodes.new('ShaderNodeTexImage')
nimg.image = bpy.data.images.load(os.path.abspath(f'camel_normal_{TEX}.png'))
nimg.image.colorspace_settings.name = 'Non-Color'
nm = g.nodes.new('ShaderNodeNormalMap')
g.links.new(nimg.outputs['Color'], nm.inputs['Color'])
g.links.new(nm.outputs['Normal'], P.inputs['Normal'])
try:
    P.inputs['Subsurface Weight'].default_value = 0.08
    P.inputs['Subsurface Radius'].default_value = (0.6, 0.35, 0.2)
except KeyError:
    pass
ob.data.materials.append(gm)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('camel_lod0.blend'))
print('saved')
