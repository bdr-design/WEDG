"""Orthographic side render at the photo's own scale, for a direct overlay with the reference."""
import sys, os, math
sys.path.insert(0, os.getcwd())
import bpy
from blend_common import desert_world, render
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(os.environ.get('BLEND', 'camel_lod0.blend')))
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -5.3
sc.render.film_transparent = True
desert_world(sun_elev=40, sun_rot=60)
PX, GROUND, U0, IW, IH = 443.0, 1032.0, 700.0, 1448, 1086
cd = bpy.data.cameras.new('ortho'); cd.type = 'ORTHO'; cd.ortho_scale = IW / PX
cam = bpy.data.objects.new('ortho', cd); sc.collection.objects.link(cam)
cam.location = ((U0 - IW / 2) / PX, 10.0, (GROUND - IH / 2) / PX)
cam.rotation_euler = (math.radians(90), 0, math.radians(180))
render(cam, os.path.abspath(os.environ.get('OUT', 'ortho_side.png')), res=(IW // 2, IH // 2), samples=12)
