#!/bin/bash
# T12 reviewer. usage: repro.sh <commit> "<build command run inside tool/canid3d, OUT is replaced by the run folder>"
#   e.g. repro.sh abc123 "build.py OUT all"
# Extracts the worker's commit (from /home/user/wt/t12) into $D/src, runs the build twice under the audit hook
# (run1, run2), compares every GLB/JPEG of the two runs byte for byte, compares run1 with the committed
# assets_src/canids/*.glb, and lists files opened for reading outside the source and the Python/Blender install,
# and any socket or subprocess event. Light: nice, one run at a time; deletes nothing outside $D.
set -e
D=/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/t12_review
PY=/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/blendenv/bin/python
C=$1; CMD=${2:-"build.py OUT"}
rm -rf $D/src $D/run1 $D/run2; mkdir -p $D/src $D/run1 $D/run2
git -C /home/user/wt/t12 archive $C | tar -x -C $D/src
for k in 1 2; do
  ( cd $D/src/tool/canid3d && timeout 1500 nice $PY $D/audit_run.py $D/run$k/audit.log ${CMD//OUT/$D/run$k} ) > $D/run$k/build.log 2>&1 || echo "run$k exit $?"
done
( cd $D/run1 && find . \( -name '*.glb' -o -name '*.jpg' -o -name '*.png' \) | sort ) | while read f; do
  a=$(sha256sum < $D/run1/$f | cut -c1-16); b=$(sha256sum < $D/run2/$f 2>/dev/null | cut -c1-16)
  echo "$f $a $b $([ "$a" = "$b" ] && echo SAME || echo DIFFERENT)"
done
echo "--- run1 vs the committed GLBs (assets_src/canids):"
for f in $D/src/assets_src/canids/*.glb; do n=$(basename $f); g=$(find $D/run1 -name $n | head -1)
  [ -n "$g" ] && echo "$n $(cmp -s $f $g && echo 'committed == built' || echo 'committed != built')" || echo "$n NOT BUILT"; done
echo "--- files read outside the source / network / subprocess (run1):"
grep -v -E " $D/(src|run1)" $D/run1/audit.log | grep -v -E "^open w" | sort | uniq -c | sort -rn | head -40
