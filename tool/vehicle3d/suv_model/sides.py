"""Step 5: the flanks. Door shut lines (grooves cut into the shell), door handles, the running boards, the fuel flap
and the black lower cladding, at the positions measured on the side photo (01_left)."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector
XF = 2.498
import realframe as RF
# Door shut lines and handles in the real frame, measured on the real side photo (Wikimedia Commons, see DIMENSIONS.md)
# as distances behind the front hub: the front door's front edge 0.617, the B-pillar seam 1.692, the rear door's rear
# edge 2.738; the door bottoms 0.455 m up; handle centres 1.522 and 2.473, 0.27 m long.
FRONT_EDGE_X = RF.AXLE_X[0] - 0.617
B_SEAM_X = RF.AXLE_X[0] - 1.692
REAR_EDGE_X = RF.AXLE_X[0] - 2.738
DOOR_BOTTOM_Z, BELT_Z = 0.455, 1.30
HANDLES = ((RF.AXLE_X[0] - 1.522, 1.157), (RF.AXLE_X[0] - 2.473, 1.180))
FUEL_FLAP = (-1.645, -1.370, 1.112, 1.262)   # left rear quarter, x0 x1 z0 z1 (both photos agree within 2 cm)

def activate(o):
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o

def _ribbon(shell, pts, s, mat, name, width=0.0042, lift=0.0012):
    """A thin dark band laid on the shell along pts [(x, z)] on side s: a shut line that leaves the shell untouched."""
    hits = []
    for x, z in pts:
        r = shell.ray_cast(Vector((x, s * 2.0, z)), Vector((0, -s, 0)))
        if r[0] and abs(r[1].y) > 0.6: hits.append((r[1].copy(), r[2].normalized()))
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

def seams(shell, groove, flare_r=0.535):
    """Shut lines round both doors (real frame, after the arches are cut): the front door's front edge, the B-pillar
    seam, the rear door's rear edge down to the rear flare and round it, and the door bottoms."""
    import ext_parts as EP
    rx, cz = RF.AXLE_X[1], EP.ARCH_CZ
    z_meet = cz + math.sqrt(max(flare_r ** 2 - (REAR_EDGE_X - rx) ** 2, 0))
    th0 = math.atan2(z_meet - cz, REAR_EDGE_X - rx); th1 = math.asin((DOOR_BOTTOM_Z - cz) / flare_r)
    arc = [(rx + flare_r * math.cos(t), cz + flare_r * math.sin(t)) for t in np.linspace(th0, th1, 24)]
    x_arc_end = arc[-1][0]
    out = []
    for s in (1, -1):
        for k, pts in enumerate((_line((FRONT_EDGE_X, BELT_Z), (FRONT_EDGE_X, DOOR_BOTTOM_Z)),
                                 _line((B_SEAM_X, BELT_Z + 0.01), (B_SEAM_X, DOOR_BOTTOM_Z)),
                                 _line((REAR_EDGE_X, BELT_Z + 0.03), (REAR_EDGE_X, z_meet)) + arc,
                                 _line((FRONT_EDGE_X, DOOR_BOTTOM_Z), (x_arc_end, DOOR_BOTTOM_Z)))):
            o = _ribbon(shell, pts, s, groove, f'seam{k}_{"L" if s > 0 else "R"}')
            if o: out.append(o)
    # the fuel flap, left side only
    x0, x1, z0, z1 = FUEL_FLAP; r = 0.02; ring = []
    for cx, cz2, a0 in ((x1 - r, z1 - r, 0), (x0 + r, z1 - r, 90), (x0 + r, z0 + r, 180), (x1 - r, z0 + r, 270)):
        ring += [(cx + r * math.cos(math.radians(a)), cz2 + r * math.sin(math.radians(a))) for a in np.linspace(a0, a0 + 90, 5)]
    ring.append(ring[0])
    dense = []
    for i in range(len(ring) - 1): dense += _line(ring[i], ring[i + 1], 0.01)[:-1]
    dense.append(ring[0])
    o = _ribbon(shell, dense, 1, groove, 'fuel_flap_line', width=0.003)
    if o: out.append(o)
    return out

def handles(shell, chrome, black):
    """Pull handles at the measured centres: a gloss-black bar 0.27 m long with a chrome top strip, standing 12 mm proud."""
    out = []
    for x, z in HANDLES:
        for s in (1, -1):
            r = shell.ray_cast(Vector((x, s * 2.0, z)), Vector((0, -s, 0)))
            if not r[0]: continue
            loc, nrm = r[1], r[2]
            bpy.ops.mesh.primitive_cube_add(size=1, location=loc + nrm * 0.012); h = bpy.context.active_object
            h.scale = (0.27, 0.022, 0.042); bpy.ops.object.transform_apply(scale=True)
            m = h.modifiers.new('bv', 'BEVEL'); m.width = 0.012; m.segments = 3; bpy.ops.object.modifier_apply(modifier='bv')
            h.data.materials.append(black); h.data.materials.append(chrome)
            for p in h.data.polygons:
                p.use_smooth = True
                if p.center.z > loc.z + 0.012 and p.normal.z > 0.3: p.material_index = 1
            out.append(h)
    return out
def running_boards(black, silver):
    out = []
    for s in (1, -1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(XF - 2.64, s * 0.88, 0.355)); b = bpy.context.active_object
        b.scale = (2.0, 0.14, 0.035); bpy.ops.object.transform_apply(scale=True)
        m = b.modifiers.new('bv', 'BEVEL'); m.width = 0.015; m.segments = 2; bpy.ops.object.modifier_apply(modifier='bv')
        b.data.materials.append(black); b.data.materials.append(silver)
        for p in b.data.polygons:
            p.use_smooth = True
            if p.normal.y * s > 0.7: p.material_index = 1          # the outer edge is a silver strip
        out.append(b)
    return out
