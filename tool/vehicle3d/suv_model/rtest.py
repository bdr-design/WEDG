"""Quick look at the roof alone: the cached bare body + the windows, mapped to the real frame, + the glass roof.
Run: blendenv/bin/python rtest.py <out.blend>"""
import bpy, sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'suv'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'out', 'body.blend'))
import mats, greenhouse as GH, realframe as RF, roof as RO, ext_parts as EP
shell = bpy.data.objects['body']
paint = mats.paint(); shell.data.materials.clear(); shell.data.materials.append(paint)
trim = mats.M('trim_black', (0.018, 0.018, 0.019), rough=0.55)
black_gloss = mats.M('black_gloss', (0.006, 0.006, 0.007), rough=0.08, coat=1.0); chrome = mats.M('chrome', (0.9, 0.9, 0.92), metal=1.0, rough=0.06)
glass_m = mats.M('glass', (0.012, 0.014, 0.017), rough=0.03, alpha=0.55)
GH.build(shell, glass_m, black_gloss, trim, chrome)
for o in list(bpy.data.objects):
    if o.type == 'MESH': RF.warp_object(o)
t = time.time(); RO.glass_roof(shell, glass_m, trim); print('roof seconds %.1f' % (time.time() - t))
if 'rails' in sys.argv: EP.roof_rails(shell, trim); EP.antenna(shell, paint)
import bmesh
for o in bpy.data.objects:
    if o.type == 'MESH': print(f'{o.name:28s} tris {sum(len(p.vertices) - 2 for p in o.data.polygons):6d}')
bpy.ops.wm.save_as_mainfile(filepath=[a for a in sys.argv if a.endswith('.blend')][-1])
