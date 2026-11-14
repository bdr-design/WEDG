# T10 reviewer: proves each new rule has a test that fails without it (adapted from t3_review/mutate.sh: one copy,
# each file restored after its mutation, the package's own tests run; analyze first so CAUGHT is a failing test).
# usage: mutate.sh <commit> <mutations file>     Each line: <name>~<path in repo>~<python re pattern>~<replacement>
set -u
export PATH=/opt/flutter/bin:/opt/flutter/bin/cache/dart-sdk/bin:$PATH
R=/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/t16_review
C=$1; M=$2; W=$R/mut; OUT=$R/mut_results_$(basename $M .txt).txt; : > $OUT
rm -rf $W; mkdir -p $W
git -C /home/user/WEDG archive $C | tar -x -C $W; cp -r /home/user/WEDG/.dart_tool $W/
while IFS='~' read -r name path pat rep; do
  [ -z "$name" ] && continue; case $name in \#*) continue;; esac
  cp $W/$path $W/$path.orig
  n=$(python3 -I - "$W/$path" "$pat" "$rep" <<'PY'
import re,sys
p,pat,rep=sys.argv[1:4]; s=open(p).read(); t,n=re.subn(pat,rep,s,count=1,flags=re.S); open(p,'w').write(t); print(n)
PY
)
  if [ "$n" != "1" ]; then echo "$name: PATTERN NOT FOUND" | tee -a $OUT; mv $W/$path.orig $W/$path; continue; fi
  case $path in packages/*) T=$W/$(echo $path | cut -d/ -f1-2);; tool/proto_engine/*) T=$W/tool/proto_engine;; *) T=$W/packages/marah_domain;; esac
  e=$(cd $T && dart analyze 2>&1 | grep -c ' error - ')
  if [ "$e" != "0" ]; then echo "$name: DOES NOT COMPILE ($e errors)" | tee -a $OUT; mv $W/$path.orig $W/$path; continue; fi
  # a domain rule is also tested where it is read: domain, then runtime
  v=MISSED; r=''
  for P in $T $( [ "$T" = "$W/packages/marah_domain" ] && echo $W/packages/marah_runtime $W/packages/marah_data ); do
    r=$(cd $P && timeout 900 dart test 2>&1 | tail -1)
    case "$r" in *"All tests passed"*) ;; *) v="CAUGHT in $(basename $P)"; break;; esac
  done
  echo "$name: $v ($r)" | tee -a $OUT
  mv $W/$path.orig $W/$path
done < $M
rm -rf $W
