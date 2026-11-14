#!/bin/bash
# T11 reviewer, phase 2. usage: phase2.sh <commit>   (after repro.sh <commit> has built run1/ run2/)
# Measures every GLB of the commit (committed copies in src/assets_src/birds), overlays the silhouettes on the
# traced references, dumps the textures for judging the plumage by eye, and checks the pictures' exposure.
D=/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/t17_review
cd $D; mkdir -p p2; G=$D/src/assets_src/birds
for f in $G/*.glb; do
  n=$(basename $f .glb); ref=; pose=
  case $n in *saker*|*falcon*|*hurr*) ref=saker_f;; *houbara*|*hubara*) ref=houbara;; *curlew*|*karawan*) ref=curlew;; esac
  case $n in *fly*|*flight*) pose=flight;; esac
  python3 -I bird_check.py $f ${ref:+--ref $ref} ${pose:+--pose $pose} > p2/$n.check.txt 2>&1
  grep -E "^draws|CHECK|memory|flag" p2/$n.check.txt | sed "s|^|$n: |"
  python3 -I dump_tex.py $f p2/tex > /dev/null 2>&1
  case $n in *lod1*|*far*|*gear*) continue;; esac
  case "$ref:$pose" in
    saker_f:flight) timeout 300 python3 -I bird_sil.py $f outl/saker_flight_below.json p2/$n --view below --fit width;;
    saker_f:)       timeout 300 python3 -I bird_sil.py $f outl/saker_perch_side.json p2/$n --axis x;;
    houbara:)       timeout 300 python3 -I bird_sil.py $f outl/houbara_side.json p2/$n --axis x;;
    curlew:)        timeout 300 python3 -I bird_sil.py $f outl/curlew_side.json p2/$n --axis x;;
  esac 2>&1 | grep -E "IoU" | sed "s|^|$n: |"
done
python3 -I pic_check.py $D/src/design/birds/*.jpg
