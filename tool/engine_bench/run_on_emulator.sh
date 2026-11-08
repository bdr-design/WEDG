#!/usr/bin/env bash
# Install a bench APK on the running emulator, start it, wait for BENCH_DONE (at most 8 min),
# then append the BENCH lines and the system's memory and frame reports to the results file.
set -u
APK="$1"; OUT="$2"; LOG="$(dirname "$OUT")/logcat.txt"
PKG=$(aapt dump badging "$APK" 2>/dev/null | sed -n "s/package: name='\([^']*\)'.*/\1/p")
if [ -z "$PKG" ]; then PKG=$(unzip -p "$APK" AndroidManifest.xml >/dev/null 2>&1 && echo ""); fi
adb install -r "$APK"
[ -z "$PKG" ] && PKG=$(adb shell pm list packages | sed -n 's/package://p' | grep -i bench | head -1 | tr -d '\r')
echo "package: $PKG"
adb logcat -c
adb shell monkey -p "$PKG" -c android.intent.category.LAUNCHER 1 >/dev/null
for i in $(seq 1 96); do
  sleep 5
  if adb logcat -d -s flutter | grep -q BENCH_DONE; then break; fi
done
adb logcat -d > "$LOG"
grep -o 'BENCH.*' "$LOG" | tee -a "$OUT"
echo "--- meminfo" | tee -a "$OUT"
adb shell dumpsys meminfo "$PKG" | sed -n '1,40p' | tee -a "$OUT"
echo "--- gfxinfo" | tee -a "$OUT"
adb shell dumpsys gfxinfo "$PKG" | sed -n '1,30p' | tee -a "$OUT"
grep -q BENCH_DONE "$LOG" || { echo "BENCH_DONE never arrived"; grep -iE 'flutter|fatal|exception|impeller|vulkan|egl' "$LOG" | tail -60; }
exit 0
