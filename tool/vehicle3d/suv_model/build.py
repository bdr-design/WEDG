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
EP.arches(shell, paint, liner, paint)
EP.mirrors(paint, mirror_glass, trim)
EP.roof_rails(trim)
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
    shot(os.path.join(OUT, 'wheel.png'), (wheels.AXLE_X[0] + 0.3, 2.0, 0.6), (wheels.AXLE_X[0], 0.86, 0.43), lens=50)
