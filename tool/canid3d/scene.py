"""The pictures with more than one model: all of them beside the player's figure and a calf (scale), the wolf at night
at the game's distances (night), the winter coat beside the summer one (winter). Built from the GLB files just written
(run the animals first).

The calf: the game has no calf model; design/prototype3d/farm.html draws a calf a few days old as the grown she-camel
(assets_src/camels/camel_wodh_female.glb) at 0.55 of her size (its SIZE_AT, a game choice there). The calf of the
research's case [168] was three days old, so it is drawn the same way here.

The night: the game has no night yet (the prototype's sun is a fixed November afternoon). The night light here is my
choice: a full moon's cool light from high in the south-east and a faint sky. How the wolf reads at night must be
judged again when the game has its night.
"""
import math
import os

import bpy
from mathutils import Vector

import common
from common import V3

CALF_AGE_SCALE = 0.55      # farm.html's SIZE_AT at 0 to a few days


def load(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in list(new):
        if o.name.startswith('Icosphere'):
            bpy.data.objects.remove(o)
            new.remove(o)
    roots = [o for o in new if o.parent is None]
    return roots[0] if len(roots) == 1 else roots


def place(root, loc, yaw_deg=0.0, scale=1.0):
    root.rotation_mode = 'XYZ'
    root.rotation_euler = (0, 0, math.radians(yaw_deg))
    root.location = V3(loc)
    root.scale = (scale, scale, scale)


def world_bounds(objs):
    bpy.context.view_layer.update()
    lo = V3((1e9, 1e9, 1e9))
    hi = -lo
    for o in objs:
        for d in [o, *o.children_recursive]:
            if d.type != 'MESH':
                continue
            for c in d.bound_box:
                w = d.matrix_world @ V3(c)
                lo = V3(map(min, lo, w))
                hi = V3(map(max, hi, w))
    return lo, hi


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


def need(out, names):
    for n in names:
        if not os.path.exists(os.path.join(out, n)):
            raise SystemExit(f'{n} missing: build the animals first')


def calf():
    rig = load(CAMEL_PATH[0])
    rigs = rig if isinstance(rig, list) else [rig]
    for r in rigs:
        if r.type == 'ARMATURE' and r.animation_data:
            r.animation_data.action = None
    return rigs


CAMEL_PATH = [None]


def scale(B):
    out = B.OUT
    need(out, ['wolf_alert.glb', 'dog_alert.glb', 'stray_alert.glb'])
    B.fresh()
    CAMEL_PATH[0] = B.CAMEL
    man = load(B.MAN)
    man = man if not isinstance(man, list) else [o for o in man if o.type == 'ARMATURE'][0]
    if man.animation_data:
        man.animation_data.action = None
    place(man, (0.0, 0.0, 0.0), 90)                    # the figure faces -Y in its file: turned to face +X
    c = calf()
    lo, hi = world_bounds(c)
    for r in c:
        place(r, (0, 0, 0), 0, CALF_AGE_SCALE)
    lo, hi = world_bounds(c)
    for r in c:
        r.location.x = -0.55 - hi.x
    animals = [('wolf_alert.glb', 0.95), ('dog_alert.glb', 2.25), ('stray_alert.glb', 3.45)]
    for f, x in animals:
        r = load(os.path.join(out, f))
        lo, hi = world_bounds([r])
        place(r, (x - lo.x, 0.15, 0.0), 0)
    lo, hi = world_bounds([o for o in bpy.data.objects if o.parent is None])
    st = common.Studio(out, samples=12 if B.QUICK else 48)
    cx = (lo.x + hi.x) / 2
    w = hi.x - lo.x
    ortho = w * 1.22
    res = (1000, 460) if B.QUICK else (2000, 920)
    cz = ortho * res[1] / res[0] / 2 - 0.12
    st.rig_lights(V3((cx, 0, 0.8)), dist=max(w * 0.9, 3.0))
    png = st.shot('canids_scale', (cx, 9.0, cz), (cx, 0.0, cz), ortho=ortho, res=res)
    pxmm = res[0] / (ortho * 1000)
    yg = res[1] / 2 + cz * 1000 * pxmm
    x_r = res[0] / 2 - (hi.x + 0.12 - cx) * 1000 * pxmm      # (+X is to the picture's left: the ruler before the first)
    vruler(png, pxmm, max(x_r - 110, 12), yg, 2000)
    B.finish(png)


def night_light(st, moon=True):
    sc = st.sc
    for l in st.lights:
        bpy.data.objects.remove(l)
    st.lights = []
    w = sc.world.node_tree.nodes['Background']
    if moon:
        w.inputs[0].default_value = (0.05, 0.07, 0.12, 1)
        w.inputs[1].default_value = 0.35
        d = bpy.data.lights.new('moon', 'SUN')
        d.energy = 0.55
        d.color = (0.70, 0.80, 1.0)
        d.angle = math.radians(0.6)
    else:
        w.inputs[0].default_value = (0.62, 0.70, 0.82, 1)
        w.inputs[1].default_value = 0.9
        d = bpy.data.lights.new('sun', 'SUN')
        d.energy = 4.4
        d.color = (1.0, 0.86, 0.68)
        d.angle = math.radians(0.6)
    o = bpy.data.objects.new('key', d)
    sc.collection.objects.link(o)
    # the moon high in the south-east (the game's sun: low in the south-west, at 24 degrees)
    el, az = (math.radians(50), math.radians(135)) if moon else (math.radians(24), math.radians(300))
    o.rotation_euler = (V3((math.cos(el) * math.sin(az), math.cos(el) * math.cos(az), math.sin(el))) * -1).to_track_quat('-Z', 'Y').to_euler()
    st.lights.append(o)
    try:
        sc.view_settings.view_transform = 'Khronos PBR Neutral'      # the game's tone mapping
    except TypeError:
        pass


def night(B):
    """The stalking wolf (the far model) 3 m from a calf a few days old, seen from the game's camera (40 degrees
    vertical field of view, the owner's phone 956 x 440, the camera's offset (30, 21, 28) m from its target as
    farm.html places it over the camp, so 28 degrees down), at 20 m and at the game's 46 m; and the same at 46 m in
    the game's afternoon light for comparison."""
    out = B.OUT
    need(out, ['wolf_stalk_lod1.glb'])
    for dist, moon, name in ((20.0, True, 'wolf_night_20m'), (46.0, True, 'wolf_night_46m'), (46.0, False, 'wolf_day_46m')):
        B.fresh()
        CAMEL_PATH[0] = B.CAMEL
        c = calf()
        for r in c:
            place(r, (2.6, 1.2, 0.0), 160, CALF_AGE_SCALE)
        wolf = load(os.path.join(out, 'wolf_stalk_lod1.glb'))
        place(wolf, (0.0, 0.0, 0.0), -15)
        st = common.Studio(out, samples=16 if B.QUICK else 64, ground_col=(0.62, 0.50, 0.36), ground_size=400.0)
        night_light(st, moon)
        off = V3((30, 28, 21)).normalized() * dist                # (three.js y up: (30, 21, 28) is x, height, z)
        target = V3((1.0, 0.4, 0.4))
        st.cam_d.sensor_fit = 'VERTICAL'
        st.cam_d.angle_y = math.radians(40)
        st.cam.location = target + off
        common.look(st.cam, target)
        st.cam_d.type = 'PERSP'
        st.cam_d.clip_start = 0.1
        st.sc.render.resolution_x, st.sc.render.resolution_y = (956, 440)
        st.sc.render.resolution_percentage = 100
        png = os.path.join(out, name + '.png')
        st.sc.render.filepath = png
        bpy.ops.render.render(write_still=True)
        # the wolf's height on the screen, in css pixels
        bpy.context.view_layer.update()
        from bpy_extras.object_utils import world_to_camera_view
        lo, hi = world_bounds([wolf])
        ys = []
        for p in (V3((lo.x, lo.y, lo.z)), V3((hi.x, hi.y, hi.z)), V3((lo.x, hi.y, hi.z)), V3((hi.x, lo.y, lo.z))):
            ys.append(world_to_camera_view(st.sc, st.cam, p).y * 440)
        print(f'{name}: the wolf is about {max(ys) - min(ys):.0f} css px tall on the 956 x 440 screen')
        # a 3x enlargement of the wolf and calf beside it, so the picture can be read (not what the phone shows)
        from PIL import Image
        im = Image.open(png).convert('RGB')
        cw = world_to_camera_view(st.sc, st.cam, target)
        cx, cy = cw.x * 956, (1 - cw.y) * 440
        box = (int(cx - 80), int(cy - 50), int(cx + 80), int(cy + 50))
        crop = im.crop(box).resize((480, 300), Image.NEAREST)
        canvas = Image.new('RGB', (956 + 480 + 12, 440), (20, 20, 20))
        canvas.paste(im, (0, 0))
        canvas.paste(crop, (956 + 12, 70))
        from PIL import ImageDraw
        dr = ImageDraw.Draw(canvas)
        dr.rectangle(box, outline=(200, 60, 60), width=1)
        dr.text((956 + 12, 380), f'x3 of the red box ({dist:.0f} m)', fill=(220, 220, 220), font=common.font(16))
        canvas.save(png)
        B.finish(png)


def winter(B):
    """The summer coat (built) beside the winter coat (a thicker neck ruff and tail, the body a little fuller), side
    views at the same scale."""
    out = B.OUT
    need(out, ['wolf_alert.glb', 'wolf_winter_alert.glb'])
    B.fresh()
    a = load(os.path.join(out, 'wolf_alert.glb'))
    b = load(os.path.join(out, 'wolf_winter_alert.glb'))
    place(a, (0, 0, 0))
    place(b, (1.35, 0, 0))
    st = common.Studio(out, samples=12 if B.QUICK else 40)
    lo, hi = world_bounds([a, b])
    cx = (lo.x + hi.x) / 2
    w = hi.x - lo.x
    ortho = w * 1.1
    res = (1000, 400) if B.QUICK else (2000, 800)
    cz = ortho * res[1] / res[0] / 2 - 0.05
    st.rig_lights(V3((cx, 0, 0.5)), dist=2.4)
    png = st.shot('wolf_summer_winter', (cx, 6.0, cz), (cx, 0, cz), ortho=ortho, res=res)
    pxmm = res[0] / (ortho * 1000)
    yg = res[1] / 2 + cz * 1000 * pxmm
    vruler(png, pxmm, 14, yg, 1000)
    B.finish(png)


def far(B):
    """The far models (wolf, guard dog, stray, standing) from the game's camera at 15 m in the game's afternoon light,
    956 x 440 as the phone shows it, with a x4 enlargement of them beside it."""
    out = B.OUT
    need(out, ['wolf_alert_lod1.glb', 'dog_alert_lod1.glb', 'stray_alert_lod1.glb'])
    B.fresh()
    for i, f in enumerate(('wolf_alert_lod1.glb', 'dog_alert_lod1.glb', 'stray_alert_lod1.glb')):
        r = load(os.path.join(out, f))
        place(r, (0.0, (i - 1) * 1.1, 0.0), 0)
    st = common.Studio(out, samples=16 if B.QUICK else 64, ground_col=(0.62, 0.50, 0.36), ground_size=400.0)
    night_light(st, moon=False)
    dist = 15.0
    off = V3((30, 28, 21)).normalized() * dist
    target = V3((0.0, 0.0, 0.35))
    st.cam_d.sensor_fit = 'VERTICAL'
    st.cam_d.angle_y = math.radians(40)
    st.cam.location = target + off
    common.look(st.cam, target)
    st.cam_d.type = 'PERSP'
    st.sc.render.resolution_x, st.sc.render.resolution_y = (956, 440)
    st.sc.render.resolution_percentage = 100
    png = os.path.join(out, 'canids_far_15m.png')
    st.sc.render.filepath = png
    bpy.ops.render.render(write_still=True)
    from PIL import Image, ImageDraw
    from bpy_extras.object_utils import world_to_camera_view
    im = Image.open(png).convert('RGB')
    cw = world_to_camera_view(st.sc, st.cam, target)
    cx, cy = cw.x * 956, (1 - cw.y) * 440
    box = (int(cx - 70), int(cy - 45), int(cx + 70), int(cy + 45))
    crop = im.crop(box).resize((560, 360), Image.NEAREST)
    canvas = Image.new('RGB', (956 + 560 + 12, 440), (20, 20, 20))
    canvas.paste(im, (0, 0))
    canvas.paste(crop, (956 + 12, 40))
    dr = ImageDraw.Draw(canvas)
    dr.rectangle(box, outline=(200, 60, 60), width=1)
    dr.text((956 + 12, 410), 'x4 of the red box (15 m): the far models', fill=(220, 220, 220), font=common.font(16))
    canvas.save(png)
    B.finish(png)


def near(B):
    """The guard dog's head 1.5 m from the game's camera (40 degrees vertical field of view, 956 x 440, looking 28
    degrees down), in the game's afternoon light: the nearest the game brings it, beside the player."""
    out = B.OUT
    need(out, ['dog_alert.glb'])
    B.fresh()
    r = load(os.path.join(out, 'dog_alert.glb'))
    place(r, (0.0, 0.0, 0.0), 0)
    st = common.Studio(out, samples=16 if B.QUICK else 64, ground_col=(0.62, 0.50, 0.36), ground_size=400.0)
    night_light(st, moon=False)
    bpy.context.view_layer.update()
    head = [o for o in bpy.data.objects if o.name.startswith('head')]
    target = head[0].matrix_world.translation.copy() if head else V3((0.35, 0, 0.6))
    off = V3((30, 28, 21)).normalized() * 1.5
    st.cam_d.sensor_fit = 'VERTICAL'
    st.cam_d.angle_y = math.radians(40)
    st.cam.location = target + off
    common.look(st.cam, target)
    st.cam_d.type = 'PERSP'
    st.cam_d.clip_start = 0.05
    st.sc.render.resolution_x, st.sc.render.resolution_y = (956, 440)
    st.sc.render.resolution_percentage = 100
    png = os.path.join(out, 'dog_head_1m5_game_camera.png')
    st.sc.render.filepath = png
    bpy.ops.render.render(write_still=True)
    B.finish(png)
