#!/bin/sh
# The private car's interior and outside from the downloaded model (see thirdparty/README.md). Run from this folder:
#   sh thirdparty_build.sh <scene.gltf> <our suv.blend> <work dir> <out dir>
# Writes lc300_interior.glb (loaded only while the player is inside), lc300_near.glb and lc300_far.glb (the outside's layers).
set -e
PY=${BLENDPY:-../blendenv/bin/python}; W=$3; O=$4; T=$(dirname "$1")/textures
$PY thirdparty_frame.py "$1" $W/tp_car.blend
$PY -I thirdparty_tex.py "$T" $W/tex                                           # the brand names off the textures
$PY thirdparty_cabin.py $W/tp_car.blend "$2" $W/tp_cabin.blend
(cd interior && $PY lod_cabin.py $W/tp_cabin.blend $W/tp_cabin_seen.blend)       # the faces no occupant sees, dropped
$PY thirdparty_clean.py $W/tp_cabin_seen.blend $W/tp_cabin_game.blend 0.16
$PY thirdparty_car.py $W/tp_car.blend "$2" $W/tp_exterior.blend "$T"           # badges, paint, glass, plates; the interior's parts out
$PY thirdparty_lod.py $W/tp_exterior.blend $W/tp_ext_near.blend 40000
$PY thirdparty_lod.py $W/tp_exterior.blend $W/tp_ext_far.blend 12000 far
$PY thirdparty_export.py $W/tp_cabin_game.blend $O/lc300_interior.glb 2048
$PY thirdparty_export.py $W/tp_ext_near.blend $O/lc300_near.glb 1024
$PY thirdparty_export.py $W/tp_ext_far.blend $O/lc300_far.glb 1024
