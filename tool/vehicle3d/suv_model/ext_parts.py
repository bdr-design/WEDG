"""Steps 2-5 parts measured on the photos: mirrors, roof rails, wheel arches (cut and flared).
All in the model frame (x forward, y left, z up), metres."""
import bpy, bmesh, math, numpy as np
from mathutils import Vector
import wheels as WH

def activate(o):
    for x in bpy.context.selected_objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o

def rbox(name, centre, size, bevel, mat, segments=3, subdiv=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=centre); o = bpy.context.active_object; o.name = name
    o.scale = size; bpy.ops.object.transform_apply(scale=True)
    if bevel:
        m = o.modifiers.new('bv', 'BEVEL'); m.width = bevel; m.segments = segments; m.limit_method = 'NONE'; bpy.ops.object.modifier_apply(modifier='bv')
    if subdiv:
        m = o.modifiers.new('sd', 'SUBSURF'); m.levels = subdiv; bpy.ops.object.modifier_apply(modifier='sd')
    o.data.materials.append(mat)
    for p in o.data.polygons: p.use_smooth = True
    return o

def join(objs, name):
    activate(objs[0])
    for o in objs: o.select_set(True)
    bpy.ops.object.join(); o = bpy.context.active_object; o.name = name; return o

def mirrors(paint, glass, black):
    """Housing 0.30 m long, out to 1.10 m from the centre line, 1.34-1.58 m up (front and top photos), on an arm from the
    door's front corner; the mirror glass faces back."""
    out = []
    for s in (1, -1):
        h = rbox(f'mirror_housing{s}', (0.66, s * 1.005, 1.46), (0.26, 0.19, 0.22), 0.06, paint, subdiv=1)
        # taper the housing toward the door and toward the front
        for v in h.data.vertices:
            t = (abs(v.co.y) - 0.91) / 0.19
            v.co.z = 1.46 + (v.co.z - 1.46) * (0.82 + 0.18 * t)
            if v.co.x > 0.66: v.co.y = s * (0.91 + (abs(v.co.y) - 0.91) * (1 - 0.25 * (v.co.x - 0.66) / 0.13))
        g = rbox(f'mirror_glass{s}', (0.528, s * 1.01, 1.46), (0.012, 0.165, 0.185), 0.03, glass)
        arm = rbox(f'mirror_arm{s}', (0.70, s * 0.93, 1.37), (0.16, 0.07, 0.05), 0.02, black)
        out.append(join([h, g, arm], f'mirror_{"L" if s > 0 else "R"}'))
    return out

def roof_rails(black):
    """Bars 1.98-2.02 m up from x 0.42 to -1.86, centred 0.545 m out, on four posts each side (side and front photos)."""
    out = []
    for s in (1, -1):
        pts = np.linspace(0.42, -1.86, 40)
        V, F = [], []
        for x in pts:
            # the bar dips to the roof at both ends
            e = min(1.0, (0.42 - x) / 0.18, (x + 1.86) / 0.18); zc = 1.958 + 0.042 * e ** 0.6
            for (dy, dz) in ((-0.022, -0.016), (0.022, -0.016), (0.016, 0.018), (-0.016, 0.018)):
                V.append((x, s * (0.545 + dy), zc + dz * max(0.4, e)))
        n = 4
        for i in range(len(pts) - 1):
            for j in range(n):
                a = i * n + j; F.append([a, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j])
        F.append([0, 1, 2, 3]); k = (len(pts) - 1) * n; F.append([k + 3, k + 2, k + 1, k])
        me = bpy.data.meshes.new(f'rail{s}'); me.from_pydata(V, [], F); me.update()
        o = bpy.data.objects.new(f'roof_rail_{"L" if s > 0 else "R"}', me); bpy.context.collection.objects.link(o)
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
        me.materials.append(black)
        for p in me.polygons: p.use_smooth = True
        posts = [rbox(f'post{s}{i}', (x, s * 0.545, 1.966), (0.07, 0.04, 0.03), 0.01, black) for i, x in enumerate((0.25, -0.45, -1.15, -1.72))]
        out.append(join([o] + posts, o.name))
    return out

ARCH_CZ, ARCH_R = 0.45, 0.476   # the real arch: its top edge 0.926 m up, 0.47 m either side of the hub at hub height

def arches(shell, paint, liner, flare_mat):
    """Cut each wheel opening from the shell round the real axle (a circle 0.476 m round a point 7 cm above the hub, as
    measured on the real side photo), line it, and add a flare round its upper edge. Runs in the real frame."""
    cutters = []
    for x in WH.AXLE_X:
        for s in (1, -1):
            bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=ARCH_R, depth=0.70, location=(x, s * (0.60 + 0.35), ARCH_CZ), rotation=(math.pi / 2, 0, 0))
            cutters.append(bpy.context.active_object)
    cut = join(cutters, 'arch_cutters'); cut.data.materials.append(liner)
    activate(shell)
    mo = shell.modifiers.new('arches', 'BOOLEAN'); mo.operation = 'DIFFERENCE'; mo.object = cut; mo.solver = 'EXACT'
    bpy.ops.object.modifier_apply(modifier='arches'); bpy.data.objects.remove(cut)
    flares = []
    for x in WH.AXLE_X:
        for s in (1, -1):
            # a half torus over the opening, flattened against the body side
            bpy.ops.mesh.primitive_torus_add(major_radius=ARCH_R + 0.02, minor_radius=0.034, major_segments=48, minor_segments=10,
                                             location=(x, s * 0.97, ARCH_CZ), rotation=(math.pi / 2, 0, 0))   # outer edge at 0.99: the spec width
            t = bpy.context.active_object; bpy.ops.object.transform_apply(location=False, rotation=True)
            bm = bmesh.new(); bm.from_mesh(t.data)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.10], context='VERTS')      # only over the top
            bm.to_mesh(t.data); bm.free()
            t.scale.y = 0.6; bpy.ops.object.transform_apply(scale=True)
            t.data.materials.append(flare_mat)
            for p in t.data.polygons: p.use_smooth = True
            flares.append(t)
    return join(flares, 'arch_flares')
