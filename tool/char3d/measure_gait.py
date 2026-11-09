import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[-1])
rig = bpy.data.objects['rig']; sc = bpy.context.scene
for name, n in (('walk', 32), ('run', 21)):
    rig.animation_data.action = bpy.data.actions[name]
    down = {'.L': 0, '.R': 0}; both0 = 0; slide = []; prev = {}
    for f in range(n):
        sc.frame_set(f)
        st = {}
        for s in ('.L', '.R'):
            pb = rig.pose.bones['toes' + s]; ball = rig.matrix_world @ pb.head
            heel = rig.matrix_world @ rig.pose.bones['foot' + s].head
            on = min(ball.z, heel.z - 0.05) < 0.045
            st[s] = on; down[s] += on
            if on and s in prev and prev[s][0]: slide.append(abs(ball.y - prev[s][1].y) * 30)
            prev[s] = (on, ball.copy())
        both0 += not (st['.L'] or st['.R'])
    print(name, 'stance L %.0f%% R %.0f%%' % (100 * down['.L'] / n, 100 * down['.R'] / n), 'airborne frames', both0, 'planted ball speed m/s ~%.2f' % (sum(slide) / max(1, len(slide))))
