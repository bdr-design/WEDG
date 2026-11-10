"""Step 5: the flanks, in the real frame (after the warp): the black sill under the doors with the side steps on it,
the door shut lines, the door handles and the fuel flap. Positions along the car and the door heights come from the
real side photo; the step's heights come from the owner's side photo, because the real photo is a GR Sport, whose
steps are a different part (see DIMENSIONS.md)."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector
import realframe as RF

# Distances behind the front hub on the real side photo: the front door's front edge 0.617, the B-pillar seam 1.692,
# the rear door's rear edge 2.738. Heights at 4.17 mm/px: the door bottoms 0.429, the window foot 1.253, the handle
# centres 1.130 and 1.152 (the handles are 0.27 m long, centres 1.522 and 2.473 behind the front hub).
FRONT_EDGE_X = RF.AXLE_X[0] - 0.617
B_SEAM_X = RF.AXLE_X[0] - 1.692
REAR_EDGE_X = RF.AXLE_X[0] - 2.738
DOOR_BOTTOM_Z, BELT_Z = 0.429, 1.253
HANDLES = ((RF.AXLE_X[0] - 1.522, 1.130), (RF.AXLE_X[0] - 2.473, 1.152))
FUEL_FLAP = (-1.645, -1.370, 1.086, 1.232)   # left rear quarter, x0 x1 z0 z1 (both photos agree within 2 cm)
# The side step: 0.599 to 2.363 m behind the front hub on the real photo (the owner's photo, mapped, gives 0.588 to
# 2.335). Heights from the owner's photo through realframe.z_real: the bottom 0.303, the top of the silver outer face
# 0.350, the tread's inner edge 0.377. Under the doors the body steps in 6 cm to a black sill that carries the step;
# the step's outer edge is flush with the door skin.
STEP_X = (RF.AXLE_X[0] - 0.599, RF.AXLE_X[0] - 2.363)
STEP_Z = (0.303, 0.350, 0.377)
STEP_CLEAR = 0.020                    # the step stops this far ahead of the rear opening (the owner's photo's opening is 20 mm
                                      # further forward than the real photo's step end, which stood 20 mm short of the real opening)
SILL_Y, STEP_Y = 0.905, 0.962

def activate(o):
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o

def sill(shell, black):
    """Under the door bottoms the shell steps in to a black sill between the two axles. Runs before the wheel openings
    are cut, so the cut removes the ends of the step-in at the axles."""
    me = shell.data
    if black.name not in me.materials: me.materials.append(black)
    bi = me.materials.find(black.name); xa, xb = RF.AXLE_X[1], RF.AXLE_X[0]; zt = DOOR_BOTTOM_Z; zc = zt - 0.012
    bm = bmesh.new(); bm.from_mesh(me)
    for z in (zt, zc):
        fs = [f for f in bm.faces if abs(f.calc_center_median().y) > 0.6 and xa - 0.3 < f.calc_center_median().x < xb + 0.3
              and f.calc_center_median().z < 0.8]
        geom = fs + list({e for f in fs for e in f.edges}) + list({v for f in fs for v in f.verts})
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1), dist=1e-6)
    moved = 0
    for v in bm.verts:
        if xa < v.co.x < xb and abs(v.co.y) > SILL_Y and v.co.z <= zc + 1e-5: v.co.y = math.copysign(SILL_Y, v.co.y); moved += 1
    for f in bm.faces:
        c = f.calc_center_median()
        if xa < c.x < xb and abs(c.y) > 0.6 and c.z < zt: f.material_index = bi
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.to_mesh(me); bm.free(); me.update()
    print(f'sill: {moved} vertices stepped in to y {SILL_Y}')

def running_boards(black, silver):
    """The side steps: a swept section with a silver outer face and a black tread that rises toward the sill; the two
    ends are rounded in plan."""
    import ext_parts as EP
    out = []; x0, x1 = STEP_X; zb, ze, zi = STEP_Z
    x1 = max(x1, RF.AXLE_X[1] - EP.ARCH_PTS[1][0][0] + STEP_CLEAR)      # it ends short of the rear wheel opening
    xs = np.linspace(x0, x1, 72); yin = SILL_Y - 0.012; n = 8
    for s in (1, -1):
        V, F = [], []
        for x in xs:
            t = min(max(min(x0 - x, x - x1) / 0.07, 0.0), 1.0); e = math.sqrt(1 - (1 - t) ** 2)
            yo = SILL_Y + 0.004 + (STEP_Y - SILL_Y - 0.004) * e; c = min(0.016, 0.3 * (yo - yin))
            V += [(x, s * y, z) for y, z in ((yin, zb), (yo - c, zb), (yo - 0.25 * c, zb + 0.004), (yo, zb + 0.010), (yo, ze - 0.008),
                                             (yo - 0.25 * c, ze - 0.002), (yo - c, ze + 0.001), (yin, zi))]
        for i in range(len(xs) - 1):
            for j in range(n): F.append([i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j])
        k = (len(xs) - 1) * n; F += [list(range(n)), [k + j for j in reversed(range(n))]]
        me = bpy.data.meshes.new('side_step'); me.from_pydata(V, [], F); me.update()
        o = bpy.data.objects.new(f'side_step_{"L" if s > 0 else "R"}', me); bpy.context.collection.objects.link(o)
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
        me.materials.append(black); me.materials.append(silver)
        for p in me.polygons:
            p.use_smooth = len(p.vertices) == 4
            if p.normal.y * s > 0.7 and zb + 0.008 < p.center.z < ze - 0.006: p.material_index = 1
        out.append(o)
    return out

def _cast(targets, x, z, s):
    """The outermost surface among targets on side s at (x, z): the point and its outward normal."""
    best = None
    for o in targets:
        r = o.ray_cast(Vector((x, s * 2.0, z)), Vector((0, -s, 0)))
        if r[0] and abs(r[1].y) > 0.6 and (best is None or abs(r[1].y) > abs(best[0].y)):
            n = r[2].normalized(); best = (r[1].copy(), n if n.y * s > 0 else -n)
    return best

def _ribbon(targets, pts, s, mat, name, width=0.0042, lift=0.0012):
    """A thin dark band laid on the outermost of targets along pts [(x, z)] on side s: a shut line that leaves the
    surfaces untouched."""
    hits = [h for h in (_cast(targets, x, z, s) for x, z in pts) if h]
    if len(hits) < 2: return None
    V, F = [], []
    for i, (p, n) in enumerate(hits):
        q0 = hits[max(i - 1, 0)][0]; q1 = hits[min(i + 1, len(hits) - 1)][0]
        t = (q1 - q0).normalized(); side = n.cross(t).normalized()
        V += [p + n * lift + side * width / 2, p + n * lift - side * width / 2]
    for i in range(len(hits) - 1):
        a = 2 * i; F.append([a, a + 1, a + 3, a + 2])
    me = bpy.data.meshes.new(name); me.from_pydata([tuple(v) for v in V], [], F); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); me.materials.append(mat)
    bm = bmesh.new(); bm.from_mesh(me)
    for f in bm.faces:
        if f.normal.y * s < 0: f.normal_flip()
    bm.to_mesh(me); bm.free()
    return o

def _line(a, b, step=0.02):
    n = max(2, int(math.dist(a, b) / step) + 1)
    return [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for t in np.linspace(0, 1, n)]

def seams(shell, groove, flares=None):
    """Shut lines round both doors (after the openings are cut): the front door's front edge, the B-pillar seam, the
    rear door's rear edge, which on the real car runs straight down across the rear flare to the wheel opening (the
    front part of that flare is on the door), and the door bottoms, which end at the rear opening."""
    import ext_parts as EP
    targets = [shell] + ([flares] if flares else [])
    z_open = max(z for x, z in EP.arch_curve(1) if abs(x - REAR_EDGE_X) < 0.012)
    x_foot = RF.AXLE_X[1] - EP.ARCH_PTS[1][0][0]
    zd = DOOR_BOTTOM_Z + 0.002
    out = []
    for s in (1, -1):
        for k, pts in enumerate((_line((FRONT_EDGE_X, BELT_Z), (FRONT_EDGE_X, zd)),
                                 _line((B_SEAM_X, BELT_Z + 0.01), (B_SEAM_X, zd)),
                                 _line((REAR_EDGE_X, BELT_Z + 0.03), (REAR_EDGE_X, z_open + 0.004)),
                                 _line((FRONT_EDGE_X, zd), (x_foot + 0.004, zd)))):
            o = _ribbon(targets, pts, s, groove, f'seam{k}_{"L" if s > 0 else "R"}')
            if o: out.append(o)
    # the fuel flap, left side only
    x0, x1, z0, z1 = FUEL_FLAP; r = 0.02; ring = []
    for cx, cz2, a0 in ((x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180), (x1 - r, z0 + r, 270)):
        ring += [(cx + r * math.cos(math.radians(a)), cz2 + r * math.sin(math.radians(a))) for a in np.linspace(a0, a0 + 90, 5)]
    ring.append(ring[0])
    dense = []
    for i in range(len(ring) - 1): dense += _line(ring[i], ring[i + 1], 0.01)[:-1]
    dense.append(ring[0])
    o = _ribbon(targets, dense, 1, groove, 'fuel_flap_line', width=0.003)
    if o: out.append(o)
    print(f'seams: rear door edge runs down to the opening at {z_open:.3f}; door bottoms end at x {x_foot:.3f}')
    return out

def handles(shell, chrome, black):
    """Pull handles at the measured centres: a gloss-black bar 0.27 m long with a chrome top strip, standing 12 mm proud."""
    out = []
    for i, (x, z) in enumerate(HANDLES):
        for s in (1, -1):
            r = shell.ray_cast(Vector((x, s * 2.0, z)), Vector((0, -s, 0)))
            if not r[0]: continue
            loc, nrm = r[1], r[2]
            bpy.ops.mesh.primitive_cube_add(size=1, location=loc + nrm * 0.012); h = bpy.context.active_object
            h.scale = (0.27, 0.022, 0.042); bpy.ops.object.transform_apply(scale=True)
            h.name = h.data.name = f"handle_{'FR'[min(i, 1)]}_{'L' if s > 0 else 'R'}"
            # the bevel stays under the bar's half thickness (11 mm), or it folds into zero-area faces
            m = h.modifiers.new('bv', 'BEVEL'); m.width = 0.009; m.segments = 3; bpy.ops.object.modifier_apply(modifier='bv')
            h.data.materials.append(black); h.data.materials.append(chrome)
            for p in h.data.polygons:
                p.use_smooth = True
                if p.center.z > loc.z + 0.012 and p.normal.z > 0.3: p.material_index = 1
            out.append(h)
    return out
