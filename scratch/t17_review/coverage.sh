#!/bin/bash
# T11 reviewer: one-sided vs two-sided coverage of every GLB from 6 directions; pixels that only the two-sided render covers = see-through.
D=/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/t17_review; cd $D
for f in /home/user/wt/t17/assets_src/birds/*.glb; do n=$(basename $f .glb)
  read cx cy cz s < <(python3 -I -c "
import sys;sys.path.insert(0,'.');from bird_check import analyse;import numpy as np
js,pr,pt,tx,tm,BV,AV=analyse('$f','zzzz');lo,hi=AV.min(0),AV.max(0);c=(lo+hi)/2;print(*np.round(c,4), round(max(hi-lo)*1000/560,3))")
  for v in side left front back below top; do
    python3 -I swrender.py r4/cov/a.png $v $s $cx $cy $cz $f --w 600 --h 600 >/dev/null
    NOCULL=1 python3 -I swrender.py r4/cov/b.png $v $s $cx $cy $cz $f --w 600 --h 600 >/dev/null
    python3 -I -c "
from PIL import Image;import numpy as np
a=np.asarray(Image.open('r4/cov/a.png')).astype(int);b=np.asarray(Image.open('r4/cov/b.png')).astype(int)
bg=np.array([140,140,140]);A=(np.abs(a-bg).sum(-1)>3);B=(np.abs(b-bg).sum(-1)>3);A[-12:]=B[-12:]=False
x=B&~A;print('$n $v see-through px',int(x.sum()))"
  done
done
