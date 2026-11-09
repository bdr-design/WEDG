"""Quick look at the front alone: the cached bare body + the front parts, mapped to the real frame.
Run: blendenv/bin/python ftest.py <out.blend>"""
import bpy, sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'suv'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'out', 'body.blend'))
import mats, fascia_front as FF, realframe as RF
shell = bpy.data.objects['body']
trim = mats.M('trim_black', (0.018, 0.018, 0.019), rough=0.55)
black_gloss = mats.M('black_gloss', (0.006, 0.006, 0.007), rough=0.08, coat=1.0); chrome = mats.M('chrome', (0.9, 0.9, 0.92), metal=1.0, rough=0.06)
MAT = mats.fascia(chrome, trim, black_gloss)
FF.front(shell, MAT)
for o in list(bpy.data.objects):
    if o.type == 'MESH': RF.warp_object(o)
import bmesh
for o in bpy.data.objects:
    if o.type == 'MESH': print(f'{o.name:28s} tris {sum(len(p.vertices) - 2 for p in o.data.polygons):6d}')
bm = bmesh.new(); bm.from_mesh(shell.data); print('shell non-manifold edges', sum(1 for e in bm.edges if not e.is_manifold)); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1])
