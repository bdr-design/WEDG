#!/bin/bash
# T11 reviewer round 3: own renders of the committed GLBs, before (262967f) and after (31af2df).
D=/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/t17_review; cd $D
N=/home/user/wt/t17/assets_src/birds; O=$D/before/assets_src/birds
r(){ name=$1; shift; for s in old new; do B=$([ $s = old ] && echo $O || echo $N); args=(); for x in "$@"; do args+=("${x//@B@/$B}"); done; python3 -I swrender.py r5/${name}_$s.png "${args[@]}" > /dev/null; done; }
r hood_head    side 0.15 0.05 0.30 0 @B@/saker_hooded.glb
r hood_tq      tq   0.25 0.03 0.28 0 @B@/saker_hooded.glb
r alert_head   side 0.15 0.05 0.30 0 @B@/saker_alert.glb
r alert_side   side 0.6  0.0 0.12 0 @B@/saker_alert.glb @B@/wakr.glb
r alert_front  front 0.6 0.0 0.12 0 @B@/saker_alert.glb @B@/wakr.glb
r feet_perch   side 0.15 0.0 0.02 0 @B@/saker_alert.glb @B@/wakr.glb
r fist_side    side 0.6  0.0 0.12 0 @B@/saker_fist.glb @B@/dass.glb
r fist_tq      tq   0.6  0.0 0.12 0 @B@/saker_fist.glb @B@/dass.glb
r fist_feet    tq   0.2  0.0 0.0 0 @B@/saker_fist.glb @B@/dass.glb
r hooded_feet  tq   0.2  0.0 0.0 0 @B@/saker_hooded.glb @B@/wakr.glb
r flight_below below 1.6 0.0 0 0 @B@/saker_flight.glb
r flight_side  side 0.8 0.15 0 0 @B@/saker_flight.glb
r houb_side    side 0.75 0.0 0.22 0 @B@/houbara_alert.glb
r houb_head    side 0.2 0.17 0.40 0 @B@/houbara_alert.glb
r houb_top     top  1.8 0.0 0 0 @B@/houbara_flight.glb
r houb_below   below 1.8 0.0 0 0 @B@/houbara_flight.glb
r cur_side     side 0.55 0.0 0.15 0 @B@/curlew_alert.glb
r cur_head     side 0.15 0.12 0.27 0 @B@/curlew_alert.glb
r cur_top      top  1.1 0.0 0 0 @B@/curlew_flight.glb
r flfeet_side  side 0.25 0.02 -0.02 0 @B@/saker_flight.glb
r flfeet_below below 0.25 0.02 0 0 @B@/saker_flight.glb
r flfeet_tq    tqb 0.3 0.02 -0.02 0 @B@/saker_flight.glb
r fist_front   front 0.2 0.0 0.0 0 @B@/saker_fist.glb @B@/dass.glb
r fist_toeside side 0.12 0.0 0.0 0 @B@/saker_fist.glb @B@/dass.glb
r houb_front   front 0.75 0.0 0.22 0 @B@/houbara_alert.glb
r houb_tq      tq 0.8 0.0 0.22 0 @B@/houbara_alert.glb
r houb_legs    side 0.4 0.0 0.12 0 @B@/houbara_alert.glb
