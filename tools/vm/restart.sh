#!/bin/bash
# Powers the VM off (hard stop if it does not go down within 90 s) and starts it again.
HERE="$(cd "$(dirname "$0")" && pwd)"
PIDF=/root/kantan-out/run/qemu.pid
if [ -f "$PIDF" ] && kill -0 "$(cat $PIDF)" 2>/dev/null; then
    python3 "$HERE/qmp.py" quit || true
    for i in $(seq 1 18); do kill -0 "$(cat $PIDF)" 2>/dev/null || break; sleep 5; done
    kill "$(cat $PIDF)" 2>/dev/null && echo "hard-stopped" || echo "powered off cleanly"
    sleep 3
fi
rm -f /root/kantan-out/run/serial.log
exec bash "$HERE/run-and-hold.sh"
