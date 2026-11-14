#!/bin/bash
SC=/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad
W=/home/user/wt/int16
export PATH=/opt/flutter/bin:/opt/flutter/bin/cache/dart-sdk/bin:$PATH
cd $W
bash $SC/dir_ci/ci_int16.sh; echo "CI-RC $?"
for p in marah_data marah_store; do echo "== pkg $p"; (cd packages/$p && dart test 2>&1 | tail -2); done
echo "== pkg marah_runtime"; (cd packages/marah_runtime && dart test --concurrency=1 2>&1 | tail -2)
echo "== assemble"; THREE_DIR=$SC/three/package python3 tool/proto_app/assemble.py 2>&1 | tail -1
python3 -m http.server 8771 --bind 127.0.0.1 -d tool/proto_app/assets/web >/dev/null 2>&1 & SRV=$!
sleep 2
for c in longpress money_meter type_audit keep_together fonts_start; do echo "== $c"; PORT=8771 NODE_PATH=$(npm root -g) timeout 900 node tool/page_checks/$c.cjs 2>&1 | tail -6; echo "rc $?"; done
kill $SRV
echo ALL-DONE
