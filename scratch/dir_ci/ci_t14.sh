set -u
export PATH=/opt/flutter/bin:/opt/flutter/bin/cache/dart-sdk/bin:$PATH
cd /home/user/wt/t14
T=/tmp/claude-0/-home-user-WEDG/d6dbc15a-e910-5754-8d25-3b30bd9632e4/scratchpad/dir_ci/t14
mkdir -p $T
echo "== format"; dart format --output=none --set-exit-if-changed packages apps/marah/lib apps/marah/test tool/proto_engine 2>&1 | tail -2
echo "== analyze"; for d in packages/marah_domain packages/marah_data packages/marah_runtime packages/marah_store tool/proto_engine; do (cd $d && dart analyze --fatal-infos 2>&1 | tail -1); done
echo "== domain node"; (cd packages/marah_domain && dart test -p node 2>&1 | tail -1)
echo "== proto vm,node"; (cd tool/proto_engine && dart test -p vm,node 2>&1 | tail -1)
cd tool/proto_engine
dart compile js -O2 bin/same_seed.dart -o "$T/same_seed.js" >/dev/null 2>&1
node "$T/same_seed.js" > "$T/js.txt"
dart run bin/same_seed.dart > "$T/vm.txt" 2>/dev/null
echo "== same seed diff"; diff <(sed '/--save--/,$d' "$T/vm.txt") <(sed '/--save--/,$d' "$T/js.txt") | head -5; echo "diff rc ${PIPESTATUS[0]}"
vm_end=$(sed '/--save--/,$d' "$T/vm.txt" | grep '^week' | tail -1 | grep -o 'length .*')
js_read=$(dart run bin/read_save.dart "$T/js.txt" 2>/dev/null)
echo "VM: $vm_end / JS: $js_read"; test -n "$vm_end" && test "$vm_end" = "$js_read" && echo SAME
for c in buyListing cancelListing declineOffer listForSale mateWithOwnBull renameCamel setCalfShare setFeedPlan withdrawEntry; do
  grep '^extras' "$T/vm.txt" | grep -Eq "$c [1-9]" || echo "$c never went through"
done
grep '^extras' "$T/vm.txt"
python3 build_worker.py "$T/engine_worker.js" >/dev/null 2>&1
node test_js/worker_smoke.cjs "$T/engine_worker.js" 2>&1 | tail -2
node test_js/engine_page.mjs "$T/engine_worker.js" 2>&1 | tail -2
cd /home/user/wt/t14/packages/marah_domain && echo "== simulate"; dart run marah_domain:simulate 10 4 2>&1 | tail -3
echo CI-DONE
