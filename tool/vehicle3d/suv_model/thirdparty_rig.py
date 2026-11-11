"""The private car's moving parts and markers for the game (design/prototype3d/play.js reads them by name).
thirdparty_rig.py cabin <cabin.blend> <out.blend>
    'steering': the steering wheel (rim, spokes, pad, switches) as its own object, its local x the column's axis
    (pointing at the driver, so a positive turn is a turn to the left as the driver sees it), its origin on that axis
    at the pad; 'doorcard_FL': the driver's door's trim under an empty at the door's hinge (it swings with door_FL);
    everything under one empty 'interior' (loaded when the player comes to the car).
thirdparty_rig.py outside <near.blend> <out.blend>
    'door_FL': the driver's door's parts (thirdparty_lod.py's door_FL.*) under an empty at its hinge.
    'eye' and 'eye_look': the seated driver's eye in this model (EYE) and a point 6 m ahead of it.
The column's axis is measured, not assumed: the normal of the rim's plane, fitted to the rim alone."""
import bpy, sys, os, numpy as np
from mathutils import Vector, Matrix
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'interior'))

HINGE_FL = Vector((0.867, 0.953, 0.849))      # the driver's door's hinge line (vertical through here): the model's own pivot for the door (its FrontLeft_Door empty), 3 to 7 cm behind the door's front edge on its skin
PAD = Vector((0.417, 0.425, 1.259))          # the pad's middle: the emblem's (the model's polySurface469) box centre, in the car's frame
NEAR, RIM, DISC, TUBE = 0.23, (0.155, 0.215), (-0.14, 0.07), 0.035
AXIS0 = (-0.908, 0.001, 0.420)             # the column's axis to start from (a torus fitted to the rim's leather in review: 24.8 degrees from level)
EYE = Vector((-0.01, 0.425, 1.56))        # the seated driver's eye in this model: about 14 cm ahead of its headrest's face (x -0.148), on the seat's middle line (y 0.425)     # candidates within NEAR of the pad; the rim's radii; the wheel's depth along the axis (behind, in front of the pad)


def cabin(src, out):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src)); o = bpy.data.objects['tp_cabin']; me = o.data
    V = np.array([v.co[:] for v in me.vertices]); E = np.array([e.vertices[:] for e in me.edges]); nv = len(V)
    k, lab = connected_components(coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(nv, nv)), directed=False)
    P = np.array(PAD[:])
    far = np.zeros(k); np.maximum.at(far, lab, np.linalg.norm(V - P, axis=1))
    cand = far[lab] < NEAR
    # the rim alone: from a first axis, the points within a ring about it (RIM radii, TUBE of its plane), their plane's
    # normal and their middle; again, five times (a plane through a shell round the pad took spokes and switches with
    # the rim, tilting the axis by 11 degrees and moving with every rebuild)
    n, c0 = np.array(AXIS0), P.copy()
    for _ in range(5):
        d = (V - c0) @ n; rad = np.linalg.norm((V - c0) - np.outer(d, n), axis=1)
        rim = V[cand & (np.abs(d) < TUBE) & (rad > RIM[0]) & (rad < RIM[1])]
        c0 = rim.mean(0); n = np.linalg.svd(rim - c0)[2][2]
        if n[0] > 0: n = -n                                                 # toward the driver
    P = c0
    d = (V - P) @ n; rad = np.linalg.norm((V - P) - np.outer(d, n), axis=1)
    inside = (rad < RIM[1] + 0.01) & (d > DISC[0]) & (d < DISC[1])
    ok = np.ones(k, bool); np.logical_and.at(ok, lab, inside); ok &= np.bincount(lab, minlength=k) > 0
    sel = ok[lab] & cand
    for v in me.vertices: v.select = bool(sel[v.index])
    for e in me.edges: e.select = bool(sel[e.vertices[0]] and sel[e.vertices[1]])
    for p in me.polygons: p.select = all(sel[i] for i in p.vertices)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    st = next(x for x in bpy.data.objects if x.type == 'MESH' and x != o); st.name = st.data.name = 'steering'
    X = Vector(n); Z = Vector((0, 0, 1)); Z = (Z - X * Z.dot(X)).normalized(); Y = Z.cross(X)
    origin = Vector(c0)
    M = Matrix(((X.x, Y.x, Z.x, origin.x), (X.y, Y.y, Z.y, origin.y), (X.z, Y.z, Z.z, origin.z), (0, 0, 0, 1)))
    st.data.transform(M.inverted()); st.matrix_world = M
    root = bpy.data.objects.new('interior', None); bpy.context.collection.objects.link(root)
    for x in (o, st): x.parent = root
    dc = bpy.data.objects.get('tp_doorcard')
    if dc: hang(dc, 'doorcard_FL', root)
    o.name = o.data.name = 'cabin'
    st.data.calc_loop_triangles()
    tilt = np.degrees(np.arcsin(abs(n[2])))
    o.data.calc_loop_triangles()
    print('cabin %d triangles; steering: %d loose parts, %d triangles; column axis (%.3f, %.3f, %.3f), %.1f degrees from level; rim fitted on %d points'
          % (len(o.data.loop_triangles), len(np.unique(lab[sel])), len(st.data.loop_triangles), *n, tilt, len(rim)))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))


def hang(ob, name, parent=None):
    """ob under a new empty `name` at the driver's door's hinge, its mesh about the hinge (the game swings the empty)."""
    e = bpy.data.objects.new(name, None); e.location = HINGE_FL; bpy.context.collection.objects.link(e); e.parent = parent
    ob.data.transform(Matrix.Translation(-HINGE_FL)); ob.matrix_world = Matrix.Identity(4); ob.parent = e; ob.location = (0, 0, 0)
    return e


def outside(src, out):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
    door = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('door_FL.')]
    if door:
        e = bpy.data.objects.new('door_FL', None); e.location = HINGE_FL; bpy.context.collection.objects.link(e)
        for o in door: o.data.transform(o.matrix_world); o.data.transform(Matrix.Translation(-HINGE_FL)); o.matrix_world = Matrix.Identity(4); o.parent = e
        print('door_FL: %d parts' % len(door))
    eye = EYE
    for name, at in (('eye', eye), ('eye_look', eye + Vector((6.0, 0.0, -0.35)))):
        e = bpy.data.objects.new(name, None); e.location = at; bpy.context.collection.objects.link(e)
    print('eye at (%.3f, %.3f, %.3f)' % tuple(eye))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[-3:]
    {'cabin': cabin, 'outside': outside}[a[0]](a[1], a[2])
