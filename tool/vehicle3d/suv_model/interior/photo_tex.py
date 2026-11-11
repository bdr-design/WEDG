"""The owner's photos as the parts' surface detail (his decision, 10 Nov: the model stays as built, which is right
from every side, and the photos give it their fine detail: stitching, perforation, wood grain, switches).
A part's faces that its photo sees from the front (facing the photo's camera within FACING and not hidden by the
part itself) are mapped to the photo's pixels. The photo's light is taken out: within each material's own area of
the photo, its brightness is scaled so that its local mean (a blur of SIGMA px inside that area only, so that nothing
bleeds across a border) is the material's own brightness (imats, measured on the same photos). The detail and the
colour are the photo's (where the photo has a silver strip on what the model has as black, it stays a lighter
strip); the light is the game's. (The detail times the material's colour was tried first: it painted such strips
the model's colour.) Faces the photo does not see keep their plain material.
project(ob, photo, pixel, toward) maps an object; bake(photo, obs, out_png) writes the texture; materials(ob,
photo, png) gives the mapped faces copies of their materials that read it."""
import bpy, bmesh, os, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from scipy import ndimage
from skimage.draw import polygon as _poly
import masks as M

FACING, SIGMA, DETAIL = 0.30, 12.0, 0.6


def project(ob, photo, pixel, toward):
    """pixel(co) -> (col, row) for a point in the object's own frame; toward(co) -> the unit direction from it to the
    photo's camera. Marks the faces the photo sees (face attribute 'photo_seen' = 1) and gives every face UVs ('photo')."""
    a = M.rgb(photo); H, W = a.shape[:2]; me = ob.data
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); tree = BVHTree.FromBMesh(bm)
    seen = np.zeros(len(bm.faces), np.int8)
    for f in bm.faces:
        c = f.calc_center_median(); d = Vector(toward(c))
        if f.normal.dot(d) < FACING: continue
        h = tree.ray_cast(c + f.normal * 2e-4, d)
        if h[0] is None or h[2] == f.index: seen[f.index] = 1
    bm.free()
    uv = me.uv_layers.get('photo') or me.uv_layers.new(name='photo')
    for p in me.polygons:
        for li in p.loop_indices:
            col, row = pixel(me.vertices[me.loops[li].vertex_index].co); uv.data[li].uv = (col / W, 1.0 - row / H)
    at = me.attributes.get('photo_seen') or me.attributes.new('photo_seen', 'INT', 'FACE'); at.data.foreach_set('value', seen.astype(np.int32))
    return int(seen.sum())


def bake(photo, obs, out_png):
    """The texture for the faces project() marked on obs (all mapped to the same photo)."""
    import imats
    a = M.rgb(photo).astype(float) / 255.0; H, W = a.shape[:2]; lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)
    idmap = -np.ones((H, W), np.int32); names = []
    for ob in obs:
        me = ob.data; at = me.attributes['photo_seen']; uv = me.uv_layers['photo']
        for p in me.polygons:
            if not at.data[p.index].value: continue
            m = me.materials[p.material_index].name.split('__')[0]
            if m not in names: names.append(m)
            pts = np.array([uv.data[li].uv[:] for li in p.loop_indices]); rr, cc = _poly((1 - pts[:, 1]) * H, pts[:, 0] * W, (H, W)); idmap[rr, cc] = names.index(m)
    idmap[ndimage.binary_dilation(M.backdrop(a * 255.0), iterations=2)] = -1      # (the photo's magenta backdrop and its fringe are no part's colour: they take their neighbours')
    out = np.zeros((H, W, 3))
    L = lin @ np.array((0.2126, 0.7152, 0.0722))
    for k, nm in enumerate(names):
        mask = (idmap == k).astype(float)
        if mask.sum() < 4: continue
        mean = ndimage.gaussian_filter(L * mask, SIGMA) / np.maximum(ndimage.gaussian_filter(mask, SIGMA), 1e-4)
        col = np.array(imats.MATS[nm][0]); lum = float(col @ np.array((0.2126, 0.7152, 0.0722)))
        ratio = np.clip(L / np.maximum(mean, 1e-4), 0.2, 5.0) ** DETAIL       # the detail, its contrast softened (the leather's sheen in the photo would read as dust)
        chroma = lin / np.maximum(L, 1e-4)[..., None]                          # the photo's own colour at each pixel
        out[mask > 0] = np.clip(chroma * (lum * ratio)[..., None], 0, 1)[mask > 0]
    # beyond the mapped faces, each pixel takes its nearest mapped pixel's colour (so that sampling at a face's edge does not reach black)
    if (idmap >= 0).any():
        _, (ir, ic) = ndimage.distance_transform_edt(idmap < 0, return_indices=True); out = out[ir, ic]
    srgb = np.where(out <= 0.0031308, out * 12.92, 1.055 * np.power(np.clip(out, 0, 1), 1 / 2.4) - 0.055)
    from PIL import Image
    Image.fromarray((np.clip(srgb, 0, 1) * 255).astype(np.uint8)).save(out_png)
    np.save(out_png.replace('.png', '_id.npy'), idmap); return names


def materials(ob, photo, png):
    """The mapped faces get copies of their materials (name__photo) whose colour is the texture."""
    me = ob.data; at = me.attributes['photo_seen']; img = bpy.data.images.get(os.path.basename(png)) or bpy.data.images.load(png)
    img.colorspace_settings.name = 'sRGB'; copies = {}
    for p in me.polygons:
        if not at.data[p.index].value: continue
        base = me.materials[p.material_index]
        if base.name.endswith('__photo'): continue
        if base.name not in copies:
            nm = base.name + '__photo'; m = bpy.data.materials.get(nm)
            if m is None:
                m = base.copy(); m.name = nm; nt = m.node_tree; b = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
                t = nt.nodes.new('ShaderNodeTexImage'); t.image = img; uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'photo'
                nt.links.new(uvn.outputs['UV'], t.inputs['Vector']); nt.links.new(t.outputs['Color'], b.inputs['Base Color']); m['photo'] = photo
            if nm not in [x.name for x in me.materials]: me.materials.append(m)
            copies[base.name] = [x.name for x in me.materials].index(nm)
        p.material_index = copies[base.name]
