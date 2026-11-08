"""Camel walk from foot physics and real proportions, baked to joint keys.

Reference: Muybridge, Animal Locomotion (1887), Plate 737, a camel walking:
long strides, the legs of one side moving almost together, the forefoot
snatched up with the carpus folded hard, the hind hock folding under, the
pad rolling onto the toes before it leaves the ground.

- Footfalls: a planted foot moves back under the body at exactly the
  ground speed and stays on the ground (no slip, no float). The heel
  lifts as the pad rolls onto the toes in the last part of the stance.
- Forelimb: while it carries weight, forearm and cannon form one straight
  column (the carpus is locked); the shoulder blade turns with the stride
  and the shoulder and elbow take up the length. In the swing the carpus
  folds and the pastern curls.
- Hind limb: the thigh swings about the hip; shin and cannon solve with
  the hock folding back.
- Body: carried at the height the planted legs allow, with a small bob,
  a shift over the side carrying the weight and a roll away from it.
  The neck and head counter the bob.
"""
import os, math, json
import bpy
from mathutils import Vector

SPEED = float(os.environ.get('SPEED', '1.15'))     # m/s, about 4 km/h
CYCLE = float(os.environ.get('CYCLE', '1.45'))     # s per stride
DUTY = 0.62
FPS = 30
FRAMES = round(CYCLE * FPS)
STRIDE = SPEED * CYCLE
PHASE = {'hind.L': 0.0, 'fore.L': 0.08, 'hind.R': 0.5, 'fore.R': 0.58}
LIFT = {'fore': 0.20, 'hind': 0.15}
ROLL = {'fore': 0.035, 'hind': 0.045}
CENTER = {'fore': -0.05, 'hind': -0.04}
CARPUS = math.radians(78)    # carpus fold at mid-swing
CURL = {'fore': math.radians(55), 'hind': math.radians(42)}   # pastern curl at mid-swing

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
    p.scale = (1, 1, 1)
bpy.context.view_layer.update()
MW = arm.matrix_world


def head(b):
    return MW @ pb[b].head


def tail(b):
    return MW @ pb[b].tail


def update():
    bpy.context.view_layer.update()


def align(name, d):
    """Turn a bone about its own lateral axis so it points along d (sagittal plane)."""
    p = pb[name]
    e = p.rotation_euler
    p.rotation_euler = (0, e[1], e[2])
    update()
    m = (MW @ p.matrix).to_3x3()
    y0 = (m @ Vector((0, 1, 0))).normalized()
    xl = (m @ Vector((1, 0, 0))).normalized()
    dd = d - xl * d.dot(xl)
    if dd.length < 1e-9:
        return
    dd.normalize()
    p.rotation_euler = (math.atan2(y0.cross(dd).dot(xl), y0.dot(dd)), e[1], e[2])
    update()


def turn(name, ang):
    p = pb[name]
    e = p.rotation_euler
    p.rotation_euler = (e[0] + ang, e[1], e[2])
    update()


def two_bone(A, F, l1, l2, apex):
    """Joint of a planar two-segment chain A->J->F; apex +1 puts J in front (+x), -1 behind, 0 below."""
    v = F - A
    d = min(max(v.length, abs(l1 - l2) + 1e-4), (l1 + l2) * 0.9995)
    a = math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    base = math.atan2(v.z, v.x)
    cands = []
    for sgn in (1, -1):
        J = A + Vector((math.cos(base + sgn * a) * l1, 0, math.sin(base + sgn * a) * l1))
        cands.append(J)
    if apex == 0:
        J = min(cands, key=lambda q: q.z)
    else:
        J = max(cands, key=lambda q: -(q - A).cross(F - A).y * apex)
    J.y = A.y
    return J


def swing_angle(restv, want):
    return math.atan2(restv.x * want.z - restv.z * want.x, restv.x * want.x + restv.z * want.z)


CH = {}
for s in 'LR':
    CH[f'fore.{s}'] = dict(kind='fore', pivot=f'scapula.{s}', upper=f'upperarm.{s}', a=f'forearm.{s}', b=f'fcannon.{s}', pastern=f'fpastern.{s}', foot=f'ffoot.{s}')
    CH[f'hind.{s}'] = dict(kind='hind', pivot=f'thigh.{s}', upper=f'thigh.{s}', a=f'shin.{s}', b=f'hcannon.{s}', pastern=f'hpastern.{s}', foot=f'hfoot.{s}')
REST = {}
for leg, c in CH.items():
    P, F = head(c['pivot']), tail(c['b'])
    REST[leg] = dict(P=P, F=F, R=(F - P).length, T=tail(c['foot']),
                     lu=pb[c['upper']].bone.length, la=pb[c['a']].bone.length, lb=pb[c['b']].bone.length,
                     lp=pb[c['pastern']].bone.length, lf=pb[c['foot']].bone.length,
                     dp=(tail(c['pastern']) - head(c['pastern'])).normalized(), df=(tail(c['foot']) - head(c['foot'])).normalized())
for leg, r in REST.items():
    chain = (r['lu'] if leg.startswith('fore') else 0) + (pb[CH[leg]['pivot']].bone.length if leg.startswith('fore') else r['lu']) + r['la'] + r['lb']
    r['reach'] = min(r['R'] * (1.012 if leg.startswith('fore') else 1.045), chain * 0.985)
    print('REACH', leg, round(r['R'], 3), round(chain, 3), round(r['reach'], 3))
HIP_TO_SHOULDER = (REST['fore.L']['P'] - head('hips')).length


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def foot_plan(ph):
    """(dx, lift, swing progress, toe-off roll, stance progress)."""
    if ph < DUTY:
        k = ph / DUTY
        return STRIDE * DUTY * (0.5 - k), 0.0, 0.0, smoothstep(0.62, 1.0, k), k
    k = (ph - DUTY) / (1 - DUTY)
    ease = 0.5 - 0.5 * math.cos(math.pi * k)
    return STRIDE * DUTY * (-0.5 + ease), math.sin(math.pi * k ** 0.8), k, 0.0, 0.0


# ---- how low the body must ride for every planted leg to reach its foot
plan, shift = [], []
need = {'fore': [], 'hind': []}
for f in range(FRAMES):
    t = f / FRAMES
    legs = {}
    for leg, ph in PHASE.items():
        dx, lift, k, roll, ks = foot_plan((t + ph) % 1.0)
        kind = leg.split('.')[0]
        legs[leg] = (dx + (REST[leg]['P'].x - REST[leg]['F'].x) + CENTER[kind], lift, k, roll, ks)
    nd = {'fore': 0.0, 'hind': 0.0}
    for leg, (dx, lift, _, roll, _) in legs.items():
        if lift:
            continue
        r, kind = REST[leg], leg.split('.')[0]
        horiz = r['F'].x + dx - r['P'].x
        fz = r['F'].z + ROLL[kind] * roll
        nd[kind] = max(nd[kind], (r['P'].z - fz) - math.sqrt(max(r['reach'] ** 2 - horiz * horiz, 0)))
    for kind in nd:
        need[kind].append(nd[kind])
    left = sum(1 for l, v in legs.items() if l.endswith('L') and not v[1])
    right = sum(1 for l, v in legs.items() if l.endswith('R') and not v[1])
    shift.append((right - left) / 2.0)
    plan.append(legs)


def smooth(vals, n=4):
    out = vals[:]
    for _ in range(n):
        out = [(out[i - 1] + 2 * out[i] + out[(i + 1) % len(out)]) / 4 for i in range(len(out))]
    return out


# a steady carriage at the lowest height the stride needs, plus a gentle bob
base = {k: max(v) + 0.004 for k, v in need.items()}
bob = [0.012 * (0.5 + 0.5 * math.cos(4 * math.pi * (f / FRAMES) - 0.6)) for f in range(FRAMES)]
drop = {k: [base[k] + bob[f] for f in range(FRAMES)] for k in base}
shift = smooth(shift)

deform = [p for p in pb if p.bone.use_deform]
prev = {p.name: p.rotation_euler.copy() for p in deform}
baked, feet = [], []
for f in range(FRAMES):
    t = f / FRAMES
    for p in pb:
        p.rotation_euler = (0, 0, 0)
        p.location = (0, 0, 0)
        p.scale = (1, 1, 1)
    dh, df = drop['hind'][f], drop['fore'][f]
    pitch = math.asin(max(-0.2, min(0.2, (df - dh) / HIP_TO_SHOULDER)))
    pb['hips'].location = (-0.035 * shift[f], 0.0, -dh)
    pb['hips'].rotation_euler = (-pitch, math.radians(-3.2 * shift[f]), 0)
    pb['neck1'].rotation_euler = (math.radians(3.0 * math.cos(4 * math.pi * t + 0.5)), 0, math.radians(2.0 * shift[f]))
    pb['neck3'].rotation_euler = (math.radians(-1.6 * math.cos(4 * math.pi * t + 1.1)), 0, 0)
    pb['head'].rotation_euler = (math.radians(-1.8 * math.cos(4 * math.pi * t + 0.5)) + pitch, 0, math.radians(-1.2 * shift[f]))
    pb['tail1'].rotation_euler = (0, 0, math.radians(7 * shift[f]))
    pb['tail2'].rotation_euler = (0, 0, math.radians(10 * math.sin(2 * math.pi * t - 0.8)))
    update()
    fw = {}
    for leg, (dx, lift, k, roll, ks) in plan[f].items():
        c, r = CH[leg], REST[leg]
        kind = c['kind']
        F = Vector((r['F'].x + dx + 0.035 * roll, r['F'].y, r['F'].z + LIFT[kind] * lift + ROLL[kind] * roll))
        T = Vector((r['T'].x + dx, r['T'].y, r['T'].z))
        swing = math.sin(math.pi * min(1.0, k * 1.1)) if lift else 0.0
        ang = swing_angle(r['F'] - r['P'], F - head(c['pivot']))
        if kind == 'fore':
            turn(c['pivot'], 0.4 * ang)                     # the shoulder blade takes part of the swing
        else:
            turn(c['upper'], ang)                           # thigh swings about the hip
        # the legs splay a little, so aim, measure the miss and re-aim until the fetlock lands on target
        aim = F.copy()
        for _ in range(5):
            if kind == 'fore':
                S = head(c['upper'])
                flex = CARPUS * swing
                col = math.sqrt(r['la'] ** 2 + r['lb'] ** 2 + 2 * r['la'] * r['lb'] * math.cos(flex))
                E = two_bone(S, aim, r['lu'], col, -1)        # the elbow points back
                align(c['upper'], E - S)
                K = two_bone(head(c['a']), aim, r['la'], r['lb'], +1)   # carpus folds forward, the cannon tucks back
                align(c['a'], K - head(c['a']))
                align(c['b'], Vector((aim.x, K.y, aim.z)) - head(c['b']))
            else:
                St = tail(c['upper'])
                Kh = two_bone(St, aim, r['la'], r['lb'], -1)  # the hock points back
                align(c['a'], Kh - St)
                align(c['b'], Vector((aim.x, Kh.y, aim.z)) - head(c['b']))
            miss = F - tail(c['b'])
            miss.y = 0
            if miss.length < 0.002:
                break
            aim += miss
        Fw = tail(c['b'])
        if lift == 0:
            # pastern and pad between the fetlock and the planted toes; the heel lifts as the pad rolls
            Tw = Vector((T.x, Fw.y, T.z))
            aimT = Tw.copy()
            for _ in range(5):
                Pd = two_bone(Fw, aimT, r['lp'], r['lf'], 0)
                align(c['pastern'], Pd - Fw)
                align(c['foot'], Vector((aimT.x, Pd.y, aimT.z)) - tail(c['pastern']))
                miss = Tw - tail(c['foot'])
                miss.y = 0
                if miss.length < 0.002:
                    break
                aimT += miss
            load = max(0.0, min(1.0, ks / 0.12, (1 - ks) / 0.2))
            load = load * load * (3 - 2 * load)
            pb[c['foot']].scale = (1 + 0.13 * load, 1 + 0.03 * load, 1 - 0.10 * load)
            update()
        else:
            align(c['pastern'], r['dp'])
            turn(c['pastern'], CURL[kind] * swing)
            align(c['foot'], r['df'])
            turn(c['foot'], 0.55 * CURL[kind] * swing)
        fw[leg] = (tail(c['foot']).copy(), tail(c['pastern']).copy(), tail(c['b']).copy(), F)
    row = {}
    for p in deform:
        e = p.rotation_euler.copy()
        e.make_compatible(prev[p.name])
        prev[p.name] = e
        row[p.name] = (tuple(e), tuple(p.location) if p.name == 'hips' else None, tuple(p.scale) if 'foot' in p.name else None)
    baked.append(row)
    feet.append(fw)

# ---- checks
report = {}
for leg in PHASE:
    slip, toe_z, clear, ferr = 0.0, [], [], 0.0
    for f in range(FRAMES):
        dx, lift, _, roll, _ = plan[f][leg]
        toe, padp, fet, Ft = feet[f][leg]
        ferr = max(ferr, math.hypot(fet.x - Ft.x, fet.z - Ft.z))
        if lift == 0:
            toe_z.append(toe.z)
            if plan[(f + 1) % FRAMES][leg][1] == 0:
                slip = max(slip, abs((feet[(f + 1) % FRAMES][leg][0].x - toe.x) + SPEED / FPS))
        else:
            clear.append(min(toe.z, padp.z))
    report[leg] = dict(toe_slip_mm_per_frame=round(slip * 1000, 1), planted_toe_height_mm=[round(min(toe_z) * 1000, 1), round(max(toe_z) * 1000, 1)],
                       swing_clearance_mm=round(max(clear) * 1000), fetlock_error_mm=round(ferr * 1000, 1))
report['carriage_drop_mm'] = {k: round(base[k] * 1000) for k in base}
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
        p.scale = (1, 1, 1)
    for name, (e, loc, scl) in row.items():
        pb[name].rotation_euler = e
        pb[name].keyframe_insert('rotation_euler', frame=f + 1)
        if loc is not None:
            pb[name].location = loc
            pb[name].keyframe_insert('location', frame=f + 1)
        if scl is not None:
            pb[name].scale = scl
            pb[name].keyframe_insert('scale', frame=f + 1)
tr = arm.animation_data.nla_tracks.new()
tr.name = 'walk'
tr.strips.new('walk', 1, act)
arm.animation_data.action = None
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath('camel_rigged.blend'))
json.dump({'speed_mps': SPEED, 'cycle_s': CYCLE, 'frames': FRAMES, 'report': report}, open('walk_meta.json', 'w'), indent=1)
print('walk rebuilt', FRAMES, 'frames')
