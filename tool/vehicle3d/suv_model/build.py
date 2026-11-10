"""The SUV modelled from scratch in Blender: runs every step and writes the .blend.
Run: blendenv/bin/python build.py <out_dir> [render]"""
import bpy, sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path[1:1] = [os.path.join(HERE, '..'), os.path.join(HERE, '..', 'suv')]      # suv_exterior.py (the tyre's maps)
OUT = sys.argv[-2] if sys.argv[-1] == 'render' else sys.argv[-1]; RENDER = sys.argv[-1] == 'render'
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
import mats, body, wheels, suv_exterior as SE, greenhouse as GH, fascia_front as FF, fascia_rear as FR
import ext_parts as EP, sides as SD, realframe as RF, roof as RO, underbody as UB, tidy
M = mats.M
paint = mats.paint(); shell = body.build(); shell.data.materials.append(paint)
trim = M('trim_black', (0.018, 0.018, 0.019), rough=0.55); liner = M('liner', (0.012, 0.012, 0.012), rough=0.85)
mirror_glass = M('mirror_glass', (0.6, 0.62, 0.65), metal=1.0, rough=0.02)
# The owner's decision (10 Nov): the glass is blacked out all round (the full dark tint), so from outside it is a black
# mirror and nothing shows through it. It is opaque, which also spares the phone a blended layer on every pane.
glass_m = M('glass', (0.004, 0.0045, 0.006), rough=0.03, coat=1.0)
black_gloss = M('black_gloss', (0.006, 0.006, 0.007), rough=0.08, coat=1.0); chrome = M('chrome', (0.9, 0.9, 0.92), metal=1.0, rough=0.06)
MAT = mats.fascia(chrome, trim, black_gloss)
# 1. in the photo frame (traced on the owner's photos): the body, the windows, the front and rear parts, the mirrors
glass, strips = GH.build(shell, glass_m, black_gloss, trim, chrome)
FF.front(shell, MAT); FR.rear(shell, MAT)
EP.mirrors(paint, mirror_glass, trim)
# 2. map all of it to the real (spec sheet) frame
for o in list(bpy.data.objects):
    if o.type == 'MESH': RF.warp_object(o)
# 3. in the real frame (measured on the real car or placed by real dimensions): the glass roof, the roof rails and the
# antenna, the sill and the side steps, the wheel openings and flares round the real axles, the shut lines, the door
# handles, the wheels (the owner's photo's size), and under the floor the rear axle in its tunnel and the front suspension
RO.glass_roof(shell, glass_m, trim)
EP.roof_rails(shell, trim); EP.antenna(shell, paint)
SD.sill(shell, trim)
flares = EP.arches(shell, paint, liner, paint)
SD.running_boards(trim, MAT['silver'])
groove = MAT['groove']
SD.seams(shell, groove, flares); SD.handles(shell, chrome, black_gloss)
tyre_mat = SE.tyre_material(SE.tyre_maps(os.path.join(OUT, 'tex')))
ws = wheels.build(tyre_mat)
UB.build(shell, M('underbody', (0.016, 0.016, 0.017), rough=0.85))
tidy.tidy_all()
print('shell sharp edges', body.crisp(bpy.data.objects['body']))
print('glass sharp edges', body.crisp(bpy.data.objects['glass']))      # the panes' lips: shaded round, they scallop the dark glass along a leaning edge
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'suv.blend'))
tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
print('triangles', tri)
if RENDER:
    sys.path[1:1] = [os.path.join(HERE, '..', '..', 'camel3d'), os.path.join(HERE, '..', 'camel')]; from blend_common import desert_world, ground
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
    desert_world(sun_elev=34, sun_rot=215); tex = os.path.join(HERE, '..', 'assets_all', '01_terrain', 'najd.png'); ground(tex if os.path.exists(tex) else None, size=120, tile_m=22)
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -5.3
    from mathutils import Vector
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    def shot(path, loc, look, lens=40, res=(1200, 700)):
        sc.render.resolution_x, sc.render.resolution_y = res; cam.data.lens = lens; cam.location = loc
        cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    shot(os.path.join(OUT, 'q34.png'), (6.8, -5.2, 2.2), (0.2, 0, 0.9))
    shot(os.path.join(OUT, 'wheel.png'), (wheels.AXLE_X[0] + 0.3, 2.0, 0.6), (wheels.AXLE_X[0], wheels.HALF_TRACK, wheels.HUB_Z), lens=50)
