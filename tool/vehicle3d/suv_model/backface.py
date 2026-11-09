"""Back-face check. Every material is swapped for one unlit shader: grey on the front of a face, red on its back.
A game engine that culls back faces draws nothing where this picture is red, so a red area seen from outside the car
is a hole in the game. Prints the share of red pixels per view.
Run: blendenv/bin/python backface.py <blend> <out_dir> name:x,y,z:lx,ly,lz:lens ...   (ONLY=prefix,prefix limits the objects)
SKIP=glass,roof_glass hides the glass to look inside (the cabin is red until the interior is built)."""
import bpy, sys, os
import numpy as np
from mathutils import Vector
a = sys.argv[1:]; bpy.ops.wm.open_mainfile(filepath=a[0]); out = a[1]; os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type in ('CAMERA', 'LIGHT') or o.name.lower() == 'ground': bpy.data.objects.remove(o)
m = bpy.data.materials.new('backface'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
geo = nt.nodes.new('ShaderNodeNewGeometry'); lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.5
grey = nt.nodes.new('ShaderNodeMapRange'); grey.inputs['To Min'].default_value = 0.75; grey.inputs['To Max'].default_value = 0.15
mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.inputs['B'].default_value = (1.0, 0.0, 0.0, 1.0)
em = nt.nodes.new('ShaderNodeEmission'); o_ = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(lw.outputs['Facing'], grey.inputs['Value']); nt.links.new(grey.outputs['Result'], mix.inputs['A'])
nt.links.new(geo.outputs['Backfacing'], mix.inputs['Factor']); nt.links.new(mix.outputs['Result'], em.inputs['Color'])
nt.links.new(em.outputs['Emission'], o_.inputs['Surface'])
only = os.environ.get('ONLY'); skip = [s for s in os.environ.get('SKIP', '').split(',') if s]
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    if (only and not any(o.name.startswith(p) for p in only.split(','))) or o.name in skip: o.hide_render = True; continue
    if not o.material_slots: o.data.materials.append(m)
    for s in o.material_slots: s.material = m
sc.render.engine = 'CYCLES'; sc.cycles.samples = 4; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = False; sc.cycles.max_bounces = 0
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.2, 0.35, 0.6, 1)
sc.view_settings.view_transform = 'Standard'; sc.render.image_settings.file_format = 'PNG'
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
sc.render.resolution_x, sc.render.resolution_y = 1100, 640
for spec in a[2:]:
    name, loc, look, lens = spec.split(':'); loc = [float(v) for v in loc.split(',')]; look = [float(v) for v in look.split(',')]
    cam.data.lens = float(lens); cam.location = loc; cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    path = os.path.join(out, name + '.png'); sc.render.filepath = path; bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(path); px = np.array(im.pixels[:]).reshape(-1, 4); bpy.data.images.remove(im)
    red = (px[:, 0] > 0.6) & (px[:, 1] < 0.25) & (px[:, 2] < 0.25); car = ~((px[:, 2] > px[:, 0] + 0.1) & (px[:, 2] > px[:, 1] + 0.1))
    print(f'backface {name:14s} red {int(red.sum()):7d} px = {100.0 * red.sum() / max(1, car.sum()):6.3f} % of the car')
