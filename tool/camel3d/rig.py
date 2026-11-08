"""Skeleton, skin weights and the first clips for the camel.

Clips (30 fps, in place; the game moves the camel):
  idle  - breathing, head and ear movement, tail swish (4 s loop)
  walk  - a pace: the two legs of one side move together, as camels walk
          (1.2 s per stride, about 1.25 m/s)
  graze - neck down to the ground, small bites (4 s loop)
"""
import sys, os, math
sys.path.insert(0, os.getcwd())
import bpy
from mathutils import Vector

PX, GROUND, U0 = 443.0, 1032.0, 700.0


def W(u, v, y=0.0):
    return Vector(((U0 - u) / PX, y, (GROUND - v) / PX))


bpy.ops.wm.open_mainfile(filepath=os.path.abspath('camel_lod0.blend'))
camel = bpy.data.objects['Camel']
sc = bpy.context.scene
sc.render.fps = 30

arm_data = bpy.data.armatures.new('CamelRig')
arm = bpy.data.objects.new('CamelRig', arm_data)
sc.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
FWD, UP = Vector((1, 0, 0)), Vector((0, 0, 1))


def bone(name, head, tail, parent=None, roll_to=UP, connect=False, deform=True):
    b = eb.new(name)
    b.head, b.tail = head, tail
    b.align_roll(roll_to)
    if parent:
        b.parent = eb[parent]
        b.use_connect = connect
    b.use_deform = deform
    return b


bone('root', Vector((0, 0, 0)), Vector((0, 0, 0.4)), deform=False)
bone('hips', W(1250, 380), W(1060, 340), 'root')
bone('spine', W(1060, 340), W(870, 320), 'hips', connect=True)
bone('chest', W(870, 320), W(680, 360), 'spine', connect=True)
neck = [W(650, 400), W(545, 430), W(455, 395), W(392, 300), W(352, 200), W(310, 128)]
bone('neck1', neck[0], neck[1], 'chest')
for i in range(1, 5):
    bone(f'neck{i + 1}', neck[i], neck[i + 1], f'neck{i}', connect=True)
bone('head', neck[5], W(150, 128), 'neck5', connect=True)
bone('lip', W(160, 165), W(118, 196), 'head')
for s, y in (('L', 1), ('R', -1)):
    bone(f'ear.{s}', W(342, 96, 0.055 * y), W(362, 60, 0.095 * y), 'head')
    f = [W(640, 455, .17 * y), W(702, 590, .17 * y), W(704, 800, .155 * y), W(694, 955, .15 * y), W(670, 1001, .15 * y), W(616, 1019, .15 * y)]
    bone(f'scapula.{s}', W(760, 270, .12 * y), f[0], 'chest', roll_to=FWD)
    bone(f'upperarm.{s}', f[0], f[1], f'scapula.{s}', roll_to=FWD, connect=True)
    bone(f'forearm.{s}', f[1], f[2], f'upperarm.{s}', roll_to=FWD, connect=True)
    bone(f'fcannon.{s}', f[2], f[3], f'forearm.{s}', roll_to=FWD, connect=True)
    bone(f'fpastern.{s}', f[3], f[4], f'fcannon.{s}', roll_to=FWD, connect=True)
    bone(f'ffoot.{s}', f[4], f[5], f'fpastern.{s}', roll_to=UP, connect=True)
    h = [W(1215, 420, .135 * y), W(1180, 560, .175 * y), W(1224, 765, .125 * y), W(1204, 955, .14 * y), W(1184, 1001, .14 * y), W(1133, 1019, .14 * y)]
    bone(f'thigh.{s}', h[0], h[1], 'hips', roll_to=FWD)
    bone(f'shin.{s}', h[1], h[2], f'thigh.{s}', roll_to=FWD, connect=True)
    bone(f'hcannon.{s}', h[2], h[3], f'shin.{s}', roll_to=FWD, connect=True)
    bone(f'hpastern.{s}', h[3], h[4], f'hcannon.{s}', roll_to=FWD, connect=True)
    bone(f'hfoot.{s}', h[4], h[5], f'hpastern.{s}', roll_to=UP, connect=True)
tail = [W(1295, 410), W(1300, 500), W(1305, 590), W(1310, 700)]
bone('tail1', tail[0], tail[1], 'hips')
bone('tail2', tail[1], tail[2], 'tail1', connect=True)
bone('tail3', tail[2], tail[3], 'tail2', connect=True)
bpy.ops.object.mode_set(mode='OBJECT')

# skin with automatic (heat) weights
bpy.ops.object.select_all(action='DESELECT')
camel.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
print('vertex groups', len(camel.vertex_groups))

# ------------------------------------------------------------ animation
pb = arm.pose.bones
for p in pb:
    p.rotation_mode = 'XYZ'
FPS = 30


def key(action_name, frames, fn):
    act = bpy.data.actions.new(action_name)
    act.use_fake_user = True
    arm.animation_data_create()
    arm.animation_data.action = act
    for f in range(frames + 1):
        t = f / frames
        for p in pb:
            p.rotation_euler = (0, 0, 0)
            p.location = (0, 0, 0)
        fn(t)
        for p in pb:
            p.keyframe_insert('rotation_euler', frame=f + 1)
            if p.name in ('root', 'hips'):
                p.keyframe_insert('location', frame=f + 1)
    for fc in getattr(act, 'fcurves', []):
        for kp in fc.keyframe_points:
            kp.interpolation = 'BEZIER'
    return act


def rx(name, deg):
    e = pb[name].rotation_euler
    pb[name].rotation_euler = (e[0] + math.radians(deg), e[1], e[2])


def rz(name, deg):
    e = pb[name].rotation_euler
    pb[name].rotation_euler = (e[0], e[1], e[2] + math.radians(deg))


def ry(name, deg):
    e = pb[name].rotation_euler
    pb[name].rotation_euler = (e[0], e[1] + math.radians(deg), e[2])


TAU = 2 * math.pi


def idle(t):
    br = math.sin(TAU * t * 2)
    rx('chest', 0.6 * br)
    rx('neck1', 1.5 * math.sin(TAU * t))
    rx('neck4', -1.2 * math.sin(TAU * t))
    rz('neck2', 4 * math.sin(TAU * t))
    rz('head', 6 * math.sin(TAU * t + 0.8))
    for s in 'LR':
        rx(f'ear.{s}', 12 * max(0, math.sin(TAU * t * 2 + (0 if s == 'L' else 1.7))) ** 6)
    rz('tail1', 10 * math.sin(TAU * t * 2))
    rz('tail2', 14 * math.sin(TAU * t * 2 - 0.6))
    rx('lip', 4 * math.sin(TAU * t * 4))


def leg_cycle(ph):
    """Sagittal angles for one leg at phase ph (0..1): stance then swing."""
    st = 0.62  # stance fraction for a walk
    if ph < st:
        k = ph / st
        swing = 18 - 36 * k          # foot moves back under the body
        lift = 0.0
    else:
        k = (ph - st) / (1 - st)
        swing = -18 + 36 * (0.5 - 0.5 * math.cos(math.pi * k))
        lift = math.sin(math.pi * k)
    return swing, lift


def walk(t):
    for s, side_ph in (('L', 0.0), ('R', 0.5)):
        sw, lift = leg_cycle((t + side_ph) % 1)       # pace: fore and hind together
        rx(f'upperarm.{s}', -sw * 0.75)
        rx(f'forearm.{s}', -sw * 0.25 + 42 * lift)    # the knee folds back in swing
        rx(f'fcannon.{s}', -48 * lift)
        rx(f'fpastern.{s}', 18 * lift)
        rx(f'thigh.{s}', -sw * 0.8)
        rx(f'shin.{s}', -30 * lift)
        rx(f'hcannon.{s}', 34 * lift)
        rx(f'hpastern.{s}', -16 * lift)
    bob = math.cos(TAU * t * 2)
    pb['hips'].location = (0, 0.012 * bob, 0)
    rz('hips', 3.0 * math.sin(TAU * t))               # pacing roll side to side
    rz('chest', -2.0 * math.sin(TAU * t))
    rx('neck1', 3 * bob)
    rx('neck3', -2 * bob)
    rx('head', -2.5 * bob)
    rz('tail1', 6 * math.sin(TAU * t))


def graze(t):
    down = 1.0
    rx('chest', -3 * down)
    rx('neck1', -40 * down)
    rx('neck2', -50 * down)
    rx('neck3', -30 * down)
    rx('neck4', -10 * down)
    rx('head', 62 * down)
    bite = max(0, math.sin(TAU * t * 6)) ** 2
    rx('head', 5 * bite)
    rx('lip', 10 * bite)
    rz('neck2', 6 * math.sin(TAU * t))
    rz('tail1', 8 * math.sin(TAU * t * 2))
    for s in 'LR':
        rx(f'upperarm.{s}', -6)
        rx(f'forearm.{s}', 3)
        rx(f'thigh.{s}', 3)


acts = {'idle': key('idle', 120, idle), 'walk': key('walk', 36, walk), 'graze': key('graze', 120, graze)}
for name, act in acts.items():
    tr = arm.animation_data.nla_tracks.new()
    tr.name = name
    tr.strips.new(name, 1, act)
arm.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('camel_rigged.blend'))
print('rigged and animated')
