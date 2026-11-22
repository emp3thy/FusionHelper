#!/usr/bin/env bash
# Rebuild one biscuit in its own (already open) Fusion document.
#   bash artifacts/biscuits/pipeline.sh jam|wafer|custard
# Run from the repo root, AFTER make.py + bundle + preflight have passed.
# Stops at the first step that does not report what it should.
set -u
kind="$1"
case "$kind" in
  jam) script=jammie ;;
  wafer) script=wafer ;;
  custard) script=custard ;;
  *) echo "unknown kind $kind"; exit 2 ;;
esac
B=artifacts/biscuits

out=$(python $B/ctl.py activate "$kind"); echo "$out" | tail -1
if ! echo "$out" | grep -q '"ok": true'; then
  # already rolled back by an earlier attempt: accept exactly one empty document
  out=$(python $B/ctl.py activate empty); echo "$out" | tail -1
  echo "$out" | grep -q '"ok": true' || { echo "STOP: could not find the $kind document"; exit 1; }
fi
python $B/ctl.py undoall
out=$(python $B/ctl.py probe); echo "$out" | tail -1
echo "$out" | grep -q '"bodies": \[\], "sketches": 0, "timeline": 0' || { echo "STOP: document not empty"; exit 1; }

python $B/run_fusion.py $B/${script}_author.bundled.py | grep "SUCCESS\|BUILD\|VERDICT\|Error\|rejected" | cut -c1-520
log=$B/${script}_author.bundled.log
grep -q '^SUCCESS=True' "$log" || { echo "STOP: build failed"; exit 1; }
grep -o '"code":"[a-z_.]*"' "$log" | sort | uniq -c
grep 'FH_VERDICT1' "$log" | grep -q '"timeline":"pass","interference":"pass","clearance":"skip","liveness":"pass"' \
  || { echo "STOP: verdict is not timeline/interference/liveness pass"; exit 1; }

python $B/run_fusion.py $B/probe_joints.py >/dev/null
grep "FH_RESULT {" $B/probe_joints.log | cut -c1-420
python $B/run_fusion.py $B/probe_brace.py >/dev/null
grep "FH_RESULT" $B/probe_brace.log | cut -c1-300

python $B/ctl.py paint | grep FH_RESULT
python $B/ctl.py shot $B/${script}_front.png "10, -24, 26" >/dev/null
python $B/ctl.py shot $B/${script}_brace.png "24, -40, 16" >/dev/null
python $B/ctl.py group | grep -o '\["Untitled", "[A-Z][^]]*\]' | grep -v skipped
echo "DONE $kind"
