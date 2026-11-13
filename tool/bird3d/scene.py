"""The picture of all of them beside the player's figure (assets_src/characters/man.glb), for scale: the hooded falcon on
the glove at the height a standing man holds it (his left forearm level), the unhooded falcon on her perch, the
houbara and the stone-curlew on the ground. Built from the GLB files just written (run the birds and the gear first).

The figure's left forearm is turned level for this picture only, and its hand bone shortened so the fingers, which
cannot curl yet (tool/char3d's known gap), stay inside the glove.
"""
import math
import os

import bpy
from mathutils import Matrix, Vector

import common
from common import V3


def load(path, name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in new if o.parent is None and o.name.startswith(name)]
    return roots[0] if roots else new[0]


def place(root, loc, yaw_deg):
    root.rotation_mode = 'XYZ'
    root.rotation_euler = (0, 0, math.radians(yaw_deg))
    root.location = V3(loc)


def pose_arm(rig):
    """The left forearm level and pointing forward (the figure faces -Y), the hand along it, shortened."""
    pb = rig.pose.bones['forearm.L']
    bone = rig.data.bones['forearm.L']
    rest = bone.matrix_local.to_3x3()
    cur = (bone.tail_local - bone.head_local).normalized()
    target = V3((0.06, -1.0, 0.0)).normalized()
    rw = cur.rotation_difference(target).to_matrix()
    local = rest.inverted() @ rw @ rest
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = local.to_quaternion()
    hb = rig.pose.bones['hand.L']
    hb.scale = (0.55, 0.55, 0.55)
    bpy.context.view_layer.update()
    m = rig.matrix_world @ rig.pose.bones['hand.L'].matrix
    head = m.translation
    axis = (m.to_3x3() @ V3((0, 1, 0))).normalized()
    return head, axis


def vruler(path, px_per_mm, x, y_ground, length_mm):
    from PIL import Image, ImageDraw
    im = Image.open(path).convert('RGB')
    d = ImageDraw.Draw(im)
    f = common.font(20)
    ink = (30, 28, 26)
    d.line((x, y_ground, x, y_ground - length_mm * px_per_mm), fill=ink, width=2)
    for mm in range(0, int(length_mm) + 1, 50):
        y = y_ground - mm * px_per_mm
        w = 22 if mm % 500 == 0 else 14 if mm % 100 == 0 else 7
        d.line((x, y, x + w, y), fill=ink, width=2)
        if mm % 500 == 0:
            d.text((x + 26, y - 11), f'{mm / 1000:.1f} m', fill=ink, font=f)
    im.save(path)


def scale(B):
    out = B.OUT
    need = ['dass.glb', 'wakr.glb', 'saker_hooded.glb', 'saker_alert.glb', 'houbara_alert.glb', 'curlew_alert.glb']
    for n in need:
        if not os.path.exists(os.path.join(out, n)):
            raise SystemExit(f'{n} missing: build the birds and the gear first')
    B.fresh()
    bpy.ops.import_scene.gltf(filepath=B.MAN)
    for o in list(bpy.data.objects):
        if o.name.startswith('Icosphere'):
            bpy.data.objects.remove(o)
    rig = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    if rig.animation_data:
        rig.animation_data.action = None
    hand, axis = pose_arm(rig)
    # the glove: its axis along the forearm (-Y), the fist's middle 8 cm into the hand from the wrist
    fist = hand + axis * 0.045
    yaw = math.degrees(math.atan2(axis.y, axis.x))
    glove = load(os.path.join(out, 'dass.glb'), 'dass')
    top = fist + V3((0, 0, 0.052)) - V3((math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), 0)) * (-0.015)
    place(glove, top, yaw)
    hooded = load(os.path.join(out, 'saker_hooded.glb'), 'saker_hooded')
    place(hooded, top + V3((0, 0, 0.002)), yaw)
    perch = load(os.path.join(out, 'wakr.glb'), 'wakr')
    place(perch, (0.0, -1.0, 0.30), -90)
    alert = load(os.path.join(out, 'saker_alert.glb'), 'saker_alert')
    place(alert, (0.0, -1.0, 0.30), -90)
    hb = load(os.path.join(out, 'houbara_alert.glb'), 'houbara_alert')
    place(hb, (0.0, 0.85, 0.0), -90)
    cu = load(os.path.join(out, 'curlew_alert.glb'), 'curlew_alert')
    place(cu, (0.0, 1.55, 0.0), -90)
    st = common.Studio(out, samples=12 if B.QUICK else 24)
    st.rig_lights(V3((0, 0.2, 0.8)), dist=3.2)
    # the camera on the figure's left (+X), looking across: the falcon on the fist and the birds in profile
    cy, cz, ortho = 0.25, 0.95, 3.4
    res = (900, 560) if B.QUICK else (1800, 1120)
    png = st.shot('birds_scale', (6.0, cy, cz), (0.0, cy, cz), ortho=ortho, res=res)
    pxmm = res[0] / (ortho * 1000)
    yg = res[1] / 2 + cz * 1000 * pxmm
    vruler(png, pxmm, 30, yg, 2000)
    B.finish(png)
    # a closer look at the fist: the hooded falcon on the glove beside the figure
    png = st.shot('birds_fist', fist + V3((1.1, -0.9, 0.25)), fist + V3((0, 0, 0.16)), lens=70, res=(800, 600) if B.QUICK else (1200, 900))
    B.finish(png)
