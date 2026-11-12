"""A parked vehicle's shadow caster: its game model (models/veh_<name>.json) joined into one mesh and decimated to about
RATIO of its triangles, positions only, written beside it as veh_<name>_shadow.json. farm.html bakes it into the fixed
shadow meshes in place of the full model, which still draws as before.

Why the shadow can be this coarse: the shadow map is 1536 texels over 144 m (9.4 cm a texel, filtered by PCF), and the
decimated outline stays within a few centimetres of the full one (printed). The two shas, the tractor and the caravan
were 48k of the 81k triangles redrawn in every shadow pass at full detail.

    python shadow_proxy.py <models dir> shas tractor caravan       (bpy as a module, Blender 4.2)
"""
import base64, json, os, sys, tempfile
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

RATIO = 0.12


def load(path):
    b = base64.b64decode(json.load(open(path))['glb'])
    t = tempfile.NamedTemporaryFile(suffix='.glb', delete=False); t.write(b); t.close()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=t.name); os.unlink(t.name)


def proxy(models, name):
    load(os.path.join(models, 'veh_%s.json' % name))
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    full = sum(len(o.data.polygons) for o in meshes)
    for o in meshes:
        bpy.context.view_layer.objects.active = o
        for x in bpy.context.view_layer.objects: x.select_set(o is x)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)      # (into the file's own frame, the root the page places)
    for o in meshes: o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.parent = None
    for x in list(bpy.data.objects):
        if x is not o: bpy.data.objects.remove(x)
    o.data.materials.clear()
    for uv in list(o.data.uv_layers): o.data.uv_layers.remove(uv)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.remove_doubles(threshold=0.002); bpy.ops.object.mode_set(mode='OBJECT')
    src = BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get())
    srcv = [v.co.copy() for v in o.data.vertices]
    m = o.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = RATIO; m.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier='dec')
    o.data.calc_loop_triangles(); tris = len(o.data.loop_triangles)
    # how far the coarse surface strays from the full one: the full model's vertices to the coarse surface, and back
    dec = BVHTree.FromObject(o, bpy.context.evaluated_depsgraph_get())
    d1 = sorted(dec.find_nearest(v)[3] for v in srcv)
    d2 = sorted(src.find_nearest(v.co)[3] for v in o.data.vertices)
    print('%s: %d faces -> %d triangles; the full surface to the coarse: median %.1f cm, 99%% %.1f cm; coarse to full: 99%% %.1f cm'
          % (name, full, tris, 100 * d1[len(d1) // 2], 100 * d1[int(len(d1) * 0.99)], 100 * d2[int(len(d2) * 0.99)]))
    out = os.path.join(models, 'veh_%s_shadow.json' % name)
    t = tempfile.NamedTemporaryFile(suffix='.glb', delete=False); t.close()
    bpy.ops.export_scene.gltf(filepath=t.name, export_format='GLB', use_selection=False, export_normals=False, export_texcoords=False,
                              export_materials='NONE', export_attributes=False, export_apply=True)
    b = open(t.name, 'rb').read(); os.unlink(t.name)
    open(out, 'w').write(json.dumps({'glb': base64.b64encode(b).decode()}))
    print('wrote %s (%d bytes)' % (out, len(b)))


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    for n in a[1:]: proxy(a[0], n)
