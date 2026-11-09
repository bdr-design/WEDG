"""Render one wheel face-on next to the owner's rim, for checking the rim design alone."""
import bpy, sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'suv'))
OUT = sys.argv[-1]; os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
import wheels, suv_exterior as SE
tm = SE.tyre_material(SE.tyre_maps(os.path.join(OUT, 'tex')))
ws = wheels.build(tm)
for w in ws[1:]: bpy.data.objects.remove(w)
w = ws[0]; w.location = (0, 0, 0)
sc = bpy.context.scene; sc.render.engine = 'CYCLES'; sc.cycles.samples = 48; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = True
world = bpy.data.worlds.new('w'); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.75, 0.78, 0.82, 1); bg.inputs[1].default_value = 1.0
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3.5
sun.rotation_euler = (math.radians(-60), math.radians(20), math.radians(10))
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 0.84; cam.location = (0, 5, 0); cam.rotation_euler = (math.pi / 2, 0, math.pi)
sc.render.resolution_x = sc.render.resolution_y = 640; sc.view_settings.view_transform = 'Standard'
sc.render.filepath = os.path.join(OUT, 'wheel_face.png'); bpy.ops.render.render(write_still=True)
