"""Our code-built car (suv.blend) as the game's car: a layer from lod_ext.py, rigged and exported for design/prototype3d.
ours_game.py near <near.blend> <out.glb> [cabin.glb]
                                              the near layer: parts merged by material (one draw each), the wheels on
                                              their corners (corner_XX steers and rides its spring, wheel_XX spins in
                                              it), the seated driver's eye ('eye', 'eye_look' 6 m ahead of it); with the
                                              cabin, what the driver cannot see from the seat goes under 'outside'
                                              (seat_split), which the game hides in the seat view
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


# the driver's door (front left): its shut lines on the body (seam0_L at x 0.94, seam1_L at -0.14, seam3_L at z 0.43),
# the belt at about z 1.22, and above it the window frame from the A pillar's foot (0.94, 1.22) to its head under the
# roof (0.11, 1.765), where the window's top chrome ends; its hinge on the front shut line, a little in from the skin
DOOR_X = (-0.14, 0.94)
DOOR_Z = (0.43, 1.22, 1.775)
DOOR_A = ((0.94, 1.22), (0.11, 1.765))
HINGE = (0.94, 0.92, 0.85)
MIRROR = ((0.50, 0.82), (0.76, 1.10), (1.24, 1.50))      # the door-mounted mirror's box: it goes with the door whole


def door_split(body):
    """The driver's door cut from the joined body along its shut lines (bisected there, so the cut follows them), as
    its own parts under an empty 'door_FL' at the hinge: play.js swings it about the vertical (60 degrees, a game
    choice) as the player gets in and out. It keeps its window, chrome, handle and mirror. Returns the door's parts."""
    import bmesh
    from mathutils import Vector
    (ax, az), (bx, bz) = DOOR_A
    na = Vector((bz - az, 0, ax - bx)).normalized()              # the A pillar line's normal in the side plane, pointing forward and up
    xa = lambda z: ax + (z - az) * (bx - ax) / (bz - az)
    bm = bmesh.new(); bm.from_mesh(body.data)
    left = lambda: [e for e in bm.verts[:] + bm.edges[:] + bm.faces[:] if (e.co.y if hasattr(e, 'co') else sum((v.co.y for v in e.verts), 0) / len(e.verts)) > 0.3]
    for co, no in (((DOOR_X[0], 0, 0), (1, 0, 0)), ((DOOR_X[1], 0, 0), (1, 0, 0)), ((0, 0, DOOR_Z[0]), (0, 0, 1)), ((0, 0, DOOR_Z[1]), (0, 0, 1)), ((0, 0, DOOR_Z[2]), (0, 0, 1)), ((ax, 0, az), tuple(na))):
        bmesh.ops.bisect_plane(bm, geom=left(), plane_co=co, plane_no=no)
    bm.faces.ensure_lookup_table()
    def on_door(f):
        c = f.calc_center_median()
        if MIRROR[0][0] < c.x < MIRROR[0][1] and MIRROR[1][0] < c.y < MIRROR[1][1] and MIRROR[2][0] < c.z < MIRROR[2][1]: return True
        if not DOOR_X[0] < c.x < DOOR_X[1]: return False
        if DOOR_Z[0] < c.z < DOOR_Z[1]: return c.y > 0.55
        return DOOR_Z[1] <= c.z < DOOR_Z[2] and c.y > 0.6 and c.x < xa(c.z)
    door_faces = {f.index for f in bm.faces if on_door(f)}
    bm.to_mesh(body.data); bm.free()
    door = body.copy(); door.data = body.data.copy(); bpy.context.collection.objects.link(door); door.name = door.data.name = 'door_body'
    for o, keep_door in ((body, False), (door, True)):
        b2 = bmesh.new(); b2.from_mesh(o.data); b2.faces.ensure_lookup_table()
        bmesh.ops.delete(b2, geom=[f for f in b2.faces if (f.index in door_faces) != keep_door], context='FACES'); b2.to_mesh(o.data); b2.free()
    parts = by_material(door)
    hinge = bpy.data.objects.new('door_FL', None); hinge.location = HINGE; bpy.context.collection.objects.link(hinge)
    bpy.context.view_layer.update()
    for p in parts:
        p.name = p.data.name = 'door_' + p.name
        p.parent = hinge; p.matrix_parent_inverse = hinge.matrix_world.inverted()
    n = sum((x.data.calc_loop_triangles(), len(x.data.loop_triangles))[1] for x in parts)
    print('door_FL: %d parts, %d triangles, hinge at (%.2f, %.2f, %.2f)' % (len(parts), n, *HINGE))
    return parts


OUT_MIN = 3000            # triangles: a material's unseen part goes apart (one draw more from outside) only past this


def seat_split(parts, wheels, cabin_glb):
    """What the driver cannot see from the seat goes under an empty 'outside', which the game hides in the seat view
    (the seat view was over the 400k triangle budget, ADR 0005). A face is seen if one of its points is in plain view,
    facing it, from one of nine eyes round the seated eye (interior/cabin.py's SEATED_EYE; the box's corners: the head
    leaning and turning, as lod_cabin.py allows), past the cabin (cabin_glb, which hides the body from inside) and
    through the glass (its back faces are culled, so from inside it hides nothing; it is itself unseen from inside). A
    face touching a seen one is kept too (no gap at the edge of what is seen). A material's unseen part goes apart
    only when it is worth a draw (OUT_MIN triangles); a material wholly unseen goes whole. Returns whether a wheel is
    seen from the seat."""
    import bmesh
    import cabin as C
    from lod_cabin import visible_faces
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(cabin_glb))
    imported = [o for o in bpy.data.objects if o not in before]
    cab = [o for o in imported if o.type == 'MESH']
    test = [p for p in parts if p.name != 'glass'] + list(wheels.values())
    for o in test:                                   # triangles first, as lod_cabin.py does (a long face can hide all its probes)
        for x in bpy.context.view_layer.objects: x.select_set(False)
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        m = o.modifiers.new('tri', 'TRIANGULATE'); m.keep_custom_normals = True; m.quad_method = 'BEAUTY'; m.ngon_method = 'BEAUTY'
        bpy.ops.object.modifier_apply(modifier='tri')
    cx, cy, cz = C.SEATED_EYE
    E = [Vector((cx, cy, cz))] + [Vector((cx + dx, cy + dy, cz + dz)) for dx in (-0.12, 0.06) for dy in (-0.20, 0.15) for dz in (-0.10, 0.08)]
    seen = visible_faces(test + cab, E)[:len(test)]
    for o in imported: bpy.data.objects.remove(o)
    root = bpy.data.objects.new('outside', None); bpy.context.collection.objects.link(root)
    wheel_seen = False
    tri = lambda o: (o.data.calc_loop_triangles(), len(o.data.loop_triangles))[1]
    for o, s in zip(test, seen):
        if o in wheels.values():
            wheel_seen = wheel_seen or bool(s); continue
        bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
        keep = set(s)
        for i in list(s):                            # and every face touching a seen one
            for v in bm.faces[i].verts:
                for f in v.link_faces: keep.add(f.index)
        n_out = len(bm.faces) - len(keep)
        if not keep:
            o.parent = root; print('  %-18s %6d triangles, none seen: outside' % (o.name, len(bm.faces))); bm.free(); continue
        if n_out < OUT_MIN:
            print('  %-18s %6d triangles, %6d unseen: kept whole' % (o.name, len(bm.faces), n_out)); bm.free(); continue
        twin = o.copy(); twin.data = o.data.copy(); bpy.context.collection.objects.link(twin); twin.name = twin.data.name = o.name + '_out'; twin.parent = root
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in keep], context='FACES'); bm.to_mesh(o.data); bm.free()
        b2 = bmesh.new(); b2.from_mesh(twin.data); b2.faces.ensure_lookup_table()
        bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.index in keep], context='FACES'); b2.to_mesh(twin.data); b2.free()
        print('  %-18s seen %6d, outside %6d' % (o.name, tri(o), tri(twin)))
    for p in parts:
        if p.name == 'glass': p.parent = root; print('  glass              %6d triangles: outside (unseen from inside by its nature)' % tri(p))
    return wheel_seen


def near(src, out, cabin_glb=None):
    import cabin as C                               # the seated eye: interior/cabin.py's SEATED_EYE (SAE J941's eyellipse centre, roughly: a choice made there)
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src)); clean_scene_of()
    wheels = {k: bpy.data.objects.get('wheel_' + k) for k in CORNERS}
    missing = [k for k, w in wheels.items() if w is None]
    if missing: sys.exit('no wheel_%s in %s' % (missing, src))
    rest = [o for o in bpy.data.objects if o.type == 'MESH' and o not in wheels.values()]
    body = join(rest, 'body')
    door_split(body)
    parts = by_material(body)
    if cabin_glb and not seat_split(parts, wheels, cabin_glb):
        e = bpy.data.objects.new('seat_hides_wheels', None); bpy.context.collection.objects.link(e)      # (no wheel is seen from the seat: the game hides them there too)
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


# the steering wheel (interior/cabin.py's WHEEL: its middle, raked 24 degrees, the top forward) and the driver's door
# trim, as the full cabin (cabin.glb, one mesh) holds them: by their loose pieces, the wheel's within its sweep (a rim
# 0.38 m across: 0.215 m round the column's axis, 7 cm either side of its plane), the trim's within its box
WHEEL_C = (0.430, 0.417, 1.247)
WHEEL_AX = (-0.9135, 0.0, 0.4067)          # the column's axis, toward the driver (the wheel's face after cabin.py's turn)
TRIM_BOX = ((-0.15, 0.92), (0.70, 0.91), (0.54, 1.26))


def cabin(src, out):
    """The cabin layer from the full cabin (cabin.glb): the steering wheel apart under an empty 'steering' on the
    column's axis (play.js turns it about its x axis, toward the driver, by the road wheels' angle times 15), the door's
    trim apart under 'doorcard_FL' at the door's hinge (it swings with the door), and the rest with the faces no one
    sees dropped (lod_cabin.py's eyes round each seat, and from outside the open driver's door, which now opens; the
    wheel and the trim move, so they keep every face and hide nothing). All under 'interior'."""
    import bmesh
    from mathutils import Vector, Matrix
    import lod_cabin as LC
    bpy.ops.wm.read_homefile(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(src))
    whole = join([o for o in bpy.data.objects if o.type == 'MESH'], 'cabin')
    for x in bpy.context.view_layer.objects: x.select_set(False)
    whole.select_set(True); bpy.context.view_layer.objects.active = whole
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    pieces = [o for o in bpy.data.objects if o.type == 'MESH']
    C, A = Vector(WHEEL_C), Vector(WHEEL_AX)
    def in_sweep(o):
        for v in o.data.vertices:
            d = v.co - C; t = d.dot(A)
            if abs(t) > 0.07 or (d - A * t).length > 0.215: return False
        return True
    def in_box(o):
        return all(TRIM_BOX[0][0] < v.co.x < TRIM_BOX[0][1] and TRIM_BOX[1][0] < v.co.y < TRIM_BOX[1][1] and TRIM_BOX[2][0] < v.co.z < TRIM_BOX[2][1] for v in o.data.vertices)
    wheel = [o for o in pieces if in_sweep(o)]; trim = [o for o in pieces if o not in wheel and in_box(o)]; rest = [o for o in pieces if o not in wheel and o not in trim]
    tri = lambda os_: sum((o.data.calc_loop_triangles(), len(o.data.loop_triangles))[1] for o in os_)
    print('cabin pieces: %d; the wheel %d pieces, %d triangles; the door trim %d pieces, %d triangles; the rest %d triangles' % (len(pieces), len(wheel), tri(wheel), len(trim), tri(trim), tri(rest)))
    wheel = join(wheel, 'tp_doorcard_wheel'); trim = join(trim, 'tp_doorcard_trim'); rest = join(rest, 'cabin')
    for o in (rest,):                                 # triangles first (lod_cabin.py's reason)
        for x in bpy.context.view_layer.objects: x.select_set(False)
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        m = o.modifiers.new('tri', 'TRIANGULATE'); m.keep_custom_normals = True; m.quad_method = 'BEAUTY'; m.ngon_method = 'BEAUTY'
        bpy.ops.object.modifier_apply(modifier='tri')
    LC.in_wheel = lambda c: False                     # (lod_cabin's sweep is the downloaded car's; ours is the 'tp_doorcard_' piece)
    E = LC.eyes(False) + [(Vector((x, 2.2, z)), LC.DOOR_X) for x in (-0.4, 0.2, 0.8) for z in (1.0, 1.5, 1.9)]
    n0 = tri([rest])
    seen = LC.visible_faces([rest, wheel, trim], E, wheel=True)[0]
    bm = bmesh.new(); bm.from_mesh(rest.data); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in seen], context='FACES'); bm.to_mesh(rest.data); bm.free()
    print('cabin rest: %d -> %d seen' % (n0, tri([rest])))
    root = bpy.data.objects.new('interior', None); bpy.context.collection.objects.link(root)
    Y = Vector((0, -1, 0)); Z = A.cross(Y)
    steer = bpy.data.objects.new('steering', None); bpy.context.collection.objects.link(steer)
    steer.matrix_world = Matrix(((A.x, Y.x, Z.x, C.x), (A.y, Y.y, Z.y, C.y), (A.z, Y.z, Z.z, C.z), (0, 0, 0, 1)))
    hinge = bpy.data.objects.new('doorcard_FL', None); bpy.context.collection.objects.link(hinge); hinge.location = HINGE
    bpy.context.view_layer.update()
    for child, parent, name in ((wheel, steer, 'steering_wheel'), (trim, hinge, 'doorcard_trim')):
        child.name = child.data.name = name; child.parent = parent; child.matrix_parent_inverse = parent.matrix_world.inverted()
    for o in (rest, steer, hinge): o.parent = root
    print('cabin: %d triangles' % tri_count())
    export(out)


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    {'near': near, 'far': far, 'cabin': cabin}[a[0]](*a[1:])
