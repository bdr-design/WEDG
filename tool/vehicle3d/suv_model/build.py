"""The SUV modelled from scratch in Blender: runs every step and writes the .blend, the game GLB and the scores.
Run: blendenv/bin/python build.py <out_dir> [render]"""
import bpy, sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'suv'))
OUT = sys.argv[-2] if sys.argv[-1] == 'render' else sys.argv[-1]; RENDER = sys.argv[-1] == 'render'
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
import body, wheels, suv_exterior as SE
paint = bpy.data.materials.new('paint'); paint.use_nodes = True; b = paint.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (0.006, 0.006, 0.007, 1); b.inputs['Roughness'].default_value = 0.45
b.inputs['Specular IOR Level'].default_value = 0.15; b.inputs['Coat Weight'].default_value = 1.0; b.inputs['Coat Roughness'].default_value = 0.03
shell = body.build(); shell.data.materials.append(paint)
import ext_parts as EP
def M(name, color, metal=0.0, rough=0.5, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b_ = m.node_tree.nodes['Principled BSDF']
    b_.inputs['Base Color'].default_value = (*color, 1); b_.inputs['Metallic'].default_value = metal; b_.inputs['Roughness'].default_value = rough; b_.inputs['Coat Weight'].default_value = coat
    return m
trim = M('trim_black', (0.018, 0.018, 0.019), rough=0.55); liner = M('liner', (0.012, 0.012, 0.012), rough=0.85)
mirror_glass = M('mirror_glass', (0.6, 0.62, 0.65), metal=1.0, rough=0.02)
import greenhouse as GH
glass_m = M('glass', (0.012, 0.014, 0.017), rough=0.03)
glass_m.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value = 0.55; glass_m.surface_render_method = 'BLENDED'; glass_m.use_backface_culling = True
black_gloss = M('black_gloss', (0.006, 0.006, 0.007), rough=0.08, coat=1.0); chrome = M('chrome', (0.9, 0.9, 0.92), metal=1.0, rough=0.06)
glass, strips = GH.build(shell, glass_m, black_gloss, trim, chrome)
import fascia_front as FF, fascia_rear as FR
def emit(name, color, strength, base=None, rough=0.2):
    m = M(name, base or color, rough=rough); b_ = m.node_tree.nodes['Principled BSDF']
    b_.inputs['Emission Color'].default_value = (*color, 1); b_.inputs['Emission Strength'].default_value = strength; return m
MAT = {'chrome': chrome, 'trim': trim, 'black_gloss': black_gloss,
       'grille': M('grille_mesh', (0.012, 0.012, 0.013), rough=0.6),
       'lens_chrome': M('lamp_lens', (0.75, 0.76, 0.78), metal=1.0, rough=0.08),
       'drl': emit('head_light', (1.0, 0.97, 0.92), 1.0, base=(0.9, 0.9, 0.9)),
       'tail': emit('tail_light', (0.8, 0.02, 0.01), 0.6, base=(0.35, 0.01, 0.01), rough=0.15),
       'silver': M('silver_trim', (0.55, 0.56, 0.58), metal=1.0, rough=0.3)}
FF.front(shell, MAT); FR.rear(shell, MAT)
import sides as SD
SD.running_boards(trim, MAT['silver'])
EP.mirrors(paint, mirror_glass, trim)
EP.roof_rails(trim)
# everything so far was built in the photo frame; map it to the real (spec sheet) frame, then cut the arches round the
# real axles and fit the real 265/55R20 wheels
import realframe as RF
for o in list(bpy.data.objects):
    if o.type == 'MESH': RF.warp_object(o)
flares = EP.arches(shell, paint, liner, paint)
groove = M('shut_line', (0.002, 0.002, 0.002), rough=0.9)
SD.seams(shell, groove); SD.handles(shell, chrome, black_gloss)
tyre_mat = SE.tyre_material(SE.tyre_maps(os.path.join(OUT, 'tex')))
ws = wheels.build(tyre_mat)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'suv.blend'))
tri = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
print('triangles', tri)
if RENDER:
    sys.path.insert(0, os.path.join(HERE, '..', 'camel')); from blend_common import desert_world, ground
    sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 32; sc.cycles.use_denoising = True; sc.cycles.device = 'CPU'
    desert_world(sun_elev=34, sun_rot=215); ground(os.path.join(HERE, '..', 'assets_all', '01_terrain', 'najd.png'), size=120, tile_m=22)
    sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -5.3
    from mathutils import Vector
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
    def shot(path, loc, look, lens=40, res=(1200, 700)):
        sc.render.resolution_x, sc.render.resolution_y = res; cam.data.lens = lens; cam.location = loc
        cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler(); sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    shot(os.path.join(OUT, 'q34.png'), (6.8, -5.2, 2.2), (0.2, 0, 0.9))
    shot(os.path.join(OUT, 'wheel.png'), (wheels.AXLE_X[0] + 0.3, 2.0, 0.6), (wheels.AXLE_X[0], wheels.HALF_TRACK, wheels.HUB_Z), lens=50)
