"""Whole-camel check views: front, rear, three-quarter front and rear, in desert light."""
import sys, os
sys.path.insert(0, os.getcwd())
import bpy
from blend_common import desert_world, ground, camera, render
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(os.environ.get('BLEND', 'camel_lod0.blend')))
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -5.3
desert_world(sun_elev=35, sun_rot=200)
ground(os.path.abspath('../assets_all/01_terrain/najd.png'), size=80, tile_m=22)
tag = os.environ.get('TAG', 'cur')
views = {'front': ((6.5, 0.0, 1.1), (0.0, 0, 1.0), 50), 'rear': ((-7.0, 0.0, 1.2), (-0.6, 0, 1.0), 50),
         'q34': ((3.6, -3.9, 1.4), (-0.2, 0, 1.0), 40), 'r34': ((-4.2, -3.4, 1.4), (-0.4, 0, 1.0), 40)}
for name, (loc, at, lens) in views.items():
    render(camera(name, loc, at, lens), os.path.abspath(f'body_{tag}_{name}.png'), res=(560, 560), samples=16)
