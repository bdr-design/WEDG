import sys, os
sys.path.insert(0, os.getcwd())
import bpy
from blend_common import desert_world, ground, camera, render
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(os.environ.get('BLEND','camel_lod0.blend')))
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.use_denoising=True
sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'; sc.view_settings.exposure=-5.3
desert_world(sun_elev=float(os.environ.get('SUN','30')), sun_rot=215)
ground(os.path.abspath('../assets_all/01_terrain/najd.png'), size=80, tile_m=22)
views = {
 'side': ((0.1, -5.6, 1.15), (0.1, 0, 1.05), 50),
 'q34': ((3.4, -3.6, 1.7), (0.1, 0, 1.0), 42),
 'rear34': ((-3.6, 3.0, 1.9), (0, 0, 1.0), 42),
 'drone': ((-4.0, -6.0, 9.0), (0, 0, 0.8), 45),
 'head': ((1.95, -1.45, 2.0), (1.2, 0, 1.92), 60),
}
only=os.environ.get('VIEWS')
for name,(loc,at,lens) in views.items():
    if only and name not in only.split(','): continue
    render(camera(name,loc,at,lens), os.path.abspath(f'tex_{name}.png'), res=(800,600), samples=int(os.environ.get('SAMPLES','24')))
