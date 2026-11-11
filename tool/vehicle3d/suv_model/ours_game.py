"""Our code-built car (suv.blend) as the game's car: a layer from lod_ext.py, rigged and exported for design/prototype3d.
ours_game.py near <near.blend> <out.glb>      the near layer: parts merged by material (one draw each), the wheels on
                                              their corners (corner_XX steers and rides its spring, wheel_XX spins in
                                              it), the seated driver's eye ('eye', 'eye_look' 6 m ahead of it)
ours_game.py far <far.blend> <out.glb>        the far layer: everything merged by material, wheels and all
ours_game.py cabin <cabin.glb> <out.glb>      the cabin layer (interior/lod_cabin.py's cabin_lod0.glb) under an empty
                                              'interior', as play.js loads it while the player is at the car
play.js reads these names (part(), getObjectByName). The player's car casts no shadow (the owner's word, 11 Nov).
The owner's choice (11 Nov): this car, ours and built by code from his photos, replaces the downloaded model.
"""
import bpy, sys, os
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'interior'))
CORNERS = ('FL', 'FR', 'RL', 'RR')


def clean_scene_of(kinds=('CAMERA', 'LIGHT')):
    for o in list(bpy.data.objects):
        if o.type in kinds: bpy.data.objects.remove(o)


def join(objs, name):
    """objs joined into one mesh object called name (transforms applied)."""
    objs = [o for o in objs if o.type == 'MESH' and len(o.data.polygons)]
    if not objs: return None
    for o in bpy.context.view_layer.objects: o.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(objs) > 1: bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active; o.name = o.data.name = name
    return o


def by_material(o):
    """o split into one object per material, each named after its material (one draw each in the game)."""
    for x in bpy.context.view_layer.objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
    parts = [x for x in bpy.context.selected_objects]
    for x in parts:
        m = x.data.materials[x.data.polygons[0].material_index] if len(x.data.polygons) else None
        x.name = x.data.name = (m.name if m else 'body')
        # one material slot left (the one used)
        if m:
            x.data.materials.clear(); x.data.materials.append(m)
    return parts


def export(path):
    # the glass is opaque black (the owner's rule: the glass fully dark) and one-sided, so the driver sees out through
    # it (its back faces are not drawn) while from outside it hides the cabin
    for m in bpy.data.materials:
        if m.name == 'glass': m.use_backface_culling = True
    bpy.ops.export_scene.gltf(filepath=os.path.abspath(path), export_format='GLB', use_selection=False, export_apply=True,
                              export_yup=True, export_texcoords=True, export_normals=True, export_materials='EXPORT',
                              export_cameras=False, export_lights=False, export_extras=False, export_animations=False)
    print('wrote %s (%d bytes)' % (path, os.path.getsize(path)))


def tri_count():
    n = 0
    for o in bpy.data.objects:
        if o.type == 'MESH': o.data.calc_loop_triangles(); n += len(o.data.loop_triangles)
    return n


def near(src, out):
    import cabin as C                               # the seated eye: interior/cabin.py's SEATED_EYE (SAE J941's eyellipse centre, roughly: a choice made there)
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src)); clean_scene_of()
    wheels = {k: bpy.data.objects.get('wheel_' + k) for k in CORNERS}
    missing = [k for k, w in wheels.items() if w is None]
    if missing: sys.exit('no wheel_%s in %s' % (missing, src))
    rest = [o for o in bpy.data.objects if o.type == 'MESH' and o not in wheels.values()]
    body = join(rest, 'body')
    for p in by_material(body): pass
    for k, w in wheels.items():
        # the wheel's mesh about its own middle (its hub), under an empty corner_XX at the same place
        bpy.context.view_layer.objects.active = w
        for x in bpy.context.view_layer.objects: x.select_set(False)
        w.select_set(True); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        lo = Vector((min(v.co.x for v in w.data.vertices), min(v.co.y for v in w.data.vertices), min(v.co.z for v in w.data.vertices)))
        hi = Vector((max(v.co.x for v in w.data.vertices), max(v.co.y for v in w.data.vertices), max(v.co.z for v in w.data.vertices)))
        c = (lo + hi) / 2
        w.data.transform(Matrix.Translation(-c)); w.location = (0, 0, 0)
        e = bpy.data.objects.new('corner_' + k, None); e.location = c; bpy.context.collection.objects.link(e)
        w.parent = e; w.name = 'wheel_' + k
        print('corner_%s at (%.3f, %.3f, %.3f), wheel %.3f m across' % (k, c.x, c.y, c.z, hi.z - lo.z))
    eye = Vector(C.SEATED_EYE)
    for name, at in (('eye', eye), ('eye_look', eye + Vector((6.0, 0.0, -0.35)))):
        e = bpy.data.objects.new(name, None); e.location = at; bpy.context.collection.objects.link(e)
    print('eye at (%.3f, %.3f, %.3f); %d triangles' % (*eye, tri_count()))
    export(out)


def far(src, out):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src)); clean_scene_of()
    body = join([o for o in bpy.data.objects if o.type == 'MESH'], 'body')
    by_material(body)
    print('far: %d triangles' % tri_count())
    export(out)


def cabin(src, out):
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(src))
    root = bpy.data.objects.new('interior', None); bpy.context.collection.objects.link(root)
    for o in list(bpy.data.objects):
        if o is not root and o.parent is None: o.parent = root
    print('cabin: %d triangles' % tri_count())
    export(out)


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    {'near': near, 'far': far, 'cabin': cabin}[a[0]](a[1], a[2])
