"""Blender helpers for the character: mesh from arrays, the rig, skinning, posing by direction, and a simple render stage."""
import bpy, numpy as np
from mathutils import Vector, Matrix

def mesh(name, P, F, mat=None, smooth=True, uv=None):
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(p) for p in P], [], F); me.update()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    if uv is not None:
        lay = me.uv_layers.new(name='UV')
        for poly in me.polygons:
            for li, vi in zip(poly.loop_indices, poly.vertices): lay.data[li].uv = uv[vi] if not callable(uv) else uv(vi, li)
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    if mat: me.materials.append(mat)
    return ob

def material(name, color, rough=0.6, sheen=0.0, spec=0.4):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bs = m.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (*color, 1); bs.inputs['Roughness'].default_value = rough
    try: bs.inputs['Sheen Weight'].default_value = sheen
    except KeyError: pass
    try: bs.inputs['Specular IOR Level'].default_value = spec
    except KeyError: pass
    return m

def armature(B):
    ad = bpy.data.armatures.new('rig'); ob = bpy.data.objects.new('rig', ad); bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.mode_set(mode='EDIT')
    for n, b in B.items():
        eb = ad.edit_bones.new(n); eb.head = Vector(b['head']); eb.tail = Vector(b['tail'])
        # roll: keep each bone's x axis as close to world x as possible, so bends read the same on both sides
        eb.align_roll(Vector((0, -1, 0)) if abs(Vector(b['tail'] - b['head']).normalized().y) < 0.8 else Vector((0, 0, 1)))
    for n, b in B.items():
        if b['parent']: ad.edit_bones[n].parent = ad.edit_bones[b['parent']]
    bpy.ops.object.mode_set(mode='OBJECT')
    return ob

def skin(ob, rig, W):
    """W: per vertex of ob, {bone: weight}. At most 4 bones per vertex (what glTF and the game engines carry), renormalised,
    so what Blender shows is what the game shows."""
    W = [dict(sorted(d.items(), key=lambda kv: -kv[1])[:4]) for d in W]
    W = [{k: v / s for k, v in d.items()} if (s := sum(d.values())) > 0 else d for d in W]
    for i, d in enumerate(W):
        for b, w in d.items():
            if w <= 1e-4: continue
            g = ob.vertex_groups.get(b) or ob.vertex_groups.new(name=b)
            g.add([i], w, 'REPLACE')
    m = ob.modifiers.new('rig', 'ARMATURE'); m.object = rig
    ob.parent = rig

def point(rig, name, direction):
    """Turn a pose bone (in armature space) so it points along `direction`, with the least twist."""
    bpy.context.view_layer.update()
    pb = rig.pose.bones[name]
    cur = pb.matrix.copy()
    d0 = (cur.to_3x3() @ Vector((0, 1, 0))).normalized()
    q = d0.rotation_difference(Vector(direction).normalized())
    pb.matrix = Matrix.Translation(cur.to_translation()) @ q.to_matrix().to_4x4() @ Matrix.Translation(-cur.to_translation()) @ cur
    bpy.context.view_layer.update()

def stage(res=(900, 1000), samples=24, bg=(0.75, 0.72, 0.68)):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = samples; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
    sc.render.resolution_x, sc.render.resolution_y = res
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (*bg, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sun.data.energy = 3.2; sun.rotation_euler = (0.85, 0.15, -0.7); sc.collection.objects.link(sun)
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    return sc, cam

def shoot(sc, cam, path, loc, rot, ortho=None, lens=None):
    if ortho: cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    else: cam.data.type = 'PERSP'; cam.data.lens = lens or 50
    cam.location = loc; cam.rotation_euler = rot
    sc.render.filepath = path; bpy.ops.render.render(write_still=True)
