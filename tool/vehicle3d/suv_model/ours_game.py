"""Our code-built car (suv.blend) as the game's car: a layer from lod_ext.py, rigged and exported for design/prototype3d.
ours_game.py near <near.blend> <out.glb> [cabin.glb]
                                              the near layer: parts merged by material (one draw each), the wheels on
                                              their corners (corner_XX steers and rides its spring, wheel_XX spins in
                                              it), the seated driver's eye ('eye', 'eye_look' 6 m ahead of it); with the
                                              cabin, what the seat view or the chase view cannot see is sorted out
                                              (view_split) for the game to leave undrawn there
ours_game.py far <far.blend> <out.glb>        the far layer: everything merged by material, wheels and all
ours_game.py cabin <cabin.glb> <out.glb>      the cabin layer (interior/lod_cabin.py's cabin_lod0.glb) under an empty
                                              'interior', as play.js loads it while the player is at the car
play.js reads these names (part(), getObjectByName). The player's car casts no shadow (the owner's word, 11 Nov).
The owner's choice (11 Nov): this car, ours and built by code from his photos, replaces the downloaded model.
"""
import bpy, sys, os, math
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
    for o in objs:                                   # one name for every part's UV map, so the join keeps one map (named apart, the
        uvs = o.data.uv_layers                       # plate's UVs went to a second map and its image never showed: the review)
        if not len(uvs): continue
        act = next((l for l in uvs if l.active_render), uvs[0])
        for l in uvs:
            if l != act and l.name == 'UVMap': l.name = 'UVMap_other'
        act.name = 'UVMap'
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
# roof (0.11, 1.765), where the window's top chrome ends; its hinge on the front shut line, a little in from the skin.
# The frame goes whole with the door, as the LC300's framed door: its top trim runs up to z 1.79 under the roof's edge
# (cut at 1.775, its upper half stayed on the body), and above the belt the door reaches back to the B pillar's black
# strip (x -0.27..-0.183, which stays): its glass did, and a 4 cm strip of it stayed on the body
DOOR_X = (-0.14, 0.94)
DOOR_XU = -0.19
DOOR_Z = (0.43, 1.22, 1.79)
DOOR_A = ((0.94, 1.22), (0.11, 1.765))
HINGE = (0.94, 0.92, 0.85)
APIL_GLASS = 0.03                       # the door's glass cut clean this far past the A pillar's line and taken to there (it runs 2-4 cm under the pillar's trim)
SASH = (-0.027, -0.003, 0.012)          # the front sash member: from 2.7 cm to 3 mm forward of the line (along the pane's front edge), 1.2 cm inside the glass
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
    # (only what lies round the door is cut: planes across the whole side split faces far from it, about 5k triangles more)
    near_door = lambda c: c.y > 0.3 and DOOR_X[0] - 0.06 < c.x < MIRROR[0][1] + 0.16 and DOOR_Z[0] - 0.06 < c.z < DOOR_Z[2] + 0.04
    mid = lambda e: e.co if hasattr(e, 'co') else sum((v.co for v in e.verts), Vector()) / len(e.verts)
    left = lambda: [e for e in bm.verts[:] + bm.edges[:] + bm.faces[:] if near_door(mid(e))]
    for co, no in (((DOOR_X[0], 0, 0), (1, 0, 0)), ((DOOR_X[1], 0, 0), (1, 0, 0)), ((0, 0, DOOR_Z[0]), (0, 0, 1)), ((0, 0, DOOR_Z[1]), (0, 0, 1)), ((0, 0, DOOR_Z[2]), (0, 0, 1)), ((ax, 0, az), tuple(na))):
        bmesh.ops.bisect_plane(bm, geom=left(), plane_co=co, plane_no=no)
    # the glass alone cut again APIL_GLASS forward of the line, so the door's pane ends on a clean edge there
    gl = {i for i, m in enumerate(body.data.materials) if m and m.name == 'glass'}
    gface = [f for f in bm.faces if f.material_index in gl and near_door(f.calc_center_median())]
    gset = set(gface) | {e for f in gface for e in f.edges} | {v for f in gface for v in f.verts}
    A = Vector((ax, 0, az))
    bmesh.ops.bisect_plane(bm, geom=list(gset), plane_co=A + na * APIL_GLASS, plane_no=na)
    bm.faces.ensure_lookup_table()
    gloss = {i for i, m in enumerate(body.data.materials) if m and m.name == 'black_gloss'}
    glass = {i for i, m in enumerate(body.data.materials) if m and m.name == 'glass'}
    def on_door(f):
        c = f.calc_center_median()
        if MIRROR[0][0] < c.x < MIRROR[0][1] and MIRROR[1][0] < c.y < MIRROR[1][1] and MIRROR[2][0] < c.z < MIRROR[2][1]: return True
        if DOOR_Z[0] < c.z < DOOR_Z[1]: return DOOR_X[0] < c.x < DOOR_X[1] and c.y > 0.55
        if not (DOOR_Z[1] <= c.z < DOOR_Z[2] and c.y > 0.6 and DOOR_XU < c.x and f.material_index not in gloss): return False
        return c.x < xa(c.z) or (f.material_index in glass and (c - A).dot(na) < APIL_GLASS)      # (the pane to its clean cut: it runs 2-4 cm under the pillar's trim, and a strip of it stayed on the body)
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


# the doorway's lower part, which the door hid: the sill under the cabin's floor edge (the floor's top at z 0.626, its
# edge at y 0.66-0.70; the door trim's bottom at z 0.558, y 0.81-0.89 shut) out to the rocker's face (y 0.873 below the
# door's cut at z 0.43), and the door's jambs at its shut lines across the door's depth (y 0.80 in to the skin)
SILL_Z = (0.43, 0.545, 0.64)            # the rocker's top under the door; the scuff plate, under the shut door's trim; the riser's top, at the floor
SILL_Y = (0.66, 0.875, 0.92)            # the riser under the floor's edge; the sill's outer face, on the rocker's; the rocker's top out to under the door's skin
JAMB_X = (-0.155, 0.938)                # the B pillar's face, behind the shut door's trim (it reaches back to x -0.15); the hinge pillar's face, at the front shut line
JAMB_Y0, JAMB_IN, JAMB_TOP = 0.80, 0.012, 1.15      # the jambs from y 0.80 out to 1.2 cm inside the skin, up to z 1.15 (above, the side curves in to the belt)


def sash_line(body):
    """The door glass's surface along the A pillar's line, at its front edge (where the front sash member runs), from the belt to
    the roof every 5%: measured on the glass alone (the mirror stands in front of it from outside)."""
    import bmesh
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    gi = {i for i, m in enumerate(body.data.materials) if m and m.name == 'glass'}
    bm = bmesh.new(); bm.from_mesh(body.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in gi], context='FACES')
    bvh = BVHTree.FromBMesh(bm)
    (ax, az), (bx, bz) = DOOR_A
    d = Vector((bx - ax, 0, bz - az)).normalized(); back = Vector((-d.z, 0, d.x))      # (across the line, into the door: -x, -z)
    if back.x > 0: back = -back
    out = []
    for i in range(21):
        t = i / 20; p = Vector((ax + (bx - ax) * t, 0, az + (bz - az) * t))
        row = []
        for off in (SASH[0], SASH[1]):
            q = p + back * off; h = bvh.ray_cast(Vector((q.x, 1.5, q.z)), Vector((0, -1, 0)), 1.2)
            row.append(Vector((q.x, h[0].y - SASH[2], q.z)) if h[0] else None)
        out.append(row)
    bm.free()
    return [r for r in out if r[0] and r[1]]


def sash(door_parts, line):
    """The front sash member along the door glass's front edge, inside it (the window's run channel, as the LC300's
    framed door has): a black strip on the door from the belt to the roof. From outside the dark glass hides it; open,
    the door's window had nothing round its front edge."""
    import bmesh
    trim = next((o for o in door_parts if o.name == 'door_trim_black'), None)
    if trim is None or len(line) < 2: print('sash: no door trim part or no glass along the line'); return
    bm = bmesh.new(); bm.from_mesh(trim.data)
    inv = trim.matrix_world.inverted()
    for (a0, a1), (b0, b1) in zip(line, line[1:]):
        f = bm.faces.new([bm.verts.new(inv @ v) for v in (a0, a1, b1, b0)]); f.smooth = False
    bm.to_mesh(trim.data); bm.free()
    print('sash: %d faces along the A pillar' % (len(line) - 1))


def skin_profile(body):
    """The side's outer skin at the two jamb planes, by height (z 0.43 to JAMB_TOP every 2 cm): measured before the door
    is cut, by a ray from outside. A straight jamb edge at y 0.925 stood out through the skin up to 9 cm by the belt."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    zs = [round(SILL_Z[0] + 0.02 * i, 3) for i in range(int((JAMB_TOP - SILL_Z[0]) / 0.02) + 1)]
    prof = {}
    for x in JAMB_X:
        prof[x] = [(z, bvh.ray_cast(Vector((x, 1.5, z)), Vector((0, -1, 0)), 1.0)[0].y) for z in zs]
    return prof


def doorway(body, prof):
    """Faces the opened door uncovers, joined into body: with the door open, a band under the seat showed straight
    through the car (nothing closed the sill below the floor's edge), and the space inside the door's depth at its
    front and rear shut lines was open. Black trim for the sill and its scuff plate, paint for the jambs (a few dozen
    triangles). Run after door_split, so they stay with the body."""
    import bmesh
    from mathutils import Vector
    x0, x1 = JAMB_X[0], DOOR_X[1] - 0.002      # (the sill back to the rear jamb behind the shut door's trim: ended at the shut line, it left a see-through notch at the doorway's rear corner)
    (za, zb, zc), (ya, yb, yc) = SILL_Z, SILL_Y
    quads = [      # four corners, the way the face looks, its material
        (((x0, yb, za), (x1, yb, za), (x1, yb, zb), (x0, yb, zb)), (0, 1, 0), 'trim_black'),        # the sill's outer face
        (((x0, ya, zb), (x1, ya, zb), (x1, yb, zb), (x0, yb, zb)), (0, 0, 1), 'trim_black'),        # the scuff plate
        (((x0, ya, zb), (x1, ya, zb), (x1, ya, zc), (x0, ya, zc)), (0, 1, 0), 'trim_black'),        # the riser to the floor
        (((x0, yb, za), (x1, yb, za), (x1, yc, za), (x0, yc, za)), (0, 0, 1), 'trim_black'),        # the rocker's top under the door
    ]
    for x, look in ((JAMB_X[1], (-1, 0, 0)), (JAMB_X[0], (1, 0, 0))):      # the jambs, strip by strip under the skin's profile
        p = prof[x]
        for (z0, y0), (z1, y1) in zip(p, p[1:]):
            quads.append((((x, JAMB_Y0, z0), (x, y0 - JAMB_IN, z0), (x, y1 - JAMB_IN, z1), (x, JAMB_Y0, z1)), look, 'paint'))
    slot = {m.name: i for i, m in enumerate(body.data.materials) if m}
    bm = bmesh.new(); bm.from_mesh(body.data)
    for corners, look, mat in quads:
        f = bm.faces.new([bm.verts.new(c) for c in corners]); f.material_index = slot[mat]; f.smooth = False
        f.normal_update()
        if f.normal.dot(Vector(look)) < 0: f.normal_flip()
    bm.to_mesh(body.data); bm.free()
    print('doorway: %d faces (the sill and the jambs); the jambs out to y %.3f..%.3f (front), %.3f..%.3f (rear)' % (len(quads),
          min(y for _, y in prof[JAMB_X[1]]) - JAMB_IN, max(y for _, y in prof[JAMB_X[1]]) - JAMB_IN, min(y for _, y in prof[JAMB_X[0]]) - JAMB_IN, max(y for _, y in prof[JAMB_X[0]]) - JAMB_IN))


def see_through(o):
    """A part drawn see-through (the lamps' clear covers): it hides nothing behind it."""
    for m in o.data.materials:
        if m and (getattr(m, 'blend_method', '') == 'BLEND' or getattr(m, 'surface_render_method', '') == 'BLENDED' or m.name == 'lamp_cover'): return True      # (not any blend mode but 'OPAQUE': Blender 4.2 gives every material 'HASHED')
    return False


def seen_both_sides(test, occluders, E):
    """For each object of test, the set of its polygon indices seen from one of the eyes E: lod_cabin.py's visible_faces,
    except that a face seen from behind counts too. The car's paint and trim go out two-sided (only the glass culls its
    back faces), so from inside their backs show where the cabin leaves a gap (the A pillar between the windshield and
    the side window went missing when only front faces counted)."""
    from mathutils.bvhtree import BVHTree
    obs = list(test) + list(occluders)
    V, P, owner = [], [], []
    for k, o in enumerate(obs):
        mw = o.matrix_world; n0 = len(V); V += [mw @ v.co for v in o.data.vertices]
        for p in o.data.polygons: P.append([n0 + i for i in p.vertices]); owner.append((k, p.index))
    # the occluders: every face but a see-through part's (the lamps' covers hid the tail lights behind them, and the
    # chase view lost them: the review of the pictures)
    clear = {k for k, o in enumerate(obs) if see_through(o)}
    solid = [fi for fi, (k, _) in enumerate(owner) if k not in clear]; at = {fi: i for i, fi in enumerate(solid)}
    tree = BVHTree.FromPolygons(V, [P[fi] for fi in solid], epsilon=0.0); seen = [set() for _ in test]
    for fi, (verts, (k, pi)) in enumerate(zip(P, owner)):
        if k >= len(test): continue
        pts = [Vector(V[i]) for i in verts]; c = sum(pts, Vector()) / len(pts)
        probes = [c] + [q + (c - q) * 0.05 for q in pts[:4]] + [(pts[i] + pts[(i + 1) % len(pts)]) * 0.5 * 0.95 + c * 0.05 for i in range(min(4, len(pts)))]
        hit = False
        for e in E:
            for q in probes:
                d = q - e; L = d.length
                if L < 1e-6: continue
                h = tree.ray_cast(e, d / L, L + 1e-4)
                if h[0] is None or (fi in at and h[2] == at[fi]) or (h[0] - q).length < 1e-3: hit = True; break
            if hit: break
        if hit: seen[k].add(pi)
    return seen


OUT_MIN = 500             # triangles: a group goes apart only past this (it costs a draw only on foot and on the map, where all are drawn)


def chase_eyes():
    """The chase camera's places round the car (play.js: 5.6 m behind the middle, 2.05 m up; its heading lags the car's
    in a turn, about the yaw rate over 4/s, so a fan of +-50 degrees behind, held through spins under about 3.5 rad/s
    (200 degrees a second; a donut with traction control off turns at about 2.5); and higher and lower for its easing
    over bumps), at 6.8 m too (it falls back 1.2 m with speed) and higher, to 4.2 m, where it rises to see over a wall (with
    eyes only 1.6-2.6 m up at 5.6 m, the game drew all of the car whenever the camera rose over a wall, 7 draws more,
    and low and far back thin slivers under the rear skid plate went missing)."""
    out = []
    for back in (5.6, 6.8):
        for a in range(-50, 51, 10):
            for up in (1.3, 1.6, 2.05, 2.6, 3.3, 4.2):
                r = math.radians(a); out.append(Vector((-back * math.cos(r), back * math.sin(r), up)))
    return out


def view_split(parts, wheels, cabin_glb):
    """What a view cannot see is not drawn in it (the seat view was 449k triangles and the view from behind 411k against
    the 400k budget, ADR 0005). Each material's faces are sorted by whether the driver sees them from the seat (nine eyes
    round interior/cabin.py's SEATED_EYE, past the cabin, cabin_glb, and through the glass, whose back faces are culled)
    and whether the chase camera sees them (chase_eyes, past the car itself): seen by both stay at the top; seen only
    from the seat go under 'seat_only', only from behind under 'chase_only', by neither under 'outside'. The game draws
    the top and 'seat_only' in the seat view, the top and 'chase_only' from behind, and all of it on foot, on the map and
    while the door stands open. Faces seen from behind count (the paint and trim go out two-sided). A face touching a
    seen one counts as seen (no gap at the edge); a part smaller than OUT_MIN stays at the top (drawn everywhere: not
    worth a draw of its own). The wheels spin in their corners and are left whole."""
    import bmesh
    import cabin as C
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(cabin_glb))
    imported = [o for o in bpy.data.objects if o not in before]
    cab = [o for o in imported if o.type == 'MESH']
    for o in parts:                                  # triangles first, as lod_cabin.py does (a long face can hide all its probes)
        for x in bpy.context.view_layer.objects: x.select_set(False)
        bpy.context.view_layer.objects.active = o; o.select_set(True)
        m = o.modifiers.new('tri', 'TRIANGULATE'); m.keep_custom_normals = True; m.quad_method = 'BEAUTY'; m.ngon_method = 'BEAUTY'
        bpy.ops.object.modifier_apply(modifier='tri')
    cx, cy, cz = C.SEATED_EYE
    E = [Vector((cx, cy, cz))] + [Vector((cx + dx, cy + dy, cz + dz)) for dx in (-0.12, 0.06) for dy in (-0.20, 0.15) for dz in (-0.10, 0.08)]
    inside = [p for p in parts if p.name != 'glass']
    seat = dict(zip(inside, seen_both_sides(inside + list(wheels.values()), cab, E)))
    for o in imported: bpy.data.objects.remove(o)
    chase = dict(zip(parts, seen_both_sides(parts + list(wheels.values()), [], chase_eyes())))
    roots = {k: bpy.data.objects.new(k, None) for k in ('seat_only', 'chase_only', 'outside')}
    for r in roots.values(): bpy.context.collection.objects.link(r)
    tri = lambda o: (o.data.calc_loop_triangles(), len(o.data.loop_triangles))[1]
    def grown(o, s):
        bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table(); out = set(s)
        for i in s:
            for v in bm.faces[i].verts:
                for f in v.link_faces: out.add(f.index)
        n = len(bm.faces); bm.free(); return out, n
    for o in parts:
        S, n = grown(o, seat.get(o, set())); Cs, _ = grown(o, chase[o])
        group = {'top': {i for i in range(n) if i in S and i in Cs}, 'seat_only': S - Cs, 'chase_only': Cs - S, 'outside': set(range(n)) - S - Cs}
        for k in ('seat_only', 'chase_only', 'outside'):
            if 0 < len(group[k]) < OUT_MIN: group['top'] |= group[k]; group[k] = set()
        made = []
        for k in ('seat_only', 'chase_only', 'outside'):
            if not group[k]: continue
            if len(group[k]) == n:                   # the whole part in one group: moved, not copied
                o.parent = roots[k]; made.append('all %s' % k); group['top'] = set(); break
            twin = o.copy(); twin.data = o.data.copy(); bpy.context.collection.objects.link(twin)
            twin.name = twin.data.name = o.name + '_' + k; twin.parent = roots[k]
            b2 = bmesh.new(); b2.from_mesh(twin.data); b2.faces.ensure_lookup_table()
            bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.index not in group[k]], context='FACES'); b2.to_mesh(twin.data); b2.free()
            made.append('%s %d' % (k, tri(twin)))
        print('  %-16s %6d: top %6d, %s' % (o.name, n, len(group['top']), ', '.join(made) or 'all at the top'))
        if not group['top']:
            if o.parent not in roots.values(): bpy.data.objects.remove(o)      # (split among the groups, none at the top: the original goes)
            continue
        if len(group['top']) < n:
            bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in group['top']], context='FACES'); bm.to_mesh(o.data); bm.free()


def near(src, out, cabin_glb=None):
    import cabin as C                               # the seated eye: interior/cabin.py's SEATED_EYE (SAE J941's eyellipse centre, roughly: a choice made there)
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src)); clean_scene_of()
    wheels = {k: bpy.data.objects.get('wheel_' + k) for k in CORNERS}
    missing = [k for k, w in wheels.items() if w is None]
    if missing: sys.exit('no wheel_%s in %s' % (missing, src))
    rest = [o for o in bpy.data.objects if o.type == 'MESH' and o not in wheels.values()]
    body = join(rest, 'body')
    prof, line = skin_profile(body), sash_line(body)
    door = door_split(body)
    sash(door, line)
    doorway(body, prof)
    parts = by_material(body)
    if cabin_glb: view_split(parts, wheels, cabin_glb)
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
    for o in by_material(body):
        # each part shaded smooth only within its panels (sharp past 25 degrees), its normals recomputed: the decimation
        # left its own, 6 to 26 degrees off the faces on average (the near layer's 1 to 9), so the side windows and
        # the B pillar's black strip caught other light than the near layer's and popped at the 20 m swap (the
        # reviewer: 696 of 6.1k car pixels changed, mostly the side glass)
        for x in bpy.context.view_layer.objects: x.select_set(False)
        o.select_set(True); bpy.context.view_layer.objects.active = o
        bpy.ops.mesh.customdata_custom_splitnormals_clear()
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(25), keep_sharp_edges=True)
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
