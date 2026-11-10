"""The interior's materials, in one place. Colours are set so that a part rendered under shot.py's light comes out
at its photo's own mean colour (measured inside each region, away from its edges); the figures in the comments are
the photos' means as sRGB 0 to 255. No image textures."""
import bpy
# name: (base colour (linear), metallic, roughness, coat)
MATS = {
    'cabin_black': ((0.017, 0.017, 0.0175), 0.0, 0.50, 0.0),          # the door's upper panel: 45 45 46
    'cabin_black_gloss': ((0.012, 0.012, 0.013), 0.0, 0.12, 1.0),
    'cabin_shadow': ((0.008, 0.008, 0.008), 0.0, 0.80, 0.0),
    'cabin_grille': ((0.018, 0.018, 0.019), 0.0, 0.75, 0.0),
    'cabin_silver': ((0.50, 0.50, 0.50), 1.0, 0.38, 0.0),
    'cabin_chrome': ((0.80, 0.80, 0.82), 1.0, 0.15, 0.0),
    'trim_leather': ((0.80, 0.57, 0.345), 0.0, 0.55, 0.0),            # the door's and dashboard's beige: 209 179 144 on door_FL
    'seat_leather': ((0.66, 0.54, 0.40), 0.0, 0.55, 0.0),             # the seats': 204 189 166 on seat_side
    'cabin_beige': ((0.60, 0.50, 0.37), 0.0, 0.45, 0.0),              # beige plastic (the seat's base)
    'cabin_wood_brown': ((0.24, 0.108, 0.058), 0.0, 0.30, 0.7),       # the door's wood: 110 85 73
    'cabin_wood_grey': ((0.075, 0.072, 0.070), 0.0, 0.40, 0.5),       # the wheel's and console's wood
    'wheel_leather': ((0.035, 0.035, 0.036), 0.0, 0.62, 0.0),         # the wheel's rim: 70 71 70; its pad 83 84 84
    'cabin_carpet': ((0.42, 0.33, 0.22), 0.0, 0.95, 0.0),
    'cabin_red': ((0.55, 0.03, 0.02), 0.0, 0.40, 0.0),
    'cabin_lamp': ((0.80, 0.80, 0.78), 0.0, 0.30, 0.0),
    'cabin_display': ((0.004, 0.006, 0.012), 0.0, 0.05, 1.0),
    'cabin_seam': ((0.006, 0.006, 0.006), 0.0, 0.90, 0.0),
    'wheel_thread': ((0.50, 0.50, 0.47), 0.0, 0.70, 0.0),
    'seat_belt': ((0.52, 0.44, 0.33), 0.0, 0.85, 0.0),               # the belts' webbing: 190 172 150 on rear_bench
    'seat_seam': ((0.33, 0.26, 0.17), 0.0, 0.80, 0.0),
    'seat_thread': ((0.70, 0.60, 0.44), 0.0, 0.70, 0.0),
}
def m(name):
    color, metal, rough, coat = MATS[name]
    mt = bpy.data.materials.get(name) or bpy.data.materials.new(name); mt.use_nodes = True; b = mt.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough; b.inputs['Coat Weight'].default_value = coat
    return mt
