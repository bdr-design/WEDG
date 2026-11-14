#!/bin/bash
# T12 reviewer. usage: commits_check.sh <base> <head>   (in /home/user/wt/t12, read only)
# What the commits add: every file with its type and size; binaries outside the expected places flagged; the code
# searched for network use, image/mesh loading, absolute paths into other folders; GLB generator strings and
# embedded images (must be PNG/JPEG made by the build: compared byte for byte by repro.sh); JPEG pictures' EXIF
# (a camera EXIF would mean a photo, not a render); design/README rows for the canids.
B=$1; H=$2; R=/home/user/wt/t12
echo "--- commits"; git -C $R log --format='%h %s' $B..$H
echo "--- files added/changed"; git -C $R diff --stat=200 $B $H | tail -60
echo "--- binaries and where"
git -C $R diff --name-only --diff-filter=AM $B $H | while read f; do
  t=$(git -C $R show $H:"$f" | file -b - | cut -c1-50); s=$(git -C $R cat-file -s $H:"$f")
  case "$f" in
    assets_src/canids/*.glb|design/canids/*.jpg) ok=expected;;
    *.py|*.md|*.txt|*.json|*.sh|*.dart|*.js|*.html) ok=text;;
    *) ok='!! CHECK';;
  esac
  echo "$ok  $s  $f  ($t)"
done
echo "--- code: network, image/mesh loads, foreign paths"
git -C $R diff $B $H -- 'tool/canid3d/*' | grep -n -E '^\+' | grep -n -i -E 'urllib|requests|http[s]?://|socket|curl|wget|\.(obj|fbx|stl|png|jpe?g|webp|exr|hdr)\b|import_scene|image.load|images.load|/tmp/|/home/' | head -40
echo "--- JPEG EXIF (camera make/model would mean a photograph)"
for f in $(git -C $R diff --name-only --diff-filter=AM $B $H | grep -E '\.jpe?g$'); do
  git -C $R show $H:"$f" > /tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/t12_review/_x.jpg
  python3 -I -c "
from PIL import Image; import sys
im=Image.open(sys.argv[1]); e=im.getexif(); print(sys.argv[2], im.size, {k:v for k,v in e.items() if k in (271,272,305,36867)} or 'no camera EXIF')" /tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/t12_review/_x.jpg "$f"
done
echo "--- design/README rows mentioning canids"
git -C $R show $H:design/README.md 2>/dev/null | grep -n -i -E 'canid|wolf|dog|ذيب|كلب' | head -20
