import sys, os
sys.path.insert(0, os.getcwd())
import bpy
from blend_common import desert_world, ground, camera, render
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(os.environ.get('BLEND', 'camel_lod0.blend')))
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -5.3
desert_world(sun_elev=35, sun_rot=215)
ground(os.path.abspath('../assets_all/01_terrain/najd.png'), size=40, tile_m=10)
tag = os.environ.get('TAG', 'cur')
for name, loc, at in (('side', (0.05, -2.2, 0.35), (0.05, 0, 0.28)), ('front34', (1.6, -1.3, 0.45), (0.0, 0.0, 0.25)),
                      ('front', (2.0, 0.0, 0.35), (0.0, 0.0, 0.25)), ('rear34', (-2.4, -1.1, 0.45), (-1.1, 0.0, 0.25))):
    render(camera(name, loc, at, 50), os.path.abspath(f'feet_{tag}_{name}.png'), res=(640, 420), samples=24)
