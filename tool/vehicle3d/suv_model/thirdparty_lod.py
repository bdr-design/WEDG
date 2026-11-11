"""The private car's outside in game layers (the owner's decision of 10 Nov: layered detail; see thirdparty/README.md).
thirdparty_lod.py <outside.blend> <out.blend> <target triangles> [far]
1. The model's hundreds of parts become one object per material (one draw each), their shading kept. In the near
   layer the wheels are apart, for the suspension and the steering: per corner, corner_XX (at the hub; it rises and
   falls with the suspension and the front ones steer) holds the brake caliper and wheel_XX (at the hub too; it spins)
   holds the tyre, the rim, the disc and the wheel nuts.
2. Faces nobody sees go: lod_ext.py's test from its ring of eyes round the car and above it (not from the seats: the
   glass is dark, and inside the interior's own file covers what the seats see). The wheels keep every face (they
   turn: a face hidden at one turn shows at the next).
3. What is left is thinned toward the target (collapse decimation), each material with its least share: the lamps
   and the tyres' texture keep more (they read close up), the plates are kept whole; each wheel to about WHEEL."""
import bpy, bmesh, sys, os, numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lod_ext as LE

NEAR = {'plate': 1.0, 'Wheel': 1.0, 'Textures_A': 1.0, 'Front_Light': 0.6, 'Light_glass': 0.5, 'Light_Red_Back': 0.6, 'GlassRed': 0.6,
        'Light_White_Back': 0.5, 'BackSpotLight': 0.5, 'SpotLight': 0.5, 'ClearGlass': 0.35, 'Mirror': 0.5, 'RearMirror_Light': 0.5}
FAR = {'plate': 1.0, 'Wheel': 0.5, 'Textures_A': 0.5}
SMALL = 300                    # a material with fewer seen triangles is kept whole (near) or halved (far)
WHEEL = 2200                   # a near wheel's triangles (tyre, rim, disc, nuts); its tyre (672, textured) kept whole
CORNERS = ('FL', 'FR', 'RL', 'RR')


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
        if lo[1] >= y0 - 0.01 and hi[1] <= y1 + 0.01 and (r < 0.02 or (s.max() < 0.05 and r < 0.1)): return 'wheel_' + k      # round about the axle (or a wheel nut), within the tyre's width
        if r < 0.3 and s.max() < 0.35 and abs(c[1] - h[1]) < 0.1: return 'corner_' + k                                           # the caliper, behind the disc
    return 'body'


def by_material(split):
    obs = [o for o in bpy.data.objects if o.type == 'MESH' and len(o.data.polygons)]
    bpy.context.view_layer.update()
    for o in obs: mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw          # (the glTF's empties carry the parts' placing: kept before they go)
    for o in [o for o in bpy.data.objects if o.type != 'MESH' or not len(o.data.polygons)]: bpy.data.objects.remove(o)
    H = hubs(); groups = {}
    for o in obs: groups.setdefault(group_of(o, H) if split else 'body', []).append(o)
    out = []
    for g, members in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in members: o.data = o.data.copy() if o.data.users > 1 else o.data; o.select_set(True)
        bpy.context.view_layer.objects.active = members[0]; bpy.ops.object.transform_apply(location=True, rotation=True, scale=True); bpy.ops.object.join()
        ob = bpy.context.view_layer.objects.active; before = set(bpy.data.objects)
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
        for o in [ob] + [o for o in bpy.data.objects if o not in before]:
            used = {p.material_index for p in o.data.polygons}
            if not used: bpy.data.objects.remove(o); continue
            m = o.material_slots[used.pop()].material; o.name = (m.name if m else 'none') if g == 'body' else g + '.' + (m.name if m else 'none'); o.data.name = o.name
            while len(o.material_slots) > 1:          # (one slot left: the material it is)
                i = next(i for i, s in enumerate(o.material_slots) if s.material != m); o.active_material_index = i; bpy.context.view_layer.objects.active = o; bpy.ops.object.material_slot_remove()
            o['group'] = g; out.append(o)
    return out, H


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
    tri = lambda o: (o.data.calc_loop_triangles(), len(o.data.loop_triangles))[1]
    before = sum(tri(o) for o in obs)
    for o in obs:
        bpy.context.view_layer.objects.active = o; m = o.modifiers.new('tri', 'TRIANGULATE'); m.keep_custom_normals = True; bpy.ops.object.modifier_apply(modifier='tri')
    seen = LE.visible(obs, LE.eyes()[:-4])                 # (lod_ext's last four eyes are the seats')
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
    r = max(0.02, (target - fixed) / max(1, free))
    for o in obs:
        k = floor[o.name] or r
        if k < 1:
            bpy.context.view_layer.objects.active = o; m = o.modifiers.new('lod', 'DECIMATE'); m.ratio = k; m.use_collapse_triangulate = True; bpy.ops.object.modifier_apply(modifier='lod')
    if not far: rig(obs, H)
    print('outside: %d -> seen %d -> %d triangles in %d objects (the rest at %.3f)' % (before, total, sum(tri(o) for o in obs), len(obs), r))
    for o in sorted(obs, key=lambda o: -culled[o.name])[:12]: print('  %-26s seen %6d -> %6d' % (o.name, culled[o.name], tri(o)))
    for k in CORNERS: print('  wheel_%s %d triangles, corner_%s %d' % (k, sum(tri(o) for o in obs if o['group'] == 'wheel_' + k), k, sum(tri(o) for o in obs if o['group'] == 'corner_' + k)))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    main(a[0], a[1], int(a[2]), len(a) > 3 and a[3] == 'far')
