"""Game mesh, baked photo texture, GLB export and check renders for one vehicle."""
import sys, os, json, math
sys.path.insert(0, os.path.abspath('../camel'))
import bpy
from blend_common import reset, mesh_from_npz, desert_world, ground, camera, render

name = os.environ['VEH']
d = os.path.abspath(name)
cfg = json.load(open(os.path.join(d, 'views.json')))
mat_cfg = json.load(open(os.path.join(d, 'mat.json')))
TEX = int(os.environ.get('TEX', '2048'))

sc = reset()
ob = mesh_from_npz(os.path.join(d, 'hull.npz'), name)
import numpy as np
wn = np.load(os.path.join(d, 'hull.npz'))['wn']
attr = ob.data.color_attributes.new('wn', 'FLOAT_COLOR', 'POINT')
attr.data.foreach_set('color', np.concatenate([wn, np.ones((len(wn), 1), np.float32)], 1).ravel())
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
dec = ob.modifiers.new('dec', 'DECIMATE')
dec.ratio = mat_cfg['tris'] / len(ob.data.polygons)
bpy.ops.object.modifier_apply(modifier='dec')
try:
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(42))
except Exception:
    for p in ob.data.polygons:
        p.use_smooth = True
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.003)
bpy.ops.object.mode_set(mode='OBJECT')

m = bpy.data.materials.new('Proj')
m.use_nodes = True
nt = m.node_tree
N, Lk = nt.nodes, nt.links
N.clear()
outn = N.new('ShaderNodeOutputMaterial')
emit = N.new('ShaderNodeEmission')
Lk.new(emit.outputs[0], outn.inputs['Surface'])
tc = N.new('ShaderNodeTexCoord')
sep = N.new('ShaderNodeSeparateXYZ')
Lk.new(tc.outputs['Object'], sep.inputs[0])
geo = N.new('ShaderNodeNewGeometry')
att = N.new('ShaderNodeAttribute')
att.attribute_name = 'wn'
unpack = N.new('ShaderNodeVectorMath')
unpack.operation = 'MULTIPLY_ADD'
Lk.new(att.outputs['Vector'], unpack.inputs[0])
unpack.inputs[1].default_value = (2, 2, 2)
unpack.inputs[2].default_value = (-1, -1, -1)
nsep = N.new('ShaderNodeSeparateXYZ')
Lk.new(unpack.outputs[0], nsep.inputs[0])


def math_node(op, a, b=None):
    n = N.new('ShaderNodeMath')
    n.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            Lk.new(v, n.inputs[i])
    return n.outputs[0]


def lin(inp, a, b):  # a * inp + b
    return math_node('ADD', math_node('MULTIPLY', inp, a), b)


def proj(view, u, v):
    c = N.new('ShaderNodeCombineXYZ')
    Lk.new(u, c.inputs['X'])
    Lk.new(v, c.inputs['Y'])
    t = N.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(os.path.join(d, f'{view}_fill.png'))
    t.extension = 'EXTEND'
    t.interpolation = 'Cubic'
    Lk.new(c.outputs[0], t.inputs['Vector'])
    return t.outputs['Color']


L = cfg['L']
X, Y, Z = sep.outputs['X'], sep.outputs['Y'], sep.outputs['Z']
s = cfg['side']
side_c = proj('01_left', lin(X, -1 / s['s'] / s['W'], (s['u0'] + L / 2 / s['s']) / s['W']), lin(Z, 1 / s['s'] / s['H'], 1 - s['v0'] / s['H']))
f = cfg['front']
front_c = proj('02_front', lin(Y, 1 / (f['s'] * f['k']) / f['W'], f['uc'] / f['W']), lin(Z, 1 / f['s'] / f['H'], 1 - f['v0'] / f['H']))
r = cfg['rear']
rear_c = proj('03_rear', lin(Y, -1 / (r['s'] * r['k']) / r['W'], r['uc'] / r['W']), lin(Z, 1 / r['s'] / r['H'], 1 - r['v0'] / r['H']))
t = cfg['top']
top_c = proj('04_top', lin(Y, -1 / (t['s'] * t['k']) / t['W'], t['uc'] / t['W']), lin(X, 1 / t['s'] / t['H'], 1 - (t['v0'] + L / 2 / t['s']) / t['H']))


def powpos(v, sign):
    return math_node('POWER', math_node('MAXIMUM', math_node('MULTIPLY', v, sign), 0.0), 6.0)


w_side = math_node('POWER', math_node('ABSOLUTE', nsep.outputs['Y']), 6.0)
w_front, w_rear = powpos(nsep.outputs['X'], 1.0), powpos(nsep.outputs['X'], -1.0)
w_top, w_bot = powpos(nsep.outputs['Z'], 1.0), powpos(nsep.outputs['Z'], -1.0)
total = math_node('ADD', math_node('ADD', math_node('ADD', w_side, w_front), math_node('ADD', w_rear, w_top)), math_node('ADD', w_bot, 1e-4))


def scaled(col, w):
    n = N.new('ShaderNodeVectorMath')
    n.operation = 'SCALE'
    Lk.new(col, n.inputs[0])
    Lk.new(math_node('DIVIDE', w, total), n.inputs['Scale'])
    return n.outputs[0]


def vadd(a, b):
    n = N.new('ShaderNodeVectorMath')
    n.operation = 'ADD'
    Lk.new(a, n.inputs[0])
    Lk.new(b, n.inputs[1])
    return n.outputs[0]


under = N.new('ShaderNodeRGB')
under.outputs[0].default_value = (0.03, 0.03, 0.03, 1)
col = vadd(vadd(vadd(scaled(side_c, w_side), scaled(front_c, w_front)), vadd(scaled(rear_c, w_rear), scaled(top_c, w_top))), scaled(under.outputs[0], w_bot))
Lk.new(col, emit.inputs['Color'])
img = bpy.data.images.new(f'{name}_albedo', TEX, TEX)
tn = N.new('ShaderNodeTexImage')
tn.image = img
N.active = tn
ob.data.materials.append(m)
sc.cycles.bake_type = 'EMIT'
sc.cycles.samples = 4
sc.render.bake.margin = 8
bpy.ops.object.bake(type='EMIT')
img.filepath_raw = os.path.join(d, 'albedo.png')
img.file_format = 'PNG'
img.save()

ob.data.materials.clear()
gm = bpy.data.materials.new(f'{name}_paint')
gm.use_nodes = True
P = gm.node_tree.nodes['Principled BSDF']
P.inputs['Roughness'].default_value = mat_cfg['rough']
for key in ('Coat Weight', 'Clearcoat'):
    if key in P.inputs:
        P.inputs[key].default_value = mat_cfg['coat']
        break
a = gm.node_tree.nodes.new('ShaderNodeTexImage')
a.image = bpy.data.images.load(os.path.join(d, 'albedo.png'))
gm.node_tree.links.new(a.outputs['Color'], P.inputs['Base Color'])
ob.data.materials.append(gm)
for o in bpy.data.objects:
    o.select_set(o == ob)
bpy.ops.export_scene.gltf(filepath=os.path.join(d, f'{name}.glb'), export_format='GLB', use_selection=True,
                          export_image_format='JPEG', export_jpeg_quality=88)
print('exported', name, len(ob.data.polygons), os.path.getsize(os.path.join(d, f'{name}.glb')) // 1024, 'KB')

# check renders in the desert light
desert_world(sun_elev=32, sun_rot=215)
ground(os.path.abspath('../assets_all/01_terrain/najd.png'), size=120, tile_m=22)
Lm = cfg['L']
k = max(Lm, 4.5)
for nm, loc in (('front34', (k * 0.95, -k * 0.85, k * 0.42)), ('rear34', (-k * 0.95, k * 0.8, k * 0.5))):
    render(camera(nm, loc, (0, 0, cfg['Hm'] * 0.42), 42), os.path.join(d, f'check_{nm}.png'), res=(640, 420), samples=24)
