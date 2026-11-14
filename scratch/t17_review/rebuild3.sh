set -x
D=/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/t17_review; PY=/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/blendenv/bin/python
rm -rf $D/src $D/run1 $D/run2; mkdir -p $D/src $D/run1 $D/run2
git -C /home/user/wt/t17 archive 28b0cae tool/bird3d assets_src/birds | tar -x -C $D/src
for k in 1 2; do
 (cd $D/src/tool/bird3d && timeout 900 $PY $D/audit_run.py $D/run$k/audit_s.log rig.py $D/run$k saker > $D/run$k/build_s.log 2>&1)
 for b in houbara curlew; do (cd $D/src/tool/bird3d && timeout 900 $PY $D/audit_run.py $D/run$k/audit_$b.log rig_quarry.py $D/run$k $b > $D/run$k/build_$b.log 2>&1); done
done
for f in $D/run1/*.glb; do n=$(basename $f); echo "$n $(sha256sum < $f | cut -c1-12) $(sha256sum < $D/run2/$n | cut -c1-12) $(sha256sum < $D/src/assets_src/birds/$n | cut -c1-12)"; done
cat $D/run1/audit_*.log | grep -v -E " $D/(src|run1)" | grep -v "^open w" | grep -v /tmp/ | sort | uniq -c
echo REBUILD_DONE
