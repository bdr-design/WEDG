"""Measure the baked walk: joint bend directions, footfall order, pastern direction in swing, side shift."""
import os, sys, json, math
import bpy
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(os.environ.get('BLEND', 'camel_rigged.blend')))
arm = bpy.data.objects['CamelRig']
for tr in arm.animation_data.nla_tracks:
    tr.mute = True
arm.animation_data.action = bpy.data.actions['walk']
pb = arm.pose.bones
MW = arm.matrix_world
sc = bpy.context.scene
H = lambda b: MW @ pb[b].head
T = lambda b: MW @ pb[b].tail


def side(J, A, F):
    """signed distance of J from line A->F in the xz plane, + = forward (+x)."""
    d = Vector((F.x - A.x, F.z - A.z)).normalized()
    n = Vector((-d.y, d.x))          # normal; make it point forward
    if n.x < 0:
        n = -n
    return (Vector((J.x - A.x, J.z - A.z))).dot(n)


N = 44
rows = []
for f in range(1, N + 1):
    sc.frame_set(f)
    r = {}
    for s in 'LR':
        sh, el, ca, fe = H(f'upperarm.{s}'), H(f'forearm.{s}'), H(f'fcannon.{s}'), T(f'fcannon.{s}')
        st, ho, hf = H(f'shin.{s}'), H(f'hcannon.{s}'), T(f'hcannon.{s}')
        toeF, toeH = T(f'ffoot.{s}'), T(f'hfoot.{s}')
        pf = T(f'fpastern.{s}') - H(f'fpastern.{s}')
        ph = T(f'hpastern.{s}') - H(f'hpastern.{s}')
        r[s] = dict(elbow_vs_shoulder=round((el.x - sh.x) * 1000), carpus=round(side(ca, el, fe) * 1000), hock=round(side(ho, st, hf) * 1000),
                    toeF=(round(toeF.x, 3), round(toeF.z * 1000)), toeH=(round(toeH.x, 3), round(toeH.z * 1000)),
                    pastF=round(math.degrees(math.atan2(pf.x, -pf.z))), pastH=round(math.degrees(math.atan2(ph.x, -ph.z))))
    r['hips_y'] = round((MW @ pb['hips'].head).y * 1000)
    r['hips_z'] = round((MW @ pb['hips'].head).z * 1000)
    rows.append(r)
json.dump(rows, open(os.environ.get('OUT', 'gait.json'), 'w'))
for f, r in enumerate(rows):
    if f % 3 == 0:
        L = r['L']
        print(f + 1, 'L elbow-sh', L['elbow_vs_shoulder'], 'carpus', L['carpus'], 'hock', L['hock'], 'toeFz', L['toeF'][1], 'toeHz', L['toeH'][1],
              'pastF', L['pastF'], 'pastH', L['pastH'], 'hips y', r['hips_y'], 'z', r['hips_z'])
