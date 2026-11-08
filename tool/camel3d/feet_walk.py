"""Close-up strip of the lower legs through one walk cycle (checks the pad roll and toe curl)."""
import sys, os
sys.path.insert(0, os.getcwd())
import bpy
from blend_common import desert_world, ground, camera, render
bpy.ops.wm.open_mainfile(filepath=os.path.abspath('camel_rigged.blend'))
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.use_denoising = True
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'; sc.view_settings.exposure = -5.3
desert_world(sun_elev=40, sun_rot=150)
ground(os.path.abspath('../assets_all/01_terrain/najd.png'), size=40, tile_m=10)
arm = bpy.data.objects['CamelRig']
for tr in arm.animation_data.nla_tracks:
    tr.mute = True
arm.animation_data.action = bpy.data.actions['walk']
cam = camera('low', (-0.5, -3.0, 0.45), (-0.5, 0, 0.3), 50)
for f in [int(x) for x in os.environ.get('FRAMES', '1,6,11,16,21,26,31,36').split(',')]:
    sc.frame_set(f)
    render(cam, os.path.abspath(f'fw_{f}.png'), res=(560, 300), samples=10)
