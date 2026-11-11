"""The outside of the downloaded model as the private car (private use only: see thirdparty/README.md), with the
owner's decisions for the car: black gloss paint, all glass fully dark, the Saudi plate ا م ن 1 front and rear, no
badges or brand names (also none on the tyres: thirdparty_tex.py). thirdparty_car.py <model in our frame.blend> <our suv.blend> <out.blend> <the model's textures dir>
- the badges (found by place and size on the model, 11 Nov): the grille's and the tailgate's emblems, the tailgate's
  name in letters and its two small badges, the left front door's badge, the four wheel caps' emblems: dropped;
- the model's plates (each reading the car's name) dropped, and ours (plate.py's texture and box) set where they
  were, on the same plane;
- the parts that make the interior (thirdparty_cabin.py's rule: the cabin's own, inside our hull) dropped too: the
  interior is its own file, loaded only while the player is inside."""
import bpy, bmesh, sys, os, math, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plate as PL, thirdparty_cabin as TC, thirdparty_tex as TX

BADGES = ['polySurface424', 'polySurface219', 'polySurface17', 'polySurface18', 'polySurface19', 'polySurface20', 'polySurface21',
          'polySurface344', 'polySurface355', 'polySurface366', 'polySurface397'] + ['polySurface%d' % i for i in range(208, 219)] + ['polySurface%d' % i for i in range(220, 231)]
PLATES = {'front': 'polySurface1496', 'rear': 'polySurface207'}
PAINT = ((0.010, 0.010, 0.012), 0.25, 1.0)          # black gloss: base colour, roughness, clear coat (as the code-built car's)
GLASS = ((0.004, 0.004, 0.005), 0.05)               # the glass: opaque black gloss


def _plane(o):
    """A plate object's middle, its outward normal (pointing away from the car's middle) and its lean."""
    mw = o.matrix_world; P = np.array([mw @ v.co for v in o.data.vertices]); c = P.mean(0)
    n = np.linalg.svd(P - c)[2][2]
    if n[0] * c[0] < 0: n = -n
    return P, c, n


def main(src, car, out, tex):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src)); bpy.context.view_layer.update()
    gone = 0
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and o.name.split('_')[0] in BADGES: bpy.data.objects.remove(o); gone += 1
    for name in ('CarPaint',):
        m = bpy.data.materials.get(name); b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
        for l in list(m.node_tree.links):
            if l.to_node == b and l.to_socket.name in ('Base Color', 'Roughness', 'Metallic'): m.node_tree.links.remove(l)
        b.inputs['Base Color'].default_value = (*PAINT[0], 1); b.inputs['Roughness'].default_value = PAINT[1]; b.inputs['Metallic'].default_value = 0.0; b.inputs['Coat Weight'].default_value = PAINT[2]
    m = bpy.data.materials.get('ClearGlass'); b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for l in list(m.node_tree.links):
        if l.to_node == b: m.node_tree.links.remove(l)
    b.inputs['Base Color'].default_value = (*GLASS[0], 1); b.inputs['Roughness'].default_value = GLASS[1]; b.inputs['Alpha'].default_value = 1.0
    b.inputs['Transmission Weight'].default_value = 0.0; m.blend_method = 'OPAQUE' if hasattr(m, 'blend_method') else None
    # the model's glass material also covers small lamp lenses (the front corners' and the bumpers'): those keep a lamp's
    # smoked lens (Light_glass), not the windows' dark glass; a window lies in the greenhouse (above the belt, in the cabin's length)
    lens = bpy.data.materials.get('Light_glass'); lensed = 0
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and any(sl.material == m for sl in o.material_slots)]:
        P = np.array([o.matrix_world @ v.co for v in o.data.vertices]); c = (P.min(0) + P.max(0)) / 2
        s = P.max(0) - P.min(0)
        if c[2] < 0.9 or c[0] > 1.5 or s.max() < 0.25 or (s[2] < 0.03 and s.max() < 0.4):      # low or ahead, small (a lamp's lens, a mirror's indicator), or a thin strip (the high stop lamp)
            for sl in o.material_slots:
                if sl.material == m: sl.material = lens
            lensed += 1
    print('lamp lenses kept clear: %d' % lensed)
    TX.main(tex, os.path.join(os.path.dirname(os.path.abspath(out)), 'tex')); TX.relink(os.path.join(os.path.dirname(os.path.abspath(out)), 'tex'))      # the tyres' maker's name and logo off
    # our plates on the model's plates' planes
    ptex = os.path.join(os.path.dirname(os.path.abspath(out)), 'plate_ksa.png'); PL.texture(ptex)
    pm = bpy.data.materials.new('plate'); pm.use_nodes = True; nt = pm.node_tree; pb = nt.nodes['Principled BSDF']; t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(ptex); t.image.pack(); nt.links.new(t.outputs['Color'], pb.inputs['Base Color']); pb.inputs['Roughness'].default_value = 0.35
    for side, nm in PLATES.items():
        o = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name.split('_')[0] == nm); P, c, n = _plane(o)
        front = P[np.argmax(P @ n)]; lean = math.atan2(-n[2], abs(n[0])) * (1 if n[0] > 0 else -1)
        bpy.data.objects.remove(o)
        f = 1 if n[0] > 0 else -1; centre = Vector((float((front @ n - (c @ n)) * n[0] + c[0]) + f * 0.001, 0.0, float(c[2])))
        PL._box('plate_' + side, centre, f, lean, pm)
    # the interior's parts out (thirdparty_cabin.py's own rule, inside the model's own outside: the same parts go there)
    bpy.context.view_layer.update(); inside = TC.model_hull();
    inner = 0
    for o in [o for o in bpy.data.objects if o.type == 'MESH' and not o.name.startswith('plate_')]:
        if any(s.material and s.material.name.split('.')[0] in TC.OUTSIDE for s in o.material_slots) and not TC.inner_small(o, inside): continue
        mw = o.matrix_world; pts = [mw @ v.co for v in o.data.vertices]
        if not pts: continue
        c = sum(pts, Vector()) / len(pts); sample = pts[::max(1, len(pts) // 40)]
        if TC.CABIN_X[0] < c.x < TC.CABIN_X[1] and c.z > TC.CABIN_Z and not TC.in_lamps(c) and sum(inside(p) for p in sample) / len(sample) >= TC.KEEP_SHARE:
            bpy.data.objects.remove(o); inner += 1
    tris = 0
    for o in bpy.data.objects:
        if o.type == 'MESH': o.data.calc_loop_triangles(); tris += len(o.data.loop_triangles)
    print('outside: %d badges dropped, plates replaced, %d interior parts dropped; %d triangles left' % (gone, inner, tris))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))


if __name__ == '__main__':
    main(*sys.argv[-4:])
