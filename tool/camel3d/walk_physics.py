"""Walk built from foot physics, solved analytically, baked to joint keys.

- Footfall plan: each foot is planted while it carries weight and moves
  back under the body at exactly the ground speed (no slip, no float);
  then it lifts and swings forward on a smooth arc.
- Gait: lateral-sequence walk close to a pace (hind foot first, the
  forefoot of the same side 8% of a stride later), the camel's walk.
- Legs: each leg turns about its top pivot (top of the shoulder blade,
  hip joint) toward its foot; the lower two segments solve as a two-bone
  chain so the knee folds forward (forelimb carpus) and the hock folds
  back, as in the real animal. Planted pads stay flat on the ground.
- Body: drops only as much as the planted legs need to reach their feet
  (an inverted pendulum), pitches between fore and hind, shifts over the
  side carrying the weight and rolls away from it: the camel's rolling
  walk. Head steadies against the bob.
"""
import os, math, json
import bpy
from mathutils import Vector

SPEED = float(os.environ.get('SPEED', '0.85'))     # m/s, an unhurried walk (estimate)
CYCLE = float(os.environ.get('CYCLE', '1.3'))      # s per stride
DUTY = 0.65
FPS = 30
FRAMES = round(CYCLE * FPS)
STRIDE = SPEED * CYCLE
PHASE = {'hind.L': 0.0, 'fore.L': 0.08, 'hind.R': 0.5, 'fore.R': 0.58}
LIFT = {'fore': 0.13, 'hind': 0.10}

bpy.ops.wm.open_mainfile(filepath=os.path.abspath('camel_rigged.blend'))
arm = bpy.data.objects['CamelRig']
for tr in arm.animation_data.nla_tracks:
    tr.mute = True
arm.animation_data.action = None
pb = arm.pose.bones
for p in pb:
    p.rotation_mode = 'XYZ'
    p.rotation_euler = (0, 0, 0)
    p.location = (0, 0, 0)
bpy.context.view_layer.update()
MW = arm.matrix_world


def head(b):
    return MW @ pb[b].head


def tail(b):
    return MW @ pb[b].tail


CH = {}
for s in 'LR':
    CH[f'fore.{s}'] = dict(pivot=f'scapula.{s}', up=[f'scapula.{s}', f'upperarm.{s}'], a=f'forearm.{s}', b=f'fcannon.{s}',
                           pastern=f'fpastern.{s}', foot=f'ffoot.{s}', apex=+1)
    CH[f'hind.{s}'] = dict(pivot=f'thigh.{s}', up=[f'thigh.{s}'], a=f'shin.{s}', b=f'hcannon.{s}',
                           pastern=f'hpastern.{s}', foot=f'hfoot.{s}', apex=-1)
REST = {}
for leg, c in CH.items():
    P = head(c['pivot'])
    F = tail(c['b'])
    REST[leg] = dict(P=P, F=F, R=(F - P).length, la=pb[c['a']].bone.length, lb=pb[c['b']].bone.length,
                     dir_pastern=(tail(c['pastern']) - head(c['pastern'])).normalized(),
                     dir_foot=(tail(c['foot']) - head(c['foot'])).normalized())
HIP_TO_SHOULDER = (REST['fore.L']['P'] - head('hips')).length


def align(name, d):
    """Rotate a bone about its own lateral axis so it points along d (sagittal)."""
    p = pb[name]
    e = p.rotation_euler
    p.rotation_euler = (0, e[1], e[2])
    bpy.context.view_layer.update()
    m = (MW @ p.matrix).to_3x3()
    y0 = (m @ Vector((0, 1, 0))).normalized()
    xl = (m @ Vector((1, 0, 0))).normalized()
    dd = d - xl * d.dot(xl)
    if dd.length < 1e-9:
        return
    dd.normalize()
    ang = math.atan2(y0.cross(dd).dot(xl), y0.dot(dd))
    p.rotation_euler = (ang, e[1], e[2])
    bpy.context.view_layer.update()


def rotate_about(name, ang):
    p = pb[name]
    e = p.rotation_euler
    p.rotation_euler = (e[0] + ang, e[1], e[2])
    bpy.context.view_layer.update()


def foot_plan(ph):
    if ph < DUTY:
        k = ph / DUTY
        return STRIDE * DUTY * (0.5 - k), 0.0, 0.0
    k = (ph - DUTY) / (1 - DUTY)
    ease = 0.5 - 0.5 * math.cos(math.pi * k)
    return STRIDE * DUTY * (-0.5 + ease), math.sin(math.pi * k) ** 1.2, k


# ---- body motion from the planted legs
plan, need_f, need_h, shift = [], [], [], []
for f in range(FRAMES):
    t = f / FRAMES
    legs = {}
    for leg, ph in PHASE.items():
        dx, lift, k = foot_plan((t + ph) % 1.0)
        # mid-stance foot sits right under its pivot, as a weight-bearing column
        legs[leg] = (dx + (REST[leg]['P'].x - REST[leg]['F'].x), lift, k)
    nf = nh = 0.0
    for leg, (dx, lift, _) in legs.items():
        if lift:
            continue
        r = REST[leg]
        horiz = r['F'].x + dx - r['P'].x
        reach = r['R'] * 0.994
        drop = (r['P'].z - r['F'].z) - math.sqrt(max(reach * reach - horiz * horiz, 0))
        if leg.startswith('fore'):
            nf = max(nf, drop)
        else:
            nh = max(nh, drop)
    left = sum(1 for l, v in legs.items() if l.endswith('L') and not v[1])
    right = sum(1 for l, v in legs.items() if l.endswith('R') and not v[1])
    plan.append(legs)
    need_f.append(nf)
    need_h.append(nh)
    shift.append((right - left) / 2.0)


def smooth(vals, n=3):
    out = vals[:]
    for _ in range(n):
        out = [(out[i - 1] + 2 * out[i] + out[(i + 1) % len(out)]) / 4 for i in range(len(out))]
    return out


raw_f, raw_h = need_f[:], need_h[:]
need_f = [max(a, b) + 0.002 for a, b in zip(smooth(raw_f), raw_f)]
need_h = [max(a, b) + 0.002 for a, b in zip(smooth(raw_h), raw_h)]
shift = smooth(shift, 4)

deform = [p for p in pb if p.bone.use_deform]
baked, feet_world = [], []
prev = {p.name: p.rotation_euler.copy() for p in deform}
for f in range(FRAMES):
    t = f / FRAMES
    for p in pb:
        p.rotation_euler = (0, 0, 0)
        p.location = (0, 0, 0)
    dh, df = need_h[f], need_f[f]
    pitch = math.asin(max(-0.2, min(0.2, (df - dh) / HIP_TO_SHOULDER)))
    hips = pb['hips']
    # hips local axes: X = -world Y, Y ~ world X (forward), Z ~ world Z
    hips.location = (-0.03 * shift[f], 0.0, -dh)
    hips.rotation_euler = (-pitch, math.radians(-3.0 * shift[f]), 0)
    pb['neck1'].rotation_euler = (math.radians(1.8 * math.cos(4 * math.pi * t + 0.5)), 0, math.radians(1.5 * shift[f]))
    pb['head'].rotation_euler = (math.radians(-1.5 * math.cos(4 * math.pi * t + 0.5)) + pitch, 0, 0)
    pb['tail1'].rotation_euler = (0, 0, math.radians(6 * shift[f]))
    pb['tail2'].rotation_euler = (0, 0, math.radians(8 * math.sin(2 * math.pi * t - 0.8)))
    bpy.context.view_layer.update()
    fw = {}
    for leg, (dx, lift, k) in plan[f].items():
        c, r = CH[leg], REST[leg]
        kind = leg.split('.')[0]
        F = Vector((r['F'].x + dx, r['F'].y, r['F'].z + LIFT[kind] * lift))
        # 1. swing the whole leg about its top pivot toward the foot
        P = head(c['pivot'])
        cur = (tail(c['b']) - P)
        want = (F - P)
        ang = math.atan2(-(cur.x * want.z - cur.z * want.x), cur.x * want.x + cur.z * want.z)
        # rotation about local X (= -world Y on leg bones): flip sign accordingly
        for i, b in enumerate(c['up']):
            rotate_about(b, -ang if i == 0 else 0.0)
        # 2. two-bone solve for the lower leg, knee apex forward (fore) or back (hind)
        A = head(c['a'])
        la, lb = r['la'], r['lb']
        v = F - A
        dist = min(v.length, (la + lb) * 0.9995)
        cosA = (la * la + dist * dist - lb * lb) / (2 * la * dist)
        alpha = math.acos(max(-1.0, min(1.0, cosA)))
        base = math.atan2(v.z, v.x)
        a_ang = base + c['apex'] * alpha if base < 0 else base - c['apex'] * alpha
        # choose the solution whose joint lies on the apex side
        cand = []
        for sgn in (+1, -1):
            ang_a = base + sgn * alpha
            K = A + Vector((math.cos(ang_a) * la, 0, math.sin(ang_a) * la))
            side_val = (K - A).cross(F - A).y * -1  # >0 when K is in front of the A->F line (x forward)
            cand.append((side_val * c['apex'], K))
        K = max(cand, key=lambda z: z[0])[1]
        K.y = A.y
        align(c['a'], K - A)
        align(c['b'], Vector((F.x, A.y, F.z)) - head(c['b']))
        # 3. pads: flat on the ground while planted, toe trails in swing
        if lift == 0:
            align(c['pastern'], r['dir_pastern'])
            align(c['foot'], r['dir_foot'])
        else:
            flex = math.radians(38 if kind == 'fore' else 28) * math.sin(math.pi * k)
            align(c['pastern'], r['dir_pastern'])
            rotate_about(c['pastern'], flex if kind == 'fore' else flex)
            align(c['foot'], r['dir_foot'])
            rotate_about(c['foot'], 0.6 * flex)
        fw[leg] = (tail(c['foot']), head(c['foot']), tail(c['b']))
    row = {}
    for p in deform:
        e = p.rotation_euler.copy()
        e.make_compatible(prev[p.name])
        prev[p.name] = e
        row[p.name] = (tuple(e), tuple(p.location) if p.name == 'hips' else None)
    baked.append(row)
    feet_world.append(fw)

# ---- check: planted pads must not slip or sink; swinging pads must clear the ground
report = {}
for leg in PHASE:
    slip, planted_z, clear, fet_err = 0.0, [], [], 0.0
    for f in range(FRAMES):
        dx, lift, _ = plan[f][leg]
        toe, pad, fet = feet_world[f][leg]
        r = REST[leg]
        fet_err = max(fet_err, (fet - Vector((r['F'].x + dx, fet.y, r['F'].z + LIFT[leg.split('.')[0]] * lift))).length)
        if lift == 0:
            planted_z.append(min(toe.z, pad.z))
            nxt = plan[(f + 1) % FRAMES][leg]
            if nxt[1] == 0:
                toe2 = feet_world[(f + 1) % FRAMES][leg][0]
                slip = max(slip, abs((toe2.x - toe.x) + SPEED / FPS))
        else:
            clear.append(min(toe.z, pad.z))
    report[leg] = dict(slip_mm_per_frame=round(slip * 1000, 1),
                       planted_pad_height_mm=[round(min(planted_z) * 1000, 1), round(max(planted_z) * 1000, 1)],
                       swing_clearance_mm=round(max(clear) * 1000, 1),
                       fetlock_error_mm=round(fet_err * 1000, 1))
report['body_drop_mm'] = dict(fore=[round(min(need_f) * 1000), round(max(need_f) * 1000)],
                              hind=[round(min(need_h) * 1000), round(max(need_h) * 1000)])
report['stride_m'] = round(STRIDE, 2)
report['speed_mps'] = SPEED
print(json.dumps(report, indent=1))

# ---- replace the walk clip
old = bpy.data.actions.get('walk')
for tr in list(arm.animation_data.nla_tracks):
    if tr.name == 'walk':
        arm.animation_data.nla_tracks.remove(tr)
if old:
    bpy.data.actions.remove(old)
act = bpy.data.actions.new('walk')
act.use_fake_user = True
arm.animation_data.action = act
for f, row in enumerate(baked + [baked[0]]):
    for p in pb:
        p.rotation_euler = (0, 0, 0)
        p.location = (0, 0, 0)
    for name, (e, loc) in row.items():
        pb[name].rotation_euler = e
        pb[name].keyframe_insert('rotation_euler', frame=f + 1)
        if loc is not None:
            pb[name].location = loc
            pb[name].keyframe_insert('location', frame=f + 1)
tr = arm.animation_data.nla_tracks.new()
tr.name = 'walk'
tr.strips.new('walk', 1, act)
arm.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('camel_rigged.blend'))
json.dump({'speed_mps': SPEED, 'cycle_s': CYCLE, 'frames': FRAMES, 'report': report}, open('walk_meta.json', 'w'), indent=1)
print('walk rebuilt', FRAMES, 'frames')
