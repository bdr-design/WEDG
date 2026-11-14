# T12 reviewer's own renders of the canid GLBs (independent of the worker's pictures). Blender as the bpy module.
# usage: blendenv/bin/python canid_render.py OUT.png VIEW SIZE_M CX CY CZ file.glb[@dx,dy,dz] ... [--night] [--dist M]
#   coordinates: Blender, Z up (glTF X forward -> Blender X; glTF -Z (animal's left?) -> Blender Y). Check the frame
#   with canid_check.py first.
#   VIEW: side (camera on the animal's right, -Y) | other | front | back | top | tq | head | game (perspective, the
#   prototype's camera: 40 deg vertical FOV, 956x440, eye 1.6 m, at --dist metres, looking at the target)
#   SIZE_M: ortho scale (m) for ortho views; ignored by 'game'.
#   day: Workbench, textured, studio light, grey background, 1 cm / 10 cm ruler drawn on the ground (side views).
#   --night: Cycles CPU 24 samples; a weak blue-white moon (sun lamp, 0.08 W/m2, 35 deg up) + a dark sky
#            (0.004): a game choice of the reviewer's for 'a moonlit night' since the prototype has no night yet;
#            prints the animal's height in screen pixels (css px at 440 high, and device px at the 2x render scale).
import bpy, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
night = '--night' in a; dist = float(a[a.index('--dist') + 1]) if '--dist' in a else 30.0
a = [x for i, x in enumerate(a) if x not in ('--night', '--dist') and not (i and a[i - 1] == '--dist')]
out, view, size = a[0], a[1], float(a[2]); c = Vector(map(float, a[3:6])); files = a[6:]
bpy.ops.wm.read_factory_settings(use_empty=True)
objs = []
for f in files:
    p, _, off = f.partition('@')
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=p)
    new = set(bpy.data.objects) - before; objs += [o for o in new if o.type == 'MESH']
    if off:
        d = Vector(map(float, off.split(',')))
        for o in new:
            if o.parent is None: o.location += d
sc = bpy.context.scene
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
dirs = {'side': Vector((0, -1, 0)), 'other': Vector((0, 1, 0)), 'front': Vector((1, 0, 0)), 'back': Vector((-1, 0, 0)),
        'top': Vector((0, 0, 1)), 'tq': Vector((0.8, -1, 0.35)).normalized(), 'head': Vector((0.5, -1, 0.1)).normalized()}
if view == 'game':
    sc.render.resolution_x, sc.render.resolution_y = 956, 440
    cam.data.type = 'PERSP'; cam.data.sensor_fit = 'VERTICAL'; cam.data.angle = math.radians(40)
    cam.location = c + Vector((0, -dist, 1.6 - c.z))
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
else:
    sc.render.resolution_x, sc.render.resolution_y = 1200, 800
    d = dirs[view]
    cam.data.type = 'PERSP' if view == 'tq' else 'ORTHO'; cam.data.ortho_scale = size; cam.data.lens = 85
    cam.location = c + d * (size * 3.2 if view == 'tq' else 20)
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Z' if view != 'top' else 'X').to_euler()
    # ruler on the ground plane: 1 cm ticks, 10 cm long ticks, along X under the animal (side views only)
    if view in ('side', 'other'):
        import bmesh
        me = bpy.data.meshes.new('ruler'); bm = bmesh.new()
        x0 = c.x - size / 2; n = int(size * 100)
        for i in range(n + 1):
            x = x0 + i / 100; h = 0.03 if i % 10 == 0 else 0.012; w = 0.0015 if i % 10 == 0 else 0.0008
            vs = [bm.verts.new((x - w, -0.6, -h)), bm.verts.new((x + w, -0.6, -h)), bm.verts.new((x + w, -0.6, 0)), bm.verts.new((x - w, -0.6, 0))]
            bm.faces.new(vs)
        bm.to_mesh(me); r = bpy.data.objects.new('ruler', me); sc.collection.objects.link(r)
        m = bpy.data.materials.new('black'); m.diffuse_color = (0, 0, 0, 1); me.materials.append(m)
if not night:   # day: Cycles too (Workbench needs EGL, missing here): a sun 35 deg up from the front-left + grey sky
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16; sc.cycles.use_denoising = False
    sc.render.threads_mode = 'FIXED'; sc.render.threads = 2; sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.5, 0.5, 0.52, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.9
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun)
    sun.data.energy = 2.5; sun.rotation_euler = (math.radians(55), 0, math.radians(-35))
else:
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 24; sc.cycles.use_denoising = False
    sc.render.threads_mode = 'FIXED'; sc.render.threads = 2
    sc.view_settings.view_transform = 'Standard'
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0.35, 0.42, 0.6, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.004
    moon = bpy.data.objects.new('moon', bpy.data.lights.new('moon', 'SUN')); sc.collection.objects.link(moon)
    moon.data.energy = 0.08; moon.data.color = (0.75, 0.82, 1.0); moon.rotation_euler = (math.radians(55), 0, math.radians(30))
    g = bpy.data.meshes.new('ground'); g.from_pydata([(-200, -200, 0), (200, -200, 0), (200, 200, 0), (-200, 200, 0)], [], [(0, 1, 2, 3)])
    go = bpy.data.objects.new('ground', g); sc.collection.objects.link(go)
    gm = bpy.data.materials.new('sand'); gm.use_nodes = True
    gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.55, 0.42, 0.28, 1); g.materials.append(gm)
sc.render.filepath = out; bpy.ops.render.render(write_still=True)
if view == 'game':
    # the animal's screen height from its bounding box corners
    from bpy_extras.object_utils import world_to_camera_view
    ys = []
    for o in objs:
        for v in o.bound_box: ys.append(world_to_camera_view(sc, cam, o.matrix_world @ Vector(v)).y)
    hpx = (max(ys) - min(ys)) * 440
    print(f'SCREEN HEIGHT at {dist} m: {hpx:.1f} css px of 440 ({hpx*2:.0f} device px at 2x)')
