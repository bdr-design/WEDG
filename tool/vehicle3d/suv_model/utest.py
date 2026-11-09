"""Quick look at the underside: the cached bare body + windows, mapped to the real frame, + sills, wheel wells,
wheels and the underbody. Run: blendenv/bin/python utest.py <out.blend>"""
import bpy, sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'suv'))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'out', 'body.blend'))
import mats, greenhouse as GH, realframe as RF, ext_parts as EP, sides as SD, wheels, underbody as UB, suv_exterior as SE
shell = bpy.data.objects['body']
paint = mats.paint(); shell.data.materials.clear(); shell.data.materials.append(paint)
trim = mats.M('trim_black', (0.018, 0.018, 0.019), rough=0.55)
black_gloss = mats.M('black_gloss', (0.006, 0.006, 0.007), rough=0.08, coat=1.0); chrome = mats.M('chrome', (0.9, 0.9, 0.92), metal=1.0, rough=0.06)
glass_m = mats.M('glass', (0.012, 0.014, 0.017), rough=0.03, alpha=0.55); liner = mats.M('arch_liner', (0.012, 0.012, 0.013), rough=0.9)
GH.build(shell, glass_m, black_gloss, trim, chrome)
for o in list(bpy.data.objects):
    if o.type == 'MESH': RF.warp_object(o)
SD.sill(shell, trim); EP.arches(shell, paint, liner, paint)
out = [a for a in sys.argv if a.endswith('.blend')][-1]
wheels.build(SE.tyre_material(SE.tyre_maps(os.path.join(os.path.dirname(out), 'tex'))))
t = time.time(); UB.build(shell, mats.M('underbody', (0.016, 0.016, 0.017), rough=0.85)); print('underbody seconds %.1f' % (time.time() - t))
for o in bpy.data.objects:
    if o.type == 'MESH': print(f'{o.name:28s} tris {sum(len(p.vertices) - 2 for p in o.data.polygons):6d}')
bpy.ops.wm.save_as_mainfile(filepath=out)
