import sys, os
sys.path.insert(0, os.getcwd())
import bpy
from blend_common import desert_world, ground, camera, render
bpy.ops.wm.open_mainfile(filepath=os.path.abspath('camel_rigged.blend'))
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.device='CPU'; sc.cycles.use_denoising=True
sc.view_settings.view_transform='AgX'; sc.view_settings.look='AgX - Medium High Contrast'; sc.view_settings.exposure=-5.3
desert_world(sun_elev=30, sun_rot=215)
ground(os.path.abspath('../assets_all/01_terrain/najd.png'), size=80, tile_m=22)
arm=bpy.data.objects['CamelRig']
for tr in arm.animation_data.nla_tracks: tr.mute=True
cam_side=camera('side', (0.1, -5.6, 1.15), (0.1, 0, 1.0), 50)
cam_q=camera('q34', (3.4, -3.6, 1.6), (0.3, 0, 0.8), 42)
jobs=os.environ['JOBS'].split(';')   # action:frame:cam
for j in jobs:
    a,f,c=j.split(':')
    arm.animation_data.action=bpy.data.actions[a]
    sc.frame_set(int(f))
    render(cam_side if c=='side' else cam_q, os.path.abspath(f'anim_{a}_{f}_{c}.png'), res=(480,360), samples=int(os.environ.get('SAMPLES','12')))
