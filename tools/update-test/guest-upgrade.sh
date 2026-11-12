# Runs inside the test VM: ask for an update the way the daily timer does, show what happened.
echo "== before"; grep -E "^KANTAN_(VERSION|BUILD)" /usr/lib/os-release
echo "== bootc upgrade"
bootc upgrade 2>&1 | tail -12
echo "exit code: ${PIPESTATUS[0]}"
echo "== status after"; bootc status 2>&1 | head -24
