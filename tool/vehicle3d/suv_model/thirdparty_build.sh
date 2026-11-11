#!/bin/sh
# The private car's interior and outside from the downloaded model (see thirdparty/README.md). Run from this folder:
#   sh thirdparty_build.sh <scene.gltf> <our suv.blend> <work dir> <out dir>
# Writes lc300_interior.glb (loaded only while the player is inside), lc300_near.glb and lc300_far.glb (the outside's layers).
set -e
# BLENDPY: the Python with Blender's bpy module (required). The work and out dirs are made absolute (a step runs in interior/).
[ -x "$BLENDPY" ] || { echo "set BLENDPY to the python with bpy" >&2; exit 1; }
# (PY absolute, but not through realpath: a venv's python is a link)
PY=$(cd "$(dirname "$BLENDPY")" && pwd)/$(basename "$BLENDPY"); mkdir -p "$3" "$4"; W=$(realpath "$3"); O=$(realpath "$4"); T=$(realpath "$(dirname "$1")")/textures
$PY thirdparty_frame.py "$1" $W/tp_car.blend
$PY -I thirdparty_tex.py "$T" $W/tex                                           # the brand names off the textures
$PY thirdparty_cabin.py $W/tp_car.blend "$2" $W/tp_cabin.blend
(cd interior && $PY lod_cabin.py $W/tp_cabin.blend $W/tp_cabin_seen.blend driver)       # the faces the driver cannot see, dropped
$PY thirdparty_clean.py $W/tp_cabin_seen.blend $W/tp_cabin_game.blend 0.12
$PY thirdparty_car.py $W/tp_car.blend "$2" $W/tp_exterior.blend "$T"           # badges, paint, glass, plates; the interior's parts out
$PY thirdparty_lod.py $W/tp_exterior.blend $W/tp_ext_near.blend 48000
$PY thirdparty_lod.py $W/tp_exterior.blend $W/tp_ext_far.blend 12000 far
$PY thirdparty_rig.py cabin $W/tp_cabin_game.blend $W/tp_cabin_rig.blend
$PY thirdparty_export.py $W/tp_cabin_rig.blend $O/lc300_interior.glb 1024
$PY thirdparty_rig.py outside $W/tp_ext_near.blend $W/tp_ext_rig.blend
$PY thirdparty_export.py $W/tp_ext_rig.blend $O/lc300_near.glb 512 512
$PY thirdparty_export.py $W/tp_ext_far.blend $O/lc300_far.glb 256 256
