"""The private car's outside in game layers (the owner's decision of 10 Nov: layered detail; see thirdparty/README.md).
thirdparty_lod.py <outside.blend> <out.blend> <target triangles> [far]
1. The model's hundreds of parts become one object per material (one draw each), their shading kept. In the near
   layer the wheels are apart, for the suspension and the steering: per corner, corner_XX (at the hub; it rises and
   falls with the suspension and the front ones steer) holds the brake caliper and wheel_XX (at the hub too; it spins)
   holds the tyre, the rim, the disc and the wheel nuts. The driver's door (the model's FrontLeft_Door: skin, glass,
   handle, mirror) is apart too, door_FL.*, for the door to open (thirdparty_rig.py hangs it on its hinge).
2. Faces nobody sees go: lod_ext.py's test from its ring of eyes round the car and above it (not from the seats: the
   glass is dark, and inside the interior's own file covers what the seats see). The wheels keep every face (they
   turn: a face hidden at one turn shows at the next), and so does the driver's door, which hides nothing (it opens:
   the doorway's jambs behind it stay).
3. What is left is thinned toward the target (collapse decimation), each material with its least share: the lamps
   and the tyres' texture keep more (they read close up), the plates are kept whole; each wheel to about WHEEL.
4. The glass's faces turned toward the cabin go (glass_out())."""
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lod_ext as LE

NEAR = {'plate': 1.0, 'Wheel': 1.0, 'Textures_A': 1.0, 'CarPaint': 0.10, 'Chrome': 0.12, 'BlackPlastic_Shiny': 0.07, 'MetalBlack': 0.025, 'Front_Light': 0.5, 'Light_glass': 0.35, 'Light_Red_Back': 0.35, 'GlassRed': 0.35,
        'Light_White_Back': 0.35, 'BackSpotLight': 0.35, 'SpotLight': 0.35, 'ClearGlass': 0.2, 'Mirror': 0.5, 'RearMirror_Light': 0.5}
# (the paint holds a tenth: black gloss shows every facet; the grille's chrome bars and black frame hold enough to stay
# whole (at 0.046 the bars broke up); the chassis's black metal, seen only from low down, gives up most, and so does
# the glass, which is flat; the rest shares what is left)
FAR = {'plate': 1.0, 'Wheel': 0.5, 'Textures_A': 0.5, 'ClearGlass': 0.4, 'Light_glass': 0.3, 'GlassRed': 0.3, 'Light_Red_Back': 0.3}      # (the glass held: thinned with the rest, the far car had no windows)
SMALL = 300                    # a material with fewer seen triangles is kept whole (near) or halved (far)
WHEEL = 2000                   # a near wheel's triangles (tyre, rim, disc, nuts); its tyre (672, textured) kept whole
CORNERS = ('FL', 'FR', 'RL', 'RR')
INSIDE = ('Fabric', 'White_Leather_Body', 'White_Leather_Seats', 'Plastic_Beige', 'Black_Leather', 'Leather_Points', 'Leather_Handles', 'Wood', 'Buttons', 'Screens')
# (the interior's materials: what of them is left in the outside, seen only through its gaps, goes; the glass is dark)
CLEAR = ('Light_glass', 'GlassRed', 'Light_Red_Back')    # the lamps' see-through lenses (their materials' alpha 0.25-0.74): seen, but hiding nothing (the lamps' insides show through them)


MERGE = {'Light_Red_Back_Lower': 'Light_Red_Back', 'RearMirror_Light': 'Light_White_Back'}      # two lamps of a few triangles each: drawn with their neighbours (two draws fewer)
PANEL = float(os.environ.get('TP_PANEL', 0.01))        # m^2: a loose part this big has its edges held in the thinning (0.05: 51k with gaps on the bonnet and the tailgate; 0.01: 66k; 0.002: 94k)
FEW = int(os.environ.get('TP_FEW', 0))                   # a loose part of fewer triangles is kept whole (40 took the near layer to 110k: off)
HOLD = [((-2.75, -2.25), (-0.18, 0.18), (0.95, 1.35))]
HOLD_ALL = [((-2.2, -1.4), (-0.12, 0.12), (1.86, 2.1))]          # held whatever the material: the roof's antenna (thinned, it vanished)          # boxes (x, y, z) whose paint is not thinned: the tailgate's emblem recess (thinned, its rim broke into a badge-like shard)


def visible(obs, E, clear_names):
    """lod_ext.visible's test, with the probes spread over a big face (one per 3 cm square, up to 36): a face seen only
    through the grille's slots or the intakes' bars was missed by a test at its middle and corners, and the sky showed
    through the grille."""
    from mathutils.bvhtree import BVHTree
    V, P, owner = [], [], []
    for k, o in enumerate(obs):
        mw = o.matrix_world; n0 = len(V); V += [mw @ v.co for v in o.data.vertices]; flip = mw.determinant() < 0
        for p in o.data.polygons: P.append([n0 + i for i in (p.vertices[::-1] if flip else p.vertices)]); owner.append((k, p.index))
    clear = {k for k, o in enumerate(obs) if any(w in o.name for w in clear_names)}
    keep = [i for i, (k, _) in enumerate(owner) if k not in clear]
    tree = BVHTree.FromPolygons(V, [P[i] for i in keep], epsilon=0.0); remap = {j: i for j, i in enumerate(keep)}; seen = [set() for _ in obs]
    rng = np.random.default_rng(1)
    for fi, (verts, (k, pi)) in enumerate(zip(P, owner)):
        pts = [Vector(V[i]) for i in verts]; c = sum(pts, Vector()) / len(pts); n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        if n.length < 1e-14: continue
        area = n.length / 2; n.normalize()
        probes = [c] + [q + (c - q) * 0.1 for q in pts]
        m = int(min(36, area / 0.0009))
        if m > 0:
            for a, b in rng.random((m, 2)):
                if a + b > 1: a, b = 1 - a, 1 - b
                probes.append(pts[0] + (pts[1] - pts[0]) * a + (pts[2] - pts[0]) * b)
        ok = False
        for e in E:
            for q in probes:
                d = q - e; L = d.length
                if n.dot(-d) <= 0: continue
                h = tree.ray_cast(e, d / L, L + 1e-4)
                if h[0] is None or remap.get(h[2]) == fi or (h[0] - q).length < 2e-4: ok = True; break
            if ok: break
        if ok: seen[k].add(pi)
    return seen


def held(o):
    """A vertex group of what decimation must keep: the big parts' own edges (thinned, the edges between panels
    opened into gaps: the arches' tops, the step bars, the bonnet's shut line) and the HOLD boxes' paint."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    me = o.data; E = np.array([e.vertices[:] for e in me.edges]); nv = len(me.vertices)
    k, lab = connected_components(coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(nv, nv)), directed=False) if len(E) else (1, np.zeros(nv, int))
    bm = bmesh.new(); bm.from_mesh(me); mw = o.matrix_world; keep = set(); bm.faces.ensure_lookup_table()
    area = np.zeros(k); np.add.at(area, [lab[f.verts[0].index] for f in bm.faces], [f.calc_area() for f in bm.faces])
    nf = np.zeros(k, int); np.add.at(nf, [lab[f.verts[0].index] for f in bm.faces], 1)
    for e in bm.edges:
        if e.is_boundary and area[lab[e.verts[0].index]] > PANEL: keep.update(v.index for v in e.verts)
    keep.update(int(i) for i in np.nonzero(nf[lab] < FEW)[0])            # small parts whole (the roof's antenna, the lamps' small pieces: thinned, they vanished or broke)      # (big panels only: every part's edges held left nothing to thin, 155k)
    boxes = HOLD_ALL + (HOLD if o.name.split('.')[-1] == 'CarPaint' else [])
    for v in bm.verts:
        p = mw @ v.co
        if any(x[0] < p.x < x[1] and y[0] < p.y < y[1] and z[0] < p.z < z[1] for x, y, z in boxes): keep.add(v.index)
    bm.free(); g = o.vertex_groups.new(name='held'); g.add(sorted(keep), 1.0, 'REPLACE'); return len(keep)


RADIATOR = ((2.05, -0.88, 0.28), (2.05, 0.88, 1.18))     # the dark face behind the grille and the intakes, where the radiator stands


def radiator(obs):
    """A dark panel across the front openings (two triangles in the chassis's rough black). The model's backing
    behind the grille is seen only through narrow slots, so the cull drops most of it and the sky showed through;
    a real car shows its radiator there."""
    o = next((o for o in obs if o.name == 'BlackPlastic_Rough'), None)
    if o is None: return
    (x, y0, z0), (_, y1, z1) = RADIATOR; mwi = o.matrix_world.inverted()
    bm = bmesh.new(); bm.from_mesh(o.data)
    vs = [bm.verts.new(mwi @ Vector(p)) for p in ((x, y1, z0), (x, y0, z0), (x, y0, z1), (x, y1, z1))]
    f = bm.faces.new(vs); f.material_index = 0; f.normal_update()
    if (o.matrix_world.to_3x3() @ f.normal).x < 0: f.normal_flip()          # facing forward (its normal computed first: a new face's is zero)
    bm.to_mesh(o.data); bm.free()


SHELLS = [((1.15, 2.2), (-0.80, 0.80), (0.50, 1.10))] + [((hx - 0.48, hx + 0.48), (s * 0.40, s * 0.88) if s > 0 else (s * 0.88, s * 0.40), (0.50, 0.85)) for hx in (1.556, -1.294) for s in (1, -1)]
# (the engine bay's from x 1.15, ahead of the footwells: from 1.0 it showed as a black floor under the pedals;
# their floors at 0.5 m, inside the body: reaching lower, below the bumpers and the sills, they showed as black boxes
# under the car; one inside the rear bumper showed below it at any height, and went)
# boxes inside the body whose faces look inward: the engine bay and the four wheel wells. From outside a
# box's own faces are back faces (unseen); through a gap the far inside of it shows, dark, where the cull had left the sky


def shells(obs):
    o = next((o for o in obs if o.name == 'BlackPlastic_Rough'), None)
    if o is None: return
    mwi = o.matrix_world.inverted(); bm = bmesh.new(); bm.from_mesh(o.data)
    for (x0, x1), (y0, y1), (z0, z1) in SHELLS:
        c = Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        v = [bm.verts.new(mwi @ Vector((x, y, z))) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        for q in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            f = bm.faces.new([v[i] for i in q]); f.normal_update()
            if (o.matrix_world.to_3x3() @ f.normal).dot(o.matrix_world @ f.calc_center_median() - c) > 0: f.normal_flip()      # facing in
    bm.to_mesh(o.data); bm.free()


def glass_orient(obs):
    """Before the cull: a pane modelled as one sheet facing into the cabin is turned to face out (seen from outside
    it was a back face, culled, and the sunroof's front showed the sky); an inner skin of a two-layer pane goes."""
    from mathutils.bvhtree import BVHTree
    turned = gone = 0
    for o in obs:
        if o.name.split('.')[-1] != 'ClearGlass': continue
        bm = bmesh.new(); bm.from_mesh(o.data); mw = o.matrix_world; R = mw.to_3x3(); bm.faces.ensure_lookup_table()
        tree = BVHTree.FromBMesh(bm); dead = []
        for f in bm.faces:
            c = mw @ f.calc_center_median(); mid = Vector((min(0.8, max(-2.0, c.x)), 0.0, 1.1)); n = R @ f.normal
            if n.dot(c - mid) >= 0: continue
            out = -f.normal                                                     # (toward the outside, in the object's frame)
            h = tree.ray_cast(f.calc_center_median() + out * 1e-4, out, 0.03)
            if h[0] is not None: dead.append(f)
            else: f.normal_flip(); turned += 1
        bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(o.data); bm.free(); gone += len(dead)
    print('glass: %d one-sheet faces turned out, %d inner skins dropped' % (turned, gone))


def unflip(o, before):
    """Faces the decimation turned over, turned back: each face is compared with the nearest face of the mesh as it
    was (its BVH); a face facing against it is flipped. (With back faces culled, a turned face shows as a hole.)"""
    me = o.data; bm = bmesh.new(); bm.from_mesh(me); flips = 0
    for f in bm.faces:
        c = f.calc_center_median(); hit = before.find_nearest(c)
        if hit[0] is not None and f.normal.dot(hit[1]) < -0.2: f.normal_flip(); flips += 1
    bm.to_mesh(me); bm.free(); return flips


def hubs():
    """Each tyre's middle (the four objects of the tyres' material), by corner."""
    H = {}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.material_slots and o.material_slots[0].material and o.material_slots[0].material.name == 'Wheel':
            P = np.array([o.matrix_world @ v.co for v in o.data.vertices]); c = (P.min(0) + P.max(0)) / 2
            H[('F' if c[0] > 0 else 'R') + ('L' if c[1] > 0 else 'R')] = (c, P[:, 1].min(), P[:, 1].max())
    assert sorted(H) == sorted(CORNERS), H
    return H


def group_of(o, H):
    """'wheel_XX' (spins), 'corner_XX' (rides with the wheel, does not spin) or 'body'."""
    P = np.array([o.matrix_world @ v.co for v in o.data.vertices]); lo, hi = P.min(0), P.max(0); c, s = (lo + hi) / 2, hi - lo
    mat = o.material_slots[0].material.name if o.material_slots and o.material_slots[0].material else ''
    for k, (h, y0, y1) in H.items():
        if mat == 'CarPaint' or abs(c[1] - h[1]) > 0.2 or s.max() > 0.9: continue
        r = np.hypot(c[0] - h[0], c[2] - h[2])
        if r < 0.02 and max(s[0], s[2]) < 0.9: return 'wheel_' + k                                                                    # round about the axle: tyre, rim, disc, hub, and the axle's stub inboard (it turns too)
        if lo[1] >= y0 - 0.01 and hi[1] <= y1 + 0.01 and s.max() < 0.05 and r < h[2]: return 'wheel_' + k                              # small, within the tyre: a wheel nut, the valve stem
        if r < 0.3 and s.max() < 0.35 and abs(c[1] - h[1]) < 0.1: return 'corner_' + k                                           # the caliper, behind the disc
    return 'body'


def one_uv(obs):
    """Every part with one UV map, named UVMap: the one its textures read (a UV Map node's, else its render map).
    Joined with parts whose maps were named otherwise, or that had none, a part's texture came to read a map of
    zeros (the far tyres and the lamps' reflectors went flat)."""
    for o in obs:
        me = o.data; want = None
        for sl in o.material_slots:
            for n in (sl.material.node_tree.nodes if sl.material and sl.material.node_tree else ()):
                if n.type == 'TEX_IMAGE' and n.inputs['Vector'].links and n.inputs['Vector'].links[0].from_node.type == 'UVMAP':
                    want = me.uv_layers.get(n.inputs['Vector'].links[0].from_node.uv_map) or want
        want = want or next((l for l in me.uv_layers if l.active_render), None) or (me.uv_layers[0] if len(me.uv_layers) else None)
        for l in [l for l in me.uv_layers if l != want]: me.uv_layers.remove(l)
        if want is None: me.uv_layers.new(name='UVMap')
        else: me.uv_layers[0].name = 'UVMap'; me.uv_layers[0].active_render = True
    for m in bpy.data.materials:
        for n in (m.node_tree.nodes if m.node_tree else ()):
            if n.type == 'UVMAP': n.uv_map = 'UVMap'


def by_material(split):
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and len(o.data.polygons)]
    bpy.context.view_layer.update()
    def under(o, name):
        p = o.parent
        while p:
            if p.name.split('.')[0] == name: return True
            p = p.parent
        return False
    door = {o.name for o in obs if under(o, 'FrontLeft_Door')}                       # the model's own group for the driver's door
    for o in obs: mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw          # (the glTF's empties carry the parts' placing: kept before they go)
    for o in [o for o in bpy.data.objects if o.type != 'MESH' or not len(o.data.polygons)]: bpy.data.objects.remove(o)
    H = hubs(); groups = {}
    for o in obs: groups.setdefault(('door_FL' if o.name in door else group_of(o, H)) if split else 'body', []).append(o)
    one_uv(obs)
    out = []
    for g, members in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in members: o.data = o.data.copy() if o.data.users > 1 else o.data; o.select_set(True)
        bpy.context.view_layer.objects.active = members[0]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); bpy.ops.object.join()
        ob = bpy.context.view_layer.objects.active; before = set(bpy.data.objects)
        names = [sl.material.name if sl.material else '' for sl in ob.material_slots]
        for i, nm in enumerate(names):
            if nm in MERGE:
                if MERGE[nm] in names:                                           # its faces to the neighbour's slot (one object after the split)
                    j = names.index(MERGE[nm]); idx = np.array([p.material_index for p in ob.data.polygons]); idx[idx == i] = j; ob.data.polygons.foreach_set('material_index', idx)
                else: ob.material_slots[i].material = bpy.data.materials[MERGE[nm]]
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
        for o in [ob] + [o for o in bpy.data.objects if o not in before]:
            used = {p.material_index for p in o.data.polygons}
            if not used: bpy.data.objects.remove(o); continue
            m = o.material_slots[used.pop()].material; o.name = (m.name if m else 'none') if g == 'body' else g + '.' + (m.name if m else 'none'); o.data.name = o.name
            while len(o.material_slots) > 1:          # (one slot left: the material it is)
                i = next(i for i, s in enumerate(o.material_slots) if s.material != m); o.active_material_index = i; bpy.context.view_layer.objects.active = o; bpy.ops.object.material_slot_remove()
            o['group'] = g; out.append(o)
    return out, H


def glass_out(obs):
    """The glass faces that face into the cabin go: the glass is dark from outside and the game sees through it from
    inside (its back faces are culled), so a face turned inward (the panes' inner skins, triangles the thinning turned
    over) would show as a dark shard over the driver's view. Inward: toward the cabin's middle line (x held within the
    cabin, y 0, z 1.1)."""
    gone = 0
    for o in obs:
        if o.name.split('.')[-1] != 'ClearGlass': continue
        bm = bmesh.new(); bm.from_mesh(o.data); mw = o.matrix_world; R = mw.to_3x3()
        dead = []
        for f in bm.faces:
            c = mw @ f.calc_center_median(); mid = Vector((min(0.8, max(-2.0, c.x)), 0.0, 1.1))
            if (R @ f.normal).dot(c - mid) < 0: dead.append(f)
        bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(o.data); bm.free(); gone += len(dead)
    print('glass: %d faces facing the cabin dropped' % gone)


def inward_out(obs):
    """The outside's faces in the greenhouse turned toward the cabin go (not the driver's door's: it opens): from the
    driver's seat one hung as a black spike in the windscreen; inside, the interior's own trims are there."""
    gone = 0
    for o in obs:
        if o['group'] != 'body' or o.name.split('.')[-1] in ('ClearGlass', 'Mirror'): continue
        bm = bmesh.new(); bm.from_mesh(o.data); mw = o.matrix_world; R = mw.to_3x3(); dead = []
        for f in bm.faces:
            c = mw @ f.calc_center_median()
            if not (c.z > 1.25 and -2.3 < c.x < 0.95 and abs(c.y) < 0.92): continue
            mid = Vector((c.x, 0.0, 1.1))
            if (R @ f.normal).dot(c - mid) < -0.3 * (c - mid).length: dead.append(f)
        bmesh.ops.delete(bm, geom=dead, context='FACES'); bm.to_mesh(o.data); bm.free(); gone += len(dead)
    print('greenhouse: %d outside faces facing the cabin dropped' % gone)


def rig(obs, H):
    """corner_XX and wheel_XX empties at the hubs; the wheel's and the corner's meshes under them, about the hub."""
    for k in CORNERS:
        h = Vector(H[k][0]); cn = bpy.data.objects.new('corner_' + k, None); cn.location = h; bpy.context.collection.objects.link(cn)
        wh = bpy.data.objects.new('wheel_' + k, None); wh.parent = cn; bpy.context.collection.objects.link(wh)
        for o in obs:
            if o['group'] in ('wheel_' + k, 'corner_' + k):
                o.data.transform(Matrix.Translation(-h)); o.location = (0, 0, 0); o.parent = wh if o['group'].startswith('wheel') else cn
    print('hubs: ' + ', '.join('%s (%.3f, %.3f, %.3f)' % (k, *H[k][0]) for k in CORNERS))


def main(src, out, target, far=False):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src)); obs, H = by_material(not far)
    for o in [o for o in obs if o.name.split('.')[-1] in INSIDE]: obs.remove(o); bpy.data.objects.remove(o)
    glass_orient(obs)
    tri = lambda o: (o.data.calc_loop_triangles(), len(o.data.loop_triangles))[1]
    before = sum(tri(o) for o in obs)
    for o in obs:
        bpy.context.view_layer.objects.active = o; m = o.modifiers.new('tri', 'TRIANGULATE'); m.keep_custom_normals = True; bpy.ops.object.modifier_apply(modifier='tri')
    seen = visible(obs, LE.eyes()[:-4], CLEAR + ('door_FL.',))          # (lod_ext's last four eyes are the seats')
    for o, s in zip(obs, seen):
        if o['group'] != 'body': continue
        bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table(); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index not in s], context='FACES')
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS'); bm.to_mesh(o.data); bm.free()
    for o in [o for o in obs if not len(o.data.polygons)]: obs.remove(o); bpy.data.objects.remove(o)
    culled = {o.name: tri(o) for o in obs}; total = sum(culled.values()); floors = FAR if far else NEAR
    floor = {}
    for k in CORNERS:                                        # each wheel to about WHEEL: its tyre whole, the rest shares what is left
        ws = [o for o in obs if o['group'] == 'wheel_' + k]; tyre = sum(culled[o.name] for o in ws if o.name.endswith('.Wheel')); rest = sum(culled[o.name] for o in ws) - tyre
        for o in ws: floor[o.name] = 1.0 if o.name.endswith('.Wheel') else min(1.0, max(0.05, (WHEEL - tyre) / max(1, rest)))
    for o in obs:
        if o.name not in floor:
            c = culled[o.name]; mat = o.name.split('.')[-1]
            floor[o.name] = floors.get(mat, 1.0 if (c < SMALL and not far) else 0.5 if c < SMALL else 0.0)
    fixed = sum(culled[n] * f for n, f in floor.items() if f > 0); free = sum(culled[n] for n, f in floor.items() if f == 0)
    r = max(0.02, (target - fixed) / max(1, free)); flipped = 0
    for o in obs:
        k = floor[o.name] or r
        if k < 1:
            from mathutils.bvhtree import BVHTree
            nh = held(o) if not far else 0; orig = BVHTree.FromPolygons([v.co.copy() for v in o.data.vertices], [list(p.vertices) for p in o.data.polygons])
            bpy.context.view_layer.objects.active = o; m = o.modifiers.new('lod', 'DECIMATE'); m.ratio = k; m.use_collapse_triangulate = True
            if not far: m.vertex_group = 'held'; m.invert_vertex_group = True
            bpy.ops.object.modifier_apply(modifier='lod'); o.vertex_groups.clear()
            flipped += unflip(o, orig)
    glass_out(obs); inward_out(obs); radiator(obs); shells(obs)      # (the radiator and the shells after the cull: one big face seen only through slots would be culled)
    if not far: rig(obs, H)
    # (the far layer, seen beyond 20 m, holds no edges: they kept it at 52k)
    print('outside: %d -> seen %d -> %d triangles in %d objects (the rest at %.3f); %d faces turned back after thinning' % (before, total, sum(tri(o) for o in obs), len(obs), r, flipped))
    for o in sorted(obs, key=lambda o: -culled[o.name])[:12]: print('  %-26s seen %6d -> %6d' % (o.name, culled[o.name], tri(o)))
    for k in CORNERS: print('  wheel_%s %d triangles, corner_%s %d' % (k, sum(tri(o) for o in obs if o['group'] == 'wheel_' + k), k, sum(tri(o) for o in obs if o['group'] == 'corner_' + k)))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    main(a[0], a[1], int(a[2]), len(a) > 3 and a[3] == 'far')
