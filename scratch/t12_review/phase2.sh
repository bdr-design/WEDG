#!/bin/bash
# T12 reviewer, phase 2 driver. usage: phase2.sh <base> <head> "<build command, OUT = output folder>"
D=/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/t12_review
PY=/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/blendenv/bin/python
B=$1; H=$2; CMD=$3
bash $D/commits_check.sh $B $H > $D/p2_commits.log 2>&1
bash $D/repro.sh $H "$CMD" > $D/p2_repro.log 2>&1
: > $D/p2_measure.log
for g in $D/src/assets_src/canids/*.glb; do
  n=$(basename $g); ref=; pose=stand
  case $n in *wolf*) ref=wolf;; *guard*) ref=guard;; *stray*) ref=stray;; esac
  case $n in *stalk*) pose=stalk;; *lie*|*rest*|*lying*) pose=lie;; *bark*) pose=bark;; *carry*|*run*|*trot*) pose=other;; esac
  timeout 300 nice $PY -I $D/canid_check.py $g ${ref:+--ref $ref} --pose $pose >> $D/p2_measure.log 2>&1
done
echo done: p2_commits.log p2_repro.log p2_measure.log
