"""Clay close-ups of the lower legs straight from camel_hi.npz (no bake)."""
import sys, os
sys.path.insert(0, os.getcwd())
import bpy
from blend_common import reset, mesh_from_npz, desert_world, ground, camera, render
sc = reset()
ob = mesh_from_npz('camel_hi.npz')
for p in ob.data.polygons:
    p.use_smooth = True
m = bpy.data.materials.new('clay'); m.use_nodes = True
m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.75, 0.70, 0.64, 1)
m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.8
ob.data.materials.append(m)
desert_world(sun_elev=35, sun_rot=215)
ground(os.path.abspath('../assets_all/01_terrain/najd.png'), size=40, tile_m=10)
tag = os.environ.get('TAG', 'clay')
for name, loc, at in (('side', (0.05, -1.5, 0.3), (0.05, 0, 0.22)), ('front34', (1.2, -0.95, 0.4), (0.1, 0.15, 0.15)),
                      ('front', (1.4, -0.15, 0.3), (0.1, 0.15, 0.15)), ('rear34', (-2.0, -0.9, 0.4), (-1.05, 0.0, 0.2))):
    render(camera(name, loc, at, 50), os.path.abspath(f'feet_{tag}_{name}.png'), res=(640, 420), samples=16)
