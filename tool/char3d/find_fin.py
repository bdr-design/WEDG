import bpy, sys, numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
rig = bpy.data.objects['rig']; sc = bpy.context.scene
rig.animation_data.action = bpy.data.actions['run']; sc.frame_set(10)
ob = bpy.data.objects['thobe']; dg = bpy.context.evaluated_depsgraph_get()
ev = ob.evaluated_get(dg); me = ev.to_mesh()
P = np.array([v.co[:] for v in me.vertices]); R = np.array([v.co[:] for v in ob.data.vertices])
E = np.array([e.vertices[:] for e in ob.data.edges])
l0 = np.linalg.norm(R[E[:, 0]] - R[E[:, 1]], axis=1); l1 = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
st = l1 / np.maximum(l0, 1e-5); bad = np.argsort(-st)[:12]
gn = [g.name for g in ob.vertex_groups]
for e in bad[:8]:
    for vi in E[e]:
        v = ob.data.vertices[vi]
        print(round(st[e], 1), vi, np.round(R[vi], 3), {gn[g.group]: round(g.weight, 2) for g in v.groups})
