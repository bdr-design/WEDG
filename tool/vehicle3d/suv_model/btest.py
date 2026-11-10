"""Quick look at the back alone: the cached bare body + the windows + the rear parts, mapped to the real frame.
Run: blendenv/bin/python btest.py <out.blend> [norear] [front]"""
import bpy, sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'suv'))
OUT = [a for a in sys.argv if a.endswith('.blend')][-1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'out', 'body.blend'))
import mats, greenhouse as GH, fascia_rear as FR, realframe as RF
shell = bpy.data.objects['body']
if not len(shell.data.materials): shell.data.materials.append(mats.paint())
print('shell materials', [m.name if m else None for m in shell.data.materials])
trim = mats.M('trim_black', (0.018, 0.018, 0.019), rough=0.55)
glass_m = mats.M('glass', (0.012, 0.014, 0.017), rough=0.03, alpha=0.55)
black_gloss = mats.M('black_gloss', (0.006, 0.006, 0.007), rough=0.08, coat=1.0); chrome = mats.M('chrome', (0.9, 0.9, 0.92), metal=1.0, rough=0.06)
MAT = mats.fascia(chrome, trim, black_gloss)
glass, strips = GH.build(shell, glass_m, black_gloss, trim, chrome)
if 'front' in sys.argv: import fascia_front as FF; FF.front(shell, MAT)
if 'norear' not in sys.argv: FR.rear(shell, MAT)
for o in list(bpy.data.objects):
    if o.type == 'MESH': RF.warp_object(o)
import bmesh
for o in bpy.data.objects:
    if o.type == 'MESH' and not o.name.startswith('window_chrome'): print(f'{o.name:28s} tris {sum(len(p.vertices) - 2 for p in o.data.polygons):6d}')
bm = bmesh.new(); bm.from_mesh(shell.data); print('shell non-manifold edges', sum(1 for e in bm.edges if not e.is_manifold)); bm.free()
import body; print('shell sharp edges', body.crisp(shell))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
