"""Walk and idle cycles for the character, made from a footfall plan and two-bone IK, then a GLB export.
Run: blendenv/bin/python char_walk.py <character.blend> <out_dir> [render]
"""
import bpy, sys, os, math, numpy as np
from mathutils import Vector, Matrix, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blendchar import point, stage, shoot

SRC, OUT = sys.argv[-3], sys.argv[-2]
RENDER = sys.argv[-1] == 'render'
bpy.ops.wm.open_mainfile(filepath=SRC)
rig = bpy.data.objects['rig']
FPS = 30
bpy.context.scene.render.fps = FPS
rest = {b.name: (Vector(b.head_local), Vector(b.tail_local)) for b in rig.data.bones}
blen = {n: (t - h).length for n, (h, t) in rest.items()}
GROUND_ANKLE = rest['foot.L'][0].z            # ankle height with the sole flat on the ground

def reset():
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = (1, 0, 0, 0); pb.location = (0, 0, 0)
    bpy.context.view_layer.update()

def set_hips(offset, yaw, roll):
    pb = rig.pose.bones['hips']
    h = rest['hips'][0]
    M = Matrix.Translation(h + Vector(offset)) @ (Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(roll, 4, 'Y')) @ Matrix.Translation(-h) @ pb.bone.matrix_local
    pb.matrix = M; bpy.context.view_layer.update()

def turn(name, axis, angle):
    """Rotate a pose bone about a world-space axis through its head."""
    bpy.context.view_layer.update()
    pb = rig.pose.bones[name]; cur = pb.matrix.copy(); h = cur.to_translation()
    pb.matrix = Matrix.Translation(h) @ Matrix.Rotation(angle, 4, Vector(axis)) @ Matrix.Translation(-h) @ cur
    bpy.context.view_layer.update()

def leg(s, ankle, toe_pitch, toe_bend):
    hip = Vector(rig.pose.bones['thigh' + s].head)
    L1, L2 = blen['thigh' + s], blen['shin' + s]
    d = (ankle - hip); dist = min(d.length, L1 + L2 - 1e-4); dn = d.normalized()
    a = (L1 * L1 - L2 * L2 + dist * dist) / (2 * dist); h = math.sqrt(max(L1 * L1 - a * a, 0))
    hint = Vector((0, -1, 0)); perp = (hint - dn * hint.dot(dn)).normalized()
    knee = hip + dn * a + perp * h
    point(rig, 'thigh' + s, knee - hip)
    point(rig, 'shin' + s, (hip + dn * dist) - knee)
    # the foot keeps its rest direction, pitched about the side axis; the toes bend back at push-off
    f0 = (rest['foot' + s][1] - rest['foot' + s][0]).normalized()
    point(rig, 'foot' + s, Matrix.Rotation(-toe_pitch, 3, 'X') @ f0)
    t0 = (rest['toes' + s][1] - rest['toes' + s][0]).normalized()
    point(rig, 'toes' + s, Matrix.Rotation(-(toe_pitch + toe_bend), 3, 'X') @ t0)

def arm(s, swing, bend):
    sx = 1 if s == '.L' else -1
    up = Vector((0.14 * sx, 0.03, -1)).normalized()
    up = Matrix.Rotation(-swing, 3, 'X') @ up               # positive swing brings the hand forward (-y)
    point(rig, 'upperarm' + s, up)
    fa = Matrix.Rotation(-(swing + bend), 3, 'X') @ Vector((0.07 * sx, -0.20, -1)).normalized()
    point(rig, 'forearm' + s, fa)
    point(rig, 'hand' + s, Matrix.Rotation(-(swing + bend * 1.1), 3, 'X') @ Vector((0.03 * sx, -0.10, -1)).normalized())

def skirt():
    """Swing the four skirt panels so the cloth clears every part of both legs (shin, ankle, foot, toes)."""
    HEM = 0.10
    head = Vector(rig.pose.bones['skirt.F'].head)
    span = head.z - HEM
    need = {'skirt.F': -0.19, 'skirt.B': 0.17, 'skirt.L': 0.25, 'skirt.R': -0.25}
    side_y = {}
    for s in ('.L', '.R'):
        k = Vector(rig.pose.bones['shin' + s].head); a = Vector(rig.pose.bones['foot' + s].head)
        t0 = Vector(rig.pose.bones['toes' + s].head); t1 = Vector(rig.pose.bones['toes' + s].tail)
        pts = [k.lerp(a, u / 6) for u in range(0, 7)] + [a.lerp(t0, 0.5), t0, t1]      # the knee too: it comes forward in the run
        for p in pts:
            if p.z > head.z - 0.05: continue
            reach = span / (head.z - p.z)                 # how far the hem must go for the panel to pass this point
            m = 0.045 + 0.05 * max(0.0, min(1.0, (0.45 - p.z) / 0.35))   # the shin is thin up high, the foot and the sandal low down
            need['skirt.F'] = min(need['skirt.F'], head.y + (p.y - m - head.y) * reach)
            need['skirt.B'] = max(need['skirt.B'], head.y + (p.y + m - head.y) * reach)
            if s == '.L': need['skirt.L'] = max(need['skirt.L'], head.x + (p.x + m - head.x) * reach)
            else: need['skirt.R'] = min(need['skirt.R'], head.x + (p.x - m - head.x) * reach)
        hk = k.lerp(a, max(0.0, min(1.0, (k.z - HEM) / max(1e-4, k.z - a.z))))
        side_y[s] = hk.y
    tgt = {'skirt.F': Vector((0, need['skirt.F'], HEM)), 'skirt.B': Vector((0, need['skirt.B'], HEM)),
           'skirt.L': Vector((need['skirt.L'], side_y['.L'], HEM)), 'skirt.R': Vector((need['skirt.R'], side_y['.R'], HEM))}
    for n, p in tgt.items(): point(rig, n, p - head)

def key_all(frame):
    for pb in rig.pose.bones:
        pb.keyframe_insert('rotation_quaternion', frame=frame)
        pb.keyframe_insert('location', frame=frame)

def smooth(t): return t * t * (3 - 2 * t)

def gait(name, speed, period, duty, lift, bob, arm_swing, lean, sink, elbow):
    """One cycle. speed m/s; period s; duty = share of the cycle a foot is on the ground."""
    act = bpy.data.actions.new(name); rig.animation_data_create(); rig.animation_data.action = act
    n = int(round(period * FPS)); travel = speed * period * duty      # how far a planted foot slides back under the body
    front = -travel * 0.42
    for f in range(n + 1):
        t = (f % n) / n
        reset()
        # pelvis: lowest just after each heel strike, highest at mid-stance; a little sway over the standing leg
        z = -sink - bob * math.cos(4 * math.pi * (t - 0.12))
        set_hips((0.012 * math.sin(2 * math.pi * t), 0, z), 0.07 * math.sin(2 * math.pi * t), -0.03 * math.sin(2 * math.pi * t))
        turn('spine', (1, 0, 0), lean)                               # lean into the walk
        turn('spine', (0, 0, 1), -0.09 * math.sin(2 * math.pi * t))  # the chest turns against the pelvis
        turn('neck', (0, 0, 1), 0.03 * math.sin(2 * math.pi * t))
        turn('neck', (1, 0, 0), -lean * 0.6)
        for s, ph in (('.L', 0.0), ('.R', 0.5)):
            p = (t + ph) % 1.0
            base = rest['foot' + s][0]
            if p < duty:
                u = p / duty
                y = front + travel * u
                heel = max(0.0, (u - 0.62) / 0.38)                 # heel rises late in stance
                zz = GROUND_ANKLE + 0.055 * heel ** 1.4
                pitch = 0.20 * max(0.0, 1 - u / 0.12) - 0.55 * heel ** 1.2
                bend = 0.55 * heel ** 1.2                           # equal to the heel lift: the toes stay flat
            else:
                u = (p - duty) / (1 - duty)
                y = front + travel - travel * smooth(u)
                zz = GROUND_ANKLE + 0.035 * (1 - u) + lift * math.sin(math.pi * min(1.0, u * 1.15)) ** 1.5
                pitch = -0.55 * (1 - smooth(min(1.0, u * 2.2))) + 0.20 * smooth(max(0.0, (u - 0.6) / 0.4))
                bend = 0.55 * max(0.0, 1 - u * 3)
            leg(s, Vector((base.x * 0.92, y + base.y, zz)), pitch, bend)
            # the arm swings against its own leg
            arm(s, arm_swing * math.cos(2 * math.pi * (p - 0.0)) * -1, elbow + 0.12 * max(0.0, -math.cos(2 * math.pi * p)))
        skirt()
        key_all(f)
    return act

def idle(n=90):
    act = bpy.data.actions.new('idle'); rig.animation_data.action = act
    for f in range(n + 1):
        t = f / n; reset()
        set_hips((0, 0, -0.004 - 0.004 * math.sin(2 * math.pi * t)), 0, 0)
        turn('chest', (1, 0, 0), 0.012 * math.sin(2 * math.pi * t))      # breathing
        for s in ('.L', '.R'):
            leg(s, Vector((rest['foot' + s][0].x, rest['foot' + s][0].y, GROUND_ANKLE)), 0, 0)
            arm(s, 0.0, 0.16)
        skirt()
        key_all(f)
    return act

walk = gait('walk', speed=1.25, period=1.05, duty=0.60, lift=0.075, bob=0.014, arm_swing=0.30, lean=0.04, sink=0.045, elbow=0.18)
run = gait('run', speed=3.4, period=0.70, duty=0.36, lift=0.16, bob=0.03, arm_swing=0.55, lean=0.12, sink=0.07, elbow=1.25)
idl = idle()
for a in (walk, run, idl): a.use_fake_user = True
rig.animation_data.action = walk

if RENDER:
    sc, cam = stage(res=(500, 900), samples=16)
    for f in (0, 8, 15, 23):
        sc.frame_set(f)
        shoot(sc, cam, f'{OUT}/walk_{f:02d}.png', (5, 0, 0.95), (1.5708, 0, 1.5708), ortho=2.0)
    rig.animation_data.action = run
    for f in (0, 5, 10, 16):
        sc.frame_set(f)
        shoot(sc, cam, f'{OUT}/run_{f:02d}.png', (5, 0, 0.95), (1.5708, 0, 1.5708), ortho=2.0)
    rig.animation_data.action = walk
    sc.frame_set(8); sc.render.resolution_x, sc.render.resolution_y = (900, 900)
    shoot(sc, cam, f'{OUT}/walk_34.png', (2.6, -3.4, 1.3), (1.38, 0, 0.66), lens=45)
    # a looping side view of the walk for the owner
    sc.render.resolution_x, sc.render.resolution_y = (360, 560); sc.cycles.samples = 12
    os.makedirs(f'{OUT}/gif', exist_ok=True)
    for f in range(30):
        sc.frame_set(f)
        shoot(sc, cam, f'{OUT}/gif/w{f:02d}.png', (4.2, -1.6, 0.95), (1.5708, 0, 1.2), ortho=2.0)

bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/animated.blend')
# one GLB with the three clips, for the prototype
for img in bpy.data.images:
    if img.size[0] > 1024: img.scale(1024, 1024)
for ob in bpy.data.objects:
    ob.select_set(ob.type in ('MESH', 'ARMATURE'))
for tr in list(rig.animation_data.nla_tracks): rig.animation_data.nla_tracks.remove(tr)
rig.animation_data.action = None
bpy.ops.export_scene.gltf(filepath=f'{OUT}/man.glb', export_format='GLB', use_selection=True, export_animations=True,
                          export_animation_mode='ACTIONS', export_skins=True, export_apply=False, export_yup=True,
                          export_image_format='JPEG', export_jpeg_quality=88)
print('exported', os.path.getsize(f'{OUT}/man.glb'))
