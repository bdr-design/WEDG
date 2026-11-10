"""The car's materials (principled, no image textures except the tyres')."""
import bpy


def M(name, color, metal=0.0, rough=0.5, coat=0.0, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1); b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough; b.inputs['Coat Weight'].default_value = coat
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha; m.surface_render_method = 'BLENDED'; m.use_backface_culling = True
    return m


def emit(name, color, strength, base=None, rough=0.2):
    m = M(name, base or color, rough=rough); b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Emission Color'].default_value = (*color, 1); b.inputs['Emission Strength'].default_value = strength
    return m


def paint():
    m = M('paint', (0.006, 0.006, 0.007), rough=0.45, coat=1.0); b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Specular IOR Level'].default_value = 0.15; b.inputs['Coat Roughness'].default_value = 0.03
    return m


def fascia(chrome, trim, black_gloss):
    """The materials of the front and rear parts."""
    return {'chrome': chrome, 'trim': trim, 'black_gloss': black_gloss,
            'grille': M('grille_mesh', (0.012, 0.012, 0.013), rough=0.6),
            'lens_chrome': M('lamp_lens', (0.75, 0.76, 0.78), metal=1.0, rough=0.08),
            'proj_glass': M('lamp_projector', (0.03, 0.035, 0.04), rough=0.03, coat=1.0),
            # a clear lens has no colour of its own, only its gloss: a pale base turns it milky over the dark housing
            'lamp_cover': M('lamp_cover', (0.02, 0.022, 0.025), rough=0.02, coat=1.0, alpha=0.18),
            'drl': emit('head_light', (1.0, 0.97, 0.92), 1.0, base=(0.9, 0.9, 0.9)),
            'drl_frost': emit('day_light', (1.0, 0.98, 0.95), 0.5, base=(0.8, 0.82, 0.85), rough=0.35),
            'tail': emit('tail_light', (0.8, 0.02, 0.01), 0.6, base=(0.35, 0.01, 0.01), rough=0.15),
            'silver': M('silver_trim', (0.55, 0.56, 0.58), metal=1.0, rough=0.3),
            'red_lens': M('red_lens', (0.42, 0.015, 0.012), rough=0.2, coat=1.0),
            'gunmetal': M('gunmetal', (0.16, 0.165, 0.17), metal=0.6, rough=0.42),
            'groove': M('shut_line', (0.002, 0.002, 0.002), rough=0.9)}
