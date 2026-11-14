#!/bin/bash
# T11 reviewer. usage: repro.sh <commit> ["<args after OUT, e.g. all>"]
# Extracts the worker's commit into $D/src, runs `build.py OUT <args>` twice (run1, run2) under the audit hook,
# compares every GLB of the two runs (sha256, and JSON/BIN equality), lists files opened outside the source and
# the Python install, and any network or subprocess event.
set -e
D=/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/t17_review
PY=/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/blendenv/bin/python
C=$1; ARGS=${2:-all}
rm -rf $D/src $D/run1 $D/run2; mkdir -p $D/src $D/run1 $D/run2
git -C /home/user/wt/t17 archive $C | tar -x -C $D/src
for k in 1 2; do
  ( cd $D/src/tool/bird3d && timeout 900 $PY $D/audit_run.py $D/run$k/audit.log build.py $D/run$k $ARGS ) > $D/run$k/build.log 2>&1 || echo "run$k exit $?"
done
( cd $D/run1 && find . -name '*.glb' | sort ) | while read f; do
  a=$(sha256sum < $D/run1/$f | cut -c1-16); b=$(sha256sum < $D/run2/$f 2>/dev/null | cut -c1-16)
  echo "$f $a $b $([ "$a" = "$b" ] && echo SAME || echo DIFFERENT)"
done
echo "--- compare with the committed GLBs (assets_src/birds):"
for f in $D/src/assets_src/birds/*.glb; do n=$(basename $f); g=$(find $D/run1 -name $n | head -1)
  [ -n "$g" ] && echo "$n $(cmp -s $f $g && echo 'committed == built' || echo 'committed != built')" || echo "$n not built"; done
echo "--- files opened for reading outside the source / network / subprocess (run1):"
grep -v -E " $D/(src|run1)" $D/run1/audit.log | grep -v -E "^open w" | sort | uniq -c | sort -rn | head -40
