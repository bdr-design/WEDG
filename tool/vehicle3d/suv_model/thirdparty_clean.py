"""The brand marks off the outside model's interior (as on the code-built car: no badges or brand names).
thirdparty_clean.py <in.blend> <out.blend> [ratio]
- then thinned to ratio of its faces (Blender's collapse decimation, keeping material and UV borders), its small loose
  parts kept whole (thin());
- the emblem on the steering wheel's pad (dropped by name in thirdparty_cabin.py; emblem() takes any chrome left in
  its box, 65 by 43 mm). The pad's recess it
  stood in then shows; where the cull has dropped the recess (it is kept when the steering wheel turns: lod_cabin's
  in_wheel), the opening is filled flat;
- the textures thirdparty_tex.py cleans (in tex/ beside out.blend) read in place of the model's: the centre screen a
  dark display (its picture was a phone's app icons), the gauges and the switches' symbols as they were."""
import bpy, bmesh, sys, os, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import thirdparty_tex as TX
EMBLEM = (0.425, 1.259, 0.036, 0.024); FEW = 60; PANEL = 0.02      # m^2: a part this big has its edges held (a slit in it shows the sky)      # the emblem's middle (y, z) and half its box with 3 mm to spare (its chrome: y 0.400-0.464, z 1.257-1.299)


def thin(o, ratio):
    """The small loose parts (fewer than FEW triangles: buttons, rings, clips; about 7000 of 8000) kept whole, the rest
    thinned to ratio of its triangles by one collapse decimation (the flattest collapses first: large smooth parts
    give up most). One decimation over everything collapsed the small parts into holes (the gauges' rings, the
    console's buttons). The parts' edges are held too (they opened into slits), and so is the pad round the emblem (thinned, its rim read as a polygon a
    hand's breadth from the driver's eye). (The decimate modifier's vertex group is a mask: its vertices are left alone.)"""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import connected_components
    me = o.data; me.calc_loop_triangles(); E = np.array([e.vertices[:] for e in me.edges]); nv = len(me.vertices)
    k, lab = connected_components(coo_matrix((np.ones(len(E)), (E[:, 0], E[:, 1])), shape=(nv, nv)), directed=False)
    tl = np.array([lab[t.vertices[0]] for t in me.loop_triangles]); cnt = np.bincount(tl, minlength=k)
    V = np.array([v.co[:] for v in me.vertices]); pad = (np.abs(V[:, 1] - EMBLEM[0]) < 0.06) & (np.abs(V[:, 2] - EMBLEM[1]) < 0.05) & (V[:, 0] > 0.35) & (V[:, 0] < 0.5)
    edge = np.zeros(nv, bool)                                               # the parts' own edges (thinned, they opened slits: the headliner by the visors, round the cupholders)
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    area = np.zeros(k); np.add.at(area, [lab[f.verts[0].index] for f in bm.faces], [f.calc_area() for f in bm.faces])
    for e in bm.edges:
        if e.is_boundary and area[lab[e.verts[0].index]] > PANEL: edge[[v.index for v in e.verts]] = True      # (only the big panels': holding every part's edges left nothing to thin, 123k)
    bm.free()
    print("  panels over %.2f m2: %d, edge vertices held %d (biggest panel %.2f m2)" % (PANEL, int((area > PANEL).sum()), int(edge.sum()), area.max()))
    small = (cnt[lab] < FEW) | pad | edge; g = o.vertex_groups.new(name='hold'); g.add([int(i) for i in np.nonzero(small)[0]], 1.0, 'REPLACE')
    bpy.context.view_layer.objects.active = o; m = o.modifiers.new('lod', 'DECIMATE'); m.ratio = (cnt[cnt < FEW].sum() + ratio * cnt[cnt >= FEW].sum()) / cnt.sum(); m.use_collapse_triangulate = True
    m.delimit = {'MATERIAL', 'SEAM', 'UV', 'SHARP'}; m.vertex_group = 'hold'; m.invert_vertex_group = True; bpy.ops.object.modifier_apply(modifier='lod')
    o.vertex_groups.clear(); me = o.data; me.calc_loop_triangles()
    print('thinned: %d loose parts, %d under %d triangles held (%d triangles); %d -> %d triangles' % (k, int((cnt < FEW).sum()), FEW, int(cnt[cnt < FEW].sum()), int(cnt.sum()), len(me.loop_triangles)))
    return o


def emblem(me):
    """The emblem's chrome faces (within the emblem's own box about its middle) dropped; it stood in an opening of the
    pad (two closed rims in the pad's leather, its front face and its recess), and those rims are filled flat."""
    names = [m.name for m in me.materials]; ch, lea = names.index('Chrome'), names.index('Black_Leather')
    inbox = lambda c: abs(c.y - EMBLEM[0]) < EMBLEM[2] and abs(c.z - EMBLEM[1]) < EMBLEM[3] and c.x < 0.45
    bm = bmesh.new(); bm.from_mesh(me)
    gone = [f for f in bm.faces if f.material_index == ch and inbox(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=gone, context='FACES'); bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    rim = [e for e in bm.edges if e.is_boundary and e.link_faces[0].material_index == lea and inbox((e.verts[0].co + e.verts[1].co) / 2)]
    new = bmesh.ops.holes_fill(bm, edges=rim, sides=0)['faces']
    for f in new: f.material_index = lea; f.smooth = False
    bm.to_mesh(me); bm.free()
    print('emblem: %d chrome faces dropped, %d rim edges filled with %d faces' % (len(gone), len(rim), len(new)))


def main(src, out, ratio='1.0'):
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src)); o = bpy.data.objects['tp_cabin']; me = o.data
    emblem(me)
    if float(ratio) < 1:
        o = thin(o, float(ratio)); me = o.data
        dc = bpy.data.objects.get('tp_doorcard')                 # the driver's door's trim (thirdparty_cabin.py), thinned alike
        if dc: thin(dc, float(ratio))
    TX.relink(os.path.join(os.path.dirname(os.path.abspath(out)), 'tex'))
    me.calc_loop_triangles(); print('%d triangles' % len(me.loop_triangles))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))


if __name__ == '__main__':
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[-3:] if sys.argv[-1].replace('.', '').isdigit() else sys.argv[-2:]
    main(*a)
